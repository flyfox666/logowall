import io
import sys
import json
import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

LOCAL_DIR = Path(__file__).resolve().parent.parent
SERVER_DIR = LOCAL_DIR / 'server'
for p in (str(LOCAL_DIR), str(SERVER_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

ADMIN_PW = 'correct-horse-battery'

# Env vars the app reads; cleared so the developer's shell can't leak in
APP_ENV = ('DATA_DIR', 'ADMIN_TOKEN', 'ADMIN_PASSWORD', 'JWT_SECRET', 'AUTH_ENABLED',
           'CORS_ORIGINS', 'FETCH_ALLOW_PRIVATE', 'LOGO_MAX_PX', 'MIN_PASSWORD_LEN',
           'LOGIN_MAX_FAILURES', 'BACKUP_MAX_UNCOMPRESSED_MB', 'MAX_UPLOAD_MB')


def load_app(monkeypatch, data_dir: Path, **env):
    """(Re)import the app fresh against `data_dir` with the given env vars."""
    for k in APP_ENV:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv('DATA_DIR', str(data_dir))
    monkeypatch.setenv('ADMIN_PASSWORD', ADMIN_PW)
    for k, v in env.items():
        if v is None:
            monkeypatch.delenv(k, raising=False)
        else:
            monkeypatch.setenv(k, str(v))
    for name in list(sys.modules):
        if name == 'logowall' or name.startswith('logowall.') or name in ('app', 'server.app'):
            del sys.modules[name]
    return importlib.import_module('server.app')


class Ctx:
    def __init__(self, mod, client, data_dir):
        self.mod = mod
        self.client = client
        self.data_dir = data_dir

    def login(self, username='admin', password=ADMIN_PW):
        r = self.client.post('/api/auth/login', data={'username': username, 'password': password})
        assert r.status_code == 200, r.text
        return r.json()['token']

    def hdr(self, token):
        return {'Authorization': 'Bearer ' + token}

    def admin(self):
        return self.hdr(self.login())

    def make_viewer(self, name='viewer', password='viewer-password'):
        r = self.client.post('/api/users', headers=self.admin(),
                             json={'username': name, 'password': password, 'role': 'viewer'})
        assert r.status_code == 200, r.text
        return self.hdr(self.login(name, password))


@pytest.fixture
def make_ctx(tmp_path, monkeypatch):
    clients = []

    def _make(seed_records=None, **env):
        data_dir = tmp_path / 'data'
        data_dir.mkdir(exist_ok=True)
        if seed_records is not None:
            (data_dir / 'data.json').write_text(json.dumps({'records': seed_records}), encoding='utf-8')
        mod = load_app(monkeypatch, data_dir, **env)
        client = TestClient(mod.app)
        client.__enter__()  # run lifespan (creates the first admin)
        clients.append(client)
        return Ctx(mod, client, data_dir)

    yield _make
    for c in clients:
        c.__exit__(None, None, None)


@pytest.fixture
def ctx(make_ctx):
    return make_ctx(seed_records=[])


def png_bytes(size=(10, 10), color=(255, 0, 0, 255)) -> bytes:
    from PIL import Image
    buf = io.BytesIO()
    Image.new('RGBA', size, color).save(buf, 'PNG')
    return buf.getvalue()
