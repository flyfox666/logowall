#!/bin/sh
set -e

mkdir -p "$DATA_DIR/logos"

# If DATA_DIR is empty (fresh volume), seed it from bundled data
if [ ! -f "$DATA_DIR/data.json" ]; then
    echo "Seeding initial data to $DATA_DIR ..."
    cp /app/seed/data.json "$DATA_DIR/data.json"
    cp -n /app/seed/logos/* "$DATA_DIR/logos/" 2>/dev/null || true
fi

# Started as root (the default): hand the data volume to the unprivileged
# user — volumes created by older images are root-owned — then drop privileges.
if [ "$(id -u)" = "0" ]; then
    chown -R logowall:logowall "$DATA_DIR"
    exec setpriv --reuid=logowall --regid=logowall --init-groups "$@"
fi

exec "$@"
