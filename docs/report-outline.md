# Dàn ý báo cáo thực hành — Đề 2: Website quản lý sinh viên

Đây là dàn ý và kế hoạch minh chứng, chưa phải báo cáo đã dàn trang hoặc xuất PDF. Dự kiến **12 trang nội dung**, không tính bìa, mục lục và phụ lục; kiểm tra lại số trang sau khi soạn theo mẫu của giảng viên để đáp ứng yêu cầu ít nhất 10 trang.

## Thông tin bìa

- Học phần: Triển khai và Quản trị Hệ thống phần mềm.
- Đề tài 2: Triển khai và quản trị website quản lý sinh viên.
- Sinh viên: **Lâm Duy Lập**.
- MSSV: **DTC245200028**.
- Trường, khoa, lớp, giảng viên hướng dẫn: **chưa cung cấp**; bổ sung theo thông tin thật và mẫu báo cáo của trường.
- Thời gian, địa điểm nộp: chưa cung cấp.

## Bố cục dự kiến

| Trang nội dung | Chương/phần | Nội dung cần viết và minh chứng |
|---|---|---|
| 1 | 1. Mục tiêu và yêu cầu | Giới thiệu bài toán quản lý sinh viên, lớp, điểm số; tóm tắt sáu nhóm công việc: GitHub, website–database–công cụ DB, Nginx, giám sát, thu log và hardening. Phân biệt yêu cầu đề với lựa chọn Django admin của bài làm. |
| 2–3 | 2. Kiến trúc và môi trường | Mô tả Ubuntu 26.04.1 trên VMware, Docker 29.1.3, Compose 2.40.3; cấu trúc dữ liệu sinh viên/lớp/môn học/điểm theo source. Vẽ luồng trình duyệt → Nginx → Django → MySQL; phpMyAdmin quản trị DB; các exporter → Prometheus → Grafana; Docker JSON → Promtail → Loki → Grafana. Giải thích network, volume và cổng localhost. |
| 4–5 | 3. Triển khai website và Nginx | Trình bày cấu trúc source/config, cách dùng Compose và tạo tài khoản quản trị; minh họa CRUD bằng dữ liệu giả. Mô tả phpMyAdmin, `/healthz`, reverse proxy, static CSS và security headers. Nêu rõ dùng HTTP localhost với security headers theo lựa chọn đề cho phép, chưa triển khai HTTPS. |
| 6 | 4. Giám sát bằng Prometheus và Grafana | Giải thích vai trò cAdvisor, Nginx exporter, MySQL exporter; dashboard CPU/RAM container, trạng thái và số liệu Nginx/MySQL. Phân biệt exporter truy cập được với dịch vụ phía sau hoạt động (`nginx_up`, `mysql_up`). |
| 7–8 | 5. Thu log và truy vấn LogQL | Mô tả cách giữ nhãn project/service và thu log qua Promtail. Trình bày ba truy vấn bên dưới cùng ảnh kết quả; giải thích 404 là request thử nghiệm. Mô tả log cũ còn và log mới tiếp tục được thu sau restart. Ghi giới hạn Promtail đã EOL nhưng được dùng đúng công cụ đề yêu cầu. |
| 9 | 6. Hardening và bảo vệ cấu hình | Trình bày bốn nhóm H1–H4 trong bảng dưới, mỗi nhóm gắn kết quả kiểm tra thực tế. Bổ sung quyền `.env`, `.gitignore` và kiểm tra lịch sử Git. Nêu ngoại lệ cAdvisor đặc quyền, Promtail root để đọc log; không khẳng định mọi container non-root. |
| 10–11 | 7. Kiểm thử, vận hành và GitHub | Lập bảng ca kiểm thử/kết quả, bảo toàn dữ liệu sau restart, hồi quy sau nâng cấp, lỗi đã gặp và cách xử lý có bằng chứng. Trình bày ba commit, cấu trúc repository/README và link GitHub sau khi push được xác nhận. Các ca còn thiếu phải để “chưa xác minh”. |
| 12 | 8. Kết luận và tài liệu tham khảo | Đối chiếu kết quả với yêu cầu; nêu giới hạn môi trường VM, tài nguyên và phần chưa kiểm chứng. Liệt kê tài liệu chính thức thực sự đã sử dụng, tên phiên bản và ngày truy cập; không ghi đã nộp bài khi chưa có bằng chứng. |

Mục lục tạo tự động sau khi hoàn thiện các tiêu đề. Dành phần lớn nội dung cho triển khai, giám sát, logging và quản trị; tránh kéo dài lý thuyết để đủ trang.

## Kết quả có thể sử dụng trong báo cáo

Căn cứ các bản ghi runtime ngày 01–02/10/2026; bằng chứng do sinh viên gửi từ VM, không phải kết quả Codex chạy Docker trực tiếp trên Windows. Các cập nhật mới hơn bên dưới thay thế trạng thái “chưa xác minh” ở những bản ghi cũ.

| Hạng mục | Kết quả đã có bằng chứng | Phần còn cần hoàn thiện |
|---|---|---|
| Website/DB | Django admin và phpMyAdmin đăng nhập được; `/healthz` HTTP 200; SVDEMO01 và điểm 9 còn sau restart | Minh chứng đầy đủ CRUD, đặc biệt xóa và validation; kiểm tra dữ liệu cũ sau nâng cấp cuối |
| Nginx | Reverse proxy hoạt động, CSS hiển thị và đủ security headers | Chọn ảnh rõ lệnh/kết quả để đưa vào báo cáo |
| Metrics | Dashboard có CPU/RAM và metrics Nginx/MySQL thực tế | Chụp dữ liệu mới trong khoảng thời gian hiện tại sau nâng cấp logging |
| Logs | Marker mới tới Loki qua Promtail; ba kết quả LogQL; sau restart thấy cả marker cũ và mới | Chọn ảnh sạch, thấy đầy đủ truy vấn và khoảng thời gian |
| Hardening | H1: app UID/GID 10001; H2: root filesystem chỉ đọc, drop ALL capabilities, no-new-privileges; H3: MySQL không publish cổng, chỉ mạng data nội bộ; H4: HTTP 200 và security headers | Trình bày H2 là một nhóm, giải thích đúng giới hạn từng biện pháp |
| `.env` | Quyền 600, được ignore, không nằm trong tracked files và lịch sử của đường dẫn `.env` | Rà ảnh, backup và tài liệu trước push; không suy rộng thành toàn repository chắc chắn không có bí mật |
| Git local | Commit 1 `2fa2384`; commit 2 `efb31b9`; commit 3 `e00c2c1` trên `master` | Chưa có bằng chứng push thành công lên GitHub |
| Tài khoản GitHub | Ảnh lệnh API trên Ubuntu sau đổi tên trả về `DTC245200028`, trùng MSSV | Chưa có URL repository hoặc bằng chứng push |

Không dùng ảnh RAM tại một thời điểm làm bằng chứng kiểm thử tải kéo dài. Không kết luận mọi ca CRUD đạt chỉ từ việc đăng nhập được và dữ liệu tồn tại sau restart.

Ba truy vấn dùng trong chương 5:

```logql
{project="qlsv",service="nginx"}
```

```logql
{project="qlsv",service="nginx"} |= "moc3-demo-404"
```

```logql
sum by (service) (count_over_time({project="qlsv"}[5m]))
```

## Danh mục ảnh minh chứng cần chọn hoặc bổ sung

| Nhóm ảnh | Yêu cầu ảnh sạch |
|---|---|
| Kiến trúc/môi trường | Sơ đồ luồng và network đọc được; Terminal thấy phiên bản và trạng thái dịch vụ; không suy ra toàn bộ stack từ ảnh bị cắt |
| Website/CRUD | Danh sách và thao tác trên dữ liệu giả của sinh viên, lớp, điểm; bổ sung ca xóa, điểm ngoài 0–10, trùng sinh viên–môn và bảo vệ bản ghi đang được tham chiếu |
| phpMyAdmin/dữ liệu | Thấy database và kết quả truy vấn; không cắt mất giá trị cần chứng minh; tránh thông tin cá nhân thật |
| Nginx/hardening | Cả lệnh và kết quả HTTP 200/headers, UID, quyền container, mạng DB; có thể ghép các lệnh ngắn trong một ảnh rõ chữ |
| Grafana metrics | Dashboard với khoảng thời gian hiện tại, tên panel và chuỗi dữ liệu mới sau nâng cấp |
| Grafana logs/restart | Ba ảnh thấy đầy đủ LogQL/kết quả; ảnh log cũ/mới sau restart và kết quả script thu marker |
| Git/GitHub | Ba commit local; sau khi hoàn tất, trang repository có source/config/README và lịch sử ba commit, tài khoản đúng tên đã xác nhận |
| Bảo vệ `.env` | Chỉ chụp quyền 600, quy tắc ignore và kết quả kiểm tra tracking/history; **không chụp nội dung `.env`** |

Mỗi ảnh đặt số, tiêu đề, chú thích “đang kiểm tra gì” và kết luận phù hợp. Không dùng ảnh từng lộ thông tin đăng nhập Grafana khi chưa che/cắt; không đưa mật khẩu, token hoặc dữ liệu thật của sinh viên vào báo cáo/GitHub. Dàn ý này không sao chép hay tạo thêm ảnh.

## Việc cần chốt trước khi hoàn thiện bản nộp

1. Bổ sung thông tin trường/lớp/giảng viên và mẫu báo cáo thực tập được yêu cầu.
2. Hoàn tất các ca CRUD/validation còn thiếu, kiểm tra dữ liệu và metrics mới sau nâng cấp; cập nhật kết quả theo bằng chứng thật.
3. Dùng tài khoản `DTC245200028` đã xác nhận để tạo repository và push lịch sử; kiểm tra repository rồi điền URL đã xác minh.
4. Chèn ảnh sạch, chú thích, sơ đồ và tài liệu tham khảo; tạo mục lục, dàn trang, kiểm tra ít nhất 10 trang và xuất bản nộp theo yêu cầu giảng viên.

Nguồn đối chiếu nội bộ: [mốc 1](sdlc/moc-1/runtime-evidence.md), [mốc 2](sdlc/moc-2/runtime-evidence.md), [mốc 3](sdlc/moc-3/runtime-evidence.md), [kiểm tra trước khi nộp](sdlc/final-verification/operations.md). Đây là ghi nhận bằng chứng và hướng dẫn, không thay thế ảnh gốc hoặc yêu cầu của giảng viên.
