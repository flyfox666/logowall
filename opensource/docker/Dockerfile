FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (better layer caching)
COPY server/requirements.txt /app/server/requirements.txt
RUN pip install --no-cache-dir -r /app/server/requirements.txt

# Copy application code
COPY server/ /app/server/
COPY index.html /app/index.html
COPY data.json /app/data.json
COPY logos/ /app/logos/

# Data directory (override via DATA_DIR env if needed)
ENV DATA_DIR=/data
RUN mkdir -p /data/logos

# Copy entrypoint (seeds initial data into volume if empty)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8080"]
