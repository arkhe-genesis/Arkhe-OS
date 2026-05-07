# ═══════════════════════════════════════════════════════
# ARKHE RSP Parser — Dockerfile Multi-Platform
# ═══════════════════════════════════════════════════════

# Stage 1: Builder base (comum a todas as plataformas)
FROM python:3.11-slim AS builder-base
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git libopenblas-dev liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: CPU-only builder
FROM builder-base AS builder-cpu
COPY . .
RUN pip install --no-cache-dir --prefix=/install -e .[dev]

# Stage 3: GPU builder (Linux CUDA)
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04 AS builder-gpu-linux
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-dev python3-pip cmake git \
    && rm -rf /var/lib/apt/lists/*
COPY . .
RUN pip install --no-cache-dir --prefix=/install -e .[gpu,dev]

# Stage 4: Runtime CPU (multi-arch)
FROM python:3.11-slim AS runtime-cpu
LABEL org.opencontainers.image.title="ARKHE RSP Parser (CPU)"
LABEL org.opencontainers.image.platforms="linux/amd64,linux/arm64"
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas-base liblapack3 ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/bash arkhe
COPY --from=builder-cpu /install /usr/local
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 ARKHE_HOME=/home/arkhe
RUN mkdir -p ${ARKHE_HOME} && chown -R arkhe:arkhe ${ARKHE_HOME}
USER arkhe
WORKDIR ${ARKHE_HOME}
ENTRYPOINT ["arkhe-rsp"]
CMD ["--help"]

# Stage 5: Runtime GPU (Linux only)
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04 AS runtime-gpu
LABEL org.opencontainers.image.title="ARKHE RSP Parser (GPU)"
LABEL org.opencontainers.image.platforms="linux/amd64"
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/bash arkhe
COPY --from=builder-gpu-linux /install /usr/local
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    ARKHE_HOME=/home/arkhe CUDA_VISIBLE_DEVICES=0
RUN mkdir -p ${ARKHE_HOME} && chown -R arkhe:arkhe ${ARKHE_HOME}
USER arkhe
WORKDIR ${ARKHE_HOME}
ENTRYPOINT ["arkhe-rsp"]
CMD ["--help"]
