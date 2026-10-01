# Minh chứng triển khai mốc 1 — 2026-10-01

Môi trường do người dùng cung cấp: Ubuntu26.04.1 trên VMware, Docker29.1.3, Compose2.40.3,4CPU/RAM3.3GiB. Codex không điều khiển trực tiếp VM; bằng chứng là ảnh/output và xác nhận của người dùng.

| Hạng mục | Kết quả có bằng chứng |
|---|---|
| Compose4dịch vụ | PASS: app/db/nginx/phpmyadmin đều healthy sau restart |
| Published ports | PASS: Nginx127.0.0.1:8080->80; phpMyAdmin127.0.0.1:8081->80 |
| Health ứng dụng và MySQL | PASS: GET/healthz HTTP200, JSON statusok |
| Nginx/securityheaders | PASS: Servernginx; nosniff, X-Frame-OptionsDENY, Referrer-Policysame-origin, Permissions-Policy camera/microphone/geolocation tắt |
| Django login và CSS | PASS: ảnh trang quản trị tiếngViệt đăng nhập thành công |
| phpMyAdmin login | PASS: kết nối db:3306 bằng user ứng dụng, databaseqlsv hiển thị |
| Câu SELECT nối SV/môn/điểm | PARTIAL: ảnh cho thấy truy vấn thành công1dòng; phần giá trị bị cắt |
| Lưu dữ liệu qua restart | PASS theo xác nhận người dùng: vẫn có SVDEMO01 và điểm9 sau restart |
| Xóa dữ liệu test/validation biên | NOT VERIFIED: đã hướng dẫn, chưa nhận bằng chứng riêng |
| Nonroot/quyền mạng thực tế | NOT VERIFIED riêng trênVM; đã có cấu hình và lệnh kiểm tra trongdemo |
| Commit1/GitHub | NOT VERIFIED: chưa nhận hash hoặc linkrepo |

Lỗi đã gặp: WordPress/cAdvisor bài cũ chiếm8080/8081; người dùng yêu cầu dừng bài cũ. phpMyAdmin đã sửa networkedge+data và probePHPCLI allow_url_fopen. Nginx bị mất attachment(networks={}), tạo lại riêng container theoCompose; ảnh mới cho thấy healthy và HTTP200.

Cảnh báo phpMyAdmin không có cột duy nhất ở kết quảJOIN nói về chỉnh sửa lưới, không chứng minh truy vấn thất bại. Không suy rộng các bằng chứng này sang mốc2/mốc3 chưa chạy tại lần ghi nhận đầu tiên.

## Cập nhật ngày 2026-10-02

Ảnh mới xác nhận commit 1 `2fa2384` trên nhánh `master`; cả ba commit mốc đã được ghi nhận. Bốn nhóm hardening và các phép kiểm tra riêng cho `.env` đã có bằng chứng VM tại [kiểm tra cuối](../final-verification/operations.md). Các mục chưa xác minh tương ứng trong bảng đầu là trạng thái lịch sử. GitHub và các ca CRUD/validation còn thiếu vẫn chưa được xác minh.
