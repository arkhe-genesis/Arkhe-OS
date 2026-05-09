# syntax=docker/dockerfile:1.4
# Dockerfile — ARKHE OS Multi-Architecture Build
# Substrate 318: Universal Architecture Builder

# ============================================================
# STAGE 1: Builder Base (multi-arch)
# ============================================================
FROM --platform=$BUILDPLATFORM ubuntu:22.04 AS builder-base

ARG TARGETPLATFORM
ARG TARGETARCH
ARG TARGETVARIANT

# Instalar dependências de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    python3-pip \
    python3-numpy \
    python3-scipy \
    pkg-config \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Configurar Python
RUN python3 -m pip install --upgrade pip setuptools wheel

# ============================================================
# STAGE 2: Build FFI Bridges (cross-compile)
# ============================================================
FROM builder-base AS ffi-builder

ARG TARGETARCH
ARG TARGETVARIANT

# Copiar código fonte
COPY agi/system32/runtime/quantum/ /src/quantum/
COPY Makefile /src/

# Compilar para arquitetura alvo
WORKDIR /src
RUN --mount=type=cache,target=/root/.cache \
    make \
    CC="$(case $TARGETARCH in amd64) echo gcc ;; arm64) echo aarch64-linux-gnu-gcc ;; riscv64) echo riscv64-linux-gnu-gcc ;; esac)" \
    CFLAGS="-O2 -fPIC -shared -I/usr/include/python3.11" \
    LDFLAGS="-lpython3.11 -lm" \
    TARGET=build/agi_rcp_bridge.so \
    SOURCES=quantum/rcp_bridge.c

# ============================================================
# STAGE 3: Runtime Final (multi-arch)
# ============================================================
FROM ubuntu:22.04 AS runtime

ARG TARGETARCH
ARG TARGETVARIANT

# Instalar runtime dependencies apenas
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-numpy \
    python3-scipy \
    libc6 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 arkhe

# Copiar artefatos construídos
COPY --from=ffi-builder /src/build/agi_rcp_bridge.so /usr/lib/agi/system32/
COPY --from=ffi-builder /src/build/agi_omni_bridge.so /usr/lib/agi/system32/ 2>/dev/null || true

# Copiar código Python e configs
COPY agi/system32/runtime/quantum/rcp_v2_engine.py /usr/lib/agi/system32/runtime/quantum/
COPY agi/system32/config/ /etc/agi/
COPY agi/system32/MANIFEST /usr/share/doc/arkhe-agi-core/

# Configurar ambiente
ENV PYTHONPATH=/usr/lib/agi/system32/runtime/quantum:$PYTHONPATH
ENV PATH=/usr/lib/agi/system32/bin:$PATH
ENV ARKHE_ARCH=$TARGETARCH

# Volume para dados persistentes
VOLUME ["/var/spool/agi", "/var/log/agi", "/etc/agi"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "from rcp_v2_engine import RetrocausalChannel8Bit; c=RetrocausalChannel8Bit(); print('OK')" || exit 1

# Usuário não-root por segurança
USER arkhe

# Entrypoint
ENTRYPOINT ["python3", "-m", "agi.system32.runtime.quantum.rcp_v2_engine"]
CMD ["--help"]
