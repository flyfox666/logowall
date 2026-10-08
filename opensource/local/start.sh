#!/bin/sh
# Logo Wall - local start script (macOS / Linux)
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 not found. Please install Python 3.9+."
    exit 1
fi

if [ ! -d .venv ]; then
    echo "First run: creating virtual environment..."
    python3 -m venv .venv
fi
. .venv/bin/activate
# (Re)install dependencies on first run and whenever requirements.txt changes
if [ ! -f .venv/.requirements-installed ] || [ server/requirements.txt -nt .venv/.requirements-installed ]; then
    echo "Installing dependencies..."
    pip install -r server/requirements.txt && touch .venv/.requirements-installed
fi

# Load config.env (PORT / ADMIN_PASSWORD / ...) if present
if [ -f config.env ]; then
    set -a
    . ./config.env
    set +a
fi

echo "========================================================"
echo "  Starting server... (actual addresses will show below)"
echo "  Config file: config.env (see config.env.example)"
echo "========================================================"

export PORT="${PORT:-8080}"

# Auto-release the configured port if it is already in use
echo "Checking port ${PORT}..."
_killed=""
if command -v lsof >/dev/null 2>&1; then
    for _pid in $(lsof -ti tcp:"${PORT}" -sTCP:LISTEN 2>/dev/null); do
        echo "  Port ${PORT} is held by PID ${_pid}, terminating..."
        kill -9 "${_pid}" 2>/dev/null && _killed="1"
    done
elif command -v fuser >/dev/null 2>&1; then
    if fuser "${PORT}"/tcp >/dev/null 2>&1; then
        echo "  Port ${PORT} is in use, terminating..."
        fuser -k "${PORT}"/tcp >/dev/null 2>&1 && _killed="1"
    fi
fi
if [ -n "$_killed" ]; then
    sleep 1
    echo "  Port ${PORT} released."
else
    echo "  Port ${PORT} is free."
fi

python3 server/app.py
