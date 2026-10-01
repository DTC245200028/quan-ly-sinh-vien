# Đề tài 2 — Hệ thống quản lý sinh viên

| Thông tin | Nội dung |
|---|---|
| Sinh viên | Lâm Duy Lập |
| MSSV | DTC245200028 |
| Tài khoản GitHub đã xác nhận | `DTC245200028` |
| Học phần | Triển khai và quản trị hệ thống phần mềm |
| Đề tài | Hệ thống quản lý sinh viên |

Website Django quản lý lớp, sinh viên, môn học và điểm trên MySQL. Toàn bộ hệ thống gồm 11 dịch vụ Docker Compose: ứng dụng, database, quản trị database, reverse proxy, giám sát và thu log tập trung.

## 1. Trạng thái và bằng chứng

Các kết quả dưới đây dựa trên ảnh, output và xác nhận từ máy Ubuntu VMware của sinh viên:

| Phần | Bằng chứng đã có |
|---|---|
| Website và database | Đăng nhập Django/phpMyAdmin, giao diện có CSS, `/healthz` trả HTTP 200, dữ liệu sinh viên và điểm còn sau restart |
| Giám sát | Bốn target thu thập thành công; CPU/RAM container, Nginx và MySQL có số liệu; `nginx_up` và `mysql_up` thành công |
| Log | Script tìm thấy request thử nghiệm mới trong Loki; ba truy vấn LogQL có kết quả; giữ log cũ và nhận log mới sau restart Loki/Promtail |
| Hardening | Bốn nhóm kiểm tra đạt: app non-root, hạn chế quyền app, database không publish cổng/mạng nội bộ, security headers |
| File bí mật | `.env` quyền `600`, được Git bỏ qua; kiểm tra file đang theo dõi và lịch sử Git không thấy `.env` |

Ba commit theo mốc đã được xác nhận trên nhánh `master` của VM:

| Commit | Nội dung |
|---|---|
| `2fa2384` | Website CRUD, MySQL, phpMyAdmin, Nginx |
| `efb31b9` | Prometheus, Grafana và giám sát |
| `e00c2c1` | Loki, Promtail và truy vấn LogQL |

Chi tiết: [minh chứng mốc 1](docs/sdlc/moc-1/runtime-evidence.md), [mốc 2](docs/sdlc/moc-2/runtime-evidence.md), [mốc 3](docs/sdlc/moc-3/runtime-evidence.md), [kiểm tra cuối](docs/sdlc/final-verification/operations.md). Các mục có ngày ghi nhận sau cập nhật trạng thái của các mục trước.

Chưa xác nhận push repository lên GitHub hoặc hoàn thành báo cáo. Một số ca xóa/validation CRUD và kiểm tra lại đầy đủ dashboard sau nâng cấp còn cần bổ sung bằng chứng; không suy ra các ca này đã đạt chỉ từ healthcheck.

## 2. Kiến trúc và chức năng

```text
Trình duyệt trong Ubuntu
 ├─ :8080 → Nginx → Django/Gunicorn → MySQL
 ├─ :8081 → phpMyAdmin ─────────────→ MySQL
 ├─ :9090 → Prometheus ← cAdvisor / Nginx exporter / MySQL exporter
 └─ :3000 → Grafana → Prometheus và Loki
                         Loki ← Promtail ← Docker JSON logs của dự án qlsv
```

| Nhóm | Dịch vụ Compose |
|---|---|
| Website và database | `app`, `db`, `nginx`, `phpmyadmin` |
| Giám sát | `prometheus`, `grafana`, `cadvisor`, `nginx-exporter`, `mysql-exporter` |
| Log | `loki`, `promtail` |

Website dùng Django 5.2 Admin tiếng Việt, MySQL 8.4 và có CRUD lớp, sinh viên, môn học, điểm. Có tìm kiếm sinh viên theo mã/tên và lọc theo lớp; mỗi cặp sinh viên–môn học có một điểm từ 0 đến 10. Các bản ghi đang được tham chiếu được bảo vệ khi xóa. Chưa có học kỳ, lần thi hoặc cổng riêng cho sinh viên.

Mạng `data` là mạng nội bộ của database; MySQL không publish cổng ra host. Các cổng web, phpMyAdmin, Grafana, Prometheus và Loki chỉ bind `127.0.0.1`. Nginx dùng security headers theo lựa chọn của đề; bài lab chưa triển khai HTTPS hoặc công bố ra Internet.

## 3. Cài mới từ repository đã clone

Mở Terminal **trong thư mục repository đã clone**, nơi có `compose.yaml`, `app/`, `scripts/` và `README.md`. Chạy lần lượt ba bước dưới đây; khi một lệnh lỗi, xem thông báo trước khi chuyển sang bước tiếp theo.

Cần Docker Engine, Docker Compose, Python 3, Git và curl. Môi trường đã dùng: Ubuntu 26.04.1 trên VMware, Docker 29.1.3, Compose 2.40.3, 4 CPU và RAM khoảng 3,3 GiB. Ảnh sau mốc 3 cho thấy khoảng 1,3 GiB RAM `available`; đây là số đo tại một thời điểm. Có thể tăng RAM lên 8 GB nếu máy thật cho phép để demo thuận tiện hơn. Kiểm tra dung lượng bằng `df -h /` trước khi tải image.

Nếu đang dùng VM đã triển khai xong, chuyển đến mục vận hành; không tạo lại `.env`, tài khoản hoặc database. Không cần cài Django/MySQL trực tiếp lên Ubuntu vì các thành phần chạy trong container.

### Bước A — Website và database

```bash
python3 scripts/init_env.py
sudo docker compose config --quiet
sudo docker compose up -d --build --wait --wait-timeout 300
sudo docker compose exec app python manage.py createsuperuser
sudo docker compose exec app python manage.py seed_demo
sudo docker compose ps
```

Script tạo `.env` với bí mật ngẫu nhiên và quyền `600`, từ chối ghi đè file đã tồn tại. Không sao chép `.env.example` thành file mật khẩu thật. Khi nhập mật khẩu cho `createsuperuser`, Terminal không hiện ký tự; tài khoản này dùng để đăng nhập website.

Ứng dụng tự chạy migrations và thu static files khi khởi động. Với database mới, `seed_demo` tạo 2 lớp, 3 môn, 6 sinh viên và 18 điểm giả; chạy lại chỉ bổ sung bản ghi thiếu, không ghi đè dữ liệu đã sửa.

### Bước B — Prometheus và Grafana

```bash
python3 scripts/init_monitoring.py
bash scripts/setup_monitoring.sh
bash scripts/monitoring.sh config --quiet
bash scripts/monitoring.sh up -d --wait --wait-timeout 300
bash scripts/monitoring.sh ps
```

Script bổ sung các biến giám sát còn thiếu, giữ nguyên bí mật cũ. Script thiết lập tạo user `qlsv_exporter` trong MySQL đang chạy, chỉ cấp quyền metadata phục vụ các collector đã chọn và tối đa 3 kết nối; không cấp quyền đọc/sửa bảng sinh viên.

Mở [Prometheus Targets](http://localhost:9090/targets), kiểm tra bốn job `prometheus`, `cadvisor`, `nginx`, `mysql`. Ngoài `up=1`, cần có `nginx_up=1`, `mysql_up=1` và số liệu CPU/RAM container. [Dashboard Grafana](http://localhost:3000/d/qlsv-overview) được nạp sẵn; chờ khoảng 2 phút để biểu đồ tốc độ có đủ mẫu.

### Bước C — Loki và Promtail

```bash
python3 scripts/prepare_logging.py
bash scripts/logging.sh config --quiet
bash scripts/logging.sh up -d --wait --wait-timeout 300
python3 scripts/check_logging.py
bash scripts/logging.sh ps
```

Script tự tìm thư mục Docker JSON logs và thêm `DOCKER_LOG_DIR` vào `.env`, giữ nguyên các giá trị đã có. Compose tạo lại các container để bổ sung nhãn log, giữ named volumes; website có thể gián đoạn ngắn.

`check_logging.py` tạo request HTTP 404 có mã riêng, rồi tìm chính dòng log mới đó trong Loki. Kết quả cần có `PASS`; trạng thái container `Up` chưa đủ chứng minh thu log thành công. Loki và Promtail không cấu hình Docker healthcheck.

Trong Grafana **Explore**, chọn **Loki QLSV**, **Code**, **Last 15 minutes**, rồi chạy ba LogQL do script in ra. Ví dụ:

```logql
{project="qlsv",service="nginx"}
```

```logql
{project="qlsv",service="nginx"} |= "moc3-demo-404"
```

```logql
sum by (service) (count_over_time({project="qlsv"}[5m]))
```

Promtail đã hết hỗ trợ từ ngày 02/03/2026; bài thực hành vẫn dùng Promtail theo yêu cầu PDF. [Thông báo của Grafana](https://grafana.com/docs/loki/latest/send-data/promtail/).

## 4. Truy cập và tài khoản

Mở trình duyệt **bên trong Ubuntu**. `localhost` trong trình duyệt Windows là máy Windows, không phải máy ảo.

| Địa chỉ | Tài khoản/cách dùng |
|---|---|
| [Website](http://localhost:8080) | Tài khoản tạo bằng `createsuperuser`; chuyển đến `/admin/` |
| [phpMyAdmin](http://localhost:8081) | `MYSQL_USER` và `MYSQL_PASSWORD` trong `.env`; database `qlsv`, server `db` |
| [Grafana](http://localhost:3000) | `GRAFANA_ADMIN_USER` và `GRAFANA_ADMIN_PASSWORD` trong `.env` |
| [Prometheus](http://localhost:9090) | Xem Targets và chạy PromQL |
| [Health ứng dụng](http://localhost:8080/healthz) | HTTP 200 và `{"status":"ok"}` khi truy cập database được |
| [Loki readiness](http://localhost:3100/ready) | HTTP 200 khi Loki sẵn sàng; tiếp tục dùng script để kiểm tra log thật |

Đọc `.env` bằng trình soạn thảo tại Ubuntu; trong Files, `Ctrl+H` hiện file ẩn. Không gửi nội dung hoặc ảnh có mật khẩu lên chat, báo cáo hay GitHub. Tài khoản Django, MySQL và Grafana là các tài khoản riêng; không dùng MySQL `root` để demo phpMyAdmin.

Giữ nguyên `.env` cùng các volume. Đổi mật khẩu trong `.env` không tự đổi mật khẩu MySQL/Grafana đã lưu khi khởi tạo volume trước đó.

## 5. Vận hành đủ 11 dịch vụ

Sau bước C, luôn dùng `bash scripts/logging.sh ...`. Wrapper tự dùng `sudo` và ghép `compose.yaml`, `compose.monitoring.yaml`, `compose.logging.yaml`; lệnh `sudo docker compose` một file chỉ quản lý mốc 1.

```bash
# Xem trạng thái và log gần nhất
bash scripts/logging.sh ps -a
bash scripts/logging.sh logs --tail=80 app nginx loki promtail

# Tạm dừng toàn hệ thống, giữ dữ liệu
bash scripts/logging.sh stop

# Chạy lại và kiểm tra luồng log
bash scripts/logging.sh up -d --wait --wait-timeout 300
python3 scripts/check_logging.py
```

Nếu chỉ cần giảm tải phần log, dùng `bash scripts/logging.sh stop promtail loki`. Chạy `up` như trên để bật lại. Named volumes lưu database, static files, Prometheus, Grafana, Loki và vị trí đọc log của Promtail.

`bash scripts/logging.sh down` gỡ container/mạng nhưng giữ named volumes. **Không thêm `-v`** khi muốn giữ dữ liệu. Không xóa volume hay tạo lại `.env` để sửa lỗi đăng nhập. [Tài liệu Docker Compose về `down`](https://docs.docker.com/reference/cli/docker/compose/down/).

## 6. Hardening và xử lý lỗi

Bốn nhóm hardening đã có output kiểm chứng trên VM:

| Nhóm | Kết quả đã quan sát |
|---|---|
| App non-root | UID/GID `10001` |
| Hạn chế quyền app | Root filesystem chỉ đọc, `CapDrop=ALL`, `no-new-privileges=true` |
| Database và mạng | `PortBindings={}`, database dùng `qlsv_data`, `Internal=true` |
| Nginx security headers | `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: same-origin`, Permissions-Policy |

Ngoài ra, `.env` có quyền `600`, khớp quy tắc `.gitignore`; kiểm tra file đang theo dõi và lịch sử Git không có `.env`. Kết quả này chỉ nói về `.env`, không thay thế việc rà toàn bộ bí mật trước khi public repository.

Giới hạn cần nêu đúng: cAdvisor có quyền `privileged` để thu số liệu host; Promtail chạy root để đọc file log. Không khẳng định mọi container non-root. Ứng dụng vẫn có `/tmp` và volume static ghi được dù root filesystem chỉ đọc.

Khi cần chẩn đoán:

```bash
bash scripts/logging.sh ps -a
bash scripts/logging.sh logs --tail=80 db app nginx prometheus grafana loki promtail
curl --noproxy '*' -sSI --max-time 10 http://127.0.0.1:8080/healthz
free -h
sudo docker stats --no-stream
df -h /
```

| Biểu hiện | Kiểm tra |
|---|---|
| Cổng đang được dùng | Xem `sudo docker ps`; chỉ dừng đúng dịch vụ cũ chiếm cổng |
| Website 502/503 | Trạng thái và log `db`, `app`, `nginx` |
| Dashboard không có dữ liệu | Targets, `nginx_up`, `mysql_up`, labels container và khoảng thời gian |
| Loki ready nhưng chưa thấy log | Log Promtail, cấu hình nhãn đã áp dụng, rồi chạy lại `check_logging.py` |
| Container khởi động lại/máy chậm | RAM, swap, dung lượng và log; tăng RAM VM nếu thiếu |
| Sai tài khoản | Phân biệt Django/MySQL/Grafana; giữ bí mật hiện có, không xóa volume |

Không chia sẻ output cấu hình chứa mật khẩu; dùng `config --quiet` khi kiểm tra. Quy trình chi tiết: [demo CRUD](docs/sdlc/moc-1/demo.md), [giám sát](docs/sdlc/moc-2/guide.md), [thu log và LogQL](docs/sdlc/moc-3/guide.md), [kiểm tra cuối](docs/sdlc/final-verification/operations.md).

## 7. Tài liệu theo mốc và phần còn lại

Các hướng dẫn mốc 2–3 có bước chép ZIP qua VMware để phục vụ quá trình triển khai ban đầu. Với repository đầy đủ đã clone, dùng mục 3 của README này; không cần giải nén lại ZIP hoặc tạo lại ba commit lịch sử.

Phần cần hoàn thiện trước khi nộp:

- Bổ sung bằng chứng các ca xóa, kiểm tra điểm biên/trùng dữ liệu và bảo vệ tham chiếu theo kịch bản CRUD; kiểm tra lại dashboard sau nâng cấp.
- Theo [hướng dẫn GitHub](docs/github-guide.md), hoàn tất repository theo yêu cầu MSSV và xác nhận push đủ mã nguồn, cấu hình, README, lịch sử commit. Chưa ghi nhận repository đã được public/push.
- Dựa vào [đề cương báo cáo](docs/report-outline.md), viết báo cáo tối thiểu 10 trang với thông tin sinh viên, kiến trúc, cách hoạt động và ảnh kết quả thực tế; diễn tập demo đầy đủ. Cắt/che mật khẩu trước khi dùng ảnh.

GitHub CLI trên Ubuntu đã xác nhận username `DTC245200028` qua `gh api user --jq .login` sau khi đổi tên. Tên tài khoản trùng MSSV theo yêu cầu đề. Chưa ghi URL repository cho đến khi repository và push được xác nhận.
