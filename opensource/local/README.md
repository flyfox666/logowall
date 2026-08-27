# Local Deployment (Python)

[English](README.md) | **简体中文**

Run directly with Python — ideal for a personal computer or an event laptop.

## Startup

- Windows: double-click `start.bat`
- macOS / Linux: `./start.sh` (a virtualenv is created automatically on
  first run and dependencies are installed)

After startup the terminal prints every reachable address:

```
On this computer:
  Brand wall :  http://localhost:8080/
  Admin panel:  http://localhost:8080/admin
From other phones/computers on the same Wi-Fi/LAN:
  Brand wall :  http://<your-LAN-IP>:8080/
```

## Configuration

Simplest: copy `config.env.example` to `config.env`, edit `PORT` /
`ADMIN_TOKEN` there and restart. Environment variables work too:

| Env var | Default | Description |
|---|---|---|
| `PORT` | 8080 | HTTP port |
| `HOST` | 0.0.0.0 | Bind address; use 127.0.0.1 for local-only |
| `ADMIN_TOKEN` | admin123 | Master token (fallback auth for write ops) |
| `AUTH_ENABLED` | true | Login page toggle (admin / viewer users) |
| `JWT_SECRET` | derived | Login session secret; set a fixed value to survive restarts |
| `JWT_EXPIRE_DAYS` | 7 | Login session lifetime (days) |
| `DATA_DIR` | this folder | Where `data.json` / `logos/` / `users.json` live |
| `MAX_UPLOAD_MB` | 5 | Max logo upload size |
| `BACKUP_MAX_MB` | 200 | Max backup zip size on import |
| `IMGPROXY_MAX_MB` | 8 | Poster proxy per-image limit |
| `IMGPROXY_TIMEOUT` | 10 | Poster proxy timeout (seconds) |
| `LOG_LEVEL` | info | info / warning / error / debug |

## Usage tips

- Front-page filters are laid out region → city → business line → owner, one
  per row; the header and filter bar can each be collapsed (state is
  remembered) for a more immersive big-screen display.
- Admin panel `/admin`: create / edit / delete clients, Excel import /
  export, automatic logo discovery and upload, shared logo library;
  pagination from 15 to 200 rows per page; the "No logo" filter or the
  "with logo" stats card quickly surfaces clients missing logos.
- "Site settings": edit title / English subtitle / tagline / footer, default
  theme and background, custom colors.
- "Export poster" (top-right of the wall): export the current filter result
  as a PNG poster (portrait / big screen / A4).
- Palette button (top-right of the wall): per-visitor theme preview that does
  not affect others; "Reset to site default" clears the preview.
- **Login & users**: the wall greets visitors with a login page; a default
  admin `admin / admin123` is created on first run (change the password in
  "User management" and add read-only viewer accounts as needed). Set
  `AUTH_ENABLED=false` to disable the login page.
- **Full backup**: the admin toolbar's "Export backup / Import backup"
  buttons download or restore a single zip (clients + logo files + user
  accounts) — ideal for cross-environment migration and scheduled backups.
- **Bilingual UI**: an "EN / 中文" button on both the wall and the admin panel
  switches the whole interface (remembered independently); the English
  subtitle / tagline / footer from site settings are shown in English mode.
- Data lives in `DATA_DIR` (this folder by default): `data.json` (clients +
  site settings), `logos/` (logo files), `users.json` (login accounts); use
  the admin backup export / import to migrate everything at once — no manual
  copying required.
