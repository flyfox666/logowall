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
python3 server/app.py
