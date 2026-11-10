# Production image: FastAPI app (src/backend) that also serves the static frontend (src/frontend).
# Runs behind the Caddy reverse proxy, which terminates HTTPS; see doc/deployment.md.
#
# Multi-stage build: the first stage installs the locked dependencies with uv, the final stage
# only contains Python, the virtual environment and the app code (no uv, no build tools).
# python:3.13-slim is a multi-architecture image, so this builds natively on arm64 (Oracle Ampere)
# as well as amd64.

# --- Stage 1: install dependencies -------------------------------------------------------------
FROM python:3.13-slim AS build

# Same uv version as CI and FormelX.
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Only the dependency files first, so this layer is cached until uv.lock changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# --- Stage 2: runtime --------------------------------------------------------------------------
FROM python:3.13-slim

# Unprivileged user: the app never needs root.
RUN groupadd --system app && useradd --system --gid app --no-create-home --home-dir /nonexistent app

WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY src ./src

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    DEFAULT_FORWARDED_ALLOW_IPS="172.16.0.0/12,192.168.0.0/16,10.0.0.0/8"

USER app
EXPOSE 8000

# Plain HTTP on 0.0.0.0:8000 inside the container; Caddy handles TLS and the HTTP->HTTPS redirect.
# --proxy-headers: trust X-Forwarded-For / X-Forwarded-Proto from the addresses in
#   FORWARDED_ALLOW_IPS (Caddy on the Docker network; default: Docker's private address ranges,
#   also used when .env sets it to an empty value), so the app sees the visitor's IP (rate limit)
#   and that the original request was HTTPS. Caddy passes the original Host header through.
# One worker on purpose: the rate limiter counts in memory per process.
CMD ["sh", "-c", "exec uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips \"${FORWARDED_ALLOW_IPS:-$DEFAULT_FORWARDED_ALLOW_IPS}\" --no-server-header"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=4)"]
