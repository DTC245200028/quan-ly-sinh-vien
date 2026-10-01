# Mốc 2 — Thiết kế giám sát

## Căn cứ và hành vi cần đạt

PDF đề bài trang 1–2 yêu cầu Prometheus + Grafana giám sát container, web server và database, lưu bằng commit 2. Mốc 1 đã có bốn dịch vụ qlsv trên Ubuntu VMware. Ảnh ngày 2026-10-01 xác nhận tất cả healthy, /healthz HTTP200 và security headers; người dùng xác nhận SVDEMO01/điểm9 còn sau restart. Các thao tác xóa và validation chưa có bằng chứng riêng.

Thêm một file Compose ghép với compose.yaml; không đổi app, MySQL volume, tài khoản website hoặc cổng8080/8081. Nginx được gắn thêm server stub_status nội bộ8082. Prometheus thu thập30s/lần từ cAdvisor, nginx-exporter và mysql-exporter; Grafana tự nạp datasource/dashboard. Không dùng lại stack bài WordPress cũ.

## Thành phần và quyền

- Prometheus3.13.3 LTS: localhost9090, volume riêng, retention1ngày/tối đa512MB; mem_limit256m. Grafana12.4.12: localhost3000, volume riêng, mem_limit256m, không cho đăng ký/anonymous. Hai mật khẩu giám sát được tạo ngẫu nhiên, chỉ bổ sung vào.env hiện có.
- cAdvisor0.56.2: API mới phù hợp Docker29, CPU/RAM/network/diskIO, chỉ giữ hai nhãn Compose để lọc projectqlsv. Mẫu upstream cần privileged, cgroup host và mount tài nguyên host: đây là ngoại lệ giám sát, không khẳng định cả stack non-root. Giới hạn192m, không publish port.
- Nginx exporter1.5.3: đọc nginx:8082/stub_status, không publish. MySQL exporter0.19.0: user qlsv_exporter riêng, tối đa3kết nối, chỉ bật global_status/global_variables. Cấp PROCESS và REPLICATION CLIENT cho metadata; không cấp quyền ghi hoặc đọc bảng sinh viên.
- Prometheus/Grafana/cAdvisor ở networkmonitoring (không internal vì cần published port). MySQL exporter nối monitoring+data; Nginx exporter nối monitoring+edge. DB vẫn chỉ nối datainternal và không publish.
- Nginx gắn thêm status.conf qua overlay nên Compose tạo lại container này khi áp dụng; không cần sửa default.conf. Chỉ port80 được publish.

## Giao diện và vận hành

Wrapper scripts/monitoring.sh ghép đúng hai file Compose và tự gọi sudo khi cần. init_monitoring.py giữ nguyên các giá trị mốc1; setup_monitoring.sh tạo/cập nhật riêng user giám sát qua mysqlroot trong container, truyền SQL bằng stdin, không đặt mật khẩu trong argv/log. Setup lặp lại phải giữ mật khẩu ổn định. Không dùng initdb.d vì mysql_data đã có dữ liệu.

Dashboard UID qlsv-overview phân biệt up của exporter với nginx_up/mysql_up. CPU theo dịch vụ tính %mộtcore; dữ liệu thiếu phải hiện No data, không bù0. Filter projectqlsv tránh hiển thị lab cũ. RAM VM chỉ3.3GiB: cấu hình là mức khởi đầu, cần đo free/dockerstats và xử lý OOM theo bằng chứng.

## Nghiệm thu

| ID | Điểm triển khai | Điều kiện trên VM |
|---|---|---|
| M2-CONTAINER | cAdvisor/Prometheus/dashboard | Có CPU/RAM mang nhãn projectqlsv và serviceapp/db/nginx/phpmyadmin |
| M2-WEB | stub_status/Nginx exporter | nginx_up=1; rate requests tăng khi tạo tải nhỏ |
| M2-DB | MySQL exporter/user riêng | mysql_up=1; số kết nối/truy vấn có dữ liệu |
| M2-DASHBOARD | provisioning | Grafana đăng nhập được, dashboard có số liệu thật, 4targetsUP |
| M2-COMPAT | overlay/scripts | Website/dbtool còn hoạt động, dữ liệu/tài khoản mốc1 còn |
| M2-REPO | guide/commit | Commit1 trước khi chép overlay; commit2 sau khi kiểm chứng, không secrets |

Local kiểm tra cú pháp YAML/JSON/shell, cấu hình bằng công cụ khả dụng và tests bảo toàn.env/không lộ mật khẩu. Chưa có Docker local hoặc quyền thực thi vàoVM: không coi kiểm tra local là nghiệm thu runtime.

## Phục hồi

Dừng riêng năm dịch vụ giám sát bằng wrapper stop; dùng Compose mốc1 để chạy app. Giữ cả.env và các volumes. Không down-v hoặc xóa tài khoản/volume để sửa lỗi. File stub_status thêm chỉ bind nội bộ, có thể giữ khi tạm dừng giám sát.

## Nguồn chính thức

- https://prometheus.io/docs/introduction/release-cycle/
- https://github.com/prometheus/prometheus/releases/tag/v3.13.3
- https://github.com/grafana/grafana/releases/tag/v12.4.12
- https://github.com/google/cadvisor/releases/tag/v0.56.2
- https://github.com/google/cadvisor/blob/v0.56.2/docs/runtime_options.md
- https://github.com/prometheus/mysqld_exporter/blob/v0.19.0/mysqld_exporter.go
- https://github.com/prometheus/mysqld_exporter/blob/v0.19.0/config/config.go
- https://nginx.org/en/docs/http/ngx_http_stub_status_module.html
- https://github.com/nginx/nginx-prometheus-exporter/releases/tag/v1.5.3
