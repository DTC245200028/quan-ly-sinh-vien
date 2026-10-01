# Minh chứng triển khai mốc 2

Cập nhật ngày 2026-10-02. Nguồn bằng chứng là ảnh và output người dùng gửi từ Ubuntu VMware. Codex chưa kết nối thực thi trực tiếp vào VM; các kết quả dưới đây không phải kết quả chạy Docker tại workspace Windows.

| Hạng mục | Kết quả quan sát được |
|---|---|
| Grafana | Đăng nhập thành công, dashboard `QLSV - Giám sát hệ thống` được nạp sẵn |
| Thu thập metrics | Bốn thẻ Prometheus, cAdvisor, Nginx exporter, MySQL exporter đều hiển thị “Thành công” |
| Container | Biểu đồ CPU và RAM có chuỗi số liệu thực tế |
| Nginx | Panel trạng thái hiển thị “Thành công”; các biểu đồ web server có số liệu |
| MySQL | Panel trạng thái hiển thị “Thành công”; các biểu đồ database có số liệu |
| Git | Ảnh xác nhận commit 1 `2fa2384` trên nhánh `master`; chưa có bằng chứng commit 2 |
| RAM | Tổng khoảng 3,3 GiB; `available` khoảng 1,3 GiB, `free` 126 MiB |
| Swap | Đang sử dụng khoảng 1,4 GiB; chưa có xác nhận nâng RAM VM |

Các panel trạng thái Nginx/MySQL dùng `nginx_up` và `mysql_up`, bổ sung bằng chứng về kết nối tới dịch vụ phía sau exporter. Cùng với các biểu đồ có dữ liệu, ảnh hiện có xác nhận giám sát đủ container, web server và database; không chỉ dựa vào trạng thái `up` của exporter.

Thông tin commit 1 ở đây cập nhật trạng thái “chưa xác minh” trong bản minh chứng mốc 1 trước đó. Cần lưu commit 2 trước khi giải nén bộ mốc 3. Chưa có bằng chứng triển khai Loki/Promtail, ba truy vấn LogQL hoặc commit 3 trên VM.

Chỉ lưu tóm tắt bằng chứng, không lưu ảnh hay mật khẩu trong tài liệu này. Cắt hoặc che phần mật khẩu trong ảnh trước khi đưa vào báo cáo hoặc GitHub.
