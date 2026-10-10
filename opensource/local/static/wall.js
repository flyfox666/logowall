// ============================================================
// DATA STATE
// ============================================================
let allRecords = [];
let activeOffice = new Set();
let activeRegion = new Set();
let activeDept = new Set();
let activeOwner = new Set();
let activeYear = new Set();
let searchQuery = '';
let selectMode = false;
const selectedIds = new Set();
let siteTitle = '客户品牌墙';
let siteTagline = '';
let siteTitleEn = 'CLIENT LOGO WALL';
let siteFooter = '连接  ·  协作  ·  共创价值';
let siteTheme = 'classic';
let sitePattern = 'none';
let siteCustomPrimary = '';
let siteCustomAccent = '';
let siteTaglineEn = '';
let siteFooterEn = '';

// ============================================================
// I18N (zh / en)
// ============================================================
const I18N = {
    zh: {
        search_ph: '搜索客户名称、城市、负责人...',
        region: '区域', city: '城市', dept: '业务线', owner: '负责人',
        all: '全部', owner_all: '全部负责人',
        show_before: '显示', show_after: '家',
        export_poster: '导出海报', export_poster_title: '将当前筛选结果导出为活动海报',
        select_mode: '多选', select_title: '自由勾选客户后导出海报',
        select_bar_label: '家客户已选中', export_selected: '导出选中',
        clear_selection: '清除', exit_select: '退出多选',
        poster_hint_sel_pre: '将导出勾选的 ', poster_hint_sel_post: ' 家客户',
        poster_alert_none_selected: '请先勾选要导出的客户',
        theme_title: '主题与背景', theme_colors: '主题配色', theme_bg: '背景纹理',
        theme_reset: '恢复站点默认',
        collapse_header: '收起 / 展开头部', collapse_toolbar: '收起 / 展开搜索与筛选',
        stat_total: '客户总数', stat_offices: '覆盖城市', stat_depts: '业务线',
        loading: '正在加载客户数据...',
        empty: '未找到匹配的客户',
        empty_data: '暂无客户数据，请联系管理员在后台添加',
        footer_admin: '数据维护请前往', footer_admin_link: '管理后台',
        poster_modal_title: '导出品牌墙海报',
        poster_size: '海报尺寸', poster_main: '主标题', poster_sub: '副标题',
        poster_quality: '清晰度', poster_showinfo: '卡片显示', poster_footer: '页脚文字',
        quality_std: '标准（1×，适合屏幕预览）',
        quality_hd: '高清（2×，推荐打印/分享）',
        quality_uhd: '超清（3×，大尺寸印刷）',
        pf_city: '城市 / 区域', pf_dept: '业务线', pf_owner: '负责人', pf_coop: '合作时间',
        coop_year: '合作年份', coop_since: '合作于 ', clear_filters: '清除筛选',
        size_portrait: '竖版海报 3:4（1800×2400）',
        size_screen: '现场大屏 16:9（1920×1080）',
        size_a4: 'A4 打印 300dpi（2480×3508）',
        poster_refresh: '刷新预览', poster_download: '下载 PNG 海报',
        poster_loading: '正在绘制海报，抓取 Logo 图片中...',
        poster_hint_pre: '将导出当前筛选显示的 ', poster_hint_post: ' 家客户（调整筛选后再导出即可只包含目标客户）',
        poster_alert_empty: '当前筛选下没有可见客户，请先调整筛选条件',
        poster_fail: '导出失败，请重试', poster_fail2: '导出失败：',
        clients_word: '家客户',
        owner_label: '负责人', owner_title: (o) => '负责人：' + o,
        owner_search_ph: '搜索负责人...', owner_empty: '没有匹配的负责人',
        dark_mode: '夜间模式', dark_mode_title: '日间 / 夜间模式',
        login: '登录', logout: '退出',
        signed_in_as: (n) => '当前登录：' + n,
    },
    en: {
        search_ph: 'Search clients, cities, owners...',
        region: 'Region', city: 'City', dept: 'Business line', owner: 'Owner',
        all: 'All', owner_all: 'All owners',
        show_before: 'Showing', show_after: 'clients',
        export_poster: 'Export poster', export_poster_title: 'Export the current filtered clients as an event poster',
        select_mode: 'Select', select_title: 'Pick clients freely, then export a poster',
        select_bar_label: 'clients selected', export_selected: 'Export selected',
        clear_selection: 'Clear', exit_select: 'Exit',
        poster_hint_sel_pre: 'Will export the ', poster_hint_sel_post: ' selected clients',
        poster_alert_none_selected: 'Please select clients to export first',
        theme_title: 'Theme & background', theme_colors: 'Theme colors', theme_bg: 'Background',
        theme_reset: 'Reset to site default',
        collapse_header: 'Collapse / expand header', collapse_toolbar: 'Collapse / expand search & filters',
        stat_total: 'Total clients', stat_offices: 'Cities covered', stat_depts: 'Business lines',
        loading: 'Loading client data...',
        empty: 'No matching clients found',
        empty_data: 'No client data yet. Please add some in the admin panel.',
        footer_admin: 'Data maintenance:', footer_admin_link: 'Admin panel',
        poster_modal_title: 'Export Logo Wall Poster',
        poster_size: 'Poster size', poster_main: 'Main title', poster_sub: 'Subtitle',
        poster_quality: 'Quality', poster_showinfo: 'Show on card', poster_footer: 'Footer text',
        quality_std: 'Standard (1×, screen preview)',
        quality_hd: 'High-res (2×, recommended for print/share)',
        quality_uhd: 'Ultra HD (3×, large format print)',
        pf_city: 'City / Region', pf_dept: 'Business line', pf_owner: 'Owner', pf_coop: 'Since',
        coop_year: 'Year', coop_since: 'Since ', clear_filters: 'Clear',
        size_portrait: 'Portrait 3:4 (1800×2400)',
        size_screen: 'On-site screen 16:9 (1920×1080)',
        size_a4: 'A4 print 300dpi (2480×3508)',
        poster_refresh: 'Refresh preview', poster_download: 'Download PNG poster',
        poster_loading: 'Drawing poster, fetching logo images...',
        poster_hint_pre: 'Will export the ', poster_hint_post: ' clients currently shown by your filters (adjust filters first to narrow down)',
        poster_alert_empty: 'No clients visible under the current filters. Adjust the filters first.',
        poster_fail: 'Export failed, please retry', poster_fail2: 'Export failed:',
        clients_word: 'clients',
        owner_label: 'Owner', owner_title: (o) => 'Owners: ' + o,
        owner_search_ph: 'Search owners...', owner_empty: 'No matching owners',
        dark_mode: 'Dark mode', dark_mode_title: 'Day / Night mode',
        login: 'Sign in', logout: 'Sign out',
        signed_in_as: (n) => 'Signed in as: ' + n,
    },
};
let lang = localStorage.getItem('lw_lang') || 'zh';

function t(key) {
    return (I18N[lang] && I18N[lang][key]) || I18N.zh[key] || key;
}

function applyLang() {
    document.documentElement.lang = (lang === 'zh') ? 'zh-CN' : 'en';
    document.querySelectorAll('[data-i18n]').forEach(el => {
        el.textContent = t(el.getAttribute('data-i18n'));
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        el.placeholder = t(el.getAttribute('data-i18n-placeholder'));
    });
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        el.title = t(el.getAttribute('data-i18n-title'));
    });
    const langBtn = document.getElementById('lang-btn');
    if (langBtn) langBtn.textContent = (lang === 'zh') ? 'EN' : '中文';
    updateAuthButton();
    applySiteTexts();
    if (typeof buildThemePop === 'function') buildThemePop();
    if (typeof updateOwnerTrigger === 'function') updateOwnerTrigger();
    render();
}

function toggleLang() {
    lang = (lang === 'zh') ? 'en' : 'zh';
    localStorage.setItem('lw_lang', lang);
    applyLang();
}

// ---- Login button / auth state ----
function getAuthUser() {
    try {
        return JSON.parse(localStorage.getItem('lw_user') || 'null');
    } catch (e) {
        return null;
    }
}

function updateAuthButton() {
    const token = localStorage.getItem('lw_token');
    const user = getAuthUser();
    const textEl = document.getElementById('login-btn-text');
    const userEl = document.getElementById('login-btn-user');
    const btn = document.getElementById('login-btn');
    if (!textEl || !btn) return;
    if (token && user) {
        const name = user.display_name || user.username || user.sub || 'user';
        textEl.textContent = t('logout');
        if (userEl) {
            userEl.textContent = name;
            userEl.hidden = false;
        }
        btn.title = t('signed_in_as')(name);
        btn.setAttribute('data-authed', '1');
    } else {
        textEl.textContent = t('login');
        if (userEl) {
            userEl.textContent = '';
            userEl.hidden = true;
        }
        btn.title = t('login');
        btn.setAttribute('data-authed', '0');
    }
}

async function handleLoginClick() {
    const token = localStorage.getItem('lw_token');
    if (token) {
        localStorage.removeItem('lw_token');
        localStorage.removeItem('lw_user');
        try { await fetch('/api/auth/logout', { method: 'POST' }); } catch (e) {}
    }
    window.location.href = '/login?redirect=display';
}

// Data-driven texts with per-language variants
function applySiteTexts() {
    const zh = (lang === 'zh');
    document.getElementById('site-title').textContent = zh ? siteTitle : (siteTitleEn || siteTitle);
    document.getElementById('site-title-en').textContent = zh ? siteTitleEn : siteTitle;
    document.getElementById('tagline').textContent = zh ? siteTagline : (siteTaglineEn || siteTagline);
    document.getElementById('site-footer').textContent = zh ? siteFooter : (siteFooterEn || siteFooter);
}

// Office code -> city mapping (for Excel uploads)
const OFFICE_MAP = {
    'BJI':'北京','CDU':'成都','CQI':'重庆','CSH':'长沙','DLI':'大连',
    'GZH':'广州','NJI':'南京','QDA':'青岛','SHA':'上海','SUZ':'苏州',
    'SZH':'深圳','TWN':'台湾','WHA':'武汉','XAN':'西安','XME':'厦门','ZZH':'郑州'
};

// ============================================================
// AUTH CHECK
// ============================================================
async function checkAuth() {
    const token = localStorage.getItem('lw_token');
    if (!token) {
        window.location.replace('/login?redirect=display');
        return false;
    }
    try {
        const resp = await fetch('/api/auth/check', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        const data = await resp.json();
        if (!data.ok) {
            localStorage.removeItem('lw_token');
            localStorage.removeItem('lw_user');
            window.location.replace('/login?redirect=display');
            return false;
        }
        if (data.user) {
            try {
                const stored = JSON.parse(localStorage.getItem('lw_user') || 'null');
                if (!stored) localStorage.setItem('lw_user', JSON.stringify(data.user));
            } catch (e) {
                localStorage.setItem('lw_user', JSON.stringify(data.user));
            }
        }
        updateAuthButton();
        return true;
    } catch (e) {
        console.warn('Auth check failed:', e);
        return true;
    }
}

function authHeaders() {
    const token = localStorage.getItem('lw_token');
    return token ? { 'Authorization': 'Bearer ' + token } : {};
}

// <img> requests are authorised by the HttpOnly session cookie the server
// sets on login / auth check, so tokens never appear in URLs or logs.
function authLogoUrl(url) {
    if (!url) return '';
    // External logos are routed through the same-origin imgproxy so:
    //   1) the canvas-based padding trim can read pixels (no CORS taint), and
    //   2) the poster exporter can draw them without cross-origin issues.
    if (/^https?:\/\//i.test(url)) {
        return '/api/imgproxy?url=' + encodeURIComponent(url);
    }
    return (url.startsWith('/') ? '' : '/') + url;
}

// ---- HTML escaping (all data is untrusted when building markup) ----
function esc(v) {
    return String(v == null ? '' : v)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
function safeColor(c) {
    return /^#[0-9a-fA-F]{3,8}$/.test(c || '') ? c : '#4F46E5';
}
function logoFallbackHtml(r, color) {
    return `<div class="logo-fallback" style="background:${color}">${esc(getInitials(r.brand))}</div>`;
}
// onerror handler for logo <img>: swap in the initials badge
function logoFallback(img) {
    const div = document.createElement('div');
    div.className = 'logo-fallback';
    div.style.background = safeColor(img.dataset.color);
    div.textContent = img.dataset.initials || '?';
    img.replaceWith(div);
}

// Trim transparent (and near-white on light cards) padding around a logo so
// external icons with lots of empty canvas don't render tiny.
function trimLogoDataUrl(img) {
    try {
        const iw = img.naturalWidth, ih = img.naturalHeight;
        if (!iw || !ih) return null;
        // Cap working size for performance.
        const maxSide = 256;
        const ratio = Math.min(1, maxSide / Math.max(iw, ih));
        const cw = Math.max(1, Math.round(iw * ratio));
        const ch = Math.max(1, Math.round(ih * ratio));
        const canvas = document.createElement('canvas');
        canvas.width = cw; canvas.height = ch;
        const ctx = canvas.getContext('2d', { willReadFrequently: true });
        ctx.drawImage(img, 0, 0, cw, ch);
        const data = ctx.getImageData(0, 0, cw, ch).data;
        const isBlank = (r, g, b, a) =>
            a < 16 || (a < 64 && r > 240 && g > 240 && b > 240);
        let minX = cw, minY = ch, maxX = -1, maxY = -1;
        for (let y = 0; y < ch; y++) {
            for (let x = 0; x < cw; x++) {
                const i = (y * cw + x) * 4;
                if (!isBlank(data[i], data[i + 1], data[i + 2], data[i + 3])) {
                    if (x < minX) minX = x;
                    if (x > maxX) maxX = x;
                    if (y < minY) minY = y;
                    if (y > maxY) maxY = y;
                }
            }
        }
        if (maxX < 0) return null; // fully blank → keep original
        // Add a small breathing margin (~4% of content size).
        const contentW = maxX - minX + 1, contentH = maxY - minY + 1;
        const margin = Math.max(2, Math.round(Math.max(contentW, contentH) * 0.06));
        let sx = Math.max(0, minX - margin);
        let sy = Math.max(0, minY - margin);
        let sw = Math.min(cw - sx, contentW + margin * 2);
        let sh = Math.min(ch - sy, contentH + margin * 2);
        // Map the trimmed crop back to original image coordinates.
        const out = document.createElement('canvas');
        out.width = Math.round(sw / ratio);
        out.height = Math.round(sh / ratio);
        out.getContext('2d').drawImage(img, sx / ratio, sy / ratio, sw / ratio, sh / ratio,
            0, 0, out.width, out.height);
        return out.toDataURL('image/png');
    } catch (e) {
        return null;
    }
}

// Given an <img>, replace its src with a trimmed version once loaded (only for
// external logos; local uploaded logos are assumed already tightly cropped).
function autoTrimLogo(img) {
    if (!img || img.dataset.trimmed) return;
    img.dataset.trimmed = '1';
    const doTrim = () => {
        const trimmed = trimLogoDataUrl(img);
        if (trimmed) {
            img.src = trimmed;
            // After trimmed src loads, check natural size. Favicons are often
            // 16/32px and render tiny; upscale the canvas-backed image so its
            // natural dimensions are comfortable (≥96px on the short side),
            // letting normal CSS max-height handle display sizing.
            img.addEventListener('load', () => {
                const w = img.naturalWidth, h = img.naturalHeight;
                if (w > 0 && h > 0 && Math.max(w, h) < 64) {
                    const scale = Math.max(2, Math.ceil(96 / Math.min(w, h)));
                    const up = document.createElement('canvas');
                    up.width = w * scale; up.height = h * scale;
                    const uctx = up.getContext('2d');
                    uctx.imageSmoothingEnabled = true;
                    uctx.imageSmoothingQuality = 'high';
                    uctx.drawImage(img, 0, 0, up.width, up.height);
                    img.src = up.toDataURL('image/png');
                }
            }, { once: true });
        }
    };
    if (img.complete && img.naturalWidth > 0) doTrim();
    else img.addEventListener('load', doTrim, { once: true });
}

// ============================================================
// DATA LOADING
// ============================================================
async function loadData() {
    try {
        const resp = await fetch('/data.json', {
            cache: 'no-cache',
            headers: authHeaders()
        });
        if (resp.status === 401 || resp.status === 403) {
            localStorage.removeItem('lw_token');
            localStorage.removeItem('lw_user');
            window.location.replace('/login?redirect=display');
            return;
        }
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const ctype = (resp.headers.get('content-type') || '');
        if (!ctype.includes('application/json')) throw new Error('Not JSON: ' + ctype);
        const data = await resp.json();
        initFromData(data);
    } catch (e) {
        console.warn('Could not load data.json, using empty state:', e);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('empty').style.display = 'block';
        const ep = document.getElementById('empty-text');
        ep.setAttribute('data-i18n', 'empty_data');
        ep.textContent = t('empty_data');
    }
}

// ============================================================
// ANIMATED COUNTER
// ============================================================
function animateCounter(el, target, duration) {
    duration = duration || 600;
    const start = performance.now();
    const fromVal = parseInt(el.textContent) || 0;
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) { el.textContent = target; return; }
    function step(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        // Ease out quint
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(fromVal + (target - fromVal) * eased);
        el.textContent = current;
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

function initFromData(data) {
    allRecords = data.records || [];
    siteTitle = data.title || '客户品牌墙';
    siteTagline = data.tagline || '';
    siteTitleEn = data.title_en || 'CLIENT LOGO WALL';
    siteFooter = data.footer_text || '连接  ·  协作  ·  共创价值';
    siteTheme = data.theme || 'classic';
    sitePattern = data.bg_pattern || 'none';
    siteCustomPrimary = data.custom_primary || '';
    siteCustomAccent = data.custom_accent || '';
    siteTaglineEn = data.tagline_en || '';
    siteFooterEn = data.footer_en || '';
    applyEffectiveTheme();
    applyLang();
    allRecords.forEach(r => {
        if (!r.region) r.region = getRegionFromCode(r.office_code);
    });
    document.getElementById('tagline').textContent = data.tagline || '';

    // Animate stat numbers
    const totalEl = document.getElementById('stat-total');
    const officesEl = document.getElementById('stat-offices');
    const deptsEl = document.getElementById('stat-depts');
    totalEl.textContent = '0';
    officesEl.textContent = '0';
    deptsEl.textContent = '0';

    // Build filters first so we can reference counts
    const offices = data.offices || [];
    const departments = data.departments || [];
    const owners = [...new Set(allRecords.flatMap(r => r.owners || []))].sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'));
    const regions = [...new Set(allRecords.map(r => r.region).filter(Boolean))].sort();
    buildFilters(offices, departments, owners, regions);

    // Now animate after DOM is ready
    setTimeout(() => {
        animateCounter(totalEl, allRecords.length, 700);
        animateCounter(officesEl, offices.length, 500);
        animateCounter(deptsEl, departments.length, 400);
    }, 80);

    render();

    document.getElementById('loading').style.display = 'none';
    document.getElementById('grid').style.display = 'grid';

    // Stagger reveal cards
    requestAnimationFrame(() => {
        revealCardsStaggered();
    });

    // Footer update date
    const today = new Date().toLocaleDateString(lang === 'zh' ? 'zh-CN' : 'en-US', { year:'numeric', month:'long', day:'numeric' });
    document.getElementById('footer-update').textContent = (lang === 'zh' ? '更新于' : 'Updated ') + today;
}

// Region mapping
const REGION_MAP = {
    BJI:'华北', DLI:'华北', QDA:'华北', XAN:'华北',
    SHA:'华东', SUZ:'华东', NJI:'华东', ZZH:'华东',
    GZH:'华南', SZH:'华南', WHA:'华南', CSH:'华南', XME:'华南',
    CDU:'华西', CQI:'华西', TWN:'台湾', HKG:'香港'
};
function getRegionFromCode(code) { return REGION_MAP[code] || '其他'; }

// ============================================================
// FILTERS
// ============================================================
function coopYear(r) {
    const d = r.cooperation_date || '';
    const m = /^(\d{4})/.exec(d);
    return m ? m[1] : '';
}

function buildFilters(offices, departments, owners, regions) {
    const officeGroup = document.getElementById('office-group');
    officeGroup.querySelectorAll('.filter-btn[data-value]:not([data-value="all"])').forEach(b => b.remove());
    offices.forEach(office => {
        const btn = document.createElement('button');
        btn.className = 'filter-btn';
        btn.dataset.filter = 'office';
        btn.dataset.value = office;
        btn.textContent = office;
        officeGroup.appendChild(btn);
    });

    const regionGroup = document.getElementById('region-group');
    regionGroup.querySelectorAll('.filter-btn[data-value]:not([data-value="all"])').forEach(b => b.remove());
    (regions || []).forEach(region => {
        const btn = document.createElement('button');
        btn.className = 'filter-btn';
        btn.dataset.filter = 'region';
        btn.dataset.value = region;
        btn.textContent = region;
        regionGroup.appendChild(btn);
    });

    const deptGroup = document.getElementById('dept-group');
    deptGroup.querySelectorAll('.filter-btn[data-value]:not([data-value="all"])').forEach(b => b.remove());
    departments.forEach(dept => {
        const btn = document.createElement('button');
        btn.className = 'filter-btn dept-' + dept;
        btn.dataset.filter = 'dept';
        btn.dataset.value = dept;
        btn.textContent = dept;
        deptGroup.appendChild(btn);
    });

    const ownerGroup = document.getElementById('owner-group');
    ownerGroup.querySelectorAll('.filter-btn[data-value]:not([data-value="all"])').forEach(b => b.remove());
    buildOwnerOptions(owners);
    updateOwnerTrigger();

    const yearGroup = document.getElementById('year-group');
    yearGroup.querySelectorAll('.filter-btn[data-value]:not([data-value="all"])').forEach(b => b.remove());
    const years = [...new Set(allRecords.map(coopYear).filter(Boolean))].sort().reverse();
    years.forEach(year => {
        const btn = document.createElement('button');
        btn.className = 'filter-btn';
        btn.dataset.filter = 'year';
        btn.dataset.value = year;
        btn.textContent = year;
        yearGroup.appendChild(btn);
    });

    bindFilterButtons();
}

function bindFilterButtons() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.onclick = () => {
            const filterType = btn.dataset.filter;
            const value = btn.dataset.value;
            const setRef = {
                office: activeOffice, region: activeRegion,
                dept: activeDept, owner: activeOwner, year: activeYear
            }[filterType];
            const group = btn.closest('.filter-group');
            if (value === 'all') {
                setRef.clear();
            } else if (setRef.has(value)) {
                setRef.delete(value);
            } else {
                setRef.add(value);
            }
            // Update active states for this group
            group.querySelectorAll('.filter-btn').forEach(b => {
                const v = b.dataset.value;
                if (v === 'all') {
                    b.classList.toggle('active', setRef.size === 0);
                } else {
                    b.classList.toggle('active', setRef.has(v));
                }
            });
            updateClearFiltersBtn();
            render();
        };
    });
}

// ---- Owner multi-select searchable dropdown ----
let allOwnerNames = [];
function buildOwnerOptions(owners) {
    allOwnerNames = owners || [];
    renderOwnerOptions(allOwnerNames);
}

function ownerCount(name) {
    return allRecords.reduce((n, r) => n + ((r.owners || []).includes(name) ? 1 : 0), 0);
}

function renderOwnerOptions(list) {
    const box = document.getElementById('owner-options');
    if (!list.length) {
        box.innerHTML = '';
        const empty = document.createElement('div');
        empty.className = 'ms-empty';
        empty.textContent = t('owner_empty');
        box.appendChild(empty);
        return;
    }
    box.innerHTML = list.map(name => {
        const sel = activeOwner.has(name) ? ' selected' : '';
        const cnt = ownerCount(name);
        return `<div class="ms-option${sel}" data-owner="${esc(name)}" onclick="toggleOwnerOption(this.dataset.owner)">
            <span class="ms-check"></span>
            <span class="ms-name">${esc(name)}</span>
            <span class="ms-count">${cnt}</span>
        </div>`;
    }).join('');
}

function toggleOwnerOption(name) {
    if (activeOwner.has(name)) activeOwner.delete(name);
    else activeOwner.add(name);
    const searchEl = document.getElementById('owner-search');
    renderOwnerOptions(filterOwnerList(searchEl ? searchEl.value : ''));
    updateOwnerTrigger();
    updateClearFiltersBtn();
    render();
}

function filterOwnerList(q) {
    const kw = (q || '').trim().toLowerCase();
    if (!kw) return allOwnerNames;
    return allOwnerNames.filter(n => n.toLowerCase().includes(kw));
}

function filterOwnerOptions(q) {
    renderOwnerOptions(filterOwnerList(q));
}

function updateOwnerTrigger() {
    const trigger = document.getElementById('owner-trigger');
    const textEl = document.getElementById('owner-trigger-text');
    if (!trigger || !textEl) return;
    const n = activeOwner.size;
    if (n === 0) {
        textEl.textContent = t('all');
        textEl.setAttribute('data-i18n', 'all');
        trigger.classList.remove('has-selection');
    } else if (n === 1) {
        textEl.textContent = [...activeOwner][0];
        textEl.removeAttribute('data-i18n');
        trigger.classList.add('has-selection');
    } else {
        textEl.textContent = (lang === 'zh' ? '已选 ' : 'Selected ') + n;
        textEl.removeAttribute('data-i18n');
        trigger.classList.add('has-selection');
    }
}

function toggleOwnerDropdown(e) {
    e.stopPropagation();
    const dd = document.getElementById('owner-dropdown');
    const panel = document.getElementById('owner-panel');
    const trigger = document.getElementById('owner-trigger');
    const open = panel.classList.toggle('open');
    trigger.classList.toggle('open', open);
    if (open) {
        const searchEl = document.getElementById('owner-search');
        searchEl.value = '';
        renderOwnerOptions(allOwnerNames);
        setTimeout(() => searchEl.focus(), 30);
    }
}

function closeOwnerDropdown() {
    const panel = document.getElementById('owner-panel');
    const trigger = document.getElementById('owner-trigger');
    if (panel) panel.classList.remove('open');
    if (trigger) trigger.classList.remove('open');
}

document.addEventListener('click', (e) => {
    const dd = document.getElementById('owner-dropdown');
    if (dd && !dd.contains(e.target)) closeOwnerDropdown();
});
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeOwnerDropdown();
});

function updateClearFiltersBtn() {
    const btn = document.getElementById('clear-filters-btn');
    if (!btn) return;
    const any = activeOffice.size + activeRegion.size + activeDept.size + activeOwner.size + activeYear.size > 0;
    btn.hidden = !any;
}

function clearAllFilters() {
    activeOffice.clear(); activeRegion.clear(); activeDept.clear();
    activeOwner.clear(); activeYear.clear();
    document.querySelectorAll('.filter-group').forEach(group => {
        group.querySelectorAll('.filter-btn').forEach(b => {
            b.classList.toggle('active', b.dataset.value === 'all');
        });
    });
    document.getElementById('search').value = '';
    searchQuery = '';
    closeOwnerDropdown();
    updateOwnerTrigger();
    const searchEl = document.getElementById('owner-search');
    if (searchEl) searchEl.value = '';
    renderOwnerOptions(allOwnerNames);
    updateClearFiltersBtn();
    render();
}

// ============================================================
// SEARCH
// ============================================================
document.getElementById('search').addEventListener('input', (e) => {
    searchQuery = e.target.value.trim().toLowerCase();
    render();
});

// ============================================================
// STAGGERED CARD REVEAL
// ============================================================
function revealCardsStaggered() {
    const cards = document.querySelectorAll('.card:not(.revealed)');
    if (cards.length === 0) return;
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    cards.forEach((card, i) => {
        const delay = prefersReduced ? 0 : i * 35;
        setTimeout(() => { card.classList.add('revealed'); }, delay);
    });
}

// ============================================================
// RENDER
// ============================================================
function getFiltered() {
    return allRecords.filter(r => {
        if (activeOffice.size > 0 && !activeOffice.has(r.office_city)) return false;
        if (activeRegion.size > 0 && !activeRegion.has(r.region || getRegionFromCode(r.office_code))) return false;
        if (activeDept.size > 0 && !(r.departments || []).some(d => activeDept.has(d))) return false;
        if (activeOwner.size > 0 && !(r.owners || []).some(o => activeOwner.has(o))) return false;
        if (activeYear.size > 0 && !activeYear.has(coopYear(r))) return false;
        if (searchQuery) {
            const haystack = [
                r.company, r.brand, r.office_city, r.office_code, r.region,
                r.cooperation_date,
                (r.owners || []).join(' '), (r.departments || []).join(' ')
            ].join(' ').toLowerCase();
            if (!haystack.includes(searchQuery)) return false;
        }
        return true;
    });
}

function getInitials(name) {
    if (!name) return '?';
    const clean = name.replace(/[（(].*?[）)]/g, '').trim();
    if (/[\u4e00-\u9fa5]/.test(clean)) {
        return clean.substring(0, 2);
    }
    const words = clean.split(/[\s,，、]+/).filter(Boolean);
    if (words.length >= 2) return (words[0][0] + words[1][0]).toUpperCase();
    return clean.substring(0, 2).toUpperCase();
}

function logoImgHtml(r, color, extraAttrs) {
    return `<img src="${esc(authLogoUrl(r.logo_url))}" alt="${esc(r.brand)}"${extraAttrs || ''}
            data-color="${esc(color)}" data-initials="${esc(getInitials(r.brand))}" onerror="logoFallback(this)">`;
}

function renderCard(r) {
    const deptTags = (r.departments || []).map(d =>
        `<span class="dept-tag ${esc(d)}">${esc(d)}</span>`
    ).join('');

    const owners = (r.owners || []).join(lang === 'zh' ? '、' : ', ');
    const color = safeColor(r.color);
    const id = Number(r.id) || 0;

    let logoHtml;
    if (r.logo_url) {
        const isExternal = /^https?:\/\//i.test(r.logo_url);
        const trimAttr = isExternal ? ' onload="autoTrimLogo(this)"' : '';
        logoHtml = logoImgHtml(r, color, ` loading="lazy"${trimAttr} referrerpolicy="no-referrer"`);
    } else {
        logoHtml = logoFallbackHtml(r, color);
    }

    const fullCompany = r.company || '';
    const companyFull = (fullCompany && fullCompany !== r.brand)
        ? `<div class="company-full" title="${esc(fullCompany)}">${esc(fullCompany)}</div>` : '';
    const ownersHtml = owners
        ? `<div class="meta-owners" title="${esc(t('owner_title')(owners))}"><span class="owner-label">${t('owner_label')}</span>${esc(owners)}</div>` : '';
    const coopDate = r.cooperation_date || '';
    const coopDateHtml = coopDate
        ? `<div class="meta-coop" title="${esc(t('coop_since') + coopDate)}">${esc(t('coop_since') + coopDate)}</div>` : '';

    const tooltipOwners = (r.owners || []).join(lang === 'zh' ? '、' : ', ');

    return `
        <div class="card${selectedIds.has(r.id) ? ' selected' : ''}" style="--card-color:${color}" data-id="${id}" onclick="openDetailModal(${id})">
            <div class="card-check"></div>
            <div class="logo-area">${logoHtml}</div>
            <div class="brand-name" title="${esc(r.brand)}">${esc(r.brand)}</div>
            ${companyFull}
            <div class="card-meta">
                <div class="meta-row meta-office">
                    <span class="city">${esc(r.office_city)}</span>
                    <span>·</span>
                    <span>${esc(r.office_code)}</span>
                </div>
                <div class="dept-tags">${deptTags}</div>
                ${ownersHtml}
                ${coopDateHtml}
            </div>
            <div class="card-tooltip">
                <div class="tip-company">${esc(r.brand || r.company)}</div>
                ${fullCompany && fullCompany !== r.brand ? '<div class="tip-company" style="font-weight:400;font-size:11px;color:rgba(255,255,255,0.7)">' + esc(fullCompany) + '</div>' : ''}
                <div>${esc(r.office_city)} (${esc(r.office_code)})</div>
                <div class="tip-owners">${esc(tooltipOwners)}</div>
            </div>
        </div>
    `;
}

function render() {
    const filtered = getFiltered();
    const grid = document.getElementById('grid');
    const empty = document.getElementById('empty');

    document.getElementById('visible-count').textContent = filtered.length;

    if (filtered.length === 0) {
        grid.style.display = 'none';
        empty.style.display = 'block';
        return;
    }

    empty.style.display = 'none';
    grid.style.display = 'grid';
    grid.innerHTML = filtered.map(renderCard).join('');

    // Reveal with stagger
    requestAnimationFrame(() => {
        revealCardsStaggered();
    });
}

// ============================================================
// DETAIL MODAL
// ============================================================
// ============================================================
// MULTI-SELECT MODE
// ============================================================
function toggleSelectMode() {
    selectMode = !selectMode;
    selectedIds.clear();
    document.body.classList.toggle('select-mode', selectMode);
    const btn = document.getElementById('select-btn');
    if (btn) btn.classList.toggle('active', selectMode);
    updateSelectBar();
    render();
}

function toggleSelectCard(clientId) {
    if (selectedIds.has(clientId)) selectedIds.delete(clientId);
    else selectedIds.add(clientId);
    const el = document.querySelector(`.card[data-id="${clientId}"]`);
    if (el) el.classList.toggle('selected', selectedIds.has(clientId));
    updateSelectBar();
}

function clearSelection() {
    selectedIds.clear();
    document.querySelectorAll('.card.selected').forEach(el => el.classList.remove('selected'));
    updateSelectBar();
}

function updateSelectBar() {
    const bar = document.getElementById('select-bar');
    if (!bar) return;
    document.getElementById('sel-count').textContent = selectedIds.size;
    bar.classList.toggle('show', selectMode);
}

function exportSelectedPoster() {
    if (selectedIds.size === 0) { alert(t('poster_alert_none_selected')); return; }
    openPosterModal();
}

function openDetailModal(clientId) {
    if (selectMode) { toggleSelectCard(clientId); return; }
    const record = allRecords.find(r => r.id === clientId);
    if (!record) return;
    const overlay = document.getElementById('detail-overlay');
    const color = safeColor(record.color);

    const logoEl = document.getElementById('detail-logo');
    if (record.logo_url) {
        logoEl.innerHTML = logoImgHtml(record, color);
    } else {
        logoEl.innerHTML = logoFallbackHtml(record, color);
    }

    document.getElementById('detail-brand').textContent = record.brand || record.company;
    document.getElementById('detail-company').textContent = (record.company && record.company !== record.brand) ? record.company : '';
    document.getElementById('detail-city').textContent = `${record.office_city} (${record.office_code})`;

    const deptsEl = document.getElementById('detail-depts');
    deptsEl.innerHTML = (record.departments || []).map(d => `<span class="dept-tag ${esc(d)}">${esc(d)}</span>`).join('');

    const descEl = document.getElementById('detail-description');
    if (record.description) {
        descEl.textContent = record.description;
        descEl.setAttribute('data-label', lang === 'zh' ? '公司简介' : 'Company Profile');
        descEl.style.display = 'block';
    } else {
        descEl.textContent = '';
        descEl.style.display = 'none';
    }

    const ownersEl = document.getElementById('detail-owners');
    const owners = (record.owners || []).join(lang === 'zh' ? '、' : ', ');
    if (owners) {
        ownersEl.textContent = owners;
        ownersEl.setAttribute('data-label', lang === 'zh' ? '负责人：' : 'Owners: ');
        ownersEl.style.display = 'block';
    } else {
        ownersEl.textContent = '';
        ownersEl.style.display = 'none';
    }

    const coopEl = document.getElementById('detail-coop');
    if (record.cooperation_date) {
        coopEl.textContent = record.cooperation_date;
        coopEl.setAttribute('data-label', lang === 'zh' ? '合作时间：' : 'Since: ');
        coopEl.style.display = 'block';
    } else {
        coopEl.textContent = '';
        coopEl.style.display = 'none';
    }

    const websiteEl = document.getElementById('detail-website');
    if (record.website) {
        let url = record.website;
        if (!/^https?:\/\//i.test(url)) url = 'https://' + url;
        websiteEl.href = url;
        websiteEl.rel = 'noopener noreferrer';
        websiteEl.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>${esc(record.website)}`;
        websiteEl.style.display = 'flex';
    } else {
        websiteEl.href = '';
        websiteEl.textContent = '';
        websiteEl.style.display = 'none';
    }

    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeDetailModal(e) {
    if (e && e.target !== e.currentTarget) return;
    document.getElementById('detail-overlay').classList.remove('show');
    document.body.style.overflow = '';
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const overlay = document.getElementById('detail-overlay');
        if (overlay.classList.contains('show')) {
            closeDetailModal();
        }
    }
});

// ============================================================
// THEME SYSTEM
// ============================================================
const THEME_META = [
    { id: 'classic', label: '经典深蓝', label_en: 'Classic Navy', c1: '#1b1f3a', c2: '#c2933e' },
    { id: 'gold',    label: '商务金',   label_en: 'Business Gold', c1: '#6b4f14', c2: '#c9a227' },
    { id: 'violet',  label: '科技紫',   label_en: 'Tech Violet',  c1: '#4c1d95', c2: '#7c3aed' },
    { id: 'orange',  label: '活力橙',   label_en: 'Vivid Orange', c1: '#7c2d12', c2: '#ea580c' },
    { id: 'green',   label: '松石绿',   label_en: 'Jade Green',   c1: '#14532d', c2: '#16a34a' },
];
const PATTERN_META = [
    { id: 'none', label: '纯净', label_en: 'Plain' },
    { id: 'dots', label: '点阵', label_en: 'Dots' },
    { id: 'grid', label: '网格', label_en: 'Grid' },
    { id: 'glow', label: '光晕', label_en: 'Glow' },
];
function metaLabel(m) { return (lang === 'zh') ? m.label : (m.label_en || m.label); }

function applyTheme(theme, pattern, customPrimary, customAccent) {
    const root = document.documentElement;
    root.setAttribute('data-theme', theme);
    root.setAttribute('data-bg', pattern);
    if (customPrimary) root.style.setProperty('--primary', customPrimary);
    else root.style.removeProperty('--primary');
    if (customAccent) root.style.setProperty('--accent', customAccent);
    else root.style.removeProperty('--accent');
}

function applyDarkMode(isDark) {
    document.documentElement.setAttribute('data-dark', isDark ? 'true' : 'false');
    const btn = document.getElementById('dark-btn');
    if (btn) btn.classList.toggle('active', isDark);
    const sw = document.getElementById('dark-switch');
    if (sw) sw.checked = isDark;
}

function isDarkMode() {
    const stored = localStorage.getItem('lw_dark');
    if (stored !== null) return stored === 'true';
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
}

function applyEffectiveTheme() {
    const t = localStorage.getItem('lw_preview_theme') || siteTheme;
    const p = localStorage.getItem('lw_preview_bg');
    applyTheme(t, p !== null ? p : sitePattern, siteCustomPrimary, siteCustomAccent);
    applyDarkMode(isDarkMode());
}

function buildThemePop() {
    const curTheme = localStorage.getItem('lw_preview_theme') || siteTheme;
    const curPattern = localStorage.getItem('lw_preview_bg') || sitePattern;
    const sw = document.getElementById('theme-swatches');
    sw.innerHTML = '';
    THEME_META.forEach(tm => {
        const b = document.createElement('button');
        b.className = 'theme-swatch' + (tm.id === curTheme ? ' active' : '');
        b.title = metaLabel(tm);
        b.style.background = `linear-gradient(135deg, ${tm.c1} 50%, ${tm.c2} 50%)`;
        b.onclick = () => {
            localStorage.setItem('lw_preview_theme', tm.id);
            applyEffectiveTheme();
            buildThemePop();
        };
        sw.appendChild(b);
    });
    const pb = document.getElementById('pattern-btns');
    pb.innerHTML = '';
    PATTERN_META.forEach(pm => {
        const b = document.createElement('button');
        b.className = 'pattern-btn' + (pm.id === curPattern ? ' active' : '');
        b.textContent = metaLabel(pm);
        b.onclick = () => {
            localStorage.setItem('lw_preview_bg', pm.id);
            applyEffectiveTheme();
            buildThemePop();
        };
        pb.appendChild(b);
    });
    const dsw = document.getElementById('dark-switch');
    if (dsw) dsw.checked = isDarkMode();
}

function toggleDarkMode(e) {
    e.stopPropagation();
    const isDark = !isDarkMode();
    localStorage.setItem('lw_dark', String(isDark));
    applyEffectiveTheme();
    buildThemePop();
}

function toggleDarkModeFromSwitch(checked) {
    localStorage.setItem('lw_dark', String(checked));
    applyEffectiveTheme();
}

function toggleThemePop(e) {
    e.stopPropagation();
    document.getElementById('theme-pop').classList.toggle('show');
}

function resetThemePreview() {
    localStorage.removeItem('lw_preview_theme');
    localStorage.removeItem('lw_preview_bg');
    localStorage.removeItem('lw_dark');
    applyEffectiveTheme();
    buildThemePop();
}

document.addEventListener('click', (e) => {
    const pop = document.getElementById('theme-pop');
    if (pop.classList.contains('show') && !e.target.closest('.theme-pop-wrap')) {
        pop.classList.remove('show');
    }
});

// ============================================================
// POSTER EXPORT (unchanged from original)
// ============================================================
const POSTER_SIZES = {
    portrait: { w: 1800, h: 2400 },
    screen:   { w: 1920, h: 1080 },
    a4:       { w: 2480, h: 3508 },
};
const POSTER_FONT = '"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",sans-serif';
const POSTER_SERIF = '"Songti SC","STSong","SimSun","Noto Serif CJK SC","Source Han Serif SC",serif';
let posterRecords = [];
let posterSeq = 0;
let posterPages = [];      // array of { records, imgs }
let posterCurrentPage = 0;
let posterOpts = null;     // shared render options across pages
let posterSizeKey = 'portrait';

function posterLogoSrc(r) {
    if (!r.logo_url) return null;
    return authLogoUrl(r.logo_url.replace(/^\/+/, ''));
}

function openPosterModal() {
    const useSelection = selectMode && selectedIds.size > 0;
    posterRecords = useSelection
        ? allRecords.filter(r => selectedIds.has(r.id))
        : getFiltered();
    posterCurrentPage = 0;
    posterPages = [];
    if (posterRecords.length === 0) {
        alert(t('poster_alert_empty'));
        return;
    }
    document.getElementById('poster-title').value = document.getElementById('site-title').textContent;
    document.getElementById('poster-subtitle').value = document.getElementById('tagline').textContent;
    // Default footer: 站点名 · N 家客户 · 日期
    const dateStr = new Date().toLocaleDateString(lang === 'zh' ? 'zh-CN' : 'en-US',
        { year: 'numeric', month: 'long', day: 'numeric' });
    document.getElementById('poster-footer').value =
        document.getElementById('site-title').textContent + '  ·  ' +
        posterRecords.length + ' ' + t('clients_word') + '  ·  ' + dateStr;
    document.getElementById('poster-count-hint').textContent = useSelection
        ? t('poster_hint_sel_pre') + posterRecords.length + t('poster_hint_sel_post')
        : t('poster_hint_pre') + posterRecords.length + t('poster_hint_post');
    document.getElementById('poster-overlay').classList.add('show');
    renderPoster();
}

function closePosterModal() {
    document.getElementById('poster-overlay').classList.remove('show');
}

document.getElementById('poster-overlay').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closePosterModal();
});

// Live re-render on any control change (size, quality, titles, checkboxes, footer)
['poster-size', 'poster-quality', 'poster-title', 'poster-subtitle', 'poster-footer',
 'pf-show-city', 'pf-show-dept', 'pf-show-owner', 'pf-show-coop'].forEach(id => {
    const el = document.getElementById(id);
    const evt = (el.tagName === 'SELECT' || el.type === 'checkbox') ? 'change' : 'input';
    let timer = null;
    el.addEventListener(evt, () => {
        if (!document.getElementById('poster-overlay').classList.contains('show')) return;
        clearTimeout(timer);
        timer = setTimeout(renderPoster, el.type === 'checkbox' ? 50 : 400);
    });
});

function loadPosterImage(src) {
    return new Promise(resolve => {
        if (!src) return resolve(null);
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => resolve(null);
        img.src = src;
    });
}

// Compute how many logos comfortably fit on one page so they don't shrink too
// small. Thresholds are tuned per orientation and how many info lines are shown.
function posterPerPage(isScreen, infoLines) {
    if (isScreen) {
        // 16:9 is short vertically — fewer rows, cap more aggressively.
        return [36, 30, 24, 18][infoLines] || 18;
    }
    // portrait / A4 (roughly 3:4) — more vertical room.
    return [64, 54, 42, 32][infoLines] || 32;
}

// Shared logo-grid geometry for one poster page. Pagination and drawing both
// use this so a full page always tiles the grid exactly (cols × rows slots,
// no empty holes); only the last page may be partially filled.
function posterBestGrid(W, H, isScreen, hasSubtitle, infoLines, n) {
    n = Math.max(1, n);
    const titleSize = Math.round(W * 0.046);
    const titleY = Math.round(H * (isScreen ? 0.12 : 0.095));
    const diamondY = titleY + titleSize * 0.95;
    const dSize = Math.max(6, Math.round(W * 0.007));
    let blockBottom = diamondY + dSize / 2;
    if (hasSubtitle) {
        const subSize = Math.round(W * (isScreen ? 0.015 : 0.018));
        const subY = diamondY + dSize * 1.8 + subSize * 0.8;
        blockBottom = subY + subSize / 2;
    }
    const labelSizeZh = Math.round(W * 0.0165);
    const labelGap = Math.round(H * (isScreen ? 0.085 : 0.055));
    const labelY = blockBottom + labelGap + labelSizeZh / 2;
    const gridTop = labelY + Math.round(H * (isScreen ? 0.025 : 0.04));
    const footerH = Math.round(H * 0.075);
    const gridBottom = H - footerH - Math.round(H * 0.012);
    const padX = Math.round(W * 0.075);
    const areaW = W - padX * 2;
    const areaH = gridBottom - gridTop;
    // Cards get taller when more info lines are shown, so logo + brand + meta all fit.
    // cardAspect = width/height; more lines → smaller ratio → taller cards.
    const cardAspect = infoLines === 0 ? 1.08
                     : infoLines === 1 ? 0.92
                     : infoLines === 2 ? 0.80
                     :                   0.72;
    let best = null;
    for (let c = 1; c <= n; c++) {
        const rows = Math.ceil(n / c);
        let cw = areaW / c;
        let ch = areaH / rows;
        if (ch > cw / cardAspect) ch = cw / cardAspect;
        else cw = ch * cardAspect;
        if (!best || cw > best.cw) best = { cols: c, rows, cw, ch };
    }
    const gridW = best.cols * best.cw;
    const gridH = best.rows * best.ch;
    return {
        best,
        capacity: best.cols * best.rows,
        offX: padX + (areaW - gridW) / 2,
        offY: gridTop + (areaH - gridH) / 2,
        gap: Math.min(best.cw, best.ch) * 0.12,
        cardW: best.cw - Math.min(best.cw, best.ch) * 0.12,
        cardH: best.ch - Math.min(best.cw, best.ch) * 0.12,
        footerH,
    };
}

async function renderPoster() {
    const seq = ++posterSeq;
    posterSizeKey = document.getElementById('poster-size').value;
    const base = POSTER_SIZES[posterSizeKey] || POSTER_SIZES.portrait;
    // Quality multiplier: canvas renders at base × scale for crisp high-res output
    const scale = Math.max(1, parseInt(document.getElementById('poster-quality').value, 10) || 1);
    const title = document.getElementById('poster-title').value.trim() || '客户品牌墙';
    const subtitle = document.getElementById('poster-subtitle').value.trim();
    const footerText = document.getElementById('poster-footer').value.trim();
    posterOpts = {
        scale,
        showCity:  document.getElementById('pf-show-city').checked,
        showDept:  document.getElementById('pf-show-dept').checked,
        showOwner: document.getElementById('pf-show-owner').checked,
        showCoop:  document.getElementById('pf-show-coop').checked,
        footer: footerText,
    };
    const isScreen = (posterSizeKey === 'screen');
    const infoLines = (posterOpts.showCity ? 1 : 0) + (posterOpts.showDept ? 1 : 0) + (posterOpts.showOwner ? 1 : 0) + (posterOpts.showCoop ? 1 : 0);
    const perPage = posterPerPage(isScreen, infoLines);

    // The optimal grid for `perPage` cards may tile cols × rows > perPage slots,
    // which would leave empty holes on every page. Pack each page up to the
    // grid's true capacity instead, so earlier pages are always completely
    // full and only the last page carries the remainder.
    let capacity = perPage;
    for (let k = 0; k < 3; k++) {
        const cap = posterBestGrid(base.w, base.h, isScreen, !!subtitle, infoLines, capacity).capacity;
        if (cap === capacity) break;
        capacity = cap;
    }

    // Split records into pages.
    posterPages = [];
    for (let i = 0; i < posterRecords.length; i += capacity) {
        posterPages.push({ records: posterRecords.slice(i, i + capacity), imgs: [] });
    }
    if (posterPages.length === 0) posterPages.push({ records: [], imgs: [] });
    posterCurrentPage = Math.min(posterCurrentPage, posterPages.length - 1);

    const W = base.w * scale, H = base.h * scale;
    const canvas = document.getElementById('poster-canvas');
    canvas.width = W;
    canvas.height = H;
    const ctx = canvas.getContext('2d');
    // Scale the drawing context so all coordinates are in base (logical) pixels,
    // while the canvas backing store is base × scale → crisp high-res export.
    ctx.setTransform(scale, 0, 0, scale, 0, 0);
    const BW = base.w, BH = base.h; // logical base dimensions used for layout
    const loading = document.getElementById('poster-loading');
    loading.style.display = 'flex';

    // Preload images for ALL pages so paging is instant.
    const allImgs = await Promise.all(
        posterRecords.map(r => loadPosterImage(posterLogoSrc(r)))
    );
    if (seq !== posterSeq) return;
    posterPages.forEach((p, idx) => {
        const start = idx * capacity;
        p.imgs = allImgs.slice(start, start + p.records.length);
    });
    loading.style.display = 'none';
    drawPosterPage(BW, BH, title, subtitle);
}

function drawPosterPage(BW, BH, title, subtitle) {
    const canvas = document.getElementById('poster-canvas');
    const ctx = canvas.getContext('2d');
    const page = posterPages[posterCurrentPage];
    const total = posterPages.length;
    // Page indicator is appended to the editable footer when multi-page.
    const opts = Object.assign({}, posterOpts);
    if (total > 1) {
        const indicator = (lang === 'zh' ? '第 ' : 'Page ') + (posterCurrentPage + 1) +
                          (lang === 'zh' ? ' / ' : ' / ') + total + (lang === 'zh' ? ' 页' : '');
        opts.footer = (opts.footer ? opts.footer + '   ' : '') + indicator;
    }
    drawPoster(ctx, BW, BH, title, subtitle, page.records, page.imgs, opts);
    updatePosterPager();
}

function updatePosterPager() {
    const pager = document.getElementById('poster-pager');
    const info = document.getElementById('pager-info');
    const prev = document.getElementById('pager-prev');
    const next = document.getElementById('pager-next');
    const total = posterPages.length;
    if (total <= 1) {
        pager.style.display = 'none';
        return;
    }
    pager.style.display = 'flex';
    info.textContent = (posterCurrentPage + 1) + ' / ' + total;
    prev.disabled = (posterCurrentPage === 0);
    next.disabled = (posterCurrentPage === total - 1);
}

function posterPrevPage() {
    if (posterCurrentPage > 0) {
        posterCurrentPage--;
        const title = document.getElementById('poster-title').value.trim() || '客户品牌墙';
        const subtitle = document.getElementById('poster-subtitle').value.trim();
        const base = POSTER_SIZES[posterSizeKey] || POSTER_SIZES.portrait;
        drawPosterPage(base.w, base.h, title, subtitle);
    }
}

function posterNextPage() {
    if (posterCurrentPage < posterPages.length - 1) {
        posterCurrentPage++;
        const title = document.getElementById('poster-title').value.trim() || '客户品牌墙';
        const subtitle = document.getElementById('poster-subtitle').value.trim();
        const base = POSTER_SIZES[posterSizeKey] || POSTER_SIZES.portrait;
        drawPosterPage(base.w, base.h, title, subtitle);
    }
}

function roundedRect(ctx, x, y, w, h, r) {
    r = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
}

function fitText(ctx, text, maxWidth) {
    if (ctx.measureText(text).width <= maxWidth) return text;
    let t = text;
    while (t.length > 1 && ctx.measureText(t + '…').width > maxWidth) {
        t = t.slice(0, -1);
    }
    return t + '…';
}

function drawCornerFrame(ctx, x, y, len, thick, r, color) {
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = thick;
    ctx.lineCap = 'round';
    // top-left
    ctx.beginPath();
    ctx.arc(x + r, y + r, r, Math.PI, Math.PI * 1.5);
    ctx.lineTo(x + r + len, y);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(x + r, y + r, r, Math.PI * 1.5, Math.PI);
    ctx.moveTo(x, y + r);
    ctx.lineTo(x, y + r + len);
    ctx.stroke();
    ctx.restore();
}

function drawAllCorners(ctx, W, H, margin, len, thick, r, color) {
    drawCornerFrame(ctx, margin, margin, len, thick, r, color);
    // top-right
    ctx.save();
    ctx.translate(W - margin, margin);
    ctx.scale(-1, 1);
    drawCornerFrame(ctx, 0, 0, len, thick, r, color);
    ctx.restore();
    // bottom-left
    ctx.save();
    ctx.translate(margin, H - margin);
    ctx.scale(1, -1);
    drawCornerFrame(ctx, 0, 0, len, thick, r, color);
    ctx.restore();
    // bottom-right
    ctx.save();
    ctx.translate(W - margin, H - margin);
    ctx.scale(-1, -1);
    drawCornerFrame(ctx, 0, 0, len, thick, r, color);
    ctx.restore();
}

function drawSpacedText(ctx, text, x, y, spacing) {
    if (!spacing || spacing <= 0 || text.length <= 1) {
        ctx.fillText(text, x, y);
        return;
    }
    const chars = Array.from(text);
    const widths = chars.map(c => ctx.measureText(c).width);
    const total = widths.reduce((a, b) => a + b, 0) + spacing * (chars.length - 1);
    let cx = x - total / 2;
    ctx.textAlign = 'left';
    chars.forEach((c, i) => {
        ctx.fillText(c, cx, y);
        cx += widths[i] + spacing;
    });
    ctx.textAlign = 'center';
}

function measureSpaced(ctx, text, spacing) {
    if (!spacing || spacing <= 0 || text.length <= 1) return ctx.measureText(text).width;
    const chars = Array.from(text);
    return chars.reduce((a, c) => a + ctx.measureText(c).width, 0) + spacing * (chars.length - 1);
}

function fitSpaced(ctx, text, maxWidth, spacing) {
    if (measureSpaced(ctx, text, spacing) <= maxWidth) return text;
    let t = text;
    while (t.length > 1 && measureSpaced(ctx, t + '…', spacing) > maxWidth) {
        t = t.slice(0, -1);
    }
    return t + '…';
}

function drawSectionLabel(ctx, cx, y, labelZh, labelEn, W, color, font) {
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const lineLen = W * 0.13;
    const gap = Math.round(W * 0.018);
    const sizeZh = Math.round(W * 0.0165);
    const sizeEn = Math.round(W * 0.0115);
    ctx.fillStyle = color;
    ctx.font = '600 ' + sizeZh + 'px ' + font;
    const wZh = ctx.measureText(labelZh).width;
    ctx.font = '500 ' + sizeEn + 'px ' + POSTER_FONT;
    const wEn = ctx.measureText(labelEn).width;
    const blockW = wZh + gap * 0.7 + wEn;
    const startX = cx - blockW / 2;
    const lineY = y;
    ctx.strokeStyle = color;
    ctx.lineWidth = Math.max(1, Math.round(W * 0.0012));
    ctx.beginPath();
    ctx.moveTo(startX - lineLen, lineY);
    ctx.lineTo(startX - gap * 0.4, lineY);
    ctx.stroke();
    ctx.font = '600 ' + sizeZh + 'px ' + font;
    ctx.fillStyle = color;
    ctx.fillText(labelZh, startX + wZh / 2, lineY);
    ctx.font = '500 ' + sizeEn + 'px ' + POSTER_FONT;
    const enX = startX + wZh + gap * 0.7 + wEn / 2;
    ctx.fillText(labelEn, enX, lineY);
    ctx.beginPath();
    ctx.moveTo(startX + blockW + gap * 0.4, lineY);
    ctx.lineTo(startX + blockW + lineLen, lineY);
    ctx.stroke();
}

function drawPoster(ctx, W, H, title, subtitle, records, imgs, opts) {
    opts = opts || {};
    const S = opts.scale || 1;
    const showCity  = opts.showCity  !== false;
    const showDept  = !!opts.showDept;
    const showOwner = !!opts.showOwner;
    const showCoop  = !!opts.showCoop;
    // Count how many info lines the card carries (drives logo box / name sizing)
    const infoLines = (showCity ? 1 : 0) + (showDept ? 1 : 0) + (showOwner ? 1 : 0) + (showCoop ? 1 : 0);
    // Premium warm-cream business palette (independent of app theme)
    const C_BG      = '#F6EEE2';
    const C_BG2     = '#FBF6EE';
    const C_INK     = '#43301F';
    const C_GOLD    = '#B8904E';
    const C_GOLD_S  = '#9A7A42';
    const C_CARD    = '#FFFFFF';
    const C_CARD_SH = 'rgba(80,55,20,0.10)';
    const C_NAME    = '#43301F';
    const C_CITY    = '#A8927A';
    const C_FOOTER  = '#B8904E';

    // Background: soft warm vertical gradient
    const bgGrad = ctx.createLinearGradient(0, 0, 0, H);
    bgGrad.addColorStop(0, C_BG2);
    bgGrad.addColorStop(0.5, C_BG);
    bgGrad.addColorStop(1, C_BG2);
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, W, H);

    // Four corner gold frame
    const isScreen = W > H;
    const margin = Math.round(W * 0.028);
    const cornerLen = Math.round(W * 0.075);
    const cornerThick = Math.max(2, Math.round(W * 0.0022));
    const cornerR = Math.round(W * 0.012);
    drawAllCorners(ctx, W, H, margin, cornerLen, cornerThick, cornerR, C_GOLD);

    // ---- Title block ----
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const titleSize = Math.round(W * 0.046);
    ctx.fillStyle = C_INK;
    ctx.font = '700 ' + titleSize + 'px ' + POSTER_SERIF;
    const titleY = Math.round(H * (isScreen ? 0.12 : 0.095));
    ctx.fillText(fitText(ctx, title, W * 0.78), W / 2, titleY);

    // Diamond separator
    const diamondY = titleY + titleSize * 0.95;
    const dSize = Math.max(6, Math.round(W * 0.007));
    ctx.save();
    ctx.fillStyle = C_GOLD;
    ctx.translate(W / 2, diamondY);
    ctx.rotate(Math.PI / 4);
    ctx.fillRect(-dSize / 2, -dSize / 2, dSize, dSize);
    ctx.restore();

    // Subtitle (letter-spaced, gold)
    let blockBottom = diamondY + dSize / 2;
    if (subtitle) {
        const subSize = Math.round(W * (isScreen ? 0.015 : 0.018));
        ctx.fillStyle = C_GOLD_S;
        ctx.font = '400 ' + subSize + 'px ' + POSTER_FONT;
        const subY = diamondY + dSize * 1.8 + subSize * 0.8;
        // Lighter tracking for landscape (mixed EN/CN), stronger for portrait
        const spacing = Math.round(subSize * (isScreen ? 0.12 : 0.35));
        drawSpacedText(ctx, fitSpaced(ctx, subtitle, W * (isScreen ? 0.72 : 0.62), spacing), W / 2, subY, spacing);
        blockBottom = subY + subSize / 2;
    }

    // ---- Section label: 战略合作伙伴 / STRATEGIC PARTNERS ----
    // Position dynamically below the title/subtitle block with a clear gap
    const labelSizeZh = Math.round(W * 0.0165);
    const labelGap = Math.round(H * (isScreen ? 0.085 : 0.055));
    const labelY = blockBottom + labelGap + labelSizeZh / 2;
    drawSectionLabel(ctx, W / 2, labelY,
        lang === 'zh' ? '战略合作伙伴' : 'STRATEGIC PARTNERS',
        lang === 'zh' ? 'STRATEGIC PARTNERS' : 'TRUSTED BY',
        W, C_GOLD, POSTER_FONT);

    // ---- Logo grid ----
    // Geometry shared with pagination (posterBestGrid) so full pages tile
    // exactly with no empty slots.
    const n = records.length;
    const grid = posterBestGrid(W, H, isScreen, !!subtitle, infoLines, n);
    const best = grid.best;
    const offX = grid.offX, offY = grid.offY;
    const gap = grid.gap, cardW = grid.cardW, cardH = grid.cardH;
    const footerH = grid.footerH;

    records.forEach((r, i) => {
        const col = i % best.cols;
        const row = Math.floor(i / best.cols);
        const x = offX + col * best.cw + gap / 2;
        const y = offY + row * best.ch + gap / 2;

        // Card: white rounded with soft warm shadow (blur/offset scaled for high-res)
        ctx.save();
        ctx.shadowColor = C_CARD_SH;
        ctx.shadowBlur = cardH * 0.07 * S;
        ctx.shadowOffsetY = cardH * 0.025 * S;
        ctx.fillStyle = C_CARD;
        roundedRect(ctx, x, y, cardW, cardH, cardW * 0.07);
        ctx.fill();
        ctx.restore();

        // Logo box shrinks as more info lines are shown, leaving room for brand + meta.
        const logoRatio = infoLines === 0 ? 0.60
                        : infoLines === 1 ? 0.52
                        : infoLines === 2 ? 0.46
                        :                   0.42;
        const logoBoxH = cardH * logoRatio;
        const pad = cardW * 0.12;
        const boxX = x + pad, boxY = y + pad * 0.7;
        const boxW = cardW - pad * 2, boxH = logoBoxH - pad * 0.7;
        const img = imgs[i];
        if (img && img.naturalWidth > 0) {
            const logoScale = Math.min(boxW / img.naturalWidth, boxH / img.naturalHeight);
            const iw = img.naturalWidth * logoScale;
            const ih = img.naturalHeight * logoScale;
            ctx.drawImage(img, boxX + (boxW - iw) / 2, boxY + (boxH - ih) / 2, iw, ih);
        } else {
            const s = Math.min(boxW, boxH) * 0.62;
            const fx = boxX + (boxW - s) / 2;
            const fy = boxY + (boxH - s) / 2;
            ctx.fillStyle = r.color || C_GOLD;
            roundedRect(ctx, fx, fy, s, s, s * 0.22);
            ctx.fill();
            ctx.fillStyle = '#ffffff';
            ctx.font = '700 ' + Math.round(s * 0.36) + 'px ' + POSTER_SERIF;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(getInitials(r.brand), fx + s / 2, fy + s * 0.53);
        }

        // Brand name sits just below the logo; its vertical start adapts to info line count.
        const nameY = y + logoBoxH + cardH * (0.045 + infoLines * 0.012);
        const nameSize = Math.min(cardH * (0.105 - infoLines * 0.006), cardW * 0.14);
        ctx.fillStyle = C_NAME;
        ctx.font = '600 ' + Math.round(nameSize) + 'px ' + POSTER_FONT;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(fitText(ctx, r.brand || r.company || '', cardW * 0.88), x + cardW / 2, nameY);

        // ---- Optional info lines (city/region · business line · owner), user-toggled ----
        const lines = [];
        if (showCity) {
            const cityPart = [r.region, r.office_city].filter(Boolean).join(' · ');
            if (cityPart) lines.push(cityPart);
        }
        if (showDept && r.departments && r.departments.length) {
            lines.push(r.departments.join(' / '));
        }
        if (showOwner && r.owners && r.owners.length) {
            lines.push((lang === 'zh' ? '负责人：' : 'Owner: ') + r.owners.join('、'));
        }
        if (showCoop && r.cooperation_date) {
            lines.push((lang === 'zh' ? '合作 ' : 'Since ') + r.cooperation_date);
        }
        // Show info even on modest cards; font auto-scales so it stays legible.
        if (lines.length) {
            const infoSize = Math.max(7, Math.round(cardH * (0.058 - infoLines * 0.004)));
            const lineGap = infoSize * 1.30;
            const blockH = lines.length * lineGap;
            const availH = (y + cardH) - (nameY + nameSize * 0.6) - cardH * 0.02;
            const startY = nameY + nameSize * 0.8 + Math.max(0, (availH - blockH) / 2) + lineGap / 2;
            ctx.font = '400 ' + infoSize + 'px ' + POSTER_FONT;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            lines.forEach((txt, idx) => {
                ctx.fillStyle = idx === 0 ? C_CITY : 'rgba(67,48,31,0.55)';
                ctx.fillText(fitText(ctx, txt, cardW * 0.88), x + cardW / 2, startY + idx * lineGap);
            });
        }
    });

    // ---- Footer: gold line + editable slogan-style text ----
    const footY = H - footerH / 2;
    ctx.strokeStyle = C_GOLD;
    ctx.lineWidth = Math.max(1, Math.round(W * 0.0012 * S));
    const fLineLen = W * 0.16;
    const fGap = Math.round(W * 0.02);
    ctx.font = '500 ' + Math.round(W * 0.014) + 'px ' + POSTER_FONT;
    ctx.fillStyle = C_FOOTER;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    // Footer text is fully user-editable; fall back to a sensible default if emptied.
    const footMain = (opts.footer && opts.footer.trim())
        ? opts.footer.trim()
        : (document.getElementById('site-title').textContent + '  ·  ' + records.length + ' ' + t('clients_word'));
    const fw = ctx.measureText(footMain).width;
    ctx.beginPath();
    ctx.moveTo(W / 2 - fw / 2 - fGap - fLineLen, footY);
    ctx.lineTo(W / 2 - fw / 2 - fGap, footY);
    ctx.moveTo(W / 2 + fw / 2 + fGap, footY);
    ctx.lineTo(W / 2 + fw / 2 + fGap + fLineLen, footY);
    ctx.stroke();
    ctx.fillText(footMain, W / 2, footY);
}

function downloadPoster() {
    if (!posterPages.length) { alert(t('poster_fail')); return; }
    const base = POSTER_SIZES[posterSizeKey] || POSTER_SIZES.portrait;
    const scale = posterOpts.scale || 1;
    const title = document.getElementById('poster-title').value.trim() || '客户品牌墙';
    const subtitle = document.getElementById('poster-subtitle').value.trim();
    const dateStr = new Date().toISOString().slice(0, 10);
    const baseName = (lang === 'zh' ? '品牌墙海报-' : 'logo-wall-poster-') + posterSizeKey + '-' + dateStr;

    // Render each page into an offscreen canvas at full export resolution,
    // then trigger a download per page.
    const total = posterPages.length;
    posterPages.forEach((page, idx) => {
        const off = document.createElement('canvas');
        off.width = base.w * scale;
        off.height = base.h * scale;
        const octx = off.getContext('2d');
        octx.setTransform(scale, 0, 0, scale, 0, 0);
        const opts = Object.assign({}, posterOpts);
        if (total > 1) {
            const indicator = (lang === 'zh' ? '第 ' : 'Page ') + (idx + 1) +
                              ' / ' + total + (lang === 'zh' ? ' 页' : '');
            opts.footer = (opts.footer ? opts.footer + '   ' : '') + indicator;
        }
        drawPoster(octx, base.w, base.h, title, subtitle, page.records, page.imgs, opts);
        try {
            off.toBlob(blob => {
                if (!blob) return;
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = baseName + (total > 1 ? ('-p' + (idx + 1) + 'of' + total) : '') + '.png';
                document.body.appendChild(a);
                a.click();
                a.remove();
                setTimeout(() => URL.revokeObjectURL(a.href), 8000);
            }, 'image/png');
        } catch (e) {
            alert(t('poster_fail2') + ' ' + e.message);
        }
    });
}

// ============================================================
// COLLAPSIBLE HEADER
// ============================================================
function toggleHeader() {
    const h = document.querySelector('.header');
    h.classList.toggle('collapsed');
    localStorage.setItem('lw_header_collapsed', h.classList.contains('collapsed') ? '1' : '');
}
if (localStorage.getItem('lw_header_collapsed') === '1') {
    document.querySelector('.header').classList.add('collapsed');
}

function toggleToolbar() {
    const t = document.querySelector('.toolbar');
    t.classList.toggle('collapsed');
    localStorage.setItem('lw_toolbar_collapsed', t.classList.contains('collapsed') ? '1' : '');
}
if (localStorage.getItem('lw_toolbar_collapsed') === '1') {
    document.querySelector('.toolbar').classList.add('collapsed');
}

// ============================================================
// INIT
// ============================================================
(async () => {
    const ok = await checkAuth();
    if (ok) loadData();
})();
