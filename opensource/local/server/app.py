#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logo Wall Server - FastAPI backend with admin panel.

Provides:
  - Static hosting of the logo wall (index.html, logos/, data.json)
  - Admin web UI at /admin for CRUD operations
  - REST API for client records
  - Logo discovery (Clearbit / Google favicon / DuckDuckGo) and upload
  - Excel import/export

Run locally:  python app.py   (or: uvicorn app:app --host 0.0.0.0 --port 8080)
Environment variables:
  ADMIN_TOKEN    - required token for write operations (default: admin123)
  DATA_DIR       - directory containing data.json/logos (default: parent of this file)
"""
import os
import io
import re
import json
import time
import uuid
import hashlib
import zipfile
import mimetypes
import urllib.parse
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------------------------
# Paths & config
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent  # project root (cwpos/)
DATA_DIR = Path(os.environ.get('DATA_DIR', str(BASE_DIR)))
DATA_JSON = DATA_DIR / 'data.json'
LOGOS_DIR = DATA_DIR / 'logos'
EXCEL_PATH = DATA_DIR / 'Logo Wall 2 with name.xlsx'

LOGOS_DIR.mkdir(parents=True, exist_ok=True)

ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', 'admin123')

# ---- Auth config -----------------------------------------------------------
AUTH_ENABLED = os.environ.get('AUTH_ENABLED', 'true').lower() in ('true', '1', 'yes')
JWT_SECRET = os.environ.get('JWT_SECRET', 'logo-wall-secret-' + hashlib.md5(ADMIN_TOKEN.encode()).hexdigest()[:16])
JWT_ALGORITHM = 'HS256'
JWT_EXPIRE_DAYS = int(os.environ.get('JWT_EXPIRE_DAYS', '7'))
USERS_JSON = DATA_DIR / 'users.json'

# ---- Runtime limits / binding (configurable via env / config.env) ----------
HOST = os.environ.get('HOST', '0.0.0.0')
MAX_UPLOAD_BYTES = int(os.environ.get('MAX_UPLOAD_MB', '5')) * 1024 * 1024
IMGPROXY_MAX_BYTES = int(os.environ.get('IMGPROXY_MAX_MB', '8')) * 1024 * 1024
IMGPROXY_TIMEOUT = float(os.environ.get('IMGPROXY_TIMEOUT', '10'))
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'info').lower()

OFFICE_MAP = {
    'BJI': '北京', 'CDU': '成都', 'CQI': '重庆', 'CSH': '长沙',
    'DLI': '大连', 'GZH': '广州', 'NJI': '南京', 'QDA': '青岛',
    'SHA': '上海', 'SUZ': '苏州', 'SZH': '深圳', 'TWN': '台湾',
    'WHA': '武汉', 'XAN': '西安', 'XME': '厦门', 'ZZH': '郑州',
}

# Region grouping
REGION_MAP = {
    'BJI': '华北', 'DLI': '华北', 'QDA': '华北', 'XAN': '华北',
    'SHA': '华东', 'SUZ': '华东', 'NJI': '华东', 'ZZH': '华东',
    'GZH': '华南', 'SZH': '华南', 'WHA': '华南', 'CSH': '华南', 'XME': '华南',
    'CDU': '华西', 'CQI': '华西',
    'TWN': '台湾',
}
# Hong Kong office code if added later
REGION_MAP.setdefault('HKG', '香港')


def get_region(office_code):
    return REGION_MAP.get(office_code, '其他')

# ---------------------------------------------------------------------------
# Brand/logo keyword database (subset used for auto-match in admin)
# ---------------------------------------------------------------------------
BRAND_KEYWORDS = {
    '小红书': 'https://cdn-icons-png.flaticon.com/512/3536/3536745.png',
    '华为': 'https://pic.pngsucai.com/00/80/95/9d5ae013f7d16592.webp',
    '百度': 'https://bkimg.cdn.bcebos.com/smart/b8014a90f603738da97755563251a751f81986184626-bkimg-process,v_1,rw_1,rh_1,pad_1,color_ffffff?x-bce-process=image/format,f_auto',
    '阿里巴巴': 'https://pic.pngsucai.com/00/78/52/e88d67fa29444baf.webp',
    '腾讯': 'https://cdn-icons-png.flaticon.com/512/1944/1944478.png',
    '字节跳动': 'http://logo800.cn/uploads/logoxinshang/56/logo800_16491624083325586.png',
    '美团': 'https://logo800.cn/uploads/logoxinshang/58/logo800_16491625929115709.png',
    '小米': 'http://www.kuaipng.com/Uploads/pic/w/2021/03-31/98651/water_98651_698_698_.png',
    '京东': 'http://www.kuaipng.com/Uploads/pic/w/2018/09-12/47466/water_47466_698_698_.png',
    '招商银行': 'https://logo800.cn/uploads/logoxinshang/56/logo800_16491623685385554.png',
    '渣打银行': 'https://logo800.cn/uploads/logoxinshang/56/logo800_16491623510295541.png',
    '中国平安': 'https://logo800.cn/uploads/logoxinshang/54/logo800_16491621460625367.png',
    '中国人寿': 'https://pic.616pic.com/ys_img/00/04/50/KQA6o4catq.jpg',
    'IBM': 'https://pngimg.com/uploads/ibm/ibm_PNG19658.png',
    '微软': 'https://cdn-icons-png.flaticon.com/512/732/732221.png',
    '苹果': 'https://cdn-icons-png.flaticon.com/512/0/747.png',
    'Google': 'https://cdn-icons-png.flaticon.com/512/2702/2702602.png',
    '西门子': 'https://cdn-icons-png.flaticon.com/512/1602/1602062.png',
    '三星': 'https://cdn-icons-png.flaticon.com/512/732/732106.png',
    '丰田': 'https://cdn-icons-png.flaticon.com/512/196/196600.png',
    '波音': 'https://www.pngmart.com/files/23/Boeing-Logo-PNG-Picture.png',
    '特斯拉': 'https://cdn-icons-png.flaticon.com/512/732/732282.png',
    'Netflix': 'https://cdn-icons-png.flaticon.com/512/732/732228.png',
    'Meta': 'https://cdn-icons-png.flaticon.com/512/5968/5968764.png',
    '亚马逊': 'https://cdn-icons-png.flaticon.com/512/2702/2702652.png',
    '甲骨文': 'https://cdn-icons-png.flaticon.com/512/5968/5968480.png',
    'SAP': 'https://cdn-icons-png.flaticon.com/512/5968/5968474.png',
    'Salesforce': 'https://cdn-icons-png.flaticon.com/512/5968/5968484.png',
    '英特尔': 'https://cdn-icons-png.flaticon.com/512/1602/1602031.png',
    '思科': 'https://cdn-icons-png.flaticon.com/512/732/732138.png',
    '高通': 'https://cdn-icons-png.flaticon.com/512/5969/5969138.png',
    '英伟达': 'https://cdn-icons-png.flaticon.com/512/5969/5969006.png',
    'AMD': 'https://cdn-icons-png.flaticon.com/512/1602/1602010.png',
    'Adobe': 'https://cdn-icons-png.flaticon.com/512/732/732236.png',
    'Autodesk': 'https://www.liblogo.com/img-logo/au96d848-autodesk-logo-download-hd-autodesk-logo-graphic-design-transparent-png-image.png',
    '耐克': 'https://cdn-icons-png.flaticon.com/512/732/732229.png',
    '阿迪达斯': 'https://cdn-icons-png.flaticon.com/512/732/732247.png',
    '星巴克': 'https://cdn-icons-png.flaticon.com/512/5977/5977591.png',
    '麦当劳': 'https://cdn-icons-png.flaticon.com/512/104/104388.png',
    '可口可乐': 'https://cdn-icons-png.flaticon.com/512/732/732222.png',
    '雀巢': 'https://cdn-icons-png.flaticon.com/512/5968/5968464.png',
    '联合利华': 'https://cdn-icons-png.flaticon.com/512/5968/5968852.png',
    '宝洁': 'https://cdn-icons-png.flaticon.com/512/5969/5969030.png',
    '强生': 'https://cdn-icons-png.flaticon.com/512/5968/5968534.png',
    '辉瑞': 'https://cdn-icons-png.flaticon.com/512/5968/5968486.png',
    '罗氏': 'https://cdn-icons-png.flaticon.com/512/5968/5968472.png',
    '诺华': 'https://cdn-icons-png.flaticon.com/512/5968/5968466.png',
    '汇丰银行': 'https://cdn-icons-png.flaticon.com/512/5968/5968456.png',
    '花旗': 'https://cdn-icons-png.flaticon.com/512/5968/5968436.png',
    '摩根大通': 'https://cdn-icons-png.flaticon.com/512/5968/5968446.png',
    '高盛': 'https://cdn-icons-png.flaticon.com/512/5968/5968450.png',
    '普华永道': 'https://cdn-icons-png.flaticon.com/512/5968/5968504.png',
    '德勤': 'https://cdn-icons-png.flaticon.com/512/5968/5968500.png',
    '安永': 'https://cdn-icons-png.flaticon.com/512/5968/5968508.png',
    '毕马威': 'https://cdn-icons-png.flaticon.com/512/5968/5968512.png',
}

# ---------------------------------------------------------------------------
# Data layer
# ---------------------------------------------------------------------------
def load_data() -> dict:
    if not DATA_JSON.exists():
        return {'title': '客户品牌墙', 'subtitle': 'CLIENT LOGO WALL',
                'tagline': 'OFFICE × BUSINESS LINE  ·  连接客户价值，共创长期合作',
                'total_count': 0, 'offices': [], 'departments': [], 'regions': [],
                'records': []}
    with open(DATA_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Ensure every record has a region field (auto-derived from office code)
    for r in data.get('records', []):
        if not r.get('region'):
            r['region'] = get_region(r.get('office_code', ''))
    return data


def save_data(data: dict):
    # Ensure every record has a region before saving
    for r in data.get('records', []):
        if not r.get('region'):
            r['region'] = get_region(r.get('office_code', ''))
    data['total_count'] = len(data.get('records', []))
    offices = sorted({r['office_city'] for r in data['records'] if r.get('office_city')})
    depts = sorted({d for r in data['records'] for d in (r.get('departments') or [])})
    regions = sorted({r.get('region', '其他') for r in data['records'] if r.get('region')})
    data['offices'] = offices
    data['departments'] = depts
    data['regions'] = regions
    tmp = DATA_JSON.with_suffix('.json.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(DATA_JSON)


def next_id(records: list) -> int:
    return max((r.get('id', 0) for r in records), default=0) + 1


def clean_owner(owner_str: str) -> List[str]:
    if not owner_str:
        return []
    return [p.strip() for p in re.split(r'[;；]', owner_str) if p.strip()]


def clean_dept(dept_str: str) -> List[str]:
    if not dept_str:
        return []
    return [p.strip() for p in re.split(r'[;；]', dept_str) if p.strip()]


def color_from_name(name: str) -> str:
    colors = ['#4F46E5', '#7C3AED', '#DB2777', '#DC2626', '#EA580C',
              '#CA8A04', '#16A34A', '#0891B2', '#2563EB', '#9333EA',
              '#0D9488', '#65A30D', '#C026D3', '#0284C7', '#475569']
    h = 0
    for ch in name or '':
        h = ord(ch) + ((h << 5) - h)
    return colors[abs(h) % len(colors)]


# ---------------------------------------------------------------------------
# User management & auth helpers
# ---------------------------------------------------------------------------
def load_users() -> dict:
    if not USERS_JSON.exists():
        return {'users': []}
    with open(USERS_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_users(data: dict):
    tmp = USERS_JSON.with_suffix('.json.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(USERS_JSON)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


def create_token(username: str, role: str) -> str:
    payload = {
        'sub': username,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS),
        'iat': datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """Extract and validate user from Authorization header. Returns None if invalid."""
    if not authorization:
        return None
    token = authorization.replace('Bearer ', '').strip()
    if not token:
        return None
    return decode_token(token)


def get_token_from_request(request) -> Optional[str]:
    """Extract token from Authorization header or query parameter."""
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        return auth[7:].strip()
    return request.query_params.get('token')


def ensure_default_admin():
    """Create a default admin user if no users exist."""
    users_data = load_users()
    if users_data.get('users'):
        return
    admin_user = {
        'username': 'admin',
        'password_hash': hash_password('admin123'),
        'role': 'admin',
        'display_name': '管理员',
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    users_data['users'] = [admin_user]
    save_users(users_data)
    print('  [Auth] Created default admin user (admin / admin123)')


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title='Logo Wall API', docs_url='/api/docs')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)


# ---- Auth middleware: protect sensitive routes when AUTH_ENABLED -----------
@app.middleware('http')
async def auth_middleware(request, call_next):
    if not AUTH_ENABLED:
        return await call_next(request)

    path = request.url.path

    # Public routes that never need auth
    public_exact = {'/login', '/api/auth/login', '/api/auth/check', '/api/health'}
    public_prefixes = ('/static/',)
    # Public pages (HTML) — JS handles redirect to /login
    public_pages = {'/', '/admin'}

    if path in public_exact or path in public_pages or any(path.startswith(p) for p in public_prefixes):
        return await call_next(request)

    # Also allow static assets that are part of the HTML pages
    if path.endswith('.html') or path.endswith('.css') or path.endswith('.js'):
        return await call_next(request)

    # Protected routes: /data.json, /logos/*, /api/*
    needs_auth = (
        path == '/data.json'
        or path.startswith('/logos/')
        or path.startswith('/api/')
    )

    if not needs_auth:
        return await call_next(request)

    # Read-only API routes that are needed by the login page
    # (currently none — login page is self-contained)

    # Check for valid token
    token = None
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:].strip()
    if not token:
        token = request.query_params.get('token')

    # Data assets fetched via fetch()/XHR/img must get a plain 401 (never an
    # HTML redirect), otherwise browsers silently follow the redirect and the
    # frontend cannot detect the unauthenticated state.
    is_data_asset = path == '/data.json' or path.startswith('/logos/')

    if not token:
        if path.startswith('/api/') or is_data_asset:
            return JSONResponse({'detail': 'Not authenticated'}, status_code=401)
        return RedirectResponse('/login')

    user = decode_token(token)
    # Backward compatibility: accept the legacy ADMIN_TOKEN as a full admin.
    # Must stay consistent with check_auth()/auth_check()/auth_me().
    if not user and token == ADMIN_TOKEN:
        user = {'sub': 'admin', 'role': 'admin'}
    if not user:
        if path.startswith('/api/') or is_data_asset:
            return JSONResponse({'detail': 'Invalid or expired token'}, status_code=401)
        return RedirectResponse('/login')

    # Admin-only routes
    admin_only_prefixes = ('/api/clients', '/api/logo', '/api/logos', '/api/settings', '/api/import', '/api/export', '/api/backup')
    if path.startswith('/api/'):
        is_write = any(path.startswith(p) for p in admin_only_prefixes)
        if is_write and request.method in ('POST', 'PUT', 'DELETE'):
            if user.get('role') != 'admin':
                return JSONResponse({'detail': 'Admin access required'}, status_code=403)

    return await call_next(request)


def check_auth(authorization: Optional[str] = Header(None)):
    """Legacy admin auth check — supports both old ADMIN_TOKEN and new JWT."""
    if not authorization:
        raise HTTPException(status_code=401, detail='Missing Authorization header')
    token = authorization.replace('Bearer ', '').strip()
    # Check JWT first
    user = decode_token(token)
    if user:
        if user.get('role') != 'admin':
            raise HTTPException(status_code=403, detail='Admin access required')
        return  # Valid admin JWT
    # Fall back to legacy ADMIN_TOKEN
    if token == ADMIN_TOKEN:
        return
    raise HTTPException(status_code=403, detail='Invalid admin token')


# ---- Models ---------------------------------------------------------------
class ClientIn(BaseModel):
    company: str
    office_code: str = ''
    departments: str = ''       # semicolon-separated in API for simplicity
    owners: str = ''            # semicolon-separated
    logo_url: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None


class ClientUpdate(BaseModel):
    company: Optional[str] = None
    office_code: Optional[str] = None
    departments: Optional[str] = None
    owners: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None


# Site appearance presets (validated server-side)
THEME_PRESETS = ['classic', 'gold', 'violet', 'orange', 'green']
BG_PATTERNS = ['none', 'dots', 'grid', 'glow']


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


# ---- Pages ----------------------------------------------------------------
@app.get('/')
def root():
    return FileResponse(BASE_DIR / 'index.html', headers={
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
    })


@app.get('/admin', response_class=HTMLResponse)
def admin_page():
    return FileResponse(Path(__file__).parent / 'templates' / 'admin.html', headers={
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
    })


@app.get('/admin/')
def admin_slash():
    return RedirectResponse(url='/admin')


# ---- Login page -----------------------------------------------------------
@app.get('/login')
def login_page():
    return FileResponse(Path(__file__).parent / 'templates' / 'login.html', headers={
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
    })


# ---- Auth API endpoints ---------------------------------------------------
@app.post('/api/auth/login')
async def auth_login(username: str = Form(...), password: str = Form(...)):
    """Authenticate user and return JWT token."""
    users_data = load_users()
    for u in users_data['users']:
        if u['username'] == username:
            if verify_password(password, u['password_hash']):
                token = create_token(u['username'], u['role'])
                return {
                    'ok': True,
                    'token': token,
                    'user': {
                        'username': u['username'],
                        'role': u['role'],
                        'display_name': u.get('display_name', u['username']),
                    }
                }
            raise HTTPException(401, '用户名或密码错误')
    raise HTTPException(401, '用户名或密码错误')


@app.get('/api/auth/check')
def auth_check(authorization: Optional[str] = Header(None)):
    """Check if current token is valid. Returns user info."""
    if not authorization:
        return {'ok': False}
    token = authorization.replace('Bearer ', '').strip()
    user = decode_token(token)
    if user:
        return {'ok': True, 'user': user}
    # Also accept legacy admin token
    if token == ADMIN_TOKEN:
        return {'ok': True, 'user': {'sub': 'admin', 'role': 'admin'}}
    return {'ok': False}


@app.get('/api/auth/me')
def auth_me(authorization: Optional[str] = Header(None)):
    """Get current user info."""
    if not authorization:
        raise HTTPException(401, 'Not authenticated')
    token = authorization.replace('Bearer ', '').strip()
    user = decode_token(token)
    if user:
        return {'ok': True, 'user': user}
    if token == ADMIN_TOKEN:
        return {'ok': True, 'user': {'sub': 'admin', 'role': 'admin'}}
    raise HTTPException(401, 'Invalid token')


# ---- User management (admin only) -----------------------------------------
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


@app.get('/api/users')
def list_users(authorization: Optional[str] = Header(None)):
    """List all users (admin only)."""
    check_auth(authorization)
    users_data = load_users()
    users = []
    for u in users_data['users']:
        users.append({
            'username': u['username'],
            'role': u['role'],
            'display_name': u.get('display_name', u['username']),
            'created_at': u.get('created_at', ''),
        })
    return {'users': users}


@app.post('/api/users')
def create_user(body: UserCreate, authorization: Optional[str] = Header(None)):
    """Create a new user (admin only)."""
    check_auth(authorization)
    if body.role not in ('admin', 'viewer'):
        raise HTTPException(400, 'Invalid role')
    if len(body.password) < 4:
        raise HTTPException(400, '密码至少4个字符')
    users_data = load_users()
    for u in users_data['users']:
        if u['username'] == body.username:
            raise HTTPException(400, '用户名已存在')
    new_user = {
        'username': body.username,
        'password_hash': hash_password(body.password),
        'role': body.role,
        'display_name': body.display_name or body.username,
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    users_data['users'].append(new_user)
    save_users(users_data)
    return {'ok': True, 'username': body.username}


@app.put('/api/users/{username}')
def update_user(username: str, body: UserUpdate, authorization: Optional[str] = Header(None)):
    """Update a user (admin only)."""
    check_auth(authorization)
    users_data = load_users()
    for u in users_data['users']:
        if u['username'] == username:
            if body.password is not None:
                if len(body.password) < 4:
                    raise HTTPException(400, '密码至少4个字符')
                u['password_hash'] = hash_password(body.password)
            if body.role is not None:
                if body.role not in ('admin', 'viewer'):
                    raise HTTPException(400, 'Invalid role')
                u['role'] = body.role
            if body.display_name is not None:
                u['display_name'] = body.display_name
            if body.username is not None and body.username != username:
                for other in users_data['users']:
                    if other['username'] == body.username:
                        raise HTTPException(400, '用户名已存在')
                u['username'] = body.username
            save_users(users_data)
            return {'ok': True}
    raise HTTPException(404, 'User not found')


@app.delete('/api/users/{username}')
def delete_user(username: str, authorization: Optional[str] = Header(None)):
    """Delete a user (admin only)."""
    check_auth(authorization)
    users_data = load_users()
    original_len = len(users_data['users'])
    users_data['users'] = [u for u in users_data['users'] if u['username'] != username]
    if len(users_data['users']) == original_len:
        raise HTTPException(404, 'User not found')
    if not users_data['users']:
        raise HTTPException(400, 'Cannot delete the last user')
    save_users(users_data)
    return {'ok': True}


# ---- Static files (logos/, data.json, and other root assets) --------------
@app.get('/data.json')
def get_data():
    data = load_data()
    return JSONResponse(data)


app.mount('/logos', StaticFiles(directory=str(LOGOS_DIR)), name='logos')


# ---- Client CRUD API ------------------------------------------------------
@app.get('/api/clients')
def list_clients(
    office: Optional[str] = None,
    dept: Optional[str] = None,
    owner: Optional[str] = None,
    region: Optional[str] = None,
    q: Optional[str] = None,
):
    data = load_data()
    records = data.get('records', [])
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
def get_client(client_id: int):
    data = load_data()
    for r in data['records']:
        if r.get('id') == client_id:
            return r
    raise HTTPException(404, 'Client not found')


@app.post('/api/clients')
def create_client(client: ClientIn, authorization: Optional[str] = Header(None)):
    check_auth(authorization)
    data = load_data()
    office_code = (client.office_code or '').strip().upper()
    record = {
        'id': next_id(data['records']),
        'company': client.company.strip(),
        'brand': client.company.strip(),
        'office_code': office_code,
        'office_city': OFFICE_MAP.get(office_code, office_code),
        'region': get_region(office_code),
        'departments': clean_dept(client.departments),
        'owners': clean_owner(client.owners),
        'logo_url': client.logo_url,
        'website': client.website or '',
        'description': client.description or '',
        'color': color_from_name(client.company),
    }
    data['records'].append(record)
    save_data(data)
    return record


@app.put('/api/clients/{client_id}')
def update_client(client_id: int, update: ClientUpdate, authorization: Optional[str] = Header(None)):
    check_auth(authorization)
    data = load_data()
    for r in data['records']:
        if r.get('id') == client_id:
            if update.company is not None:
                r['company'] = update.company.strip()
                r['brand'] = update.company.strip()
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
            if update.logo_url is not None:
                r['logo_url'] = update.logo_url
            if update.website is not None:
                r['website'] = update.website
            if update.description is not None:
                r['description'] = update.description
            save_data(data)
            return r
    raise HTTPException(404, 'Client not found')


@app.delete('/api/clients/{client_id}')
def delete_client(client_id: int, authorization: Optional[str] = Header(None)):
    check_auth(authorization)
    data = load_data()
    before = len(data['records'])
    data['records'] = [r for r in data['records'] if r.get('id') != client_id]
    if len(data['records']) == before:
        raise HTTPException(404, 'Client not found')
    save_data(data)
    return {'ok': True}


# ---- Health check (public, used by Docker healthcheck) ---------------------
@app.get('/api/health')
def health_check():
    return {'status': 'ok'}


# ---- Filters metadata -----------------------------------------------------
@app.get('/api/filters')
def get_filters():
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


# ---- Logo discovery -------------------------------------------------------
def _domain_from_url(url: str) -> str:
    url = (url or '').strip()
    if not url:
        return ''
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    parsed = urllib.parse.urlparse(url)
    return parsed.netloc.lower().lstrip('www.')


@app.get('/api/logo/discover')
async def discover_logo(
    company: str = Query(...),
    website: Optional[str] = Query(None),
):
    """Try multiple strategies to find a logo URL for a company.
    Priority when website is provided: domain-based services first, then keyword DB.
    """
    results = []
    company_lower = company.lower()
    domain = _domain_from_url(website or '')

    # 1. If website given, try domain-based services FIRST (most accurate)
    if domain:
        results.append({
            'source': 'clearbit',
            'url': f'https://logo.clearbit.com/{domain}',
            'note': f'Clearbit Logo ({domain})',
        })
        results.append({
            'source': 'google_favicon',
            'url': f'https://www.google.com/s2/favicons?domain={domain}&sz=128',
            'note': f'Google Favicon ({domain})',
        })
        results.append({
            'source': 'duckduckgo',
            'url': f'https://icons.duckduckgo.com/ip3/{domain}.ico',
            'note': f'DuckDuckGo Favicon ({domain})',
        })

    # 2. Check built-in brand keyword DB
    for kw, url in BRAND_KEYWORDS.items():
        if kw.lower() in company_lower or company_lower in kw.lower():
            results.append({'source': 'builtin', 'keyword': kw, 'url': url,
                            'note': f'内置品牌库 ({kw})'})

    # 3. If no website and ASCII name, try guessing domain
    if not domain and company.isascii():
        guessed = re.sub(r'[^a-zA-Z0-9]', '', company).lower()
        if guessed and len(guessed) > 2:
            results.append({
                'source': 'guess',
                'url': f'https://logo.clearbit.com/{guessed}.com',
                'note': f'猜测域名 ({guessed}.com)',
            })

    # 4. Verify URLs are reachable (HEAD request)
    verified = []
    async with httpx.AsyncClient(timeout=5, follow_redirects=True) as client:
        for item in results:
            try:
                resp = await client.head(item['url'])
                item['status'] = resp.status_code
                item['ok'] = resp.status_code == 200
                item['content_type'] = resp.headers.get('content-type', '')
            except Exception as e:
                item['status'] = 0
                item['ok'] = False
                item['error'] = str(e)[:80]
            verified.append(item)

    return {'company': company, 'domain': domain, 'results': verified}


# ---- Logo library ---------------------------------------------------------
@app.get('/api/logos')
def list_logos():
    """List all logo files in the logos/ directory with usage info."""
    data = load_data()
    # Build reverse map: logo_url -> list of client brands using it
    usage = {}
    for r in data['records']:
        url = r.get('logo_url') or ''
        if url:
            usage.setdefault(url, []).append(r.get('brand', r.get('company', '')))

    logos = []
    if LOGOS_DIR.exists():
        for f in sorted(LOGOS_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if not f.is_file():
                continue
            rel = f'logos/{f.name}'
            stat = f.stat()
            logos.append({
                'url': rel,
                'filename': f.name,
                'size': stat.st_size,
                'modified': int(stat.st_mtime),
                'used_by': usage.get(rel, []),
            })
    return {'total': len(logos), 'logos': logos}


@app.post('/api/logo/batch-upload')
async def batch_upload_logos(
    files: List[UploadFile] = File(...),
    authorization: Optional[str] = Header(None),
):
    """Upload multiple logo files at once."""
    check_auth(authorization)
    results = []
    for file in files:
        content = await file.read()
        if len(content) > MAX_UPLOAD_BYTES:
            results.append({'ok': False, 'filename': file.filename, 'error': 'too large'})
            continue
        ext = Path(file.filename or 'logo.png').suffix.lower()
        if ext not in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'):
            ct = file.content_type or ''
            ext = mimetypes.guess_extension(ct.split(';')[0].strip()) or '.png'
            if ext == '.jpe':
                ext = '.jpg'
        key = hashlib.md5(content).hexdigest()[:12] + ext
        filepath = LOGOS_DIR / key
        if not filepath.exists():
            with open(filepath, 'wb') as f:
                f.write(content)
        results.append({
            'ok': True, 'url': f'logos/{key}',
            'filename': key, 'original': file.filename, 'size': len(content),
        })
    return {'uploaded': sum(1 for r in results if r['ok']), 'results': results}


@app.delete('/api/logos/{filename}')
def delete_logo(filename: str, authorization: Optional[str] = Header(None)):
    """Delete a logo file (only if not used by any client)."""
    check_auth(authorization)
    # Prevent path traversal
    safe_name = Path(filename).name
    filepath = LOGOS_DIR / safe_name
    if not filepath.exists():
        raise HTTPException(404, 'Logo not found')
    data = load_data()
    used_by = [r for r in data['records'] if r.get('logo_url') == f'logos/{safe_name}']
    if used_by:
        raise HTTPException(400, f'Logo is used by {len(used_by)} client(s), cannot delete')
    filepath.unlink()
    return {'ok': True}


@app.post('/api/logo/assign')
def assign_logo(
    client_id: int = Form(...),
    logo_url: str = Form(...),
    authorization: Optional[str] = Header(None),
):
    """Assign a logo from the library to a client."""
    check_auth(authorization)
    data = load_data()
    for r in data['records']:
        if r.get('id') == client_id:
            r['logo_url'] = logo_url
            save_data(data)
            return {'ok': True, 'client_id': client_id, 'logo_url': logo_url}
    raise HTTPException(404, 'Client not found')


@app.post('/api/logo/replace')
async def replace_logo(
    filename: str = Form(...),
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
):
    """Replace an existing logo file with a new image, keeping the same filename."""
    check_auth(authorization)
    safe_name = Path(filename).name
    filepath = LOGOS_DIR / safe_name
    if not filepath.exists():
        raise HTTPException(404, 'Logo file not found')

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, f'File too large (max {MAX_UPLOAD_BYTES // (1024 * 1024)}MB)')

    # Overwrite the file in place (same path, all clients using it get updated)
    with open(filepath, 'wb') as f:
        f.write(content)
    return {'ok': True, 'url': f'logos/{safe_name}', 'size': len(content)}


@app.get('/api/logo/info/{filename}')
def logo_info(filename: str):
    """Get detailed info about a specific logo."""
    safe_name = Path(filename).name
    filepath = LOGOS_DIR / safe_name
    if not filepath.exists():
        raise HTTPException(404, 'Logo not found')

    data = load_data()
    used_by = [{'id': r['id'], 'brand': r.get('brand', r.get('company', ''))}
               for r in data['records'] if r.get('logo_url') == f'logos/{safe_name}']

    stat = filepath.stat()
    return {
        'filename': safe_name,
        'url': f'logos/{safe_name}',
        'size': stat.st_size,
        'modified': int(stat.st_mtime),
        'used_by': used_by,
        'used_count': len(used_by),
    }


# ---- Logo upload ----------------------------------------------------------
@app.post('/api/logo/upload')
async def upload_logo(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
):
    check_auth(authorization)
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, f'File too large (max {MAX_UPLOAD_BYTES // (1024 * 1024)}MB)')

    ext = Path(file.filename or 'logo.png').suffix.lower()
    if ext not in ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'):
        # Guess from content-type
        ct = file.content_type or ''
        ext = mimetypes.guess_extension(ct.split(';')[0].strip()) or '.png'
        if ext == '.jpe':
            ext = '.jpg'

    key = hashlib.md5(content).hexdigest()[:12] + ext
    filepath = LOGOS_DIR / key
    with open(filepath, 'wb') as f:
        f.write(content)
    return {'ok': True, 'url': f'logos/{key}', 'filename': key, 'size': len(content)}


@app.post('/api/logo/fetch')
async def fetch_logo(
    url: str = Form(...),
    authorization: Optional[str] = Header(None),
):
    """Download a remote logo URL and save it locally."""
    check_auth(authorization)
    if not url.startswith(('http://', 'https://')):
        raise HTTPException(400, 'Invalid URL')
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                              'AppleWebKit/537.36 Chrome/120.0 Safari/537.36',
                'Referer': 'https://www.google.com/',
            })
            resp.raise_for_status()
            content = resp.read()
    except Exception as e:
        raise HTTPException(400, f'Failed to download: {e}')

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, f'File too large (max {MAX_UPLOAD_BYTES // (1024 * 1024)}MB)')

    ctype = resp.headers.get('content-type', '')
    if 'svg' in ctype:
        ext = '.svg'
    elif 'png' in ctype:
        ext = '.png'
    elif 'jpeg' in ctype or 'jpg' in ctype:
        ext = '.jpg'
    elif 'gif' in ctype:
        ext = '.gif'
    elif 'webp' in ctype:
        ext = '.webp'
    else:
        ext = Path(urllib.parse.urlparse(url).path).suffix or '.png'

    key = hashlib.md5(content).hexdigest()[:12] + ext
    filepath = LOGOS_DIR / key
    with open(filepath, 'wb') as f:
        f.write(content)
    return {'ok': True, 'url': f'logos/{key}', 'size': len(content)}


# ---- Excel import/export --------------------------------------------------
@app.post('/api/import-excel')
async def import_excel(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
):
    check_auth(authorization)
    import pandas as pd
    content = await file.read()
    df = pd.read_excel(io.BytesIO(content))
    if len(df.columns) < 2:
        raise HTTPException(400, 'Excel must have at least 2 columns')

    data = load_data()
    added = 0
    logo_matched = 0
    for _, row in df.iterrows():
        vals = list(row)
        if not vals or pd.isna(vals[0]):
            continue
        company = str(vals[0]).strip()
        if not company:
            continue
        office_code = str(vals[1]).strip().upper() if len(vals) > 1 and pd.notna(vals[1]) else ''
        depts = clean_dept(str(vals[2])) if len(vals) > 2 and pd.notna(vals[2]) else []
        owners = clean_owner(str(vals[3])) if len(vals) > 3 and pd.notna(vals[3]) else []

        # Auto-match logo from keyword DB
        logo_url = None
        company_lower = company.lower()
        for kw, url in BRAND_KEYWORDS.items():
            if kw.lower() in company_lower or company_lower in kw.lower():
                logo_url = url
                logo_matched += 1
                break

        record = {
            'id': next_id(data['records']),
            'company': company,
            'brand': company,
            'office_code': office_code,
            'office_city': OFFICE_MAP.get(office_code, office_code),
            'region': get_region(office_code),
            'departments': depts,
            'owners': owners,
            'logo_url': logo_url,
            'website': '',
            'color': color_from_name(company),
        }
        data['records'].append(record)
        added += 1
    save_data(data)
    return {'ok': True, 'added': added, 'total': len(data['records']), 'logo_matched': logo_matched}


@app.get('/api/export-excel')
def export_excel(authorization: Optional[str] = Header(None)):
    check_auth(authorization)
    import pandas as pd
    data = load_data()
    rows = []
    for r in data['records']:
        owners = r.get('owners') or []
        depts = r.get('departments') or []
        rows.append({
            '租客/买方': r.get('company', '') or '',
            '办公室（城市）': r.get('office_code', '') or '',
            '区域': r.get('region') or get_region(r.get('office_code', '')),
            '申报部门（合并）': '；'.join(depts),
            '业务负责人（合并）': '；'.join(owners),
        })
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            'Content-Disposition': 'attachment; filename="logo_wall_export.xlsx"'
        },
    )


# ---- Auth check -----------------------------------------------------------
@app.get('/api/auth/check')
def auth_check(authorization: Optional[str] = Header(None)):
    try:
        check_auth(authorization)
        return {'ok': True}
    except HTTPException:
        return {'ok': False}


# ---- Site settings (title / tagline / theme) -------------------------------
@app.put('/api/settings')
def update_settings(s: SettingsIn, authorization: Optional[str] = Header(None)):
    check_auth(authorization)
    data = load_data()
    for field in ('title', 'title_en', 'tagline', 'tagline_en', 'footer_text', 'footer_en'):
        value = getattr(s, field)
        if value is not None:
            data[field] = value.strip()
    if s.theme is not None:
        data['theme'] = s.theme if s.theme in THEME_PRESETS else 'classic'
    if s.bg_pattern is not None:
        data['bg_pattern'] = s.bg_pattern if s.bg_pattern in BG_PATTERNS else 'none'
    for field in ('custom_primary', 'custom_accent'):
        value = getattr(s, field)
        if value is not None:
            v = value.strip()
            if v and not re.fullmatch(r'#[0-9a-fA-F]{6}', v):
                raise HTTPException(400, f'{field} must be a #RRGGBB hex color')
            data[field] = v
    save_data(data)
    return {'ok': True}


# ---- Full backup export / import (data.json + logos/ + users.json) ---------
BACKUP_MAX_BYTES = int(os.environ.get('BACKUP_MAX_MB', '200')) * 1024 * 1024


@app.get('/api/backup/export')
def backup_export(authorization: Optional[str] = Header(None)):
    """Export the full data directory as a single zip backup."""
    check_auth(authorization)
    data = load_data()
    manifest = {
        'app': 'logo-wall',
        'version': 1,
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'records': len(data.get('records', [])),
        'logos': len([f for f in LOGOS_DIR.iterdir() if f.is_file()]) if LOGOS_DIR.exists() else 0,
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        if DATA_JSON.exists():
            zf.write(DATA_JSON, 'data.json')
        if USERS_JSON.exists():
            zf.write(USERS_JSON, 'users.json')
        if LOGOS_DIR.exists():
            for f in sorted(LOGOS_DIR.iterdir()):
                if f.is_file():
                    zf.write(f, 'logos/' + f.name)
    fname = 'logo-wall-backup-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.zip'
    return Response(
        content=buf.getvalue(),
        media_type='application/zip',
        headers={'Content-Disposition': 'attachment; filename="' + fname + '"'},
    )


@app.post('/api/backup/import')
async def backup_import(file: UploadFile = File(...), authorization: Optional[str] = Header(None)):
    """Import a zip backup: replaces data.json/users.json, merges logos/ files."""
    check_auth(authorization)
    content = await file.read()
    if len(content) > BACKUP_MAX_BYTES:
        raise HTTPException(413, f'Backup zip exceeds limit ({BACKUP_MAX_BYTES // 1024 // 1024} MB)')
    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile:
        raise HTTPException(400, 'Not a valid zip file')

    names = zf.namelist()
    if 'data.json' not in names:
        raise HTTPException(400, 'Backup zip is missing data.json (not a Logo Wall backup?)')

    # Validate data.json before touching anything
    try:
        new_data = json.loads(zf.read('data.json').decode('utf-8'))
        if not isinstance(new_data.get('records'), list):
            raise ValueError('records must be a list')
    except Exception as e:
        raise HTTPException(400, f'Invalid data.json in backup: {e}')

    # Extract logo files (zip-slip protected)
    imported_logos = 0
    for info in zf.infolist():
        name = info.filename.replace('\\', '/')
        if name.startswith('/') or '..' in name.split('/'):
            raise HTTPException(400, f'Illegal path in backup: {name}')
        if name.startswith('logos/') and not name.endswith('/'):
            rel = name[len('logos/'):]
            if not rel or '/' in rel:
                continue
            target = LOGOS_DIR / rel
            with open(target, 'wb') as f:
                f.write(zf.read(info))
            imported_logos += 1

    # Replace data (save_data recomputes aggregates atomically)
    save_data(new_data)

    imported_users = False
    if 'users.json' in names:
        try:
            users = json.loads(zf.read('users.json').decode('utf-8'))
            if isinstance(users.get('users'), list):
                save_users(users)
                imported_users = True
        except Exception:
            pass

    return {'ok': True, 'records': len(new_data['records']),
            'logos': imported_logos, 'users': imported_users}


# ---- Image proxy (used by poster export to avoid canvas CORS tainting) ----
@app.get('/api/imgproxy')
def img_proxy(url: str):
    if not url.lower().startswith(('http://', 'https://')):
        raise HTTPException(400, 'Only http/https URLs are allowed')
    try:
        r = httpx.get(
            url, timeout=IMGPROXY_TIMEOUT, follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (LogoWall Poster Export)'},
        )
        if r.status_code != 200:
            raise HTTPException(502, f'Upstream returned {r.status_code}')
        content = r.content
        if len(content) > IMGPROXY_MAX_BYTES:
            raise HTTPException(502, 'Image too large')
        ctype = (r.headers.get('content-type') or 'image/png').split(';')[0].strip()
        if not ctype.startswith('image/'):
            ctype = 'image/png'
        return Response(content=content, media_type=ctype,
                        headers={'Cache-Control': 'public, max-age=86400'})
    except httpx.HTTPError as e:
        raise HTTPException(502, f'Fetch failed: {e}')


# ---- Startup event --------------------------------------------------------
@app.on_event('startup')
async def startup():
    if AUTH_ENABLED:
        ensure_default_admin()


# ---- Main -----------------------------------------------------------------
def get_local_ips():
    """Return the main local LAN IP address (the one used for default route)."""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
        except Exception:
            return None
        finally:
            s.close()
    except Exception:
        return None


if __name__ == '__main__':
    import uvicorn
    port = int(os.environ.get('PORT', 8080))
    lan_ip = get_local_ips()
    print(f'\n{"="*58}')
    print(f'  Logo Wall server is running')
    print(f'{"-"*58}')
    print(f'  On this computer:')
    print(f'    Brand wall :  http://localhost:{port}/')
    print(f'    Admin panel:  http://localhost:{port}/admin')
    print(f'    API docs   :  http://localhost:{port}/api/docs')
    print(f'    (also works with http://127.0.0.1:{port}/)')
    if lan_ip:
        print(f'{"-"*58}')
        print(f'  From other phones/computers on the same Wi-Fi/LAN:')
        print(f'    Brand wall :  http://{lan_ip}:{port}/')
        print(f'    Admin panel:  http://{lan_ip}:{port}/admin')
    print(f'{"-"*58}')
    print(f'  Admin token :  {ADMIN_TOKEN}')
    if AUTH_ENABLED:
        print(f'  Auth        :  ENABLED (JWT, {JWT_EXPIRE_DAYS}-day token)')
        print(f'  Login page  :  http://localhost:{port}/login')
    else:
        print(f'  Auth        :  DISABLED')
    print(f'{"="*58}\n')
    uvicorn.run(app, host=HOST, port=port, log_level=LOG_LEVEL)
