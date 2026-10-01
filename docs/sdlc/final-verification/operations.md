# Kiểm tra trước khi nộp bài

Áp dụng cho Đề 2 trên Ubuntu VMware, dự án `~/quan-ly-sinh-vien`, Compose project `qlsv`. Các lệnh dưới đây đọc trạng thái, không thay đổi cấu hình. Dùng Terminal trong Ubuntu; Codex trên Windows chưa có kết nối thực thi vào VM.

## Trạng thái đã quan sát

Ngày 2026-10-02, ảnh người dùng xác nhận ba commit trên `master`:

| Mốc | Commit | Bằng chứng triển khai đã có |
|---|---|---|
| 1 | `2fa2384` | Django/phpMyAdmin đăng nhập được, healthz và security headers, dữ liệu SVDEMO01/điểm 9 còn sau restart |
| 2 | `efb31b9` | Grafana có metrics container, Nginx và MySQL |
| 3 | `e00c2c1` | Loki/Promtail nhận marker mới; ba kết quả LogQL; sau restart có cả marker cũ/mới; healthz HTTP 200 |

Git hiện được xác nhận trên VM; chưa có bằng chứng repository đã lên GitHub. Ảnh Terminal ngày 2026-10-02 xác nhận đủ bốn nhóm hardening và các phép kiểm tra riêng cho `.env`/Git bên dưới.

## Bốn biện pháp hardening

Phóng to Terminal để ảnh minh chứng hiển thị cả lệnh và kết quả. Chạy tại thư mục dự án:

```bash
cd ~/quan-ly-sinh-vien
bash scripts/logging.sh exec -T app id
sudo docker inspect qlsv-app-1 --format 'ReadonlyRootfs={{.HostConfig.ReadonlyRootfs}} CapDrop={{json .HostConfig.CapDrop}} SecurityOpt={{json .HostConfig.SecurityOpt}}'
sudo docker inspect qlsv-db-1 --format 'PortBindings={{json .HostConfig.PortBindings}} Networks={{range $name, $config := .NetworkSettings.Networks}}{{$name}} {{end}}'
sudo docker network inspect qlsv_data --format 'Internal={{.Internal}}'
curl --noproxy '*' -sSI --max-time 10 http://127.0.0.1:8080/healthz
```

| ID | Biện pháp và kết quả mong đợi | Căn cứ cấu hình | Trạng thái runtime |
|---|---|---|---|
| H1 | Ứng dụng non-root: UID/GID 10001, khác 0 | `app/Dockerfile` đặt USER 10001:10001 | Đạt qua ảnh VM: uid=10001(app), gid=10001(app) |
| H2 | Hạn chế quyền ứng dụng: ReadonlyRootfs=true, CapDrop có ALL, SecurityOpt có no-new-privileges | `compose.yaml` service app | Đạt qua ảnh VM: true, ["ALL"], ["no-new-privileges:true"] |
| H3 | Cô lập MySQL: PortBindings rỗng `{}` hoặc `null`, chỉ mạng qlsv_data; mạng có Internal=true | `compose.yaml` service db và network data | Đạt qua ảnh VM: PortBindings={}, Networks=qlsv_data, Internal=true |
| H4 | Security headers: HTTP 200, X-Content-Type-Options nosniff, X-Frame-Options DENY, Referrer-Policy same-origin và Permissions-Policy | `nginx/default.conf` | Đạt qua ảnh mới: HTTP 200 và đủ các header nêu trên |

H2 gồm nhiều hạn chế bổ trợ nhưng tính là một nhóm biện pháp. Root filesystem chỉ đọc không có nghĩa mọi nơi đều không ghi được: `/tmp` và volume static có thể ghi theo cấu hình. H3 không có nghĩa MySQL chặn mọi container cùng mạng; app, phpMyAdmin và exporter được nối để làm việc.

Chỉ khẳng định `app` non-root từ H1. cAdvisor có `privileged: true` để thu metrics host; Promtail chạy root để đọc file log Docker. Bộ triển khai không có cam kết mọi container đều non-root hoặc không đặc quyền. Website dùng HTTP localhost với security headers theo lựa chọn đề cho phép, chưa có HTTPS.

Nếu lệnh trả khác kỳ vọng, giữ kết quả để chẩn đoán; không xóa volume hoặc tạo lại `.env`.

## Bảo vệ cấu hình trước khi đưa lên GitHub

```bash
stat -c '%a %n' .env
git check-ignore -v .env
git ls-files -- .env
git log --all --oneline -- .env
```

Kỳ vọng: quyền `600`; có quy tắc `.gitignore` khớp; hai lệnh cuối không có output. Không chụp nội dung `.env`. Các phép kiểm tra này chỉ chứng minh quyền file và tình trạng theo dõi đường dẫn `.env`, không tự chứng minh mật khẩu mạnh hoặc mọi file trong repository đều không có bí mật. Source tạo mật khẩu ngẫu nhiên bằng script, không lưu mật khẩu mặc định.

Ảnh ngày 2026-10-02 đã xác nhận `600 .env`, quy tắc `.gitignore` khớp `.env`; `git ls-files -- .env` và `git log --all --oneline -- .env` không có output. `git status --short` chỉ hiển thị `?? plan.md`: file kế hoạch chưa được theo dõi, không có thay đổi được báo ở các file đã commit. Có thể giữ file kế hoạch ngoài Git; điều này không ngăn push các commit đã có.

Trước khi push cần kiểm tra thêm các ảnh, file backup và tài liệu có chứa mật khẩu hay không. Một ảnh đã gửi trước đây có thông tin đăng nhập Grafana; dùng ảnh đã che/cắt phần đó trong báo cáo. Chưa thực hiện push hay tạo repository từ workspace Windows.

## Kiểm tra chức năng còn lại

- Mở lại danh sách sinh viên và phpMyAdmin, xác nhận dữ liệu cũ còn nguyên sau nâng cấp.
- Mở dashboard QLSV, chọn khoảng thời gian hiện tại, xác nhận CPU/RAM/Nginx/MySQL vẫn có dữ liệu mới.
- Trên dữ liệu giả, minh chứng thêm/sửa/xóa và ràng buộc điểm 0–10, không trùng sinh viên–môn học, không xóa bản ghi đang được tham chiếu. Kịch bản chi tiết ở [demo mốc 1](../moc-1/demo.md).
- Dùng ba ảnh LogQL và kết quả restart đã có; không cần tái triển khai chỉ để chụp lại.

## GitHub và báo cáo

PDF trang 1–2 yêu cầu tài khoản GitHub đặt theo MSSV, repository có source/config/README và ba commit có ý nghĩa; báo cáo ít nhất 10 trang, bìa có thông tin sinh viên và chủ đề, mô tả kiến trúc/cách hoạt động/kết quả có ảnh. Đã có ba commit local, còn cần bằng chứng repo trên GitHub.

Sinh viên **Lâm Duy Lập — DTC245200028** đã đăng nhập GitHub CLI và thiết lập xác thực Git trên Ubuntu. Ảnh Terminal ngày 02/10/2026 sau đổi tên xác nhận `gh api user --jq .login` trả về **`DTC245200028`**, trùng MSSV theo yêu cầu đề. Chưa có bằng chứng tạo/push repository. Xem [hướng dẫn GitHub](../../github-guide.md) và [dàn ý báo cáo](../../report-outline.md). Không suy ra đã nộp bài từ việc có mã nguồn hoặc commit trên VM. Báo cáo chỉ ghi các kết quả đã được kiểm chứng.
