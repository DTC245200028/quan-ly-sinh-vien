# Mốc 3 — Loki, Promtail và LogQL trên Ubuntu

Mục tiêu: thu log tập trung, xem log trong Grafana và demo 3 truy vấn LogQL. Giữ nguyên website, database và giám sát đã chạy ở mốc 1–2. Thực hiện trong `~/quan-ly-sinh-vien` trên Ubuntu; dùng trình duyệt bên trong máy ảo.

Promtail đã hết hỗ trợ từ ngày **02/03/2026**. Bài thực hành này vẫn dùng Promtail theo công nghệ PDF yêu cầu. [Thông báo chính thức của Grafana](https://grafana.com/docs/loki/latest/send-data/promtail/).

Máy hiện có RAM khả dụng (`available`) khoảng 1,3 GiB; 126 MiB là cột `free`, không phải toàn bộ RAM còn có thể cấp thêm. Swap đang dùng khoảng 1,4 GiB. Có thể thử mốc 3 và theo dõi tài nguyên; Loki được giới hạn 384 MiB, Promtail 128 MiB. Nếu máy chậm hoặc container thiếu RAM, tạm dừng hai dịch vụ log và tăng RAM VMware nếu máy thật cho phép.

## 1. Lưu commit 2 trước khi giải nén

Mốc 2 đã có bằng chứng số liệu container, Nginx và MySQL. Ảnh Git trước đó mới có commit 1 (`2fa2384`, nhánh `master`). Chạy trên bản đang triển khai, **trước khi chép mốc 3**:

```bash
cd ~/quan-ly-sinh-vien
git log --oneline -3
git check-ignore .env
git add compose.monitoring.yaml .env.example .gitignore README.md scripts monitoring docs
git diff --cached --stat
git diff --cached --name-only
```

Danh sách chờ commit không được có `.env`, ảnh chứa mật khẩu hoặc bản sao database. Nếu commit 2 đã có và không còn thay đổi tương ứng, bỏ qua việc tạo lại. Khi danh sách đúng:

```bash
git commit -m "feat: giam sat container Nginx MySQL bang Prometheus Grafana"
git log --oneline -2
git status --short
```

Giữ nguyên Git đã tạo, không chạy lại bước khởi tạo danh tính. Nếu có chỉnh sửa riêng chưa lưu, kiểm tra và lưu chúng trước khi giải nén đè file.

## 2. Chép bộ mốc 3 và khởi động

Đặt `quan-ly-sinh-vien-moc-3.zip` vào thư mục chia sẻ VMware `baithuchanh`. Bộ ZIP bổ sung cấu hình, không chứa `.env`, `.git` hoặc dữ liệu volume.

```bash
cd ~/quan-ly-sinh-vien
unzip -o /mnt/hgfs/baithuchanh/quan-ly-sinh-vien-moc-3.zip -d ~/quan-ly-sinh-vien
python3 scripts/prepare_logging.py
bash scripts/logging.sh config --quiet
bash scripts/logging.sh up -d --wait --wait-timeout 300
bash scripts/logging.sh ps
```

Nếu ZIP nằm trong Downloads của Ubuntu, thay đường dẫn bằng `~/Downloads/quan-ly-sinh-vien-moc-3.zip`. Chạy từng lệnh; nếu một lệnh lỗi thì xem thông báo trước khi tiếp tục.

Mốc 2 phải đang chạy để script kiểm tra các container `qlsv`. `prepare_logging.py` tự tìm thư mục log Docker, kiểm tra driver `json-file`, rồi thêm `DOCKER_LOG_DIR` vào `.env`; giữ nguyên mật khẩu và các giá trị đã có. Không cần chạy lại script tạo mật khẩu.

`logging.sh` tự dùng `sudo` và ghép đủ `compose.yaml`, `compose.monitoring.yaml`, `compose.logging.yaml`. Từ đây dùng wrapper này cho toàn bộ hệ thống. Lần đầu áp dụng sẽ tạo lại các container để bổ sung nhãn log, nên website có thể gián đoạn ngắn; named volumes và dữ liệu vẫn được giữ.

Loki ở `localhost:3100`; Promtail chỉ có cổng 9080 trong mạng Docker. Hai dịch vụ không cấu hình Docker healthcheck nên trạng thái `Up` là bình thường. Cần kiểm tra log thật ở bước tiếp, không kết luận đạt chỉ từ `ps`.

## 3. Kiểm tra log đi từ website đến Loki

```bash
python3 scripts/check_logging.py
```

Script chờ Loki sẵn sàng, gọi một đường dẫn thử nghiệm không tồn tại trên website để tạo HTTP 404 với mã nhận diện riêng, rồi tìm đúng dòng đó trong Loki. Chờ đến khi hiện:

```text
PASS: website -> Docker JSON -> Promtail -> Loki da nhan marker moi.
```

HTTP 404 ở đây là kết quả chủ động tạo để demo log. Script còn in 3 truy vấn LogQL có thể sao chép vào Grafana. Nếu báo chưa đạt, xem mục xử lý lỗi; không chuyển sang commit 3.

Promtail đọc file JSON log ở chế độ chỉ đọc, chỉ gửi dòng thuộc dự án `qlsv` vào Loki, không dùng Docker API/socket. Log có nhãn dự án/dịch vụ xuất hiện từ khi container áp dụng cấu hình mốc 3; không yêu cầu phải có đủ log lịch sử trước đó.

## 4. Demo 3 truy vấn trong Grafana

Mở [Grafana](http://localhost:3000), đăng nhập bằng tài khoản đang dùng. Vào **Explore**, chọn nguồn dữ liệu **Loki QLSV**, chuyển trình soạn thảo sang **Code**, chọn **Last 15 minutes**. Chạy từng truy vấn bằng **Run query**. Xem [hướng dẫn LogQL](https://grafana.com/docs/loki/latest/query/).

**Truy vấn 1 — Xem log Nginx của bài làm:**

```logql
{project="qlsv",service="nginx"}
```

Kết quả cần có các dòng truy cập website mới phát sinh.

**Truy vấn 2 — Tìm đúng request 404 thử nghiệm:** sao chép truy vấn số 2 do `check_logging.py` in ra để tìm mã nhận diện duy nhất của lần kiểm tra vừa chạy. Hoặc tạo request thủ công:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:8080/moc3-demo-404
```

Terminal cần in `404`. Trong Grafana chạy:

```logql
{project="qlsv",service="nginx"} |= "moc3-demo-404"
```

Kết quả cần thấy đường dẫn thử nghiệm và mã HTTP 404. Bộ lọc trên cũng tìm được các mã nhận diện do script tạo vì có cùng tiền tố.

**Truy vấn 3 — Đếm số dòng log trong 5 phút theo dịch vụ:**

```logql
sum by (service) (count_over_time({project="qlsv"}[5m]))
```

Kết quả là số liệu/bảng/biểu đồ theo nhãn `service`. Dịch vụ chưa ghi log trong cửa sổ thời gian có thể không xuất hiện; không suy ra mất log chỉ từ một dịch vụ đang nhàn rỗi.

Chụp kết quả của cả 3 truy vấn, giữ rõ biểu thức và khoảng thời gian. **Cắt hoặc che phần mật khẩu trong ảnh trước khi đưa vào báo cáo**, không đưa ảnh có mật khẩu lên GitHub.

## 5. Kiểm tra hồi quy và lưu tài nguyên

- [ ] `check_logging.py` in `PASS`, ba truy vấn có kết quả thực tế.
- [ ] Website `localhost:8080` và phpMyAdmin `localhost:8081` còn dữ liệu cũ; mở được danh sách sinh viên.
- [ ] Grafana vẫn có CPU/RAM container, Nginx và MySQL; bốn target Prometheus vẫn `UP`, `nginx_up` và `mysql_up` bằng `1`.
- [ ] `/healthz` trả HTTP 200; không có container liên tục khởi động lại.

```bash
curl -i http://localhost:8080/healthz
bash scripts/logging.sh ps -a
free -h
sudo docker stats --no-stream
df -h /
```

Loki giữ log theo thời gian lưu cấu hình cho lab; đây không phải bản sao lưu database. Chụp ảnh minh chứng khi log còn trong khoảng thời gian truy vấn, không lưu log vô hạn trên ổ đĩa nhỏ.

Để kiểm tra log còn sau restart, lưu lại truy vấn marker ở bước 3 rồi chạy:

```bash
bash scripts/logging.sh restart loki promtail
python3 scripts/check_logging.py
```

Sau khi script đạt, chạy lại **truy vấn marker cũ** trong Grafana và chọn khoảng thời gian bao gồm lần kiểm tra trước. Marker cũ vẫn cần xuất hiện; marker mới của script xác nhận việc thu log tiếp tục hoạt động.

## 6. Khi lỗi hoặc cần tạm dừng

```bash
bash scripts/logging.sh logs --tail=80 loki promtail
curl -i http://localhost:3100/ready
```

| Biểu hiện | Kiểm tra tiếp |
|---|---|
| Script chuẩn bị báo sai driver/đường dẫn log | Giữ nguyên thông báo, kiểm tra container của dự án; không tự đổi đường dẫn hay mở rộng quyền cả thư mục Docker |
| Loki chưa ready hoặc container thoát | Xem log Loki, RAM và trạng thái container; không coi `Up` là đã sẵn sàng |
| Loki ready nhưng không có dòng thử nghiệm | Xem log Promtail; kiểm tra lần `up` đã áp dụng cấu hình cho các dịch vụ và chạy lại `check_logging.py` |
| Grafana không thấy Loki QLSV | Chạy `bash scripts/logging.sh restart grafana`, chờ Grafana khởi động rồi mở lại Explore |
| Explore không có kết quả | Chọn đúng datasource, Last 15 minutes, chạy lại script để tạo log mới rồi truy vấn lại |
| Máy chậm hoặc thiếu RAM | Kiểm tra `free -h`, `docker stats`; tạm dừng hai dịch vụ dưới đây và tăng RAM nếu cần |

Tạm dừng riêng log:

```bash
bash scripts/logging.sh stop promtail loki
```

Chạy lại bằng `bash scripts/logging.sh up -d --wait --wait-timeout 300`, rồi chạy lại `python3 scripts/check_logging.py`. Giữ `.env`, các volume và dữ liệu; không dùng `down -v`. Khi gửi lỗi, chỉ gửi thông báo liên quan và che thông tin riêng, không gửi `.env`.

## 7. Tạo commit 3 sau khi kiểm tra đạt

```bash
cd ~/quan-ly-sinh-vien
git check-ignore .env
git add compose.logging.yaml .env.example .gitignore README.md scripts logging monitoring/grafana/provisioning/datasources/loki.yml docs
git diff --cached --stat
git diff --cached --name-only
```

Kiểm tra danh sách không có bí mật hoặc dữ liệu volume; sau đó:

```bash
git commit -m "feat: thu log tap trung bang Loki Promtail va truy van LogQL"
git log --oneline -3
```

Sau mốc 3 còn hoàn thiện minh chứng hardening, đưa mã nguồn lên GitHub theo yêu cầu MSSV, viết báo cáo tối thiểu 10 trang và diễn tập demo. Chỉ ghi kết quả thực tế đã kiểm tra vào báo cáo.
