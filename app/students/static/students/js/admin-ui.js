'use strict';

// Progressive enhancement: navigation and forms remain usable without JavaScript.
document.documentElement.classList.add('qlsv-js');
const resultsTable = document.querySelector('#changelist .results');
if (resultsTable) {
    resultsTable.tabIndex = 0;
    resultsTable.setAttribute('role', 'region');
    resultsTable.setAttribute('aria-label', 'Bảng dữ liệu, có thể cuộn ngang để xem thêm cột');
    const tableHint = document.createElement('p');
    tableHint.className = 'ui-table-hint';
    tableHint.textContent = 'Vuốt ngang để xem thêm cột.';
    resultsTable.before(tableHint);
}
const menuToggle = document.getElementById('qlsv-menu-toggle');
const sidebar = document.getElementById('qlsv-sidebar');
if (menuToggle && sidebar) {
    const setMenu = (open) => {
        document.body.classList.toggle('ui-menu-open', open);
        menuToggle.setAttribute('aria-expanded', String(open));
        menuToggle.setAttribute('aria-label', open ? 'Đóng menu quản lý' : 'Mở menu quản lý');
    };
    menuToggle.addEventListener('click', () => setMenu(menuToggle.getAttribute('aria-expanded') !== 'true'));
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && menuToggle.getAttribute('aria-expanded') === 'true') {
            setMenu(false);
            menuToggle.focus();
        }
    });
    document.addEventListener('click', (event) => {
        if (!sidebar.contains(event.target) && !menuToggle.contains(event.target)) setMenu(false);
    });
    window.matchMedia('(min-width: 1025px)').addEventListener('change', () => setMenu(false));
}

const passwordToggle = document.getElementById('ui-password-toggle');
const passwordInput = document.getElementById('id_password');
if (passwordToggle && passwordInput) {
    passwordToggle.hidden = false;
    passwordToggle.addEventListener('click', () => {
        const show = passwordInput.type === 'password';
        passwordInput.type = show ? 'text' : 'password';
        passwordToggle.setAttribute('aria-pressed', String(show));
        passwordToggle.setAttribute('aria-label', show ? 'Ẩn mật khẩu' : 'Hiện mật khẩu');
    });
}
