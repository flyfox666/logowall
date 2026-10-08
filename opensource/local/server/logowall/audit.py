"""Append-only audit log of write operations (DATA_DIR/audit.log, JSON lines)."""
import json
import threading
from collections import deque
from datetime import datetime, timezone

from . import config

_lock = threading.Lock()


def record(user: str, ip: str, method: str, path: str, status: int, detail: str = ''):
    entry = {
        'ts': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'user': user or '-',
        'ip': ip,
        'method': method,
        'path': path,
        'status': status,
    }
    if detail:
        entry['detail'] = detail
    line = json.dumps(entry, ensure_ascii=False) + '\n'
    with _lock:
        try:
            if config.AUDIT_LOG.exists() and config.AUDIT_LOG.stat().st_size > config.AUDIT_LOG_MAX_BYTES:
                config.AUDIT_LOG.replace(config.AUDIT_LOG.with_suffix('.log.1'))
            with open(config.AUDIT_LOG, 'a', encoding='utf-8') as f:
                f.write(line)
        except OSError:
            pass  # auditing must never break the request


def tail(limit: int = 200) -> list:
    if not config.AUDIT_LOG.exists():
        return []
    with _lock, open(config.AUDIT_LOG, 'r', encoding='utf-8') as f:
        lines = deque(f, maxlen=max(1, min(limit, 5000)))
    out = []
    for ln in reversed(lines):
        try:
            out.append(json.loads(ln))
        except ValueError:
            continue
    return out
