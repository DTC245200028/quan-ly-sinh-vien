# Mốc 2 — triển khai và kiểm chứng

Ngày 2026-10-01. Môi trường kiểm tra local: Windows/PowerShell/Python3.12. VM Ubuntu do người dùng điều khiển; chưa chạy mốc2 trênVM.

## Thay đổi

- compose.monitoring.yaml thêm5dịch vụ giám sát, ghép cùng mốc1. MySQL/app/phpMyAdmin không đổi; Nginx chỉ thêm mount serverstatus nội bộ8082.
- Prometheus có4jobs30s/lần; Grafana tự nạp datasource/dashboardqlsv-overview gồm13panel số liệu và các hàng/ghi chú.
- Userqlsv_exporter chỉ lấy global_status/global_variables; mật khẩu monitoring bổ sung vào.env, không đổi bí mật mốc1. SQL chạy qua stdin trong containerdb bằng rootlocal, không đưa mật khẩu vào argv.
- scripts/monitoring.sh quản lý cả2fileCompose; hướng dẫn commit1 trước nâng cấp, commit2 sau kiểm chứng. README/envexample/gitignore cập nhật; loại file backup khỏiGit.

## Kiểm tra đã chạy

| Kiểm tra | Kết quả |
|---|---|
| Docker Compose2.40.3 config --quiet với2file và envgiả | PASS;9dịch vụ, schema/ghép hợp lệ |
| So JSON configbase/merged | PASS: app/db/phpMyAdmin y nguyên; Nginx chỉ thêm1volume; giữ projectqlsv |
| Network/ports từ configmerged | PASS: db chỉdata, khôngpublish;exporters/cAdvisor khôngpublish;mọiportpublish bind127.0.0.1 và có networknoninternal |
| promtool3.13.3 check config | PASS: prometheus.yml hợp lệ |
| promtool check rules cho13exprdashboard | PASS: thay biếnGrafana bằng giá trị kiểm tra hợp lệ,13rulesfound |
| Unittest discover scripts/test_monitoring.py | PASS15test;SKIP1testPOSIXpermission dohostWindows |
| YAML/JSON | PASS5YAML vàdashboardJSON; cấu trúc/provisioning được đối chiếu |
| Bash syntax, LF | PASS hai script; khôngCR trong.sh |
| Triển khai5image trênVM | NOT RUN; người dùng thực hiện theo guide |
| Nginx -t / exporterSQL live / metrics / dashboardrender | NOT RUN local; cần runtimeVM |

Tests bảo vệ byte.env cũ, idempotence, cấu hìnhmộtphần, từ chối duplicate/empty/invalid trước ghi, SQLpassword qua stdin và che tronglỗi. Không chạy lại DjangoCRUDtests vìapp không đổi.

Compose/promtool lấy từ releaseGitHub chính thức, đối chiếuSHA256 của upstream trước chạy; chỉ đặt trong tmp/, không đóng gói. Lần tải đầu bị sandbox chặn socket, retry download được auto-review cho phép. Không cài Docker hoặc khởi tạo daemonlocal.

## Nghiệm thu còn lại

Thực hiện guide:4targetsUP, nginx_up/mysql_up=1, cóCPU/RAM theo serviceqlsv, dashboard hiển thịsốliệu, website vàDBtool còn dữ liệu. `Up` củaexporter không thay thế chỉ sốkết nối. Chưa có commit/hashGitHub hoặc kếtquảmốc2VM; không coi testsconfig là deploymentpassed.

Giới hạn: RAM3.3GiB cần kiểm tra thật; cAdvisor privileged đọc tài nguyênhost; Prometheusretention512MB chỉáp dụngblocks khônggồmtoànbộWAL/head. Grafana đổi mật khẩu quaUI saukhởi tạo phải ghi nhớ; sửa.env không resetvolume. Có thểstop riêng5dịch vụđểgiảmtải, giữdatavolumes.
