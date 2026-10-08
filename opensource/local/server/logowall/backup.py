"""Full backup export / import (data.json + logos/ + optionally users.json).

Import is validate-everything-first: the zip is fully checked (entry count,
total uncompressed size, paths, logo names and content, data.json and
users.json structure) before a single file on disk is touched, and an
automatic snapshot of the current data is written to DATA_DIR/backups/ so a
bad import can be rolled back.
"""
import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Optional

from . import config
from .images import is_safe_logo_name, sniff_image
from .storage import load_data, save_data, save_users, DATA_LOCK


class BackupError(ValueError):
    pass


def build_backup_zip() -> bytes:
    data = load_data()
    logo_files = sorted(f for f in config.LOGOS_DIR.iterdir() if f.is_file()) \
        if config.LOGOS_DIR.exists() else []
    manifest = {
        'app': 'logo-wall',
        'version': 1,
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'records': len(data.get('records', [])),
        'logos': len(logo_files),
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        if config.DATA_JSON.exists():
            zf.write(config.DATA_JSON, 'data.json')
        if config.USERS_JSON.exists():
            zf.write(config.USERS_JSON, 'users.json')
        for f in logo_files:
            zf.write(f, 'logos/' + f.name)
    return buf.getvalue()


def write_snapshot(reason: str) -> Optional[str]:
    """Save the current state into DATA_DIR/backups/, keeping the newest N."""
    if config.AUTO_SNAPSHOTS_KEEP <= 0:
        return None
    config.BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    name = f'auto-{reason}-{datetime.now().strftime("%Y%m%d-%H%M%S-%f")}.zip'
    (config.BACKUPS_DIR / name).write_bytes(build_backup_zip())
    snaps = sorted(config.BACKUPS_DIR.glob('auto-*.zip'))
    for old in snaps[:-config.AUTO_SNAPSHOTS_KEEP]:
        old.unlink(missing_ok=True)
    return name


def _read_member(zf: zipfile.ZipFile, info: zipfile.ZipInfo, budget: list) -> bytes:
    """Read one member, enforcing the remaining uncompressed-byte budget on the
    actual decompressed stream (the size in the zip header can lie)."""
    with zf.open(info) as fh:
        data = fh.read(budget[0] + 1)
    if len(data) > budget[0]:
        raise BackupError('Backup expands beyond the allowed size '
                          f'({config.BACKUP_MAX_UNCOMPRESSED_BYTES // 1024 // 1024} MB uncompressed)')
    budget[0] -= len(data)
    return data


def _validate_users(users) -> dict:
    if not isinstance(users, dict) or not isinstance(users.get('users'), list):
        raise BackupError('users.json: "users" must be a list')
    seen = set()
    for u in users['users']:
        if not isinstance(u, dict):
            raise BackupError('users.json: every user must be an object')
        name, pw, role = u.get('username'), u.get('password_hash'), u.get('role')
        if not isinstance(name, str) or not name.strip():
            raise BackupError('users.json: user without a username')
        if name in seen:
            raise BackupError(f'users.json: duplicate username {name!r}')
        seen.add(name)
        if not isinstance(pw, str) or not pw.startswith('$2'):
            raise BackupError(f'users.json: user {name!r} has no valid bcrypt password_hash')
        if role not in ('admin', 'viewer'):
            raise BackupError(f'users.json: user {name!r} has invalid role {role!r}')
    if not any(u['role'] == 'admin' for u in users['users']):
        raise BackupError('users.json contains no admin account; refusing to lock you out')
    return users


def import_backup(content: bytes, restore_users: bool) -> dict:
    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile:
        raise BackupError('Not a valid zip file')

    with zf:
        infos = zf.infolist()
        if len(infos) > config.BACKUP_MAX_ENTRIES:
            raise BackupError(f'Backup has too many files (> {config.BACKUP_MAX_ENTRIES})')
        declared = sum(i.file_size for i in infos)
        if declared > config.BACKUP_MAX_UNCOMPRESSED_BYTES:
            raise BackupError('Backup expands beyond the allowed size '
                              f'({config.BACKUP_MAX_UNCOMPRESSED_BYTES // 1024 // 1024} MB uncompressed)')
        budget = [config.BACKUP_MAX_UNCOMPRESSED_BYTES]

        by_name = {}
        for info in infos:
            name = info.filename.replace('\\', '/')
            if name.startswith('/') or '..' in name.split('/') or ':' in name:
                raise BackupError(f'Illegal path in backup: {name}')
            by_name[name] = info

        if 'data.json' not in by_name:
            raise BackupError('Backup zip is missing data.json (not a Logo Wall backup?)')
        try:
            new_data = json.loads(_read_member(zf, by_name['data.json'], budget).decode('utf-8'))
            if not isinstance(new_data, dict) or not isinstance(new_data.get('records'), list):
                raise ValueError('records must be a list')
            if not all(isinstance(r, dict) for r in new_data['records']):
                raise ValueError('every record must be an object')
        except BackupError:
            raise
        except Exception as e:
            raise BackupError(f'Invalid data.json in backup: {e}')

        new_users = None
        if restore_users:
            if 'users.json' not in by_name:
                raise BackupError('Backup has no users.json to restore')
            try:
                raw = json.loads(_read_member(zf, by_name['users.json'], budget).decode('utf-8'))
            except BackupError:
                raise
            except Exception as e:
                raise BackupError(f'Invalid users.json in backup: {e}')
            new_users = _validate_users(raw)

        logos, skipped = {}, []
        for name, info in by_name.items():
            if not name.startswith('logos/') or name.endswith('/'):
                continue
            rel = name[len('logos/'):]
            if '/' in rel:
                skipped.append(name)
                continue
            if not is_safe_logo_name(rel):
                skipped.append(name)
                continue
            blob = _read_member(zf, info, budget)
            if not sniff_image(blob):
                skipped.append(name)
                continue
            logos[rel] = blob

    # ---- everything validated: snapshot, then apply ----
    with DATA_LOCK:
        snapshot = write_snapshot('before-import')
        for rel, blob in logos.items():
            target = config.LOGOS_DIR / rel
            tmp = target.with_name(target.name + '.tmp')
            tmp.write_bytes(blob)
            tmp.replace(target)
        save_data(new_data)
        if new_users is not None:
            save_users(new_users)

    return {'ok': True, 'records': len(new_data['records']), 'logos': len(logos),
            'users': new_users is not None, 'skipped': skipped, 'snapshot': snapshot}
