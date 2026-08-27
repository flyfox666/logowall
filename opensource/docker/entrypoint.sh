#!/bin/sh
set -e

# If DATA_DIR is empty (fresh volume), seed it from bundled data
if [ ! -f "$DATA_DIR/data.json" ]; then
    echo "Seeding initial data to $DATA_DIR ..."
    cp /app/data.json "$DATA_DIR/data.json"
    cp -n /app/logos/* "$DATA_DIR/logos/" 2>/dev/null || true
fi

exec "$@"
