"""Runtime configuration, read once from environment variables / config.env.

Security-relevant defaults:
  * JWT_SECRET  - when unset, a random secret is generated once and persisted
                  to DATA_DIR/.jwt_secret (never derived from a guessable value).
  * ADMIN_TOKEN - the legacy master API token is DISABLED unless explicitly set
                  to a non-trivial value (the old default `admin123` is refused).
"""
import os
import secrets
import logging
from pathlib import Path

log = logging.getLogger('logowall')


def _env_bool(name: str, default: str) -> bool:
    return os.environ.get(name, default).strip().lower() in ('true', '1', 'yes', 'on')


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


# ---- Paths -----------------------------------------------------------------
# App root: the folder holding index.html (local/ in the repo, /app in Docker)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / 'server' / 'templates'
DATA_DIR = Path(os.environ.get('DATA_DIR') or str(BASE_DIR))
DATA_JSON = DATA_DIR / 'data.json'
LOGOS_DIR = DATA_DIR / 'logos'
USERS_JSON = DATA_DIR / 'users.json'
SECRET_FILE = DATA_DIR / '.jwt_secret'
AUDIT_LOG = DATA_DIR / 'audit.log'
BACKUPS_DIR = DATA_DIR / 'backups'
BRAND_KEYWORDS_JSON = DATA_DIR / 'brand_keywords.json'

LOGOS_DIR.mkdir(parents=True, exist_ok=True)

# ---- Server ----------------------------------------------------------------
HOST = os.environ.get('HOST', '0.0.0.0')
PORT = _env_int('PORT', 8080)
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'info').lower()
# Comma-separated list of extra origins allowed to call the API cross-origin.
# Empty (default) = same-origin only, which is all the bundled pages need.
CORS_ORIGINS = [o.strip() for o in os.environ.get('CORS_ORIGINS', '').split(',') if o.strip()]

# ---- Auth ------------------------------------------------------------------
AUTH_ENABLED = _env_bool('AUTH_ENABLED', 'true')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRE_DAYS = _env_int('JWT_EXPIRE_DAYS', 7)
MIN_PASSWORD_LEN = _env_int('MIN_PASSWORD_LEN', 8)
# Password for the admin account created on first start (random when unset)
INITIAL_ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
# Brute-force protection for /api/auth/login
LOGIN_MAX_FAILURES = _env_int('LOGIN_MAX_FAILURES', 5)
LOGIN_LOCK_MINUTES = _env_int('LOGIN_LOCK_MINUTES', 15)
SESSION_COOKIE = 'lw_session'

# Known-weak legacy master tokens that are refused even if configured
WEAK_TOKENS = {'admin123', 'admin', 'password', 'changeme', 'change-this-to-a-strong-password'}
MIN_ADMIN_TOKEN_LEN = 12


def _resolve_admin_token() -> str:
    token = os.environ.get('ADMIN_TOKEN', '').strip()
    if not token:
        return ''
    if token.lower() in WEAK_TOKENS or len(token) < MIN_ADMIN_TOKEN_LEN:
        log.warning('ADMIN_TOKEN is weak (a default value or shorter than %d chars); '
                    'the legacy master token is DISABLED. Use account login, or set a '
                    'strong random ADMIN_TOKEN.', MIN_ADMIN_TOKEN_LEN)
        print(f'  [Auth] WARNING: ADMIN_TOKEN is weak (default value or < {MIN_ADMIN_TOKEN_LEN} '
              'chars) and has been disabled.')
        return ''
    return token


def _resolve_jwt_secret() -> str:
    env_secret = os.environ.get('JWT_SECRET', '').strip()
    if env_secret:
        return env_secret
    try:
        existing = SECRET_FILE.read_text(encoding='utf-8').strip()
        if existing:
            return existing
    except FileNotFoundError:
        pass
    new_secret = secrets.token_urlsafe(48)
    SECRET_FILE.write_text(new_secret, encoding='utf-8')
    try:
        os.chmod(SECRET_FILE, 0o600)
    except OSError:
        pass
    return new_secret


ADMIN_TOKEN = _resolve_admin_token()
JWT_SECRET = _resolve_jwt_secret()

# ---- Limits ----------------------------------------------------------------
MAX_UPLOAD_BYTES = _env_int('MAX_UPLOAD_MB', 5) * 1024 * 1024
MAX_EXCEL_BYTES = _env_int('MAX_EXCEL_MB', 20) * 1024 * 1024
IMGPROXY_MAX_BYTES = _env_int('IMGPROXY_MAX_MB', 8) * 1024 * 1024
IMGPROXY_TIMEOUT = float(os.environ.get('IMGPROXY_TIMEOUT', '10'))
BACKUP_MAX_BYTES = _env_int('BACKUP_MAX_MB', 200) * 1024 * 1024
BACKUP_MAX_UNCOMPRESSED_BYTES = _env_int('BACKUP_MAX_UNCOMPRESSED_MB', 1024) * 1024 * 1024
BACKUP_MAX_ENTRIES = _env_int('BACKUP_MAX_ENTRIES', 20000)
# Automatic safety snapshots taken before a backup import overwrites data
AUTO_SNAPSHOTS_KEEP = _env_int('AUTO_SNAPSHOTS_KEEP', 5)
# Longest side (px) a raster logo is downscaled to on upload; 0 disables
LOGO_MAX_PX = _env_int('LOGO_MAX_PX', 800)
# Allow server-side fetches (imgproxy / logo fetch) to reach private, loopback
# or link-local addresses. Off by default to prevent SSRF; enable only when
# your logos are hosted on an intranet server.
FETCH_ALLOW_PRIVATE = _env_bool('FETCH_ALLOW_PRIVATE', 'false')
AUDIT_LOG_MAX_BYTES = _env_int('AUDIT_LOG_MAX_MB', 5) * 1024 * 1024
