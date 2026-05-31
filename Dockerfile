# ---------------------------------------------------------------------------
# STAGE 1 — Build liboqs native shared library (pinned release)
# ---------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git ninja-build libssl-dev \
    && rm -rf /var/lib/apt/lists/*

ARG LIBOQS_VERSION=0.14.0
RUN git clone --branch ${LIBOQS_VERSION} --depth 1 \
    https://github.com/open-quantum-safe/liboqs.git /liboqs \
    && cd /liboqs && mkdir build && cd build \
    && cmake -GNinja \
        -DOQS_USE_OPENSSL=ON \
        -DBUILD_SHARED_LIBS=ON \
        -DCMAKE_BUILD_TYPE=Release \
        .. \
    && ninja install \
    && ldconfig

# ---------------------------------------------------------------------------
# STAGE 2 — Production image
# ---------------------------------------------------------------------------
FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/include /usr/local/include
COPY --from=builder /usr/local/lib     /usr/local/lib
RUN ldconfig

RUN groupadd -r appuser && useradd -r -g appuser -u 8888 appuser
RUN mkdir -p /app/data /tmp/qshield && chown -R appuser:appuser /app /tmp/qshield

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py security_engine.py auth.py database.py models.py audit_store.py \
     constants.py dashboard.html ./

COPY observability/ ./observability/
COPY landing/ ./landing/

COPY providers/ ./providers/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY scripts/docker-entrypoint.sh ./scripts/docker-entrypoint.sh
COPY benchmarks/ ./benchmarks/

RUN chmod +x ./scripts/docker-entrypoint.sh && chown -R appuser:appuser /app

USER appuser

ENV PYTHONUNBUFFERED=1 \
    UVICORN_WORKERS=4 \
    UVICORN_TIMEOUT_KEEP_ALIVE=30

EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=5s --start-period=30s --retries=3 \
    CMD curl --fail --silent http://localhost:8000/health || exit 1

ENTRYPOINT ["./scripts/docker-entrypoint.sh"]
