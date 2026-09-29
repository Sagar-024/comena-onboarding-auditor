# syntax=docker/dockerfile:1

# --- Stage 1: build a self-contained virtualenv ---------------------------
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
COPY requirements.txt ./
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r requirements.txt

# --- Stage 2: slim runtime -------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8080

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY app ./app

# Run as a non-root user; uploads/ is the ephemeral scratch dir the app writes to.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p uploads \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

# Cloud Run injects PORT; fall back to 8080 for local docker runs.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
