#!/bin/sh
# Logo Wall - local start script (macOS / Linux)
set -e
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] python3 not found. Please install Python 3.9+."
    exit 1
fi

if [ ! -d .venv ]; then
    echo "First run: creating virtual environment and installing dependencies..."
    python3 -m venv .venv
    . .venv/bin/activate
    pip install -r server/requirements.txt
else
    . .venv/bin/activate
fi

# Load config.env (PORT / ADMIN_TOKEN) if present
if [ -f config.env ]; then
    set -a
    . ./config.env
    set +a
fi

echo "========================================================"
echo "  Starting server... (actual addresses will show below)"
echo "  Config file: config.env (PORT / ADMIN_TOKEN)"
echo "========================================================"

export ADMIN_TOKEN="${ADMIN_TOKEN:-admin123}"
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
