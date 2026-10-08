#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logo Wall Server - FastAPI backend with admin panel.

Provides:
  - Static hosting of the logo wall (index.html, logos/, data.json)
  - Admin web UI at /admin for CRUD operations
  - REST API for client records
  - Logo discovery (Clearbit / Google favicon / DuckDuckGo) and upload
  - Excel import/export, full backup export/import

Run locally:  python server/app.py   (or: uvicorn server.app:app --port 8080)
Configuration is via environment variables / config.env — see
server/logowall/config.py and the README for the full list.
"""
import sys
import asyncio
import logging
import urllib.parse
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

# Make the `logowall` package importable both as `python server/app.py` and
# as `uvicorn server.app:app`.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query, Request, Depends
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from logowall import config, audit
from logowall.auth import (
    authenticate, create_token, current_user, require_user, require_admin, require_reader,
    hash_password, validate_new_password, find_user, bump_token_version, public_user,
    set_session_cookie, clear_session_cookie, client_ip, login_throttle,
    ensure_default_admin, WEAK_DEFAULT_PASSWORD,
)
from logowall.backup import build_backup_zip, import_backup, BackupError
from logowall.constants import OFFICE_MAP, REGION_MAP, get_region, brand_keywords, match_brand_logo
from logowall.excel import read_rows, write_rows, normalize_date, opt_str, ExcelError
from logowall.images import (
    prepare_logo, content_key, is_safe_logo_name, sniff_image, InvalidImage,
)
from logowall.netfetch import fetch as safe_fetch, FetchError
from logowall.storage import load_data, save_data, load_users, save_users, data_etag, DATA_LOCK

log = logging.getLogger('logowall')

LOGOS_DIR = config.LOGOS_DIR
NO_CACHE = {'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache'}
IMAGE_MIME = {'.png': 'image/png', '.jpg': 'image/jpeg', '.gif': 'image/gif',
              '.webp': 'image/webp', '.svg': 'image/svg+xml', '.ico': 'image/x-icon'}
# Untrusted images (uploaded SVGs, proxied files) must never run script if a
# user opens them directly: sandbox them with a locked-down CSP.
IMAGE_CSP = "default-src 'none'; style-src 'unsafe-inline'; sandbox"


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def next_id(records: list) -> int:
    return max((r.get('id', 0) for r in records), default=0) + 1


def split_list(s: Optional[str]) -> List[str]:
    if not s:
        return []
    return [p.strip() for p in str(s).replace('；', ';').split(';') if p.strip()]


clean_owner = clean_dept = split_list


def color_from_name(name: str) -> str:
    colors = ['#4F46E5', '#7C3AED', '#DB2777', '#DC2626', '#EA580C',
              '#CA8A04', '#16A34A', '#0891B2', '#2563EB', '#9333EA',
              '#0D9488', '#65A30D', '#C026D3', '#0284C7', '#475569']
    h = 0
    for ch in name or '':
        h = ord(ch) + ((h << 5) - h)
    return colors[abs(h) % len(colors)]


def check_logo_url(v: Optional[str]) -> Optional[str]:
    """A logo is either a library file (logos/<name>) or an http(s) URL."""
    if v is None:
        return None
    v = v.strip()
    if not v:
        return ''
    if v.startswith('/'):
        v = v.lstrip('/')
    if v.startswith('logos/') and is_safe_logo_name(v[len('logos/'):]):
        return v
    if urllib.parse.urlsplit(v).scheme in ('http', 'https'):
        return v
    raise HTTPException(400, 'logo_url must be logos/<file> or an http(s) URL')


def check_website(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    v = v.strip()
    if not v:
        return ''
    scheme = urllib.parse.urlsplit(v).scheme
    if scheme and scheme not in ('http', 'https') and '.' not in scheme:
        raise HTTPException(400, 'website must be an http(s) URL or a domain')
    return v


async def read_upload(file: UploadFile, limit: int) -> bytes:
    content = await file.read(limit + 1)
    if len(content) > limit:
        raise HTTPException(413, f'File too large (max {limit // (1024 * 1024)}MB)')
    return content


def store_logo(content: bytes) -> dict:
    """Validate, optimise and store a logo under a content-addressed name."""
    try:
        data, ext = prepare_logo(content)
    except InvalidImage as e:
        raise HTTPException(400, str(e))
    key = content_key(content, ext)
    path = LOGOS_DIR / key
    if not path.exists():
        tmp = path.with_name(path.name + '.tmp')
        tmp.write_bytes(data)
        tmp.replace(path)
    return {'url': f'logos/{key}', 'filename': key, 'size': len(data)}


# ---------------------------------------------------------------------------
# App, lifespan & middleware
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(_app):
    ensure_default_admin()
    yield


app = FastAPI(title='Logo Wall API', docs_url='/api/docs', lifespan=lifespan)

if config.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_methods=['GET', 'POST', 'PUT', 'DELETE'],
        allow_headers=['Authorization', 'Content-Type'],
    )

PUBLIC_API = {'/api/auth/login', '/api/auth/check', '/api/auth/logout', '/api/health'}
WRITE_METHODS = ('POST', 'PUT', 'DELETE', 'PATCH')


def _needs_auth(path: str) -> bool:
    if path in PUBLIC_API:
        return False
    return path == '/data.json' or path.startswith('/logos/') or path.startswith('/api/')


@app.middleware('http')
async def auth_and_headers(request: Request, call_next):
    path = request.url.path

    # Gate data + API behind login. Pages (/, /admin, /login) are public HTML
    # shells that redirect to /login client-side and contain no data.
    if config.AUTH_ENABLED and _needs_auth(path) and not current_user(request):
        response = JSONResponse({'detail': 'Not authenticated'}, status_code=401)
    else:
        response = await call_next(request)

    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('Referrer-Policy', 'same-origin')
    if path.startswith('/logos/') or path == '/api/imgproxy':
        response.headers['Content-Security-Policy'] = IMAGE_CSP

    if request.method in WRITE_METHODS and path.startswith('/api/') and path != '/api/auth/login':
        user = getattr(request.state, 'user', None)
        audit.record(user.get('sub') if user else '', client_ip(request),
                     request.method, path, response.status_code)
    return response


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ClientIn(BaseModel):
    company: str
    office_code: str = ''
    departments: str = ''       # semicolon-separated in API for simplicity
    owners: str = ''            # semicolon-separated
    cooperation_date: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None


class ClientUpdate(BaseModel):
    company: Optional[str] = None
    office_code: Optional[str] = None
    departments: Optional[str] = None
    owners: Optional[str] = None
    cooperation_date: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = 'viewer'
    display_name: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    display_name: Optional[str] = None


# Site appearance presets (validated server-side)
THEME_PRESETS = ['classic', 'gold', 'violet', 'orange', 'green']
BG_PATTERNS = ['none', 'dots', 'grid', 'glow']
SETTINGS_TEXT_FIELDS = ('title', 'title_en', 'tagline', 'tagline_en', 'footer_text', 'footer_en')
SETTINGS_TEXT_MAX = 300


class SettingsIn(BaseModel):
    title: Optional[str] = None
    title_en: Optional[str] = None
    tagline: Optional[str] = None
    tagline_en: Optional[str] = None
    footer_text: Optional[str] = None
    footer_en: Optional[str] = None
    theme: Optional[str] = None
    bg_pattern: Optional[str] = None
    custom_primary: Optional[str] = None     # hex color or '' to clear
    custom_accent: Optional[str] = None      # hex color or '' to clear


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
@app.get('/')
def root():
    return FileResponse(config.BASE_DIR / 'index.html', headers=NO_CACHE)


@app.get('/admin')
def admin_page():
    return FileResponse(config.TEMPLATES_DIR / 'admin.html', headers=NO_CACHE)


@app.get('/admin/')
def admin_slash():
    return RedirectResponse(url='/admin')


@app.get('/login')
def login_page():
    return FileResponse(config.TEMPLATES_DIR / 'login.html', headers=NO_CACHE)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@app.post('/api/auth/login')
async def auth_login(request: Request, username: str = Form(...), password: str = Form(...)):
    """Authenticate user and return a JWT (also set as an HttpOnly cookie)."""
    ip = client_ip(request)
    wait = login_throttle.retry_after(ip, username)
    if wait:
        audit.record(username, ip, 'POST', '/api/auth/login', 429, 'throttled')
        return JSONResponse({'detail': f'尝试次数过多，请 {wait // 60 + 1} 分钟后再试 / '
                                       f'Too many attempts, retry in {wait}s'},
                            status_code=429, headers={'Retry-After': str(wait)})
    user = await asyncio.get_running_loop().run_in_executor(None, authenticate, username, password)
    if not user:
        login_throttle.record_failure(ip, username)
        audit.record(username, ip, 'POST', '/api/auth/login', 401, 'bad credentials')
        raise HTTPException(401, '用户名或密码错误')
    login_throttle.record_success(ip, username)
    audit.record(username, ip, 'POST', '/api/auth/login', 200)
    token = create_token(user)
    resp = JSONResponse({
        'ok': True,
        'token': token,
        'user': {
            'username': user['username'],
            'role': user['role'],
            'display_name': user.get('display_name', user['username']),
        },
        # Lets the UI nag users still on a weak/default password
        'password_weak': password == WEAK_DEFAULT_PASSWORD or len(password) < config.MIN_PASSWORD_LEN,
    })
    set_session_cookie(resp, request, token)
    return resp


@app.get('/api/auth/check')
def auth_check(request: Request):
    """Check whether the caller's token is valid. Returns user info.

    A valid Bearer token also (re)issues the HttpOnly session cookie, so pages
    can load protected images without putting the token in URLs.
    """
    user = current_user(request)
    if not user:
        resp = JSONResponse({'ok': False})
        clear_session_cookie(resp)
        return resp
    resp = JSONResponse({'ok': True, 'user': user})
    auth = request.headers.get('Authorization', '')
    if auth[:7].lower() == 'bearer ' and not user.get('legacy_token'):
        set_session_cookie(resp, request, auth[7:].strip())
    return resp


@app.post('/api/auth/logout')
def auth_logout():
    resp = JSONResponse({'ok': True})
    clear_session_cookie(resp)
    return resp


@app.get('/api/auth/me')
def auth_me(user: dict = Depends(require_user)):
    return {'ok': True, 'user': user}


# ---------------------------------------------------------------------------
# User management (admin only)
# ---------------------------------------------------------------------------
def _check_username(name: str) -> str:
    name = (name or '').strip()
    if not name or len(name) > 64 or any(c in name for c in '/\\<>"\'&'):
        raise HTTPException(400, 'Invalid username')
    return name


@app.get('/api/users')
def list_users(_admin: dict = Depends(require_admin)):
    users = [{
        'username': u['username'],
        'role': u.get('role', 'viewer'),
        'display_name': u.get('display_name', u['username']),
        'created_at': u.get('created_at', ''),
    } for u in load_users()['users']]
    return {'users': users}


@app.post('/api/users')
def create_user(body: UserCreate, _admin: dict = Depends(require_admin)):
    if body.role not in ('admin', 'viewer'):
        raise HTTPException(400, 'Invalid role')
    username = _check_username(body.username)
    validate_new_password(body.password)
    with DATA_LOCK:
        users_data = load_users()
        if find_user(users_data, username):
            raise HTTPException(400, '用户名已存在')
        users_data['users'].append({
            'username': username,
            'password_hash': hash_password(body.password),
            'role': body.role,
            'display_name': (body.display_name or username).strip(),
            'token_version': 0,
            'created_at': datetime.now(timezone.utc).isoformat(),
        })
        save_users(users_data)
    return {'ok': True, 'username': username}


def _admin_count(users: list) -> int:
    return sum(1 for u in users if u.get('role') == 'admin')


@app.put('/api/users/{username}')
def update_user(username: str, body: UserUpdate, admin: dict = Depends(require_admin)):
    with DATA_LOCK:
        users_data = load_users()
        u = find_user(users_data, username)
        if u is None:
            raise HTTPException(404, 'User not found')
        revoke = False
        if body.password is not None and body.password != '':
            validate_new_password(body.password)
            u['password_hash'] = hash_password(body.password)
            revoke = True
        if body.role is not None and body.role != u.get('role'):
            if body.role not in ('admin', 'viewer'):
                raise HTTPException(400, 'Invalid role')
            if u.get('role') == 'admin' and _admin_count(users_data['users']) <= 1:
                raise HTTPException(400, 'Cannot demote the last admin')
            u['role'] = body.role
            revoke = True
        if body.display_name is not None:
            u['display_name'] = body.display_name.strip()
        if body.username is not None and body.username.strip() != username:
            new_name = _check_username(body.username)
            if find_user(users_data, new_name):
                raise HTTPException(400, '用户名已存在')
            u['username'] = new_name
            revoke = True
        if revoke:
            # Log out every existing session of this account
            bump_token_version(u)
        save_users(users_data)
    result = {'ok': True}
    # Editing your own account revokes your session too: hand back a new one
    if revoke and admin.get('sub') == username and not admin.get('legacy_token'):
        result['token'] = create_token(u)
        result['user'] = public_user(u)
    return result


@app.delete('/api/users/{username}')
def delete_user(username: str, _admin: dict = Depends(require_admin)):
    with DATA_LOCK:
        users_data = load_users()
        u = find_user(users_data, username)
        if u is None:
            raise HTTPException(404, 'User not found')
        if u.get('role') == 'admin' and _admin_count(users_data['users']) <= 1:
            raise HTTPException(400, 'Cannot delete the last admin')
        users_data['users'] = [x for x in users_data['users'] if x is not u]
        save_users(users_data)
    return {'ok': True}


# ---------------------------------------------------------------------------
# Data + static logos
# ---------------------------------------------------------------------------
@app.get('/data.json')
def get_data(request: Request, _user=Depends(require_reader)):
    etag = data_etag()
    headers = {'ETag': etag, 'Cache-Control': 'no-cache'}
    if request.headers.get('if-none-match') == etag:
        return Response(status_code=304, headers=headers)
    return JSONResponse(load_data(), headers=headers)


app.mount('/logos', StaticFiles(directory=str(LOGOS_DIR)), name='logos')


@app.get('/api/health')
def health_check():
    writable = True
    try:
        probe = config.DATA_DIR / '.health'
        probe.write_text('ok')
        probe.unlink()
    except OSError:
        writable = False
    return JSONResponse({'status': 'ok' if writable else 'degraded', 'data_writable': writable},
                        status_code=200 if writable else 503)


@app.get('/api/audit')
def get_audit(limit: int = 200, _admin: dict = Depends(require_admin)):
    """Most recent write operations / logins, newest first."""
    return {'entries': audit.tail(limit)}


# ---------------------------------------------------------------------------
# Client CRUD
# ---------------------------------------------------------------------------
@app.get('/api/clients')
def list_clients(
    office: Optional[str] = None,
    dept: Optional[str] = None,
    owner: Optional[str] = None,
    region: Optional[str] = None,
    q: Optional[str] = None,
    _user=Depends(require_reader),
):
    records = load_data().get('records', [])
    if office and office != 'all':
        records = [r for r in records if r.get('office_city') == office]
    if dept and dept != 'all':
        records = [r for r in records if dept in (r.get('departments') or [])]
    if owner and owner != 'all':
        records = [r for r in records if owner in (r.get('owners') or [])]
    if region and region != 'all':
        records = [r for r in records if r.get('region') == region]
    if q:
        ql = q.lower()
        records = [r for r in records if ql in (r.get('company', '') + ' ' +
                   r.get('brand', '') + ' ' + ' '.join(r.get('owners', []) or [])).lower()]
    return {'total': len(records), 'records': records}


@app.get('/api/clients/{client_id}')
def get_client(client_id: int, _user=Depends(require_reader)):
    for r in load_data()['records']:
        if r.get('id') == client_id:
            return r
    raise HTTPException(404, 'Client not found')


@app.post('/api/clients')
def create_client(client: ClientIn, _admin: dict = Depends(require_admin)):
    company = client.company.strip()
    if not company:
        raise HTTPException(400, 'company is required')
    logo_url = check_logo_url(client.logo_url)
    website = check_website(client.website)
    office_code = (client.office_code or '').strip().upper()
    with DATA_LOCK:
        data = load_data()
        record = {
            'id': next_id(data['records']),
            'company': company,
            'brand': company,
            'office_code': office_code,
            'office_city': OFFICE_MAP.get(office_code, office_code),
            'region': get_region(office_code),
            'departments': clean_dept(client.departments),
            'owners': clean_owner(client.owners),
            'cooperation_date': normalize_date(client.cooperation_date),
            'logo_url': logo_url or None,
            'website': website or '',
            'description': client.description or '',
            'color': color_from_name(company),
        }
        data['records'].append(record)
        save_data(data)
    return record


@app.put('/api/clients/{client_id}')
def update_client(client_id: int, update: ClientUpdate, _admin: dict = Depends(require_admin)):
    logo_url = check_logo_url(update.logo_url)
    website = check_website(update.website)
    with DATA_LOCK:
        data = load_data()
        for r in data['records']:
            if r.get('id') != client_id:
                continue
            if update.company is not None and update.company.strip():
                r['company'] = update.company.strip()
                r['brand'] = r['company']
                r['color'] = color_from_name(r['company'])
            if update.office_code is not None:
                oc = update.office_code.strip().upper()
                r['office_code'] = oc
                r['office_city'] = OFFICE_MAP.get(oc, oc)
                r['region'] = get_region(oc)
            if update.departments is not None:
                r['departments'] = clean_dept(update.departments)
            if update.owners is not None:
                r['owners'] = clean_owner(update.owners)
            if update.cooperation_date is not None:
                r['cooperation_date'] = normalize_date(update.cooperation_date)
            if logo_url is not None:
                r['logo_url'] = logo_url
            if website is not None:
                r['website'] = website
            if update.description is not None:
                r['description'] = update.description
            save_data(data)
            return r
    raise HTTPException(404, 'Client not found')


@app.delete('/api/clients/{client_id}')
def delete_client(client_id: int, _admin: dict = Depends(require_admin)):
    with DATA_LOCK:
        data = load_data()
        before = len(data['records'])
        data['records'] = [r for r in data['records'] if r.get('id') != client_id]
        if len(data['records']) == before:
            raise HTTPException(404, 'Client not found')
        save_data(data)
    return {'ok': True}


@app.get('/api/filters')
def get_filters(_user=Depends(require_reader)):
    data = load_data()
    owners = sorted({o for r in data['records'] for o in (r.get('owners') or [])})
    regions = sorted({r.get('region') or get_region(r.get('office_code', ''))
                      for r in data['records'] if r.get('region') or r.get('office_code')})
    return {
        'offices': data.get('offices', []),
        'departments': data.get('departments', []),
        'regions': regions,
        'owners': owners,
        'office_codes': OFFICE_MAP,
        'region_map': REGION_MAP,
    }


# ---------------------------------------------------------------------------
# Logo discovery
# ---------------------------------------------------------------------------
def _domain_from_url(url: str) -> str:
    url = (url or '').strip()
    if not url:
        return ''
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    host = (urllib.parse.urlsplit(url).hostname or '').lower()
    return host[4:] if host.startswith('www.') else host


@app.get('/api/logo/discover')
async def discover_logo(
    company: str = Query(...),
    website: Optional[str] = Query(None),
    _admin: dict = Depends(require_admin),
):
    """Try multiple strategies to find a logo URL for a company.
    Priority when website is provided: domain-based services first, then keyword DB.
    """
    results = []
    company_lower = company.lower()
    domain = _domain_from_url(website or '')
    q_domain = urllib.parse.quote(domain)

    # 1. If website given, try domain-based services FIRST (most accurate)
    if domain:
        results.append({'source': 'clearbit', 'url': f'https://logo.clearbit.com/{q_domain}',
                        'note': f'Clearbit Logo ({domain})'})
        results.append({'source': 'google_favicon',
                        'url': f'https://www.google.com/s2/favicons?domain={q_domain}&sz=128',
                        'note': f'Google Favicon ({domain})'})
        results.append({'source': 'duckduckgo', 'url': f'https://icons.duckduckgo.com/ip3/{q_domain}.ico',
                        'note': f'DuckDuckGo Favicon ({domain})'})

    # 2. Check built-in brand keyword DB
    for kw, url in brand_keywords().items():
        if kw.lower() in company_lower or company_lower in kw.lower():
            results.append({'source': 'builtin', 'keyword': kw, 'url': url,
                            'note': f'内置品牌库 ({kw})'})

    # 3. If no website and ASCII name, try guessing domain
    if not domain and company.isascii():
        guessed = ''.join(ch for ch in company if ch.isalnum()).lower()
        if len(guessed) > 2:
            results.append({'source': 'guess', 'url': f'https://logo.clearbit.com/{guessed}.com',
                            'note': f'猜测域名 ({guessed}.com)'})

    # 4. Verify URLs are reachable (HEAD requests, in parallel)
    async def verify(item):
        try:
            resp = await safe_fetch(item['url'], method='HEAD', max_bytes=config.IMGPROXY_MAX_BYTES,
                                    timeout=5)
            item['status'] = resp.status_code
            item['ok'] = resp.status_code == 200
            item['content_type'] = resp.headers.get('content-type', '')
        except FetchError as e:
            item['status'] = 0
            item['ok'] = False
            item['error'] = str(e)[:80]
        return item

    verified = await asyncio.gather(*(verify(i) for i in results))
    return {'company': company, 'domain': domain, 'results': list(verified)}


# ---------------------------------------------------------------------------
# Logo library
# ---------------------------------------------------------------------------
def _logo_usage(data: dict) -> dict:
    usage = {}
    for r in data['records']:
        url = r.get('logo_url') or ''
        if url:
            usage.setdefault(url, []).append(r)
    return usage


def _safe_logo_path(filename: str) -> Path:
    name = Path(filename).name
    if not is_safe_logo_name(name):
        raise HTTPException(400, 'Invalid logo filename')
    return LOGOS_DIR / name


@app.get('/api/logos')
def list_logos(_user=Depends(require_reader)):
    """List all logo files in the logos/ directory with usage info."""
    usage = _logo_usage(load_data())
    logos = []
    files = [f for f in LOGOS_DIR.iterdir() if f.is_file() and not f.name.endswith('.tmp')]
    for f in sorted(files, key=lambda p: p.stat().st_mtime, reverse=True):
        rel = f'logos/{f.name}'
        stat = f.stat()
        logos.append({
            'url': rel,
            'filename': f.name,
            'size': stat.st_size,
            'modified': int(stat.st_mtime),
            'used_by': [r.get('brand', r.get('company', '')) for r in usage.get(rel, [])],
        })
    return {'total': len(logos), 'logos': logos}


@app.post('/api/logo/batch-upload')
async def batch_upload_logos(files: List[UploadFile] = File(...), _admin: dict = Depends(require_admin)):
    """Upload multiple logo files at once."""
    results = []
    for file in files:
        content = await file.read(config.MAX_UPLOAD_BYTES + 1)
        if len(content) > config.MAX_UPLOAD_BYTES:
            results.append({'ok': False, 'filename': file.filename, 'error': 'too large'})
            continue
        try:
            stored = store_logo(content)
        except HTTPException as e:
            results.append({'ok': False, 'filename': file.filename, 'error': e.detail})
            continue
        results.append({'ok': True, 'original': file.filename, **stored})
    return {'uploaded': sum(1 for r in results if r['ok']), 'results': results}


@app.delete('/api/logos/{filename}')
def delete_logo(filename: str, _admin: dict = Depends(require_admin)):
    """Delete a logo file (only if not used by any client)."""
    filepath = _safe_logo_path(filename)
    with DATA_LOCK:
        if not filepath.exists():
            raise HTTPException(404, 'Logo not found')
        used_by = _logo_usage(load_data()).get(f'logos/{filepath.name}', [])
        if used_by:
            raise HTTPException(400, f'Logo is used by {len(used_by)} client(s), cannot delete')
        filepath.unlink()
    return {'ok': True}


@app.post('/api/logo/assign')
def assign_logo(client_id: int = Form(...), logo_url: str = Form(...),
                _admin: dict = Depends(require_admin)):
    """Assign a logo from the library to a client."""
    logo_url = check_logo_url(logo_url)
    with DATA_LOCK:
        data = load_data()
        for r in data['records']:
            if r.get('id') == client_id:
                r['logo_url'] = logo_url
                save_data(data)
                return {'ok': True, 'client_id': client_id, 'logo_url': logo_url}
    raise HTTPException(404, 'Client not found')


@app.post('/api/logo/replace')
async def replace_logo(filename: str = Form(...), file: UploadFile = File(...),
                       _admin: dict = Depends(require_admin)):
    """Replace an existing logo file with a new image.

    Every client using the old file is updated. If the new image has a
    different type (e.g. png -> svg) it is stored under the new extension so
    it is always served with the right content type.
    """
    filepath = _safe_logo_path(filename)
    content = await read_upload(file, config.MAX_UPLOAD_BYTES)
    try:
        data_bytes, ext = prepare_logo(content)
    except InvalidImage as e:
        raise HTTPException(400, str(e))
    with DATA_LOCK:
        if not filepath.exists():
            raise HTTPException(404, 'Logo file not found')
        old_ext = filepath.suffix.lower().replace('.jpeg', '.jpg')
        target = filepath if old_ext == ext else filepath.with_suffix(ext)
        tmp = target.with_name(target.name + '.tmp')
        tmp.write_bytes(data_bytes)
        tmp.replace(target)
        if target != filepath:
            data = load_data()
            old_rel, new_rel = f'logos/{filepath.name}', f'logos/{target.name}'
            for r in data['records']:
                if r.get('logo_url') == old_rel:
                    r['logo_url'] = new_rel
            save_data(data)
            filepath.unlink(missing_ok=True)
    return {'ok': True, 'url': f'logos/{target.name}', 'filename': target.name,
            'size': len(data_bytes)}


@app.get('/api/logo/info/{filename}')
def logo_info(filename: str, _user=Depends(require_reader)):
    """Get detailed info about a specific logo."""
    filepath = _safe_logo_path(filename)
    if not filepath.exists():
        raise HTTPException(404, 'Logo not found')
    used_by = [{'id': r['id'], 'brand': r.get('brand', r.get('company', ''))}
               for r in _logo_usage(load_data()).get(f'logos/{filepath.name}', [])]
    stat = filepath.stat()
    return {
        'filename': filepath.name,
        'url': f'logos/{filepath.name}',
        'size': stat.st_size,
        'modified': int(stat.st_mtime),
        'used_by': used_by,
        'used_count': len(used_by),
    }


@app.post('/api/logo/upload')
async def upload_logo(file: UploadFile = File(...), _admin: dict = Depends(require_admin)):
    content = await read_upload(file, config.MAX_UPLOAD_BYTES)
    return {'ok': True, **store_logo(content)}


@app.post('/api/logo/fetch')
async def fetch_logo(url: str = Form(...), _admin: dict = Depends(require_admin)):
    """Download a remote logo URL and save it locally."""
    try:
        resp = await safe_fetch(url, max_bytes=config.MAX_UPLOAD_BYTES, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 Chrome/120.0 Safari/537.36',
        })
    except FetchError as e:
        raise HTTPException(400, f'Failed to download: {e}')
    if resp.status_code != 200:
        raise HTTPException(400, f'Failed to download: upstream returned {resp.status_code}')
    return {'ok': True, **store_logo(resp.content)}


# ---------------------------------------------------------------------------
# Excel import/export
# ---------------------------------------------------------------------------
@app.post('/api/import-excel')
async def import_excel(file: UploadFile = File(...), _admin: dict = Depends(require_admin)):
    content = await read_upload(file, config.MAX_EXCEL_BYTES)
    try:
        rows = list(read_rows(content))
    except ExcelError as e:
        raise HTTPException(400, str(e))

    added = logo_matched = 0
    with DATA_LOCK:
        data = load_data()
        for row in rows:
            company = opt_str(row['company'])
            if not company:
                continue
            office_code = opt_str(row['office']).upper()
            _kw, logo_url = match_brand_logo(company)
            if logo_url:
                logo_matched += 1
            data['records'].append({
                'id': next_id(data['records']),
                'company': company,
                'brand': company,
                'office_code': office_code,
                'office_city': OFFICE_MAP.get(office_code, office_code),
                'region': get_region(office_code),
                'departments': clean_dept(opt_str(row['depts'])),
                'owners': clean_owner(opt_str(row['owners'])),
                'cooperation_date': normalize_date(row['coop']),
                'logo_url': logo_url,
                'website': '',
                'color': color_from_name(company),
            })
            added += 1
        save_data(data)
    return {'ok': True, 'added': added, 'total': len(data['records']), 'logo_matched': logo_matched}


@app.get('/api/export-excel')
def export_excel(_admin: dict = Depends(require_admin)):
    rows = [[
        r.get('company', '') or '',
        r.get('office_code', '') or '',
        r.get('region') or get_region(r.get('office_code', '')),
        '；'.join(r.get('departments') or []),
        '；'.join(r.get('owners') or []),
        r.get('cooperation_date', '') or '',
    ] for r in load_data()['records']]
    return Response(
        content=write_rows(rows),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename="logo_wall_export.xlsx"'},
    )


# ---------------------------------------------------------------------------
# Site settings (title / tagline / theme)
# ---------------------------------------------------------------------------
@app.put('/api/settings')
def update_settings(s: SettingsIn, _admin: dict = Depends(require_admin)):
    with DATA_LOCK:
        data = load_data()
        for field in SETTINGS_TEXT_FIELDS:
            value = getattr(s, field)
            if value is not None:
                if len(value) > SETTINGS_TEXT_MAX:
                    raise HTTPException(400, f'{field} is too long (max {SETTINGS_TEXT_MAX})')
                data[field] = value.strip()
        if s.theme is not None:
            data['theme'] = s.theme if s.theme in THEME_PRESETS else 'classic'
        if s.bg_pattern is not None:
            data['bg_pattern'] = s.bg_pattern if s.bg_pattern in BG_PATTERNS else 'none'
        for field in ('custom_primary', 'custom_accent'):
            value = getattr(s, field)
            if value is not None:
                v = value.strip()
                if v and not (len(v) == 7 and v[0] == '#' and
                              all(c in '0123456789abcdefABCDEF' for c in v[1:])):
                    raise HTTPException(400, f'{field} must be a #RRGGBB hex color')
                data[field] = v
        save_data(data)
    return {'ok': True}


# ---------------------------------------------------------------------------
# Full backup export / import (data.json + logos/ + users.json)
# ---------------------------------------------------------------------------
@app.get('/api/backup/export')
def backup_export(_admin: dict = Depends(require_admin)):
    """Export the full data directory as a single zip backup."""
    fname = 'logo-wall-backup-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.zip'
    return Response(
        content=build_backup_zip(),
        media_type='application/zip',
        headers={'Content-Disposition': f'attachment; filename="{fname}"'},
    )


@app.post('/api/backup/import')
async def backup_import(
    file: UploadFile = File(...),
    restore_users: str = Form('false'),
    _admin: dict = Depends(require_admin),
):
    """Import a zip backup: replaces data.json, merges logos/ files and, only
    when restore_users=true, replaces users.json. A snapshot of the current
    state is saved to DATA_DIR/backups/ first."""
    content = await read_upload(file, config.BACKUP_MAX_BYTES)
    want_users = restore_users.strip().lower() in ('true', '1', 'yes', 'on')
    try:
        return await asyncio.get_running_loop().run_in_executor(
            None, import_backup, content, want_users)
    except BackupError as e:
        raise HTTPException(400, str(e))


# ---------------------------------------------------------------------------
# Image proxy (used by poster export to avoid canvas CORS tainting)
# ---------------------------------------------------------------------------
@app.get('/api/imgproxy')
async def img_proxy(url: str, _user=Depends(require_reader)):
    try:
        r = await safe_fetch(url, max_bytes=config.IMGPROXY_MAX_BYTES, timeout=config.IMGPROXY_TIMEOUT,
                             headers={'User-Agent': 'Mozilla/5.0 (LogoWall Poster Export)'})
    except FetchError as e:
        raise HTTPException(e.status if e.status in (400, 403, 413) else 502, str(e))
    if r.status_code != 200:
        raise HTTPException(502, f'Upstream returned {r.status_code}')
    ext = sniff_image(r.content)
    if not ext:
        raise HTTPException(415, 'Upstream did not return an image')
    return Response(content=r.content, media_type=IMAGE_MIME[ext],
                    headers={'Cache-Control': 'private, max-age=86400'})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def get_local_ip():
    """Return the main local LAN IP address (the one used for default route)."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
        finally:
            s.close()
    except Exception:
        return None


if __name__ == '__main__':
    import uvicorn
    port = config.PORT
    lan_ip = get_local_ip()
    print(f'\n{"="*58}')
    print('  Logo Wall server is running')
    print(f'{"-"*58}')
    print('  On this computer:')
    print(f'    Brand wall :  http://localhost:{port}/')
    print(f'    Admin panel:  http://localhost:{port}/admin')
    print(f'    API docs   :  http://localhost:{port}/api/docs')
    if lan_ip and config.HOST != '127.0.0.1':
        print(f'{"-"*58}')
        print('  From other phones/computers on the same Wi-Fi/LAN:')
        print(f'    Brand wall :  http://{lan_ip}:{port}/')
        print(f'    Admin panel:  http://{lan_ip}:{port}/admin')
    print(f'{"-"*58}')
    print(f'  Master API token: {"set" if config.ADMIN_TOKEN else "disabled (use account login)"}')
    if config.AUTH_ENABLED:
        print(f'  Auth        :  ENABLED (JWT, {config.JWT_EXPIRE_DAYS}-day session)')
        print(f'  Login page  :  http://localhost:{port}/login')
    else:
        print('  Auth        :  DISABLED (wall is public; admin still needs login)')
    print(f'{"="*58}\n')
    uvicorn.run(app, host=config.HOST, port=port, log_level=config.LOG_LEVEL)
