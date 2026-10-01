# Mốc 2 — Prometheus và Grafana trên Ubuntu

Mục tiêu: có dashboard hiển thị dữ liệu thực của container, Nginx và MySQL, đồng thời giữ nguyên website, tài khoản và dữ liệu mốc 1. Tất cả lệnh dưới đây chạy trong Terminal Ubuntu; các trang web mở bằng trình duyệt bên trong Ubuntu.

Hướng dẫn này dành cho mốc 1 đã chạy. Nếu cài từ máy mới, hoàn thành README mốc 1 trước, sau đó mới bổ sung mốc 2.

Mốc 1 đã có bằng chứng từ người dùng về bốn dịch vụ healthy, `/healthz` trả 200, security headers và dữ liệu còn sau khởi động lại. Cảnh báo phpMyAdmin về kết quả không có cột duy nhất khi chạy câu `SELECT ... JOIN ...` chỉ có nghĩa không thể sửa trực tiếp lưới kết quả đó; không phải lỗi truy vấn hay lỗi lưu dữ liệu.

VM hiện có khoảng 3,3 GiB RAM. Nên tăng lên 8 GB nếu máy thật cho phép trước khi chạy thêm năm dịch vụ giám sát. Nếu giữ cấu hình hiện tại, theo dõi RAM/swap và tình trạng container; không kết luận lỗi ứng dụng chỉ từ việc máy phản hồi chậm.

## 1. Tạo commit 1 trước khi chép bản mốc 2

Làm bước này trên **bản mốc 1 đang chạy trong Ubuntu**, trước khi giải nén ZIP mới để lịch sử Git thể hiện đúng từng mốc. Nếu đã có commit 1 đúng nội dung, kiểm tra `git log --oneline -3` và bỏ qua việc tạo lại.

```bash
cd ~/quan-ly-sinh-vien
git --version
git init
read -r -p "Tên của bạn dùng trong Git: " qlsv_git_name
read -r -p "Email của bạn dùng trong Git: " qlsv_git_email
git config user.name "$qlsv_git_name"
git config user.email "$qlsv_git_email"
git check-ignore .env
git add README.md compose.yaml .env.example .gitignore .gitattributes app nginx scripts docs
git diff --cached --name-only
```

Nếu chưa có Git, cài `sudo apt update` rồi `sudo apt install -y git`. `git check-ignore .env` phải in `.env`; danh sách chờ commit không được chứa `.env`, mật khẩu hoặc file sao lưu database. Các lệnh `git config` trên chỉ đặt danh tính trong repository này.

Khi danh sách đúng, tạo commit và kiểm tra:

```bash
git commit -m "feat: trien khai CRUD sinh vien voi MySQL va Nginx"
git log --oneline -1
git status --short
```

Đây là commit thật trên máy đang triển khai. Chưa push lên GitHub trong bước này. Nếu có thay đổi chưa lưu ngoài danh sách dự kiến, kiểm tra chúng trước khi chép ZIP; không ghi đè chỉnh sửa riêng mà chưa lưu.

## 2. Chép mã nguồn mốc 2

Đặt `quan-ly-sinh-vien-moc-2.zip` trong thư mục chia sẻ VMware `baithuchanh`, giống lần cập nhật mốc 1. Bộ ZIP không chứa `.env`, `.git` hoặc dữ liệu MySQL.

```bash
cd ~/quan-ly-sinh-vien
unzip -o /mnt/hgfs/baithuchanh/quan-ly-sinh-vien-moc-2.zip -d ~/quan-ly-sinh-vien
ls compose.monitoring.yaml scripts/monitoring.sh
```

Nếu ZIP nằm trong `Downloads` của Ubuntu, thay đường dẫn ZIP bằng `~/Downloads/quan-ly-sinh-vien-moc-2.zip`. Giữ nguyên thư mục dự án, `.env` và các named volumes đã có; không tạo dự án Compose tên khác.

Mốc 2 bổ sung `compose.monitoring.yaml`. Script `scripts/monitoring.sh` tự dùng `sudo` khi cần và ghép file này với `compose.yaml`, tương đương `sudo docker compose -f compose.yaml -f compose.monitoring.yaml ...`. Từ bước này dùng script cho thao tác với toàn bộ hệ thống để không bỏ sót dịch vụ giám sát. Cơ chế ghép file theo [tài liệu Docker Compose](https://docs.docker.com/compose/how-tos/multiple-compose-files/merge/).

## 3. Khởi tạo giám sát và chạy dịch vụ

Mốc 1 phải đang chạy để thiết lập tài khoản giám sát trong MySQL. Nếu đã dừng, chạy `sudo docker compose up -d --wait --wait-timeout 300` trước. Sau đó chạy lần lượt, chỉ chuyển sang lệnh tiếp theo khi lệnh trước thành công:

```bash
cd ~/quan-ly-sinh-vien
python3 scripts/init_monitoring.py
bash scripts/setup_monitoring.sh
bash scripts/monitoring.sh config --quiet
bash scripts/monitoring.sh up -d --wait --wait-timeout 300
bash scripts/monitoring.sh ps
```

Script khởi tạo chỉ thêm các biến giám sát còn thiếu vào `.env`, giữ nguyên nội dung và mật khẩu mốc 1. Script thiết lập tạo user `qlsv_exporter` với quyền đọc trạng thái (`PROCESS`, `REPLICATION CLIENT`), tối đa 3 kết nối; không cấp quyền đọc bảng sinh viên. Lệnh chạy qua MySQL root bên trong container, không xóa hay khởi tạo lại database. Không sửa mật khẩu gốc hoặc gửi `.env` cho người khác.

Các dịch vụ mới là `prometheus`, `grafana`, `cadvisor`, `nginx-exporter` và `mysql-exporter`. Website vẫn ở cổng 8080, phpMyAdmin vẫn ở 8081. Hai exporter không cấu hình healthcheck nên chỉ hiện `Up` là bình thường; cần kiểm tra số liệu thực ở bước sau. Cổng trạng thái Nginx 8082 chỉ dùng bên trong mạng Docker, không mở ra Ubuntu.

## 4. Kiểm tra Prometheus và dữ liệu thật

Mở [Prometheus Targets](http://localhost:9090/targets). Chờ khoảng 1–2 phút sau khi khởi động để có đủ mẫu số liệu.

- [ ] Bốn nhóm target `prometheus`, `cadvisor`, `nginx`, `mysql` đều `UP`.
- [ ] Website và phpMyAdmin vẫn truy cập được; dữ liệu sinh viên từ mốc 1 vẫn còn.

Mở trang Query của [Prometheus](http://localhost:9090), nhập từng biểu thức rồi bấm **Execute**:

| Biểu thức PromQL | Kết quả cần thấy |
|---|---|
| `up` | Cả bốn target có giá trị `1` |
| `nginx_up` | Giá trị `1`: exporter đọc được trạng thái Nginx |
| `mysql_up` | Giá trị `1`: exporter kết nối được MySQL |
| `container_memory_working_set_bytes{job="cadvisor",container_label_com_docker_compose_project="qlsv",container_label_com_docker_compose_service!=""}` | Các container dự án `qlsv` có số liệu RAM |
| `rate(container_cpu_usage_seconds_total{job="cadvisor",container_label_com_docker_compose_project="qlsv",container_label_com_docker_compose_service!=""}[2m])` | Có chuỗi số liệu CPU của container `qlsv`, dù có thể rất nhỏ lúc nhàn rỗi |

`UP` chỉ chứng minh Prometheus lấy được dữ liệu từ endpoint exporter; ví dụ exporter vẫn có thể `UP` trong khi `mysql_up` là `0`. Vì vậy, không bỏ qua hai chỉ số `nginx_up`, `mysql_up` và các chuỗi CPU/RAM theo container. Cách kiểm tra target và chạy truy vấn theo [hướng dẫn Prometheus](https://prometheus.io/docs/prometheus/latest/getting_started/).

## 5. Mở Grafana và tạo hoạt động demo

Mở [Grafana](http://localhost:3000). Tên đăng nhập là giá trị `GRAFANA_ADMIN_USER` trong `.env` (mặc định `admin`); mật khẩu là `GRAFANA_ADMIN_PASSWORD`. Mở `.env` bằng trình soạn thảo Ubuntu để đọc, không dùng tài khoản Django hoặc mật khẩu MySQL và không chụp màn hình có mật khẩu.

Dashboard đã được cung cấp tự động cùng nguồn dữ liệu Prometheus. Vào **Dashboards**, mở **QLSV - Giám sát hệ thống**, hoặc mở [dashboard quản lý sinh viên](http://localhost:3000/d/qlsv-overview). Cách nạp sẵn nguồn dữ liệu và dashboard dùng [Grafana provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/).

Chọn khoảng thời gian **Last 15 minutes**, giữ làm mới **30s** và bộ lọc **Dịch vụ container → All**. Tạo một ít lượt truy cập:

```bash
for i in {1..30}; do
  curl -fsS http://localhost:8080/healthz -o /dev/null || break
  sleep 1
done
```

Sau đó dùng website để xem danh sách sinh viên, mở trang sửa rồi lưu một thay đổi trên dữ liệu giả. Quan sát dashboard thêm khoảng 1–2 phút.

- [ ] Dashboard có dữ liệu CPU và RAM theo container `qlsv`, không chỉ số liệu của chính cAdvisor.
- [ ] Nhóm biểu đồ Nginx có số liệu request/kết nối; trạng thái Nginx là hoạt động.
- [ ] Nhóm biểu đồ MySQL có số liệu kết nối/truy vấn; trạng thái MySQL là hoạt động.
- [ ] Khi tạo truy cập, các số liệu liên quan có mẫu mới hoặc thay đổi. Một giá trị `0` lúc nhàn rỗi vẫn là dữ liệu; `No data` cần được kiểm tra.

Chụp ảnh trang Targets có bốn target `UP` và dashboard thể hiện đủ container, Nginx, MySQL. Đây là minh chứng giám sát cho báo cáo; không dùng ảnh dashboard trống.

## 6. Khi gặp lỗi và khi tạm dừng

```bash
bash scripts/monitoring.sh ps -a
bash scripts/monitoring.sh logs --tail=80 prometheus grafana cadvisor nginx-exporter mysql-exporter
free -h
df -h /
sudo docker stats --no-stream
```

| Biểu hiện | Việc cần kiểm tra |
|---|---|
| Cổng 3000/9090 đã được dùng | Xem `sudo docker ps`; bài lab cũ có thể vẫn giữ cổng. Xác định đúng container trước khi dừng, không dừng toàn bộ Docker |
| Target Nginx/MySQL `UP` nhưng `nginx_up`/`mysql_up` bằng 0 | Xem log exporter tương ứng; kiểm tra bước thiết lập account và kết nối đến dịch vụ |
| Không có CPU/RAM của `qlsv` | Xem log cAdvisor và truy vấn metric/labels; không kết luận giám sát container đạt chỉ vì target `UP` |
| Grafana `No data` | Kiểm tra Prometheus trước, chọn Last 15 minutes, chờ đủ mẫu rồi xem lại |
| Container thoát/khởi động lại, máy chậm | Kiểm tra RAM/swap, log và `docker stats`; tăng RAM VM nếu thiếu |

Khi gửi lỗi, chỉ gửi phần liên quan và che thông tin riêng. Không gửi `.env`, output cấu hình đã mở rộng bí mật hoặc câu SQL chứa mật khẩu.

Nếu log Prometheus báo lỗi cấu hình, kiểm tra bằng công cụ có sẵn trong image:

```bash
bash scripts/monitoring.sh run --rm --no-deps --entrypoint /bin/promtool prometheus check config /etc/prometheus/prometheus.yml
```

Tạm dừng riêng giám sát để giảm tải:

```bash
bash scripts/monitoring.sh stop prometheus grafana cadvisor nginx-exporter mysql-exporter
```

Chạy lại bằng `bash scripts/monitoring.sh up -d --wait --wait-timeout 300`. Không dùng `down -v`, không xóa volume để sửa lỗi. cAdvisor cần truy cập số liệu host/container để giám sát; không ghi báo cáo rằng tất cả container đều chạy non-root.

## 7. Tạo commit 2 khi kiểm tra đạt

Chỉ thực hiện sau khi Targets, các chỉ số thực và dashboard đã đạt; giữ ảnh minh chứng riêng, không đưa mật khẩu vào ảnh hoặc Git.

```bash
cd ~/quan-ly-sinh-vien
git check-ignore .env
git add compose.monitoring.yaml .env.example .gitignore README.md scripts monitoring docs
git diff --cached --stat
git diff --cached --name-only
```

Kiểm tra danh sách không có `.env`, dữ liệu volume hoặc file sao lưu. Sau đó:

```bash
git commit -m "feat: giam sat container Nginx MySQL bang Prometheus Grafana"
git log --oneline -2
```

Mốc 3 tiếp theo là Loki + Promtail và 2–3 truy vấn LogQL. Hoàn thành mốc 2 chưa đồng nghĩa hoàn thành phần log hoặc báo cáo toàn bộ đề tài.
