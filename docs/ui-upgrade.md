# Nâng cấp giao diện quản lý sinh viên

Gói `quan-ly-sinh-vien-giao-dien-moi.zip` cập nhật giao diện Django Admin: trang tổng quan, điều hướng, đăng nhập, danh sách và biểu mẫu. Giữ tài khoản đăng nhập, các đường dẫn `/admin/`, dữ liệu MySQL và các quy tắc điểm số hiện có.

Hướng dẫn này dành cho Ubuntu VM đang chạy đủ ba mốc trong `~/quan-ly-sinh-vien`. Mã và lệnh được đối chiếu trên Windows; việc dựng container và kiểm tra giao diện mới trên VM **chưa được thực hiện bởi Codex**.

## 1. Áp dụng gói và tạo bản sao trước khi thay đổi

Đặt ZIP vào thư mục Windows đang chia sẻ với Ubuntu tại `/mnt/hgfs/baithuchanh`. Chạy khối sau trong Terminal Ubuntu:

```bash
cd ~/quan-ly-sinh-vien
bash scripts/logging.sh ps app db nginx
unzip -p /mnt/hgfs/baithuchanh/quan-ly-sinh-vien-giao-dien-moi.zip scripts/ui_upgrade.py > /tmp/qlsv-ui-upgrade.py && python3 /tmp/qlsv-ui-upgrade.py apply /mnt/hgfs/baithuchanh/quan-ly-sinh-vien-giao-dien-moi.zip
```

Ba dịch vụ cần đang chạy trước khi dựng lại riêng `app`. Khi áp dụng thành công, công cụ in `Backup: .../tmp/ui-backups/...` và `Applied ... UI files`. Ghi lại đường dẫn backup. Nếu có `ERROR`, dừng tại đây và đọc thông báo; chưa chạy lệnh dựng lại.

`ui_upgrade.py` chỉ chấp nhận danh sách file giao diện cố định và tài liệu/công cụ đi kèm. Trước khi chép, nó lưu nội dung cũ của các file sẽ thay đổi, ghi nhận file nào chưa tồn tại và mã SHA-256. Nó từ chối đường dẫn ngoài dự án, đường dẫn liên kết và file ZIP ngoài danh sách. Backup nằm trong `tmp/ui-backups`, thuộc thư mục đã được Git bỏ qua. Không đưa backup lên GitHub.

## 2. Dựng lại riêng ứng dụng

```bash
bash scripts/logging.sh up -d --build --no-deps --wait --wait-timeout 180 app
curl --noproxy '*' -fsS --max-time 10 --retry 4 --retry-delay 3 --retry-connrefused -w '\nHTTP %{http_code}\n' http://127.0.0.1:8080/healthz
```

Lệnh đầu đợi healthcheck của `app`; kết quả mong đợi của lệnh thứ hai là `{"status": "ok"}` và `HTTP 200`. Cần cả hai kết quả trước khi kiểm tra giao diện. `--no-deps` giữ các container cơ sở dữ liệu, Nginx và giám sát đang chạy. Website có thể gián đoạn ngắn khi container `app` được thay thế.

Entrypoint hiện có chạy `migrate --noinput`, rồi `collectstatic --noinput` trước Gunicorn. Gói giao diện không thêm migration; bước collectstatic chép CSS/JS mới vào volume `static_data` dùng chung với Nginx. Không cần dựng lại Nginx hoặc xoá volume. Không chạy `down -v`, không tạo lại `.env` và không chạy lại dữ liệu mẫu.

Mở [website trong Ubuntu](http://127.0.0.1:8080/admin/), nhấn **Ctrl + Shift + R** để tải lại CSS/JS và đăng nhập bằng tài khoản đang dùng.

## 3. Kiểm tra sau nâng cấp

| Nội dung | Kết quả cần quan sát |
| --- | --- |
| Đăng nhập | Tài khoản cũ đăng nhập được; trang đăng nhập hiển thị rõ nhãn và lỗi khi thông tin không hợp lệ. |
| Tổng quan | Số liệu lấy từ dữ liệu hiện có; liên kết dẫn tới danh sách tương ứng. Không coi số liệu tổng quan là phép đo sức khoẻ dịch vụ. |
| Danh sách | Mở Sinh viên, Lớp học, Môn học, Điểm số; thử tìm kiếm, bộ lọc và phân trang khi có đủ bản ghi. |
| Dữ liệu cũ | `SVDEMO01` / `MONDEMO01` vẫn có điểm `9`; giữ nguyên bộ dữ liệu này. |
| Biểu mẫu | Mở sửa một bản ghi rồi quay lại mà không lưu; kiểm tra nhãn, trường ngày, chọn lớp, autocomplete sinh viên/môn và các nút thao tác. |
| Quyền | Với tài khoản nhân viên đã có quyền hạn chế, chỉ thấy chức năng được phép; tài khoản chưa đăng nhập được chuyển về đăng nhập. Không cấp thêm quyền chỉ để kiểm tra giao diện. |
| Màn hình hẹp | Thu cửa sổ hoặc dùng chế độ điện thoại của trình duyệt; điều hướng mở/đóng được, bảng cuộn ngang khi cần, nút lưu vẫn dùng được. |
| Bàn phím | Dùng Tab để tới menu, tìm kiếm và các nút; vị trí đang được chọn hiển thị rõ. |

Các ràng buộc điểm `0–10`, không trùng cặp sinh viên/môn và bảo vệ bản ghi có liên kết vẫn thuộc backend hiện có. Nếu cần kiểm thử thao tác ghi trên VM, dùng bản ghi kiểm thử riêng; không sửa hoặc xoá `SVDEMO01` để kiểm tra giao diện.

Nếu `app` không healthy hoặc website báo lỗi:

```bash
bash scripts/logging.sh ps app db nginx
bash scripts/logging.sh logs --tail=60 app
```

Không gửi thông tin đăng nhập hoặc toàn bộ `.env` khi chia sẻ lỗi. HTTP 200 của `/healthz` chỉ xác nhận ứng dụng kết nối được cơ sở dữ liệu tại thời điểm kiểm tra; không thay thế kiểm tra danh sách và biểu mẫu.

## 4. Quay lại giao diện trước nâng cấp

Dùng khi bản mới không khởi động, thiếu CSS/JS sau khi tải lại mạnh, hoặc phát hiện chức năng quản lý bị lỗi. Công cụ khôi phục các file cũ đã lưu và chỉ xoá những file giao diện được gói thêm mới. Nó không đụng tới MySQL, `.env`, migration, dữ liệu mẫu hoặc các file ngoài danh sách.

Với bản backup mới nhất:

```bash
cd ~/quan-ly-sinh-vien
python3 /tmp/qlsv-ui-upgrade.py rollback
bash scripts/logging.sh up -d --build --no-deps --wait --wait-timeout 180 app
curl --noproxy '*' -fsS --max-time 10 --retry 4 --retry-delay 3 --retry-connrefused -w '\nHTTP %{http_code}\n' http://127.0.0.1:8080/healthz
```

Nếu đã khởi động lại Ubuntu và file `/tmp/qlsv-ui-upgrade.py` không còn, chạy lại phần `unzip -p ... > /tmp/qlsv-ui-upgrade.py` ở bước 1 để lấy công cụ; **không chạy `apply` lần nữa** trước rollback. Có thể chọn một bản backup cụ thể bằng `python3 /tmp/qlsv-ui-upgrade.py rollback TEN_THU_MUC_BACKUP`, trong đó tên lấy từ đường dẫn công cụ đã in.

Chỉ dựng lại sau khi công cụ báo `Restored source ...`. Nếu có thông báo `File changed after upgrade`, dừng để giữ lại thay đổi mới; công cụ chủ động từ chối ghi đè file đã sửa sau nâng cấp. Backup đã khôi phục sẽ được đánh dấu, không khôi phục lặp lại cùng bản.

CSS/JS mới có thể còn trong volume static sau rollback, nhưng template cũ không gọi chúng. Không cần xoá `static_data`. Tải lại mạnh trang và xác nhận giao diện cũ cùng dữ liệu trước khi tiếp tục.

## 5. Lưu thay đổi đã kiểm tra lên GitHub

Chỉ thực hiện sau khi bản mới chạy đúng trên VM:

```bash
git add app/config/settings.py app/students/admin.py app/students/apps.py app/students/admin_site.py app/students/test_admin_ui.py app/templates/admin app/students/static/students docs/ui-upgrade.md scripts/ui_upgrade.py
git diff --cached --stat
git diff --cached --check
git commit -m "feat: nang cap giao dien quan ly sinh vien"
git push
```

Xem danh sách đã thêm trước khi commit; không thêm `.env`, backup hoặc file trong `tmp`. Báo cáo PDF và ảnh minh chứng cũ mô tả giao diện trước nâng cấp; chỉ bổ sung ảnh mới sau khi kiểm tra thực tế, không ghi nhận trạng thái VM mới từ bản xem trước local.

## Kiểm chứng công cụ áp dụng gói

Giao diện dùng CSS/JS phục vụ tại chỗ, không thêm thư viện hoặc dịch vụ mạng ngoài. Màu nền sáng, xanh ngọc; menu theo quyền, số liệu tổng quan từ database, biểu mẫu và xác nhận xóa tiếp tục do Django xử lý. Không sửa model hoặc migration.

Kiểm chứng giao diện local ngày 11/10/2026: 29 bài kiểm thử Django đạt (13 bài mới về dashboard/quyền/đăng nhập, 16 bài có sẵn); kiểm tra migration không phát sinh thay đổi; collectstatic tìm thấy hai asset CSS/JS mới. Trình duyệt Chromium kiểm tra đăng nhập/đăng xuất có CSRF, ẩn/hiện mật khẩu, menu điện thoại, tìm kiếm, autocomplete và lưu điểm hợp lệ/chặn điểm 11. Các màn hình kiểm tra ở độ rộng 1440, 1024 và 390 px không làm tràn ngang toàn trang; bảng dài cuộn trong vùng riêng. Đã sửa lỗi co hẹp header, cắt ô nhập trên điện thoại và độ tương phản viền điều khiển sau rà soát ảnh.

Do môi trường chặn kết nối localhost, trình duyệt kiểm tra bằng phản hồi trực tiếp qua Django test client với middleware/CSRF và SQLite riêng. Redirect được mô phỏng trong bộ kiểm tra; các kết quả này không thay thế kiểm tra HTTP qua Nginx/MySQL trên Ubuntu. Ảnh trong `output/ui-preview` là bản xem trước local, không phải minh chứng triển khai VM. Bộ dò CSS chỉ chạy được chế độ regex; đánh giá bố cục dựa thêm trên ảnh và thao tác trình duyệt.

Ngày 11/10/2026, công cụ được chạy trên các thư mục dự án giả lập trong `tmp` của Windows: 10 kiểm tra đạt, gồm áp dụng đủ 14 file, giữ nguyên file ngoài phạm vi, khôi phục nội dung cũ, xoá đúng file mới, chặn rollback lặp, chặn file `.env`/đường dẫn vượt thư mục/file trùng/liên kết trong ZIP, và từ chối rollback khi file nguồn đã bị sửa hoặc backup sai checksum. Python đã được kiểm tra cú pháp. Các kết quả này kiểm chứng thao tác file local; chưa xác nhận việc dựng Docker hoặc chạy giao diện trên Ubuntu VM.
