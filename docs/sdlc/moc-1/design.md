# Thiết kế mốc 1

## Căn cứ và hiện trạng
Xem intent.md. Đây là cấu trúc mới được đề xuất, chưa phải hệ thống đã chạy trên VM. Framework Django nằm trong danh sách gợi ý của đề; MySQL và phpMyAdmin là yêu cầu riêng Đề 2.

## Luồng và giao diện
Trình duyệt bên trong Ubuntu -> 127.0.0.1:8080 Nginx -> app:8000 Gunicorn/Django -> db:3306 MySQL. Nginx phục vụ static từ volume chỉ đọc; app collectstatic khi khởi động. / chuyển tới /admin/; /healthz kiểm tra truy vấn DB và trả mã 200 hoặc 503. phpMyAdmin riêng tại 127.0.0.1:8081 kết nối cùng db.

Django Admin dành cho người quản lý có đăng nhập. Lớp có mã/tên; sinh viên có mã/họ tên/ngày sinh/email/lớp; môn có mã/tên; điểm gắn sinh viên+môn, thang 0–10. Mã và cặp sinh viên/môn duy nhất. Khóa ngoại PROTECT ngăn xóa dữ liệu đang được tham chiếu; người dùng xóa điểm trước khi xóa sinh viên/môn. Chưa có học kỳ vì đề chưa quy định. Dữ liệu demo hoàn toàn giả, chạy seed lại không ghi đè nội dung đã chỉnh.

## Triển khai và quyền
- Compose chờ MySQL healthy trước app và app healthy trước Nginx; health DB dùng tài khoản ứng dụng, không chỉ kiểm tra tiến trình.
- MySQL chỉ trên network data internal, không publish 3306. Nginx chỉ vào edge; app là thành phần nối hai mạng. phpMyAdmin vào data và publish loopback.
- App UID/GID 10001, read-only root filesystem, tmpfs, cap_drop ALL, no-new-privileges. Không tuyên bố toàn bộ image vendor chạy non-root.
- .env tạo một lần bằng secrets, quyền 0600 trên Ubuntu; app không nhận mật khẩu root. Tài khoản MySQL chỉ được quyền database qlsv theo official image; cần DDL cho Django migrations.
- HTTP chỉ trên localhost của VM; chọn security headers theo lựa chọn đề cho phép. HTTPS/cookies secure là bước khác nếu mở truy cập ngoài máy. Không tắt CSRF.
- Một Gunicorn worker; hạn mức bộ nhớ từng container và log rotation để phù hợp lab nhỏ. Named volume giữ DB qua restart/down.

## Ảnh hưởng và phục hồi
Migration đầu tiên tạo bảng mới; không chạy migration trên dữ liệu của dự án khác. Mật khẩu trong .env phải giữ cùng mysql_data; sửa .env không tự đổi user trong DB đã khởi tạo. docker compose down dừng dịch vụ, giữ dữ liệu. Chưa có chuyển đổi dữ liệu tồn tại.

## Ma trận nghiệm thu
| ID | Quyết định/điểm sửa | Tiêu chí | Kiểm chứng |
| --- | --- | --- | --- |
| R1 CRUD | app/students và MySQL | CRUD có login, lưu đúng dữ liệu | Django tests + demo thật và phpMyAdmin |
| R2 Compose/DB tool | compose.yaml | 4 dịch vụ hoạt động, DB bền vững | Compose ps, health, restart, query DB trên Ubuntu |
| R3 Nginx | nginx/default.conf | Web và static qua proxy, security headers | curl health/static/headers + trình duyệt VM |
| R4 GitHub | README, .gitignore | Source/cấu hình/README sẵn commit 1, không secrets | Kiểm tra ZIP/Git diff; người dùng tạo commit sau demo |
| R5 hardening nền | Dockerfile, networks, env | app non-root, DB cô lập, secrets riêng | config review + docker exec id/inspect trên VM |

## Giới hạn kiểm chứng
Kiểm thử SQLite cục bộ không thay cho MySQL/container thật. Không có Docker/WSL trong workspace của Codex; mọi bằng chứng VM phải ghi riêng sau khi người dùng chạy.
