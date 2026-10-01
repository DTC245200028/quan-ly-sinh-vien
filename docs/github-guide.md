# Đưa bài thực hành lên GitHub

Sinh viên: **Lâm Duy Lập — DTC245200028**. Tài khoản GitHub đang sử dụng: **`DTC245200028`**. GitHub CLI đã được đăng nhập và thiết lập xác thực Git trên Ubuntu; ảnh Terminal ngày 02/10/2026 sau đổi tên xác nhận `gh api user --jq .login` trả về `DTC245200028`. Chưa có bằng chứng tạo repository hoặc push. Tên repository dự kiến: `quan-ly-sinh-vien`.

## 1. Tài khoản đã xác nhận

Các bước tiếp theo dùng tài khoản `DTC245200028` vừa xác nhận. Username đã trùng MSSV theo yêu cầu PDF; phần tạo repository và đưa lịch sử commit lên GitHub vẫn cần thực hiện.

Trên VM đang dùng, có thể chuyển sang bước cập nhật tài liệu bên dưới; không cần đăng nhập lại. Phần 3 dành cho lần thiết lập trên máy khác hoặc khi chưa đăng nhập.

## 2. Cập nhật tài liệu trong Ubuntu

Bộ ZIP dưới đây chỉ cập nhật README và tài liệu. Dùng sau khi đã triển khai đủ ba mốc. Thư mục chia sẻ VMware đã dùng trong bài là `/mnt/hgfs/baithuchanh`:

```bash
cd ~/quan-ly-sinh-vien
unzip -l /mnt/hgfs/baithuchanh/quan-ly-sinh-vien-hoan-thien-tai-lieu.zip
unzip -o /mnt/hgfs/baithuchanh/quan-ly-sinh-vien-hoan-thien-tai-lieu.zip -d .
git diff --stat
git status --short
```

Đọc lại các thay đổi trước khi commit, nhất là username đã xác nhận và các ca kiểm thử còn thiếu. Chỉ thêm những file tài liệu của gói:

```bash
git add README.md docs/github-guide.md docs/report-outline.md docs/sdlc/final-verification/operations.md docs/sdlc/moc-1/runtime-evidence.md docs/sdlc/moc-2/runtime-evidence.md docs/sdlc/moc-3/runtime-evidence.md
git diff --cached --stat
git diff --cached
```

Nếu nội dung đúng và không có thông tin đăng nhập, tạo commit tài liệu:

```bash
git commit -m "docs: hoan thien README va huong dan nop bai"
git log --oneline -4
```

Ba commit đã xác nhận trên VM là `2fa2384`, `efb31b9`, `e00c2c1`. Commit tài liệu bổ sung giữ nguyên lịch sử ba mốc. `plan.md` có thể tiếp tục ở trạng thái untracked; không cần thêm file đó để push.

## 3. Đăng nhập GitHub CLI trên Ubuntu

VM hiện tại đã hoàn tất bước này. Khi cần thiết lập trên Ubuntu khác, cài `gh` từ kho Ubuntu đang cấu hình:

```bash
sudo apt update
sudo apt install -y gh
gh auth login --hostname github.com --git-protocol https --web
```

Làm theo mã xác thực và trang đăng nhập do Terminal hiển thị, chọn đúng tài khoản `DTC245200028`. Nhập mã trên GitHub, không gửi mã đó trong chat hoặc đưa vào báo cáo. Lệnh dùng luồng đăng nhập trình duyệt của [GitHub CLI](https://cli.github.com/manual/gh_auth_login).

Sau khi đăng nhập thành công:

```bash
gh auth setup-git --hostname github.com
gh api user --jq .login
```

Lệnh đầu cấu hình Git dùng thông tin xác thực của `gh`; lệnh sau chỉ in username để kiểm tra đang dùng đúng tài khoản. [Tài liệu setup-git](https://cli.github.com/manual/gh_auth_setup-git).

## 4. Tạo repository và push lịch sử hiện có

Trước bước này, rà những file sẽ đưa lên: ảnh, tài liệu và backup không chứa thông tin đăng nhập. Các phép kiểm tra riêng cho `.env` đã đạt trên VM, xem [biên bản kiểm tra](sdlc/final-verification/operations.md). Không đưa ảnh Terminal từng hiển thị mật khẩu Grafana vào repository.

Trong thư mục bài làm, xem tên các remote đã có:

```bash
cd ~/quan-ly-sinh-vien
git remote
```

Nếu chưa có remote và chưa tạo repository trên GitHub, dùng trình hướng dẫn:

```bash
gh repo create
```

Chọn đưa repository local hiện có lên GitHub, đường dẫn `.`, owner là tài khoản vừa xác nhận, tên `quan-ly-sinh-vien`, remote `origin`. Tự chọn mức hiển thị phù hợp cách nộp bài: **Public** cho phép mọi người xem, **Private** cần cấp quyền cho giảng viên. Chọn push các commit hiện có khi trình hướng dẫn hỏi. Lệnh có chế độ tương tác để tạo repository từ source local. [Tài liệu repo create](https://cli.github.com/manual/gh_repo_create).

Nếu đã có `origin`, hoặc đã tạo repository trên web, kiểm tra repository đích trước khi làm tiếp; không tạo trùng hay ghi đè remote. Khi tạo trên web để nhận source hiện có, để repository trống, không khởi tạo README, license hoặc `.gitignore`. [Hướng dẫn đưa mã local lên GitHub](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).

## 5. Kiểm tra bài trên GitHub

Sau khi trình hướng dẫn báo push thành công, với nhánh `master` và remote `origin` của bài:

```bash
git rev-parse HEAD
git ls-remote origin refs/heads/master
gh repo view --web
```

Hai lệnh Git phải cho cùng mã commit ở đầu dòng. Trên trình duyệt, kiểm tra đúng owner, có README/source/ba file Compose, lịch sử còn đủ ba commit mốc và commit tài liệu. Ghi URL repository thực tế vào README và báo cáo khi đã xác nhận. Không suy ra push thành công chỉ từ việc có commit local.

Báo cáo thực hành chưa hoàn thành; xem [dàn ý và phần minh chứng còn thiếu](report-outline.md).
