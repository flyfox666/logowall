import hashlib

import jwt
import pytest

from conftest import ADMIN_PW, load_app


# ---- Default credentials / secrets -----------------------------------------
def test_jwt_secret_is_random_and_persisted(make_ctx):
    c = make_ctx(seed_records=[])
    secret_file = c.data_dir / '.jwt_secret'
    assert secret_file.exists()
    first = secret_file.read_text()
    assert len(first) >= 40
    assert c.mod.config.JWT_SECRET == first
    # A restart keeps the same secret, so sessions survive restarts
    c2 = make_ctx()
    assert c2.mod.config.JWT_SECRET == first


def test_token_forged_with_old_derived_secret_is_rejected(ctx):
    old_secret = 'logo-wall-secret-' + hashlib.md5(b'admin123').hexdigest()[:16]
    forged = jwt.encode({'sub': 'admin', 'role': 'admin', 'exp': 9999999999}, old_secret, algorithm='HS256')
    r = ctx.client.get('/api/users', headers=ctx.hdr(forged))
    assert r.status_code == 401


def test_jwt_secret_env_overrides(make_ctx):
    c = make_ctx(seed_records=[], JWT_SECRET='x' * 50)
    assert c.mod.config.JWT_SECRET == 'x' * 50


@pytest.mark.parametrize('token', ['admin123', 'short', 'change-this-to-a-strong-password'])
def test_weak_admin_token_is_disabled(make_ctx, token):
    c = make_ctx(seed_records=[], ADMIN_TOKEN=token)
    assert c.mod.config.ADMIN_TOKEN == ''
    c.client.cookies.clear()
    assert c.client.get('/api/users', headers=c.hdr(token)).status_code == 401


def test_admin_token_unset_by_default(ctx):
    assert ctx.mod.config.ADMIN_TOKEN == ''


def test_strong_admin_token_still_works(make_ctx):
    tok = 'a-very-strong-master-token-123'
    c = make_ctx(seed_records=[], ADMIN_TOKEN=tok)
    assert c.client.get('/api/users', headers=c.hdr(tok)).status_code == 200


def test_first_admin_uses_admin_password_env(ctx):
    ctx.login('admin', ADMIN_PW)
    r = ctx.client.post('/api/auth/login', data={'username': 'admin', 'password': 'admin123'})
    assert r.status_code == 401


def test_first_admin_random_password_when_unset(make_ctx, capsys):
    c = make_ctx(seed_records=[], ADMIN_PASSWORD=None)
    out = capsys.readouterr().out
    assert 'password:' in out
    pw = out.split('password:')[1].split()[0]
    assert len(pw) >= 12 and pw != 'admin123'
    c.login('admin', pw)
    r = c.client.post('/api/auth/login', data={'username': 'admin', 'password': 'admin123'})
    assert r.status_code == 401


def test_existing_default_password_warns(make_ctx, capsys):
    c = make_ctx(seed_records=[])
    users = c.mod.load_users()
    users['users'][0]['password_hash'] = c.mod.hash_password('admin123')
    c.mod.save_users(users)
    capsys.readouterr()
    c.mod.ensure_default_admin()
    assert 'default password' in capsys.readouterr().out
    r = c.client.post('/api/auth/login', data={'username': 'admin', 'password': 'admin123'})
    assert r.json()['password_weak'] is True


# ---- Route protection ---------------------------------------------------------
@pytest.mark.parametrize('path', ['/data.json', '/api/clients', '/api/filters', '/api/logos',
                                  '/logos/x.png', '/api/logo/info/x.js', '/api/logo/info/x.png',
                                  '/api/imgproxy?url=https://example.com/a.png'])
def test_protected_reads_need_login(ctx, path):
    ctx.client.cookies.clear()
    assert ctx.client.get(path).status_code == 401


@pytest.mark.parametrize('path', ['/', '/admin', '/login', '/api/health', '/api/auth/check'])
def test_public_routes(ctx, path):
    ctx.client.cookies.clear()
    assert ctx.client.get(path).status_code == 200


def test_viewer_can_read_but_not_write(ctx):
    v = ctx.make_viewer()
    assert ctx.client.get('/api/clients', headers=v).status_code == 200
    ctx.client.cookies.clear()
    assert ctx.client.post('/api/clients', headers=v, json={'company': 'X'}).status_code == 403
    assert ctx.client.get('/api/users', headers=v).status_code == 403
    assert ctx.client.get('/api/backup/export', headers=v).status_code == 403
    assert ctx.client.get('/api/logo/discover?company=x', headers=v).status_code == 403


def test_auth_disabled_makes_wall_public_but_writes_still_need_admin(make_ctx):
    c = make_ctx(seed_records=[], AUTH_ENABLED='false')
    c.client.cookies.clear()
    assert c.client.get('/data.json').status_code == 200
    assert c.client.post('/api/clients', json={'company': 'X'}).status_code == 401
    assert c.client.post('/api/clients', headers=c.admin(), json={'company': 'X'}).status_code == 200


# ---- Session cookie (replaces ?token= in image URLs) -------------------------
def test_login_sets_httponly_cookie_for_image_loads(ctx, tmp_path):
    (ctx.data_dir / 'logos' / 'abc.png').write_bytes(b'\x89PNG\r\n\x1a\n')
    ctx.client.cookies.clear()
    r = ctx.client.post('/api/auth/login', data={'username': 'admin', 'password': ADMIN_PW})
    set_cookie = r.headers['set-cookie']
    assert 'lw_session=' in set_cookie and 'HttpOnly' in set_cookie and 'samesite=lax' in set_cookie.lower()
    assert ctx.client.get('/logos/abc.png').status_code == 200


def test_cookie_alone_cannot_write(ctx):
    ctx.login()  # cookie now in the client jar
    r = ctx.client.post('/api/clients', json={'company': 'CSRF'})
    assert r.status_code == 401


def test_query_token_no_longer_accepted(ctx):
    tok = ctx.login()
    ctx.client.cookies.clear()
    assert ctx.client.get('/data.json?token=' + tok).status_code == 401


def test_auth_check_issues_cookie_for_existing_bearer_sessions(ctx):
    tok = ctx.login()
    ctx.client.cookies.clear()
    r = ctx.client.get('/api/auth/check', headers=ctx.hdr(tok))
    assert r.json()['ok'] is True
    assert 'lw_session=' in r.headers.get('set-cookie', '')


def test_logout_clears_cookie(ctx):
    ctx.login()
    r = ctx.client.post('/api/auth/logout')
    assert r.status_code == 200
    assert ctx.client.get('/data.json').status_code == 401


# ---- Revocation ------------------------------------------------------------------
def test_password_change_revokes_old_sessions(ctx):
    admin = ctx.admin()
    v = ctx.make_viewer()
    ctx.client.cookies.clear()
    r = ctx.client.put('/api/users/viewer', headers=admin, json={'password': 'brand-new-password'})
    assert r.status_code == 200
    ctx.client.cookies.clear()
    assert ctx.client.get('/api/clients', headers=v).status_code == 401
    ctx.login('viewer', 'brand-new-password')


def test_deleted_user_token_is_revoked(ctx):
    admin = ctx.admin()
    v = ctx.make_viewer()
    ctx.client.cookies.clear()
    assert ctx.client.delete('/api/users/viewer', headers=admin).status_code == 200
    assert ctx.client.get('/api/clients', headers=v).status_code == 401


def test_demoted_admin_loses_rights_immediately(ctx):
    admin = ctx.admin()
    r = ctx.client.post('/api/users', headers=admin,
                        json={'username': 'boss2', 'password': 'boss2-password', 'role': 'admin'})
    assert r.status_code == 200
    boss2 = ctx.hdr(ctx.login('boss2', 'boss2-password'))
    ctx.client.cookies.clear()
    ctx.client.put('/api/users/boss2', headers=admin, json={'role': 'viewer'})
    assert ctx.client.get('/api/users', headers=boss2).status_code == 401


def test_self_password_change_returns_fresh_token(ctx):
    admin = ctx.admin()
    r = ctx.client.put('/api/users/admin', headers=admin, json={'password': 'another-strong-pw'})
    body = r.json()
    assert body['ok'] and body['token']
    ctx.client.cookies.clear()
    assert ctx.client.get('/api/users', headers=admin).status_code == 401
    assert ctx.client.get('/api/users', headers=ctx.hdr(body['token'])).status_code == 200


def test_last_admin_cannot_be_deleted_or_demoted(ctx):
    admin = ctx.admin()
    assert ctx.client.delete('/api/users/admin', headers=admin).status_code == 400
    assert ctx.client.put('/api/users/admin', headers=admin, json={'role': 'viewer'}).status_code == 400


def test_password_minimum_length(ctx):
    admin = ctx.admin()
    r = ctx.client.post('/api/users', headers=admin, json={'username': 'u', 'password': '1234', 'role': 'viewer'})
    assert r.status_code == 400
    r = ctx.client.put('/api/users/admin', headers=admin, json={'password': 'short'})
    assert r.status_code == 400


def test_invalid_username_rejected(ctx):
    admin = ctx.admin()
    r = ctx.client.post('/api/users', headers=admin,
                        json={'username': '<script>', 'password': 'long-enough-pw', 'role': 'viewer'})
    assert r.status_code == 400


# ---- Brute-force throttling -------------------------------------------------------
def test_login_is_throttled_after_repeated_failures(ctx):
    for _ in range(5):
        r = ctx.client.post('/api/auth/login', data={'username': 'admin', 'password': 'wrong'})
        assert r.status_code == 401
    r = ctx.client.post('/api/auth/login', data={'username': 'admin', 'password': ADMIN_PW})
    assert r.status_code == 429
    assert int(r.headers['Retry-After']) > 0


def test_unknown_usernames_count_towards_ip_limit(ctx):
    for i in range(20):
        ctx.client.post('/api/auth/login', data={'username': f'nobody{i}', 'password': 'x'})
    r = ctx.client.post('/api/auth/login', data={'username': 'admin', 'password': ADMIN_PW})
    assert r.status_code == 429


def test_success_resets_user_counter(ctx):
    for _ in range(4):
        ctx.client.post('/api/auth/login', data={'username': 'admin', 'password': 'wrong'})
    ctx.login()
    for _ in range(4):
        ctx.client.post('/api/auth/login', data={'username': 'admin', 'password': 'wrong'})
    ctx.login()


# ---- Misc ---------------------------------------------------------------------------
def test_cors_closed_by_default(ctx):
    r = ctx.client.get('/api/health', headers={'Origin': 'https://evil.example'})
    assert 'access-control-allow-origin' not in r.headers


def test_cors_allowlist(make_ctx):
    c = make_ctx(seed_records=[], CORS_ORIGINS='https://wall.example.com')
    r = c.client.get('/api/health', headers={'Origin': 'https://wall.example.com'})
    assert r.headers.get('access-control-allow-origin') == 'https://wall.example.com'
    r = c.client.get('/api/health', headers={'Origin': 'https://evil.example'})
    assert 'access-control-allow-origin' not in r.headers


def test_security_headers(ctx):
    r = ctx.client.get('/')
    assert r.headers['x-content-type-options'] == 'nosniff'


def test_audit_log_records_writes_and_logins(ctx):
    admin = ctx.admin()
    ctx.client.post('/api/clients', headers=admin, json={'company': 'Audited'})
    ctx.client.post('/api/auth/login', data={'username': 'admin', 'password': 'bad'})
    entries = ctx.client.get('/api/audit', headers=admin).json()['entries']
    paths = [(e['path'], e['status'], e['user']) for e in entries]
    assert ('/api/clients', 200, 'admin') in paths
    assert ('/api/auth/login', 401, 'admin') in paths
