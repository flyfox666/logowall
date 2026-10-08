# Build context is the `opensource/` directory (see docker-compose.yml), so the
# image is built from the single source of truth in `local/` — there is no
# second copy of the app to keep in sync.
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (better layer caching)
COPY local/server/requirements.txt /app/server/requirements.txt
RUN pip install --no-cache-dir -r /app/server/requirements.txt

# Copy application code
COPY local/server/ /app/server/
COPY local/index.html /app/index.html
# Seed data, copied into the volume on first start by entrypoint.sh
COPY local/data.json /app/seed/data.json

# Run as an unprivileged user; /data is the persistent volume
RUN useradd --system --uid 10001 --home-dir /app --shell /usr/sbin/nologin logowall \
    && mkdir -p /data/logos /app/seed/logos \
    && chown -R logowall:logowall /data

# Data directory (override via DATA_DIR env if needed)
ENV DATA_DIR=/data \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy entrypoint (seeds initial data into volume if empty)
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod 0755 /entrypoint.sh

# entrypoint.sh fixes volume ownership (volumes from older root-based images)
# and then drops privileges to the `logowall` user before starting the app.
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health')"

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers", "--forwarded-allow-ips", "*"]
