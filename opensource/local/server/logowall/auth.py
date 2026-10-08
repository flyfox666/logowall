"""Authentication: password hashing, JWT sessions, login throttling.

Tokens carry the user's `token_version`; bumping it (password / role /
username change) invalidates every previously issued token for that user, and
deleting a user invalidates theirs immediately because each request re-checks
the account in users.json.
"""
import hmac
import time
import secrets
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, Request

from . import config
from .storage import load_users, save_users, DATA_LOCK

# Used to spend the same bcrypt time on unknown usernames, so response timing
# does not reveal which accounts exist.
_DUMMY_HASH = bcrypt.hashpw(b'logo-wall-dummy-password', bcrypt.gensalt()).decode()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False


def validate_new_password(password: str):
    if len(password or '') < config.MIN_PASSWORD_LEN:
        raise HTTPException(400, f'密码至少{config.MIN_PASSWORD_LEN}个字符 / '
                                 f'Password must be at least {config.MIN_PASSWORD_LEN} characters')


def find_user(users_data: dict, username: str) -> Optional[dict]:
    for u in users_data.get('users', []):
        if u.get('username') == username:
            return u
    return None


def public_user(u: dict) -> dict:
    return {
        'sub': u['username'],
        'username': u['username'],
        'role': u.get('role', 'viewer'),
        'display_name': u.get('display_name', u['username']),
    }


def authenticate(username: str, password: str) -> Optional[dict]:
    """Return the stored user on valid credentials, else None (constant-ish time)."""
    user = find_user(load_users(), username)
    if user is None:
        verify_password(password, _DUMMY_HASH)
        return None
    if verify_password(password, user.get('password_hash', '')):
        return user
    return None


def create_token(user: dict) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        'sub': user['username'],
        'role': user.get('role', 'viewer'),
        'tv': int(user.get('token_version', 0)),
        'iat': now,
        'exp': now + timedelta(days=config.JWT_EXPIRE_DAYS),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def resolve_token(token: Optional[str]) -> Optional[dict]:
    """Map a bearer token (JWT or legacy ADMIN_TOKEN) to a user dict, or None.

    Role and display name come from users.json, not the token, so demoting
    or deleting an account takes effect immediately.
    """
    if not token:
        return None
    if config.ADMIN_TOKEN and hmac.compare_digest(token.encode(), config.ADMIN_TOKEN.encode()):
        return {'sub': 'admin', 'username': 'admin', 'role': 'admin',
                'display_name': 'API token', 'legacy_token': True}
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        return None
    user = find_user(load_users(), payload.get('sub'))
    if user is None:
        return None
    if int(user.get('token_version', 0)) != int(payload.get('tv', 0)):
        return None
    return public_user(user)


def bump_token_version(user: dict):
    user['token_version'] = int(user.get('token_version', 0)) + 1


# ---- Request helpers --------------------------------------------------------
def token_from_request(request: Request, allow_cookie: bool) -> Optional[str]:
    auth = request.headers.get('Authorization', '')
    if auth[:7].lower() == 'bearer ':
        tok = auth[7:].strip()
        if tok:
            return tok
    if allow_cookie:
        return request.cookies.get(config.SESSION_COOKIE) or None
    return None


def current_user(request: Request) -> Optional[dict]:
    """Resolve (and cache on the request) the authenticated user.

    The HttpOnly session cookie is only honoured for safe methods (GET/HEAD),
    so it can authenticate <img> loads of protected logos without enabling
    cross-site request forgery against write endpoints, which always require
    the Authorization header.
    """
    if hasattr(request.state, 'user'):
        return request.state.user
    safe = request.method in ('GET', 'HEAD')
    user = resolve_token(token_from_request(request, allow_cookie=safe))
    request.state.user = user
    return user


def require_user(request: Request) -> dict:
    user = current_user(request)
    if not user:
        raise HTTPException(401, 'Not authenticated')
    return user


def require_admin(request: Request) -> dict:
    user = current_user(request)
    if not user:
        raise HTTPException(401, 'Not authenticated')
    if user.get('role') != 'admin':
        raise HTTPException(403, 'Admin access required')
    return user


def require_reader(request: Request) -> Optional[dict]:
    """Read access: any logged-in user, or anyone when AUTH_ENABLED=false."""
    if not config.AUTH_ENABLED:
        return current_user(request)
    return require_user(request)


def client_ip(request: Request) -> str:
    return request.client.host if request.client else 'unknown'


def set_session_cookie(response, request: Request, token: str):
    secure = request.url.scheme == 'https'
    response.set_cookie(
        config.SESSION_COOKIE, token,
        max_age=config.JWT_EXPIRE_DAYS * 86400,
        httponly=True, samesite='lax', secure=secure, path='/',
    )


def clear_session_cookie(response):
    response.delete_cookie(config.SESSION_COOKIE, path='/')


# ---- Login throttling -------------------------------------------------------
class LoginThrottle:
    """In-memory sliding-window limiter keyed by (ip, username) and by ip."""

    PER_IP_FACTOR = 4  # an IP may fail this many times more across usernames

    def __init__(self):
        self._lock = threading.Lock()
        self._fails = {}

    def _window(self) -> float:
        return config.LOGIN_LOCK_MINUTES * 60

    def _prune(self, key, now):
        lst = [t for t in self._fails.get(key, []) if now - t < self._window()]
        if lst:
            self._fails[key] = lst
        else:
            self._fails.pop(key, None)
        return lst

    def retry_after(self, ip: str, username: str) -> int:
        """Seconds until another attempt is allowed (0 = allowed now)."""
        now = time.monotonic()
        with self._lock:
            limits = (
                (('u', ip, username.lower()), config.LOGIN_MAX_FAILURES),
                (('ip', ip), config.LOGIN_MAX_FAILURES * self.PER_IP_FACTOR),
            )
            wait = 0
            for key, limit in limits:
                lst = self._prune(key, now)
                if len(lst) >= limit:
                    wait = max(wait, int(self._window() - (now - lst[0])) + 1)
            return wait

    def record_failure(self, ip: str, username: str):
        now = time.monotonic()
        with self._lock:
            self._fails.setdefault(('u', ip, username.lower()), []).append(now)
            self._fails.setdefault(('ip', ip), []).append(now)

    def record_success(self, ip: str, username: str):
        with self._lock:
            self._fails.pop(('u', ip, username.lower()), None)

    def reset(self):
        with self._lock:
            self._fails.clear()


login_throttle = LoginThrottle()


# ---- Bootstrap ----------------------------------------------------------------
WEAK_DEFAULT_PASSWORD = 'admin123'


def ensure_default_admin():
    """Create the first admin account if no users exist.

    Uses ADMIN_PASSWORD when set, otherwise a random password that is printed
    once to the console / container logs. Also warns loudly when an existing
    account still uses the old well-known default password.
    """
    with DATA_LOCK:
        users_data = load_users()
        if users_data.get('users'):
            for u in users_data['users']:
                if u.get('role') == 'admin' and verify_password(WEAK_DEFAULT_PASSWORD, u.get('password_hash', '')):
                    print(f"  [Auth] WARNING: user '{u['username']}' still uses the default password "
                          f"'{WEAK_DEFAULT_PASSWORD}'. Change it in 用户管理 / User management now!")
            return
        generated = not config.INITIAL_ADMIN_PASSWORD
        password = config.INITIAL_ADMIN_PASSWORD or secrets.token_urlsafe(12)
        users_data['users'] = [{
            'username': 'admin',
            'password_hash': hash_password(password),
            'role': 'admin',
            'display_name': '管理员',
            'token_version': 0,
            'created_at': datetime.now(timezone.utc).isoformat(),
        }]
        save_users(users_data)
    if generated:
        bar = '!' * 58
        print(f'\n{bar}\n  [Auth] Created the first admin account:\n'
              f'           username: admin\n           password: {password}\n'
              f'  Save this password now - it is shown only once.\n'
              f'  (Set ADMIN_PASSWORD to choose it yourself.)\n{bar}\n')
    else:
        print('  [Auth] Created admin user "admin" with the password from ADMIN_PASSWORD')
