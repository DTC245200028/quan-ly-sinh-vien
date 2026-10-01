# Mốc 3 — Kết quả kiểm chứng local

Cập nhật ngày 2026-10-02. Đây là kiểm chứng tại workspace Windows, chưa phải kết quả triển khai container trên Ubuntu VMware.

## Thành phần đã chuẩn bị

- Overlay `compose.logging.yaml`: thêm Loki 3.7.8, Promtail 3.6.11 và nhãn log cho 11 dịch vụ.
- Loki dùng TSDB v13/filesystem, volume riêng, retention 24 giờ, giới hạn RAM 384 MiB.
- Promtail đọc Docker JSON chỉ đọc, lọc đúng dự án `qlsv`, lưu positions, giới hạn RAM 128 MiB. Tắt tracing không dùng trong lab.
- Datasource `Loki QLSV` được thêm vào provisioning có sẵn của Grafana.
- Scripts chuẩn bị đường dẫn log, wrapper ba file Compose và kiểm tra marker mới từ website đến Loki.
- Hướng dẫn lưu commit 2 trước khi giải nén, triển khai, demo ba truy vấn, kiểm tra sau restart và lưu commit 3.

## Kiểm tra đã chạy

| Kiểm tra | Kết quả |
|---|---|
| Compose CLI 2.40.3 `config --quiet` với ba file | Đạt; đủ 11 dịch vụ |
| So sánh cấu hình với mốc 2 | Chín dịch vụ cũ chỉ đổi logging options; giữ nguyên volumes, networks, ports và các cấu hình khác |
| Ranh giới dịch vụ mới | Loki chỉ publish loopback; Promtail không publish; hai dịch vụ chỉ nối monitoring |
| Loki 3.7.8 `-verify-config=true` | Đạt với cấu hình bàn giao |
| Loki native Windows chạy thật | Ready, nhận log thử qua API và trả kết quả cho cả ba LogQL; chỉ đổi đường dẫn dữ liệu và cổng sang thư mục/cổng thử nghiệm |
| Promtail 3.6.11 `-check-syntax` | Đạt |
| Promtail native đọc file JSON thử và dry-run | Giữ hai dòng `qlsv/nginx`, `qlsv/app`; loại năm dòng ngoài dự án, thiếu nhãn hoặc sai JSON; giữ timestamp/stream/message, bỏ filename và JSON wrapper |
| Promtail dry-run với chính cấu hình bàn giao qua stdin | Exit 0, hai dòng được giữ và năm dòng bị loại |
| `python -m unittest discover -s scripts -p test_logging.py -v` | 17/17 đạt: bảo toàn `.env`, kiểm tra đường dẫn/driver, từ chối marker sai và timeout, chỉ báo PASS khi có marker mới đúng dịch vụ |
| Bash syntax, YAML, LF/no BOM | Đạt cho các script/config mới |

Các binary kiểm chứng tải từ GitHub release chính thức của Grafana Loki, đối chiếu SHA256 của từng asset trước khi chạy. Dữ liệu thử là dữ liệu giả, không đọc `.env` thật của người dùng. Binary, cache và log thử trong `tmp/` không nằm trong bộ bàn giao.

Lần dry-run đầu với tracing mặc định chờ khởi tạo lâu trong môi trường Windows. Cấu hình đã tắt tracing không dùng; phép thử độc lập và phép thử cuối đều kết thúc thành công. Điều này không thay đổi pipeline thu log của bài.

## Cần kiểm chứng trên Ubuntu

- Docker pull/start, quyền mount log host và quyền volume với các image Linux.
- `check_logging.py` tìm được marker mới từ website thật qua Docker → Promtail → Loki.
- Grafana Explore trả kết quả cho ba truy vấn, marker cũ còn sau restart.
- Website, MySQL/phpMyAdmin và dashboard metrics vẫn hoạt động.
- RAM, swap, restart/OOM và đĩa ở mức phù hợp trên VM 3,3 GiB RAM.
- Commit 2 được lưu trước khi chép bộ này; commit 3 chỉ tạo sau khi kiểm tra thực tế đạt.

Không có Docker daemon/SSH vào VM từ workspace này. Các kiểm tra local không thay thế các kết quả trên.
