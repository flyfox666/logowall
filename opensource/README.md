# Logo Wall · 客户品牌墙

**English** | [简体中文](README.zh-CN.md)

A self-hosted client logo wall with an admin panel, one-click poster export,
full data backup, multi-user login and theme customization. Built for teams
who want to showcase their clients on a big screen at events, in the office,
or in a browser.

---

## Table of Contents

- [Screenshots](#screenshots)
- [Features](#features)
- [Quick Start](#quick-start)
  - [Local (Python 3.9+)](#local-python-39)
  - [Docker](#docker)
- [Architecture: Code–Data Separation](#architecture-code-data-separation)
- [Full Backup Export / Import](#full-backup-export--import)
- [Configuration](#configuration)
- [Onboarding a New Team](#onboarding-a-new-team)
- [Demo Data & Anonymization](#demo-data--anonymization)
- [Repository Layout](#repository-layout)
- [License](#license)

---

## Screenshots

| Brand wall | Poster export |
|---|---|
| ![front](docs/screenshots/front.png) | ![poster](docs/screenshots/poster-export.png) |

| Admin panel |
|---|
| ![admin](docs/screenshots/admin.png) |

## Features

- **Brand wall** — responsive grid grouped by office, business line, region
  and owner, with live search and filters (region → city → business line →
  owner).
- **Admin panel** (`/admin`) — CRUD for clients, Excel import / export, logo
  discovery (Clearbit / Google favicon / DuckDuckGo), logo upload and a
  shared logo library.
- **Poster export** — export the currently filtered clients as a ready-to-use
  PNG poster (3:4 poster, 16:9 screen, A4 @300dpi).
- **Full backup** — one-click export / import of the entire dataset (clients +
  logo files + user accounts) as a single zip. Move or migrate a deployment
  without touching the database by hand.
- **Multi-user auth** — login page with `admin` and `viewer` roles; visitors
  see the wall, admins manage it. The legacy `ADMIN_TOKEN` still works as a
  master token for API calls.
- **Theming** — 5 preset color themes × 4 background patterns, visitor preview
  in the toolbar palette, site-wide default + custom colors in admin site
  settings.
- **Site settings** — title, English subtitle, tagline and footer text are all
  editable from the admin panel.
- **Bilingual UI** — one-click EN / 中文 switch on both the wall and the admin
  panel (remembered independently).
- **Missing-logo helper** — the admin stats card shows how many clients have
  no logo and lists them with one click.

## Quick Start

### Local (Python 3.9+)

```bash
cd local
# Windows
start.bat
# macOS / Linux
./start.sh
```

Then open http://localhost:8080/ (admin: http://localhost:8080/admin,
default account `admin / admin123` — change the password in "User management"
after first login; `ADMIN_TOKEN` works for API access only).

### Docker

```bash
cd docker
docker compose up -d --build
```

Data (clients + uploaded logos) is persisted in the `logo-wall-data` volume.
For public deployment behind a Cloudflare Tunnel, see
[docker/README.md](docker/README.md).

## Architecture: Code–Data Separation

All runtime data lives in a single directory pointed to by `DATA_DIR`:

```
DATA_DIR/
├── data.json     # clients, site settings, filters cache
├── logos/        # uploaded logo files
└── users.json    # login accounts (admin / viewer roles)
```

The code never mixes with data. Point `DATA_DIR` at any folder and the same
codebase serves a different dataset — no code copies, no sync scripts:

```bash
# same code, environment A
DATA_DIR=/srv/logo-wall-a ./start.sh
# same code, environment B
DATA_DIR=/srv/logo-wall-b ./start.sh
```

Docker works the same way: mount any host folder at `/data` and set
`DATA_DIR=/data` (see `docker/docker-compose.yml`).

If `DATA_DIR` is empty, the app bootstraps itself: an empty `data.json` is
created and a default admin user (`admin / admin123`) is generated on first
run.

## Full Backup Export / Import

The admin panel toolbar has **Export backup / Import backup** buttons (API:
`GET /api/backup/export`, `POST /api/backup/import`).

- **Export** downloads `logo-wall-backup-YYYYMMDD-HHMMSS.zip` containing
  `data.json` + `logos/` + `users.json` + a `manifest.json` with record counts
  and a timestamp.
- **Import** validates the zip, then replaces client data and user accounts
  and merges logo files (zip-slip protected, size-limited via `BACKUP_MAX_MB`).

Typical uses: migrating between local ↔ Docker, handing a dataset to a new
team, or scheduled off-site backups.

## Configuration

| Env var     | Default    | Purpose                          |
|-------------|------------|----------------------------------|
| `PORT`      | `8080`     | HTTP port                        |
| `HOST`      | `0.0.0.0`  | Bind address (`127.0.0.1` = local only) |
| `ADMIN_TOKEN` | `admin123` | Master token for API calls (pages use account login) |
| `AUTH_ENABLED` | `true`   | Enable the login page (multi-user auth) |
| `JWT_SECRET` | derived    | Secret for login sessions; set a fixed value to keep users logged in across restarts |
| `JWT_EXPIRE_DAYS` | `7`   | Login session lifetime in days   |
| `DATA_DIR`  | app folder | Where `data.json` / `logos/` / `users.json` live |
| `MAX_UPLOAD_MB` | `5`    | Max logo upload size             |
| `BACKUP_MAX_MB` | `200`  | Max backup zip size on import    |
| `IMGPROXY_MAX_MB` | `8`  | Poster proxy per-image limit     |
| `IMGPROXY_TIMEOUT` | `10`| Poster proxy timeout (seconds)   |
| `LOG_LEVEL` | `info`     | info / warning / error / debug   |

Easier than env vars:
- **local**: copy `local/config.env.example` to `local/config.env` and edit
  `PORT` / `ADMIN_TOKEN` there.
- **docker**: create a `.env` next to `docker-compose.yml` with `PORT=8081`
  etc.

## Onboarding a New Team

Give a new team exactly two things:

1. **The code** — a clone of this repository (it ships with fictional demo
   data only, safe to share).
2. **An empty data folder** — nothing to prepare; on first run the app
   creates `data.json` and a default `admin` user automatically.

They then run:

```bash
# local
git clone <this-repo> && cd logo-wall/local && ./start.sh

# docker
cd docker && cp .env.example .env && docker compose up -d --build
```

To run multiple environments from one codebase, point `DATA_DIR` at each
team's own folder. To hand over an existing dataset, export a backup zip in
the admin panel and let them import it in theirs. Code upgrades are just
`git pull` + restart — data directories are never touched.

## Demo Data & Anonymization

The bundled `data.json` is fully fictional. If you maintain a private fork
with real data, regenerate a safe demo dataset with:

```bash
python tools/anonymize.py --src /path/to/real/data.json --out local/data.json
```

The script replaces company names, brands, owners, offices/cities/regions,
business lines, logos and websites with fictional values. Cities, regions and
business lines are freshly reshuffled with a plausible weighted distribution
(deterministic, seeded — same output every run).

## Repository Layout

```
local/    Run directly with Python (venv created automatically)
docker/   Docker Compose deployment with persistent volume
tools/    anonymize.py — demo data generator
docs/     Screenshots
```

## License

MIT — see [LICENSE](LICENSE).
