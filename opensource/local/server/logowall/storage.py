"""JSON file storage for data.json / users.json.

Every read-modify-write sequence must run under DATA_LOCK: FastAPI runs sync
endpoints in a thread pool, so two concurrent edits would otherwise both load
the same snapshot and the later save would silently drop the earlier change.
(Run a single uvicorn worker process; the lock is per-process.)
"""
import os
import json
import threading
from pathlib import Path

from . import config
from .constants import get_region

DATA_LOCK = threading.RLock()


def _atomic_write_json(path: Path, data: dict, mode: int = None):
    tmp = path.with_suffix(path.suffix + '.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    if mode is not None:
        try:
            os.chmod(tmp, mode)
        except OSError:
            pass
    tmp.replace(path)


def empty_data() -> dict:
    return {'title': '客户品牌墙', 'subtitle': 'CLIENT LOGO WALL',
            'tagline': 'OFFICE × BUSINESS LINE  ·  连接客户价值，共创长期合作',
            'total_count': 0, 'offices': [], 'departments': [], 'regions': [],
            'records': []}


def load_data() -> dict:
    if not config.DATA_JSON.exists():
        return empty_data()
    with open(config.DATA_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Ensure every record has a region field (auto-derived from office code)
    for r in data.get('records', []):
        if not r.get('region'):
            r['region'] = get_region(r.get('office_code', ''))
    return data


def save_data(data: dict):
    records = data.setdefault('records', [])
    for r in records:
        if not r.get('region'):
            r['region'] = get_region(r.get('office_code', ''))
    data['total_count'] = len(records)
    data['offices'] = sorted({r['office_city'] for r in records if r.get('office_city')})
    data['departments'] = sorted({d for r in records for d in (r.get('departments') or [])})
    data['regions'] = sorted({r.get('region', '其他') for r in records if r.get('region')})
    with DATA_LOCK:
        _atomic_write_json(config.DATA_JSON, data)


def data_etag() -> str:
    """Cheap validator for data.json derived from file metadata."""
    try:
        st = config.DATA_JSON.stat()
    except FileNotFoundError:
        return '"empty"'
    return f'"{st.st_mtime_ns:x}-{st.st_size:x}"'


def load_users() -> dict:
    if not config.USERS_JSON.exists():
        return {'users': []}
    with open(config.USERS_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data.setdefault('users', [])
    return data


def save_users(data: dict):
    with DATA_LOCK:
        # users.json holds password hashes: keep it private to the service user
        _atomic_write_json(config.USERS_JSON, data, mode=0o600)
