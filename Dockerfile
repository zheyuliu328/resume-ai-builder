# Lightweight runtime image for local-first Resume AI Builder
# Note: This image is primarily for packaging / logistics (GHCR). No secrets baked in.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_PORT=5001 \
    LOG_LEVEL=INFO \
    FLASK_DEBUG=0

WORKDIR /app

# System deps: keep minimal.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001

CMD ["python", "backend/api_server.py"]
