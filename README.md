# Đề tài 2 — Hệ thống quản lý sinh viên

Bộ mã nguồn mốc 1 và 2: website Django quản lý lớp, sinh viên, môn học và điểm; MySQL lưu dữ liệu; phpMyAdmin quản trị database; Nginx tiếp nhận truy cập. Mốc 2 bổ sung Prometheus/Grafana và exporters. Tất cả dịch vụ chạy bằng Docker Compose trên Ubuntu.

Mốc 1 đã có bằng chứng chạy trên VM và giữ dữ liệu sau restart. Mốc 2 có mã/config và hướng dẫn, cần kiểm chứng số liệu thật trên VM. Loki + Promtail, 2–3 truy vấn LogQL và báo cáo tối thiểu 10 trang là phần còn lại. Không coi mã nguồn có sẵn là bằng chứng mọi mốc đã hoạt động.

**Đang nâng cấp từ mốc 1:** làm theo [hướng dẫn mốc 2](docs/sdlc/moc-2/guide.md), lưu commit 1 trước khi giải nén bản mới. Sau nâng cấp, dùng `bash scripts/monitoring.sh ...` để quản lý cả chín dịch vụ; `sudo docker compose ...` một file chỉ quản lý phần mốc 1.

## 1. Môi trường và cấu trúc

Máy đích là Ubuntu trong VMware. Docker và Docker Compose đã được cài và chạy thành công `hello-world`; không cần cài lại. Với 4 CPU, RAM khoảng 3,3 GiB và 17 GB ổ đĩa trống, làm mốc 1 trước; khi thêm giám sát và log, nên tăng RAM lên 8 GB nếu máy thật đáp ứng được.

```text
Trình duyệt bên trong Ubuntu
 ├─ localhost:8080 → Nginx → Django/Gunicorn → MySQL
 └─ localhost:8081 → phpMyAdmin ─────────────→ MySQL
```

| Thành phần | Dịch vụ Compose | Vai trò |
|---|---|---|
| Django 5.2 + Gunicorn | `app` | Đăng nhập quản trị và CRUD |
| MySQL 8.4 | `db` | Lưu dữ liệu trong volume `mysql_data` |
| Nginx | `nginx` | Reverse proxy, phục vụ CSS và security headers |
| phpMyAdmin | `phpmyadmin` | Xem dữ liệu MySQL qua trình duyệt |

Website dùng Django Admin tiếng Việt. Danh mục môn học hỗ trợ nhập điểm; mỗi cặp sinh viên–môn học có một điểm từ 0 đến 10. Chưa có học kỳ, lần thi hoặc cổng riêng cho sinh viên.

## 2. Chuyển mã nguồn vào Ubuntu

Tải `quan-ly-sinh-vien-moc-1.zip` từ bộ bàn giao trên máy Windows. Chuyển ZIP vào thư mục `Downloads` của Ubuntu bằng kéo thả nếu VMware hỗ trợ; nếu không, dùng thư mục chia sẻ VMware hoặc USB. Không giải nén rồi chép từng file vì có thể bỏ sót các file ẩn.

Mở Terminal **trong Ubuntu**. Thư mục `~/quan-ly-sinh-vien` đã tạo phải còn trống ở lần giải nén đầu:

```bash
cd ~/quan-ly-sinh-vien
unzip ~/Downloads/quan-ly-sinh-vien-moc-1.zip -d ~/quan-ly-sinh-vien
ls -a
```

Nếu `unzip` chưa có, chạy `sudo apt update` và `sudo apt install -y unzip` rồi giải nén lại. Nếu ZIP nằm ở thư mục khác, thay đường dẫn `~/Downloads/...` bằng vị trí thật. Sau giải nén, `compose.yaml`, `README.md`, `.env.example`, `app/`, `nginx/` và `scripts/` phải nằm trực tiếp trong `~/quan-ly-sinh-vien`.

Từ đây, chạy tất cả lệnh tại `~/quan-ly-sinh-vien`. Không chạy lại bước giải nén đè lên dự án đã chỉnh sửa hoặc có dữ liệu mà chưa kiểm tra nội dung.

## 3. Tạo cấu hình và khởi động

Tạo `.env` một lần, bằng tài khoản Ubuntu thông thường:

```bash
cd ~/quan-ly-sinh-vien
python3 scripts/init_env.py
sudo docker compose config --quiet
sudo docker compose up -d --build --wait --wait-timeout 300
sudo docker compose ps
```

Script tự tạo mật khẩu và khóa bí mật ngẫu nhiên, đặt quyền `.env` là `600` trên Ubuntu và từ chối ghi đè nếu file đã tồn tại. Nếu báo file đã tồn tại, giữ nguyên file và tiếp tục kiểm tra cấu hình. Không dùng `.env.example` làm file mật khẩu thật, không gửi nội dung `.env` lên chat hoặc GitHub.

Lần chạy đầu cần Internet để tải image và thư viện. `config --quiet` thành công sẽ không in nội dung cấu hình hay mật khẩu. `up --wait` chờ dịch vụ đạt trạng thái chạy hoặc khỏe theo healthcheck; lần đầu có thể mất vài phút. Cách dùng tham số theo [tài liệu Docker Compose](https://docs.docker.com/reference/cli/docker/compose/up/).

Nếu `up` báo lỗi, dừng ở bước này và xem mục xử lý lỗi bên dưới; chưa tạo tài khoản khi `app` chưa chạy. Khi khởi động, ứng dụng tự áp dụng migrations và gom static files vào volume `static_data` để Nginx phục vụ.

## 4. Tạo tài khoản và dữ liệu mẫu

```bash
sudo docker compose exec app python manage.py createsuperuser
```

Nhập tên đăng nhập, email và mật khẩu quản trị do bạn chọn. Khi nhập mật khẩu, Terminal không hiện ký tự; đó là bình thường. Chọn mật khẩu đạt yêu cầu thay vì bỏ qua cảnh báo. Tài khoản này dùng cho website Django. Lệnh được mô tả trong [tài liệu Django](https://docs.djangoproject.com/en/5.2/ref/django-admin/#createsuperuser).

Sau đó tạo dữ liệu giả để thực hành:

```bash
sudo docker compose exec app python manage.py seed_demo
sudo docker compose ps
```

Với database mới, lệnh tạo 2 lớp, 3 môn học, 6 sinh viên và 18 điểm. Chạy lại chỉ bổ sung bản ghi còn thiếu, không tạo trùng hoặc ghi đè những giá trị bạn đã sửa.

Mở trình duyệt **bên trong Ubuntu**:

| Địa chỉ | Cách dùng |
|---|---|
| [Website](http://localhost:8080) | Đăng nhập bằng tài khoản vừa tạo; trang gốc chuyển đến `/admin/` |
| [phpMyAdmin](http://localhost:8081) | Dùng `MYSQL_USER` và `MYSQL_PASSWORD` trong `.env`; server là `db` nếu có ô hỏi |
| [Kiểm tra sức khỏe](http://localhost:8080/healthz) | Phải trả HTTP 200 và `{"status":"ok"}` khi ứng dụng kết nối được database |

Để đọc thông tin đăng nhập phpMyAdmin, mở thư mục dự án trong Files của Ubuntu, nhấn `Ctrl+H` để hiện file ẩn rồi mở `.env` bằng trình soạn thảo. Mặc định tên user là `qlsv_app`, database là `qlsv`. Không dùng tài khoản MySQL `root` để demo. Tài khoản MySQL và tài khoản quản trị website là hai tài khoản khác nhau.

Hai cổng chỉ lắng nghe trên `127.0.0.1` của Ubuntu. `localhost` trong trình duyệt Windows là máy Windows, nên dùng trình duyệt trong Ubuntu với bộ cấu hình này.

## 5. Kiểm tra và lấy ảnh minh chứng

Làm theo [kịch bản demo mốc 1](docs/sdlc/moc-1/demo.md). Các kết quả cần đạt:

- Đăng nhập được, giao diện quản trị có CSS; xem, thêm, sửa, xóa lớp, sinh viên, môn học và điểm.
- Tìm sinh viên theo mã hoặc tên, lọc theo lớp; điểm ngoài 0–10 và cặp sinh viên–môn học trùng bị từ chối.
- Không xóa được lớp còn sinh viên hoặc sinh viên/môn học còn điểm tham chiếu; thử trên dữ liệu giả.
- Dữ liệu vừa nhập xuất hiện trong phpMyAdmin và vẫn còn sau khi khởi động lại dịch vụ.
- Nginx trả security headers; ứng dụng chạy bằng user khác root; MySQL không có cổng công bố ra host.

Chạy kiểm tra nhanh trong Terminal:

```bash
curl -i http://localhost:8080/healthz
curl -I http://localhost:8080/admin/login/
sudo docker compose exec app id
sudo docker compose ps
```

Nếu chưa có `curl`, cài bằng `sudo apt install -y curl`. Ghi lại kết quả thực tế trên máy Ubuntu; việc có sẵn mã nguồn không phải bằng chứng triển khai thành công.

## 6. Dừng, chạy lại và giữ dữ liệu

Tạm dừng khi không học:

```bash
sudo docker compose stop
```

Chạy lại:

```bash
sudo docker compose up -d --wait --wait-timeout 300
```

Có thể dùng `sudo docker compose down` để gỡ container và mạng của bộ Compose; named volumes vẫn được giữ. **Không thêm `-v`** khi muốn giữ database: tùy chọn đó xóa named volumes, làm mất dữ liệu và tài khoản web. Xem [phân biệt các tùy chọn `down`](https://docs.docker.com/reference/cli/docker/compose/down/).

Giữ nguyên `.env` và tên dự án Compose `qlsv` để sử dụng đúng database đã khởi tạo. Đổi mật khẩu trong `.env` không tự đổi mật khẩu đã lưu trong MySQL volume. Không xóa `.env` rồi tạo lại để xử lý lỗi đăng nhập.

## 7. Khi có lỗi

Thu thập trạng thái và log gần nhất:

```bash
cd ~/quan-ly-sinh-vien
sudo docker compose ps -a
sudo docker compose logs --tail=80 db app nginx phpmyadmin
free -h
df -h /
```

Chỉ chia sẻ thông báo lỗi liên quan, kiểm tra và che mật khẩu hoặc thông tin riêng trước khi gửi. Không gửi `.env`, không chạy `docker compose config` không có `--quiet` để chia sẻ cấu hình vì có thể lộ bí mật.

| Biểu hiện | Việc nên kiểm tra |
|---|---|
| Báo không tìm thấy file Compose | Chạy `pwd`; phải ở `~/quan-ly-sinh-vien` và có `compose.yaml` |
| Build hoặc tải image lỗi | Xem lỗi mạng/tên image/dung lượng; giữ nguyên log lỗi đầu tiên |
| Chờ quá 300 giây | Xem `ps -a` và log; VM ít RAM có thể khởi tạo MySQL chậm |
| `port is already allocated` | Kiểm tra chương trình đang dùng cổng 8080/8081; chưa đổi cổng hoặc CSRF origin tùy ý |
| Website trả 502/503 | Xem trạng thái và log `app`, `db`, rồi `nginx` |
| Sai mật khẩu phpMyAdmin | Dùng user/password MySQL trong `.env`, không dùng tài khoản Django |
| Trang web từ Windows không mở | Mở trình duyệt bên trong Ubuntu; bộ cấu hình mặc định chỉ cho localhost Ubuntu |

Nếu `localhost:8080` hiện WordPress hoặc một bài lab khác, kiểm tra `sudo docker ps --format 'table {{.Names}}\t{{.Ports}}'`. Chỉ tắt các container của bài cũ khi bạn đã xác nhận không cần chúng; không dùng lệnh dừng toàn bộ Docker. Trong môi trường đã được người dùng xác nhận ở bài này, WordPress dùng 8080 và cAdvisor dùng 8081.

Bản sửa ngày 2026-10-01: phpMyAdmin nối cả `edge` và `data` để port publishing hoạt động. Healthcheck thêm `php -d allow_url_fopen=1` vì image tắt HTTP stream wrapper mặc định; chỉ probe được bật, cấu hình PHP phục vụ web giữ nguyên. Người đã giải nén bản đầu có thể thay riêng `compose.yaml`, giữ `.env` và database, rồi chạy `sudo docker compose up -d --wait --wait-timeout 300`.

Không dùng xóa volume hoặc xóa dữ liệu như cách sửa lỗi mặc định.

## 8. Bảo mật trong mốc 1

Bài thực hành dùng HTTP trên localhost với security headers, tương ứng lựa chọn security headers của đề. Đây chưa phải cấu hình HTTPS để công bố website ra Internet.

| Biện pháp | Cách kiểm chứng |
|---|---|
| Container ứng dụng chạy non-root | `sudo docker compose exec app id` có UID khác 0 |
| Database ở mạng nội bộ, không công bố cổng | Kiểm tra Compose và `docker inspect`; không có ánh xạ cổng host cho MySQL |
| Mật khẩu ngẫu nhiên, cấu hình bí mật ngoài Git | `.env` quyền `600`, được `.gitignore` loại trừ |
| User database riêng, quyền trong database bài làm | phpMyAdmin dùng `qlsv_app`; xem `SHOW GRANTS FOR CURRENT_USER;` |
| Hạn chế quyền ứng dụng, security headers | Kiểm tra `cap_drop`, `no-new-privileges` trong Compose và headers từ Nginx |

Chỉ khẳng định container `app` chạy non-root sau khi kiểm tra; không suy ra mọi image đều chạy non-root. User database có quyền phục vụ migrations trong database `qlsv`, không dùng quyền quản trị toàn bộ MySQL.

## 9. Tạo commit 1 sau khi demo đạt

Nếu chưa có Git, cài `sudo apt install -y git`. Khởi tạo repository trong thư mục dự án:

```bash
cd ~/quan-ly-sinh-vien
git init
```

Nếu Git chưa biết danh tính, thay hai giá trị minh họa bằng thông tin thật rồi chạy:

```bash
git config user.name "Ten cua ban"
git config user.email "email-cua-ban@example.com"
```

Kiểm tra bí mật đã được loại trừ và tạo commit:

```bash
git check-ignore .env
git add README.md compose.yaml .env.example .gitignore .gitattributes app nginx scripts docs
git diff --cached --stat
git diff --cached --name-only
git commit -m "feat: trien khai CRUD sinh vien voi MySQL va Nginx"
```

`git check-ignore .env` cần in `.env`; danh sách file chờ commit không được có `.env`, mật khẩu, bản sao database hoặc dữ liệu cá nhân. Không dùng `git add -f .env`. Bước này mới tạo commit ở Ubuntu; tạo repository GitHub và push sẽ làm sau khi có MSSV/tài khoản của bạn theo yêu cầu đề.

## 10. Mốc 2 — giám sát

[Hướng dẫn cài, kiểm tra và commit 2](docs/sdlc/moc-2/guide.md) mô tả đầy đủ thao tác. Trên mốc 1 đang chạy, sau khi chép bộ bổ sung:

```bash
python3 scripts/init_monitoring.py
bash scripts/setup_monitoring.sh
bash scripts/monitoring.sh config --quiet
bash scripts/monitoring.sh up -d --wait --wait-timeout 300
bash scripts/monitoring.sh ps
```

| Dịch vụ | Image đã chọn | Vai trò |
|---|---|---|
| prometheus | prom/prometheus:v3.13.3 | Thu thập metrics mỗi30s; localhost9090 |
| grafana | grafana/grafana:12.4.12 | Dashboard nạp sẵn; localhost3000 |
| cadvisor | ghcr.io/google/cadvisor:0.56.2 | Metrics container có nhãn Composeqlsv |
| nginx-exporter | nginx/nginx-prometheus-exporter:1.5.3 | Đọc stub_status nội bộ8082 |
| mysql-exporter | prom/mysqld-exporter:v0.19.0 | Đọc trạng thái/biến MySQL bằng user riêng |

Mở [Targets](http://localhost:9090/targets) để xem4jobsUP; kiểm tra thêm `nginx_up=1`, `mysql_up=1` và CPU/RAM của các dịch vụ qlsv. Mở [dashboard Grafana](http://localhost:3000/d/qlsv-overview), dùng `GRAFANA_ADMIN_USER`/`GRAFANA_ADMIN_PASSWORD` trong.env. Biến môi trường này chỉ khởi tạo mật khẩu Grafana khi volume mới; sửa.env không tự đổi mật khẩu Grafana đã lưu.

Prometheus giữ tối đa1ngày hoặc512MB blockmetrics (WAL/head có thể dùng thêm đĩa). Giới hạn RAM của5dịch vụ giám sát tổng800MiB; đây là giới hạn, không phải số đo đã chạy. cAdvisor có quyền host/privileged để đọc số liệu; các exporter không publish cổng. User MySQL giám sát chỉ có quyền metadata, không SELECT/UPDATE bảng sinh viên. Thiết kế và nguồn upstream trong [design.md](docs/sdlc/moc-2/design.md).

## 11. Phần còn lại

1. Kiểm chứng dashboard mốc2 trênVM và lưu commit2.
2. Mốc3: Loki + Promtail, thu thập log và trình diễn2–3truy vấn LogQL; commit3.
3. Hoàn thiện minh chứng3–4biện pháp hardening, GitHub và báo cáo tối thiểu10trang; diễn tập demo toàn bộ hệ thống.

Giữ lại ảnh và ghi chú kết quả từ mỗi mốc để viết báo cáo theo triển khai thực tế.
