# Kịch bản kiểm tra và demo mốc 1

Thực hiện trên Ubuntu sau khi đã chạy các bước trong README. Dùng dữ liệu giả. Các ô dưới đây là việc cần kiểm tra, **không phải kết quả đã được xác nhận**.

## 1. Dịch vụ, Nginx và giao diện

```bash
cd ~/quan-ly-sinh-vien
sudo docker compose ps
curl -i http://localhost:8080/healthz
curl -I http://localhost:8080/admin/login/
curl -I http://localhost:8080/static/admin/css/base.css
```

- [ ] Bốn dịch vụ `db`, `app`, `nginx`, `phpmyadmin` đang chạy; các dịch vụ có healthcheck đạt `healthy`.
- [ ] `/healthz` trả HTTP 200 và `{"status":"ok"}`, xác nhận ứng dụng truy cập được database.
- [ ] `/admin/login/` trả thành công, có `X-Content-Type-Options: nosniff`, `X-Frame-Options` và `Referrer-Policy` theo cấu hình Nginx.
- [ ] CSS trả HTTP 200; trang đăng nhập trong trình duyệt Ubuntu có giao diện và chữ tiếng Việt hiển thị đúng.
- [ ] Mở `http://localhost:8080` chuyển đến trang quản trị. Khi chưa đăng nhập, không sửa được dữ liệu.

Chụp màn hình trạng thái dịch vụ và trang đăng nhập. Không chụp mật khẩu.

## 2. CRUD và ràng buộc dữ liệu

Đăng nhập website bằng tài khoản từ `createsuperuser`. Tạo bộ dữ liệu tạm riêng để không làm mất dữ liệu mẫu:

| Đối tượng | Dữ liệu gợi ý | Thao tác |
|---|---|---|
| Lớp | Mã `DEMO01`, tên `Lớp demo` | Thêm, xem, đổi tên thành `Lớp demo đã sửa` |
| Sinh viên | Mã `SVDEMO01`, họ tên `Sinh viên thử nghiệm`, lớp `DEMO01`, ngày sinh 15/01/2005, email `demo@example.com` | Thêm, xem, sửa tên; tìm bằng mã và tên, lọc theo lớp |
| Môn học | Mã `MONDEMO01`, tên `Môn thử nghiệm` | Thêm, xem, sửa tên |
| Điểm | Chọn `SVDEMO01` và `MONDEMO01`, điểm `8.5` | Thêm, xem, sửa thành `9` |

- [ ] Các trang thêm, danh sách và sửa hoạt động với cả bốn đối tượng.
- [ ] Nhập điểm `-1` hoặc `11` bị từ chối với thông báo trên biểu mẫu; nhập `0` và `10` hợp lệ.
- [ ] Thêm điểm lần nữa cho cùng sinh viên và môn học bị từ chối; không tạo bản ghi trùng.
- [ ] Thêm lớp, sinh viên hoặc môn học trùng mã bị từ chối.
- [ ] Thử xóa lớp `DEMO01` khi còn sinh viên: hệ thống chặn và giải thích bản ghi đang được tham chiếu.
- [ ] Thử xóa sinh viên hoặc môn học khi còn điểm: hệ thống chặn.

Giữ dữ liệu tạm đến khi kiểm tra phpMyAdmin và khả năng lưu dữ liệu ở mục tiếp theo. Chụp danh sách sinh viên, lớp, điểm và một thông báo kiểm tra dữ liệu.

## 3. MySQL, phpMyAdmin và lưu dữ liệu

Mở `http://localhost:8081` trong Ubuntu. Dùng `MYSQL_USER`/`MYSQL_PASSWORD` từ `.env`, không dùng tài khoản quản trị Django. Chọn database `qlsv` rồi xem bảng dữ liệu sinh viên, lớp và điểm tương ứng.

- [ ] Tìm thấy mã `SVDEMO01`, tên đã sửa và điểm đã sửa trong phpMyAdmin.
- [ ] Trong tab SQL, chạy `SHOW GRANTS FOR CURRENT_USER;`; user ứng dụng có quyền trong database bài làm, không có quyền quản trị toàn máy chủ.

Ghi lại dữ liệu vừa xem rồi chạy:

```bash
sudo docker compose restart
sudo docker compose up -d --wait --wait-timeout 300
```

- [ ] Sau khi dịch vụ sẵn sàng, đăng nhập website và phpMyAdmin vẫn được; sinh viên và điểm vừa tạo vẫn còn.

Kiểm tra thêm khả năng tạo lại container mà giữ named volume:

```bash
sudo docker compose down
sudo docker compose up -d --wait --wait-timeout 300
```

- [ ] Dữ liệu và tài khoản vẫn còn sau `down`/`up`. Không thêm `-v` vào `down`.

Chụp phpMyAdmin có dữ liệu giả và trang sinh viên sau khi chạy lại. Sau đó hoàn thành thao tác xóa: xóa điểm `SVDEMO01`/`MONDEMO01`, xóa sinh viên, xóa môn học và xóa lớp `DEMO01`.

- [ ] Cả bốn thao tác xóa thành công khi không còn bản ghi tham chiếu.
- [ ] phpMyAdmin không còn các bản ghi thử nghiệm đã xóa.

## 4. Kiểm chứng hardening

Chạy từ thư mục dự án:

```bash
sudo docker compose exec app id
stat -c '%a %n' .env
sudo docker inspect "$(sudo docker compose ps -q db)" --format '{{json .HostConfig.PortBindings}}'
sudo docker inspect "$(sudo docker compose ps -q db)" --format '{{json .NetworkSettings.Networks}}'
sudo docker inspect "$(sudo docker compose ps -q app)" --format '{{json .HostConfig.CapDrop}} {{json .HostConfig.SecurityOpt}}'
```

- [ ] UID của `app` khác `0`.
- [ ] Quyền `.env` là `600`.
- [ ] `PortBindings` của database rỗng hoặc `null`, không có host port cho MySQL; `3306/tcp` trong danh sách cổng nội bộ không phải cổng được công bố ra host.
- [ ] Database chỉ nối mạng `data` đã đánh dấu `internal: true` trong `compose.yaml`. Dùng tên mạng in ra từ lệnh inspect để thay `TEN_MANG` trong `sudo docker network inspect TEN_MANG --format '{{.Internal}}'`; kết quả phải ra `true`.
- [ ] Ứng dụng bỏ capabilities theo Compose và có `no-new-privileges`.
- [ ] `.gitignore` loại trừ `.env`; sau khi `git init`, kiểm tra `git check-ignore .env` in đúng tên file.

Chụp kết quả non-root, cấu hình mạng và headers. Không chụp hoặc chia sẻ `.env`. Dự án dùng security headers cho lab localhost; không ghi báo cáo rằng đã triển khai HTTPS hoặc mọi container đều non-root.

## 5. Ghi kết quả để đưa vào báo cáo

| Hạng mục | Trạng thái thực tế | Ảnh/ghi chú lỗi |
|---|---|---|
| Bốn dịch vụ và healthcheck | Chưa kiểm tra | |
| CRUD lớp, sinh viên, môn, điểm | Chưa kiểm tra | |
| Điểm hợp lệ, trùng mã, bảo vệ dữ liệu tham chiếu | Chưa kiểm tra | |
| Nginx, CSS, security headers | Chưa kiểm tra | |
| phpMyAdmin và dữ liệu MySQL | Chưa kiểm tra | |
| Lưu dữ liệu sau restart và down/up | Chưa kiểm tra | |
| Non-root, mạng, quyền database, bí mật | Chưa kiểm tra | |
| Commit 1 | Chưa kiểm tra | |

Thay trạng thái bằng kết quả quan sát và ghi cách tái hiện nếu có lỗi. Không dùng bảng này làm bằng chứng hoàn thành các phần Prometheus/Grafana hoặc Loki/Promtail chưa triển khai.
