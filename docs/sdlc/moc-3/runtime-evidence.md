# Minh chứng triển khai mốc 3

## 2026-10-02 — Thu log thực tế trên Ubuntu

Nguồn: ảnh Terminal người dùng gửi từ VM, thư mục `~/quan-ly-sinh-vien`.

- `python3 scripts/check_logging.py` báo Loki ready, tạo request 404 thử nghiệm và in `PASS: website -> Docker JSON -> Promtail -> Loki da nhan marker moi.`
- Kết quả xác nhận một dòng log mới của website đã tới Loki qua Promtail; đây là bằng chứng trên VM, không chỉ kiểm tra cấu hình local.
- Ảnh hiển thị Promtail đang chạy. Phần danh sách container bị cắt, không suy ra trạng thái của toàn bộ 11 dịch vụ từ ảnh này.
- RAM tổng 3,3 GiB, used 1,9 GiB, free 122 MiB, available 1,3 GiB; swap used 1,5 GiB trên tổng 3,3 GiB. Đây là ảnh chụp tại một thời điểm, chưa phải kiểm tra tải kéo dài.

Tại lần ghi nhận Terminal đầu tiên, các truy vấn Grafana chưa được xác minh. Cập nhật bằng chứng bên dưới.

## 2026-10-02 — Ba kết quả Grafana Explore

Nguồn: ba ảnh mới của người dùng trên datasource `Loki QLSV`.

| Truy vấn | Kết quả quan sát |
|---|---|
| `{project="qlsv",service="nginx"}` | Biểu thức rõ trong ảnh; 54 dòng log, có truy cập `/healthz` |
| Lọc request `moc3-demo-404` | Một dòng request thử nghiệm, HTTP 404, thời điểm hiển thị 00:20:54; từ khóa được tô sáng. Ô biểu thức bị cuộn khỏi ảnh, nên ảnh báo cáo cần chụp thêm phần query |
| `sum by (service) (count_over_time({project="qlsv"}[5m]))` | Biểu thức rõ trong ảnh; biểu đồ nhiều chuỗi có nhãn các dịch vụ trong dự án |

Cùng với kết quả script PASS trước đó, đã có bằng chứng thu log và xem/lọc/thống kê trên Grafana thực tế. Chưa có bằng chứng giữ log sau restart, kiểm tra hồi quy website/metrics sau nâng cấp hoặc commit 2/3. Không diễn giải số dòng log là số lỗi; 404 trên đây do chủ động tạo để thử.

## 2026-10-02 — Restart, giữ log và kiểm tra website

Hai ảnh tiếp theo xác nhận:

- `bash scripts/logging.sh restart loki promtail`: cả hai container được khởi động lại.
- `check_logging.py` sau restart tiếp tục báo `PASS`, nhận marker mới.
- Grafana chạy rõ biểu thức `{project="qlsv",service="nginx"} |= "moc3-demo-404"`, hiển thị hai dòng: dòng cũ 00:20:54 và dòng mới 00:28:31. Như vậy log cũ còn sau restart và thu log mới tiếp tục hoạt động; ảnh cũng bổ sung ô biểu thức còn thiếu trước đó.
- `/healthz` trả `{"status": "ok"}` và `HTTP 200` sau restart.
- `git log --oneline -3` cho thấy commit 2 `efb31b9` (giám sát Prometheus/Grafana) nằm trên commit 1 `2fa2384`, nhánh `master`.

Có thể lưu commit 3 cho phần logging. Chưa nhận bằng chứng commit 3, GitHub, các ca CRUD/validation còn thiếu hoặc kiểm tra lại dashboard metrics sau nâng cấp. Các phần đó vẫn cần hoàn thiện trước nghiệm thu toàn bài.

## 2026-10-02 — Commit 3

Ảnh Terminal mới xác nhận commit `e00c2c1` với nội dung thu log bằng Loki/Promtail và LogQL; Git báo 14 file thay đổi. `git log --oneline -3` hiển thị lần lượt `e00c2c1`, `efb31b9`, `2fa2384` trên nhánh `master`. Đã có đủ ba commit local theo ba mốc; chưa có bằng chứng push lên GitHub.
