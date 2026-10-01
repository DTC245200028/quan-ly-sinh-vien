# Mốc 3 — Thiết kế thu log

## Yêu cầu và căn cứ

PDF trang 1–2 yêu cầu Loki, Promtail, ít nhất 2–3 truy vấn LogQL và commit 3. Người dùng muốn giữ đúng công nghệ trong đề. Mốc 2 đã có ảnh số liệu container, Nginx và MySQL. Git trên VM có commit 1; phải lưu commit 2 trước khi chép mốc 3.

Promtail đã hết hỗ trợ ngày 02/03/2026. Bài này vẫn dùng Promtail trong lab localhost theo yêu cầu PDF, không tự thay bằng Alloy. Đây không phải đề xuất dùng Promtail cho hệ thống mới ngoài bài thực hành.

## Luồng dữ liệu

Docker `json-file` → Promtail đọc file → Loki TSDB v13/filesystem → Grafana Explore.

`logging.sh` ghép ba file Compose. Overlay thêm hai nhãn Compose project/service vào log của 11 dịch vụ, giữ xoay vòng 10 MB × 3 file. Lần áp dụng đầu tạo lại chín container hiện có để nhận tùy chọn log; các volume, mạng, cổng và mật khẩu vẫn giữ nguyên.

Promtail đọc thuộc tính `attrs` của từng dòng JSON, chỉ giữ dự án `qlsv` có nhãn dịch vụ. Loại dòng sai JSON, thiếu nhãn và log bài cũ. Nhãn truy vấn gồm `project`, `service`, `stream`, `job`; không dùng URL, ID container hoặc tên file làm nhãn. Promtail không kết nối Docker API/socket. Script chuẩn bị lấy `DockerRootDir` từ daemon, đối chiếu `LogPath` và driver của container đang chạy trước khi thêm `DOCKER_LOG_DIR` vào `.env`.

Chỉ theo dõi file đang hoạt động `*-json.log`; Docker quản lý việc xoay vòng. Volume positions lưu vị trí đọc, không phải hàng đợi bảo đảm không mất log khi dịch vụ ngừng lâu hơn cửa sổ xoay vòng.

## Tài nguyên và quyền

Loki 3.7.8 chạy bằng UID 10001, volume riêng tại `/loki`; image distroless không có shell/wget nên không gắn healthcheck giả. Script trên Ubuntu kiểm tra `/ready`, sau đó kiểm tra một dòng log mới từ website đến Loki.

Promtail 3.6.11 chạy root để đọc log Docker, bỏ toàn bộ capabilities, bật `no-new-privileges`, root filesystem chỉ đọc. Thư mục Docker log được mount chỉ đọc, positions ở volume riêng. Loki và Promtail chỉ nối mạng `monitoring`, không nối mạng database. Loki publish trên `127.0.0.1:3100`, Promtail không publish cổng.

Datasource Loki được thêm vào thư mục provisioning Grafana đang được mount sẵn, không tạo mount lồng trong mount chỉ đọc. Datasource Prometheus vẫn là mặc định.

Loki giới hạn 384 MiB, Promtail 128 MiB; Go memory limit thấp hơn mức này, query concurrency 2, cache 16 MiB và WAL replay 64 MB. Retention 24 giờ có compactor, không phải hạn mức đĩa tuyệt đối. Ảnh `free -h` của người dùng có available 1,3 GiB, free 126 MiB và swap dùng 1,4 GiB. Có thể thử bộ log rồi đo RAM thực tế; chưa có bằng chứng mức dùng RAM sau khi bật.

## Tiêu chí nghiệm thu

| ID | Kết quả | Kiểm chứng |
|---|---|---|
| M3-COLLECT | Log dự án tới Loki, bài cũ bị loại | Nhãn project/service và request mới có marker duy nhất |
| M3-QUERY | Ba truy vấn LogQL có kết quả | Log Nginx, lọc marker, đếm theo dịch vụ |
| M3-PERSIST | Log và vị trí đọc được lưu | Volume riêng; thử lại truy vấn sau restart |
| M3-COMPAT | Website và metrics tiếp tục hoạt động | Healthz, Django, phpMyAdmin, dashboard |
| M3-REPO | Có commit 2 và 3 riêng | Lưu commit 2 trước giải nén, commit 3 sau kiểm chứng |

Kiểm chứng local: Compose merge đủ 11 dịch vụ và giữ nguyên phần triển khai cũ ngoài log options; binary Loki xác thực config; binary Promtail kiểm tra pipeline trên log mẫu; tests kiểm tra bảo toàn `.env` và lệnh kiểm chứng không báo thành công giả. Docker Linux, quyền đọc log host, giới hạn RAM và Grafana thực tế cần kiểm tra trên VM.

## Phục hồi

Nếu thiếu RAM, dừng riêng `promtail loki`, giữ volume và `.env`. Sau mốc 3 dùng wrapper `logging.sh` cho các thao tác; chạy `up` chỉ với hai file mốc 2 có thể đưa tùy chọn logging về cấu hình cũ khi container được tạo lại.

## Nguồn chính thức

- [Promtail và thời điểm hết hỗ trợ](https://grafana.com/docs/loki/latest/send-data/promtail/)
- [Docker JSON file logging driver](https://docs.docker.com/engine/logging/drivers/json-file/)
- [Ví dụ cấu hình Loki](https://grafana.com/docs/loki/latest/configure/examples/)
- [Loki retention](https://grafana.com/docs/loki/latest/operations/storage/retention/)
- [Loki HTTP API](https://grafana.com/docs/loki/latest/reference/loki-http-api/)
