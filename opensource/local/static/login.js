const I18N = {
    zh: {
        title: '客户品牌墙',
        subtitle: '请登录以继续访问',
        username: '用户名',
        username_ph: '请输入用户名',
        password: '密码',
        password_ph: '请输入密码',
        login: '登录',
        logging_in: '登录中...',
        redirect_text: '登录后将跳转到',
        display_link: '展示页',
        admin_link: '管理后台',
        footer: 'Logo Wall &copy; 2026',
        error_invalid: '用户名或密码错误',
        error_server: '服务器连接失败',
        error_empty: '请输入用户名和密码',
    },
    en: {
        title: 'Client Logo Wall',
        subtitle: 'Please sign in to continue',
        username: 'Username',
        username_ph: 'Enter your username',
        password: 'Password',
        password_ph: 'Enter your password',
        login: 'Sign In',
        logging_in: 'Signing in...',
        redirect_text: 'After login, go to',
        display_link: 'Display Page',
        admin_link: 'Admin Panel',
        footer: 'Logo Wall &copy; 2026',
        error_invalid: 'Invalid username or password',
        error_server: 'Server connection failed',
        error_empty: 'Please enter username and password',
    }
};

let lang = localStorage.getItem('lw_lang') || 'zh';

function toggleLang() {
    lang = lang === 'zh' ? 'en' : 'zh';
    localStorage.setItem('lw_lang', lang);
    applyLang();
}

function applyLang() {
    const t = I18N[lang];
    document.getElementById('login-title').textContent = t.title;
    document.getElementById('login-subtitle').textContent = t.subtitle;
    document.getElementById('label-username').textContent = t.username;
    document.getElementById('username').placeholder = t.username_ph;
    document.getElementById('label-password').textContent = t.password;
    document.getElementById('password').placeholder = t.password_ph;
    document.getElementById('login-btn').textContent = t.login;
    document.getElementById('redirect-text').textContent = t.redirect_text;
    document.getElementById('login-footer').innerHTML = t.footer;
    document.getElementById('lang-btn').textContent = lang === 'zh' ? 'EN' : '中文';
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';

    // Determine redirect target
    const redirect = getRedirectTarget();
    const linkEl = document.getElementById('redirect-link');
    if (redirect === 'admin') {
        linkEl.textContent = t.admin_link;
        linkEl.href = '/admin';
    } else {
        linkEl.textContent = t.display_link;
        linkEl.href = '/';
    }
}

function getRedirectTarget() {
    const params = new URLSearchParams(window.location.search);
    return params.get('redirect') || 'display';
}

function showError(msg) {
    const el = document.getElementById('error-msg');
    el.textContent = msg;
    el.classList.add('show');
}

function hideError() {
    document.getElementById('error-msg').classList.remove('show');
}

async function handleLogin(e) {
    e.preventDefault();
    hideError();

    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const t = I18N[lang];

    if (!username || !password) {
        showError(t.error_empty);
        return;
    }

    const btn = document.getElementById('login-btn');
    btn.disabled = true;
    btn.textContent = t.logging_in;

    try {
        const form = new URLSearchParams();
        form.append('username', username);
        form.append('password', password);

        const resp = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: form.toString(),
        });

        const data = await resp.json();

        if (resp.ok && data.ok) {
            // Store token and user info
            localStorage.setItem('lw_token', data.token);
            localStorage.setItem('lw_user', JSON.stringify(data.user));
            // Admin panel shows a "change your password" banner while this is set
            if (data.password_weak) localStorage.setItem('lw_password_weak', '1');
            else localStorage.removeItem('lw_password_weak');

            // Redirect
            const redirect = getRedirectTarget();
            if (redirect === 'admin' && data.user.role === 'admin') {
                window.location.href = '/admin';
            } else {
                window.location.href = '/';
            }
        } else {
            showError(data.detail || t.error_invalid);
        }
    } catch (err) {
        showError(t.error_server);
    } finally {
        btn.disabled = false;
        btn.textContent = t.login;
    }
}

// Check if already logged in
async function checkExistingAuth() {
    const token = localStorage.getItem('lw_token');
    if (!token) return;

    try {
        const resp = await fetch('/api/auth/check', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        const data = await resp.json();
        if (data.ok) {
            // Already logged in, redirect
            const redirect = getRedirectTarget();
            if (redirect === 'admin' && data.user.role === 'admin') {
                window.location.href = '/admin';
            } else {
                window.location.href = '/';
            }
        }
    } catch (e) {
        // Ignore errors, show login form
    }
}

// Init
applyLang();
checkExistingAuth();
document.getElementById('username').focus();
