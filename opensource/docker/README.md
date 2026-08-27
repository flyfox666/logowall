# Docker Deployment

[English](README.md) | **简体中文**

Built for long-running deployments on servers / NAS with data persisted in a
Docker volume.

## Startup

```bash
docker compose up -d --build
```

Open http://localhost:8080/ (admin panel: http://localhost:8080/admin).

A default admin `admin / admin123` is created on first run — change the
password in "User management" afterwards and add read-only viewer accounts as
needed. `ADMIN_TOKEN` still works as a master token for API calls.

Both the wall and the admin panel have an "EN / 中文" button (top-right) that
switches the interface language (remembered independently).

## Configuration

Edit the `environment` section of `docker-compose.yml`, or create a `.env`
file next to it:

```
ADMIN_TOKEN=your-secret-token
```

| Env var | Default | Description |
|---|---|---|
| `ADMIN_TOKEN` | admin123 | Master token for API calls (pages use account login — change in production) |
| `AUTH_ENABLED` | true | Login page toggle (admin / viewer users) |
| `JWT_SECRET` | derived | Login session secret; set a fixed value to survive restarts |
| `JWT_EXPIRE_DAYS` | 7 | Login session lifetime (days) |
| `DATA_DIR` | /data | In-container data directory (mounted to a volume) |
| `BACKUP_MAX_MB` | 200 | Max backup zip size on import |

Port mapping is set in the `ports` section of `docker-compose.yml`
(default `8080:8080`).

## Data

- Client data and uploaded logos live in the `logo-wall-data` volume
  (`data.json` + `logos/` + `users.json`).
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
