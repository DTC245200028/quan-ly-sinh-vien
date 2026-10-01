# Intent

## Problem / Opportunity
Người học chưa quen lập trình web, cần làm Đề 2 Hệ thống Quản lý Sinh viên theo PDF học phần Triển khai và Quản trị Hệ thống Phần mềm, trang 1–2.

## Desired Outcome
Giao bộ mã nguồn có thể chuyển vào ~/quan-ly-sinh-vien trên Ubuntu VMware, kèm các lệnh chạy và demo mốc 1.

## Success Criteria
- CRUD sinh viên, lớp, điểm; dữ liệu trong MySQL và nhìn thấy qua phpMyAdmin.
- Toàn bộ dịch vụ qua Docker Compose; truy cập web qua Nginx có security headers.
- Hướng dẫn tạo tài khoản quản trị, dữ liệu giả, kiểm tra sức khỏe và lưu dữ liệu qua restart.
- Source/cấu hình/README sẵn cho commit 1; không đưa bí mật vào Git hoặc ZIP.
- Phân biệt kiểm thử code trên Windows với bằng chứng triển khai container trên Ubuntu.

## Constraints
- Stack đề yêu cầu: MySQL, phpMyAdmin, Nginx, Docker Compose, GitHub; Django là framework trong danh sách gợi ý và đã đề xuất trong chat.
- Người dùng xác nhận Ubuntu 26.04.1, VMware, 4 CPU, RAM 3.3 GiB, ổ / còn 17 GB; Docker 29.1.3 và Compose 2.40.3; hello-world thành công, đã tạo thư mục dự án.
- Ngày 2026-10-01: workspace Windows ban đầu rỗng, chưa có Git; không tự suy diễn có truy cập SSH vào VM.

## Non-Goals
Chưa triển khai monitoring/logging trong mốc 1. Không tự tạo GitHub account, push repository, mở cổng mạng ngoài VM hoặc viết báo cáo kết quả chưa diễn ra.

## Risks / Assumptions
Demo bằng trình duyệt bên trong Ubuntu qua localhost. Dùng Django Admin tiếng Việt cho quản trị; thêm danh mục môn học hỗ trợ điểm, mỗi sinh viên/môn có một điểm thang 0–10. Chưa có yêu cầu kỳ học/cổng sinh viên riêng. RAM hạn chế nên chỉ khởi động mốc 1 và dùng một Gunicorn worker.

## Open Questions
Chưa có thông tin tài khoản GitHub/MSSV; người dùng tự điền khi tạo Git commit và repository.

## References
- D:/Dowloads/De_Tai_Thuc_Hanh - TKQT HTPM K23.pdf, trang 1–2.
- https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
- https://docs.docker.com/compose/how-tos/startup-order/
