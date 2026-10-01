# Kết quả chuẩn bị mốc 1

Ngày: 2026-10-01. Bộ source được chuẩn bị trên Windows; chưa triển khai container trên Ubuntu của người dùng.

## Thay đổi
- app/: Django 5.2.17, Gunicorn 26.2.0, mysqlclient 2.3.0; admin tiếng Việt quản lý lớp/sinh viên/môn/điểm, migration đầu tiên, seed và tests.
- compose.yaml, nginx/, app/Dockerfile: bốn dịch vụ với healthchecks, named volumes, log rotation, giới hạn RAM và hardening nền. HTTP localhost với security headers theo lựa chọn PDF.
- scripts/init_env.py: sinh thông tin bí mật một lần; .env bị loại khỏi Git và gói bàn giao.
- README.md và demo.md: hướng dẫn Ubuntu, chạy, xử lý lỗi, giữ dữ liệu, kiểm chứng và commit 1.

## Bằng chứng đã chạy
Python 3.12 trong .venv riêng; thư viện lấy từ PyPI. Lệnh dưới đây chạy từ app/ với interpreter .venv (Windows dùng đường dẫn tương ứng):

| Kiểm tra | Kết quả |
| --- | --- |
| python manage.py test --settings=config.test_settings --verbosity 2 | 16/16 đạt trên SQLite, gồm admin CRUD/quyền, ràng buộc điểm/mã/FK, seed và health |
| python manage.py check --settings=config.test_settings | 0 issues |
| python manage.py makemigrations --check --dry-run --settings=config.test_settings | No changes detected |
| python -X utf8 manage.py collectstatic --noinput --settings=config.test_settings | Thành công; 127 file static, có admin/css/base.css |
| Production config.settings + Django setup + check --deploy (biến môi trường giả chỉ cho kiểm tra) | Không có lỗi; 4 cảnh báo HTTPS W004/W008/W012/W016 phù hợp lab HTTP localhost; không bỏ qua bằng cách silence |
| PyYAML safe_load compose.yaml | Đọc được 4 dịch vụ db/app/nginx/phpmyadmin |
| bash -n app/entrypoint.sh | Exit 0; tệp dùng LF |
| Chạy init_env.py hai lần trong thư mục tạm | Mật khẩu ngẫu nhiên khác nhau, khóa đủ độ dài, lần hai giữ nguyên file; không in bí mật |

Lần thử collectstatic đầu trên Windows vướng console cp1252 khi in đường dẫn tiếng Việt; chạy lại với -X utf8 thành công. Đây là lỗi môi trường kiểm tra, không sửa app vì lỗi này. Check production chạy qua Python API cần django.setup() trước call_command; lần chạy đúng sau đó trả các cảnh báo HTTPS ở trên.

## Chưa đủ bằng chứng
- Chưa chạy docker compose config/build/up vì máy Codex không có Docker/WSL. Parse YAML không tương đương kiểm chứng Compose runtime.
- Chưa chạy migration/test trên MySQL thật, kiểm tra named volume/static permissions, Nginx headers hoặc phpMyAdmin trong container. Phải làm trên Ubuntu theo demo.md.
- Chưa tạo GitHub repository/commit, chưa monitoring/logging, chưa báo cáo hoặc screenshot.
- Không coi 16 tests SQLite là bằng chứng hệ thống MySQL đã hoạt động.

## Phục hồi và bước tiếp theo
Giữ .env cùng mysql_data; down không kèm -v. Chuyển ZIP vào Ubuntu, tạo .env, chạy Compose với --wait, tạo superuser và seed, kiểm tra theo demo.md. Nếu lỗi, lấy ps -a và logs giới hạn, không gửi .env. Chỉ tạo commit 1 sau khi demo đạt.
