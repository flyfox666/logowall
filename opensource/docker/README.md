# Docker Deployment

**English** | [简体中文](README.zh-CN.md)

Built for long-running deployments on servers / NAS with data persisted in a
Docker volume.

## Startup

```bash
docker compose up -d --build
```

Open http://localhost:8080/ (admin panel: http://localhost:8080/admin).

On first run an `admin` account is created. Its random password is printed
once in the log (`docker compose logs logo-wall | grep password`), or set
`ADMIN_PASSWORD` in `.env` before the first start to choose it. Add read-only
viewer accounts in "User management". For anything beyond a trusted LAN, put
the container behind an HTTPS reverse proxy (see "Security & Production
Deployment" in the root README).

Both the wall and the admin panel have an "EN / 中文" button (top-right) that
switches the interface language (remembered independently).

## Configuration

Edit the `environment` section of `docker-compose.yml`, or create a `.env`
file next to it:

```
ADMIN_PASSWORD=choose-a-strong-password
# optional master token for API scripts (>= 12 chars), e.g. `openssl rand -hex 24`
ADMIN_TOKEN=
```

| Env var | Default | Description |
|---|---|---|
| `ADMIN_PASSWORD` | random | Password of the first `admin` account (printed to the log when unset) |
| `ADMIN_TOKEN` | *(disabled)* | Optional master token for API scripts; < 12 chars or `admin123` is refused |
| `AUTH_ENABLED` | true | Login page toggle (admin / viewer users) |
| `JWT_SECRET` | random | Session secret; random and stored in the volume (`/data/.jwt_secret`) when unset |
| `FORWARDED_ALLOW_IPS` | 127.0.0.1 | Reverse-proxy address(es) whose `X-Forwarded-For` is trusted |
| `JWT_EXPIRE_DAYS` | 7 | Login session lifetime (days) |
| `DATA_DIR` | /data | In-container data directory (mounted to a volume) |
| `BACKUP_MAX_MB` | 200 | Max backup zip size on import |

Port mapping is set in the `ports` section of `docker-compose.yml`
(default `8080:8080`).

## Data

- Client data and uploaded logos live in the `logo-wall-data` volume
  (`data.json` + `logos/` + `users.json`, plus `audit.log` and pre-import
  snapshots in `backups/`).
- The container runs as an unprivileged user (uid 10001); the entrypoint
  fixes ownership of volumes created by older, root-based images.
- On first start the built-in demo data is automatically seeded into the
  volume.
- **Recommended backup**: the admin toolbar's "Export backup / Import backup"
  buttons download or restore a single zip (clients + logo files + user
  accounts) — ideal for migration and scheduled backups.
- Cold backup from the command line (while the service is stopped):
  `docker run --rm -v logo-wall-data:/data -v $PWD:/backup alpine tar czf /backup/logo-wall-backup.tgz -C /data .`

## Multi-environment deployment (optional)

One image can serve several data environments: in compose, mount any host
folder at `/data` and keep `DATA_DIR=/data` — every team / business line gets
its own data while code upgrades are just an image re-pull; data is never
touched. See the "Architecture: Code–Data Separation" section of the
repository root README.

## Public access (optional)

To expose the service through a Cloudflare Tunnel, add a `cloudflared`
service to `docker-compose.yml` (see the official
`cloudflare/cloudflared:latest` image), or point a `cloudflared tunnel`
at this service's port.
