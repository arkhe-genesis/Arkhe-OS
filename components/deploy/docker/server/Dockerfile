# ═══════════════════════════════════════════════════════
# ARKHE OS — Dockerfile: Server Node
# ═══════════════════════════════════════════════════════

FROM ubuntu:24.04 AS builder

# Variáveis de ambiente para build
ENV DEBIAN_FRONTEND=noninteractive
ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH \
    GO_VERSION=1.22.0

# Dependências de sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    pkg-config \
    libssl-dev \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    tar \
    clang \
    llvm \
    && rm -rf /var/lib/apt/lists/*

# Instalar Rust (Cargo)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
RUN rustup component add rustfmt clippy

# Instalar Go
RUN wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz && \
    rm go${GO_VERSION}.linux-amd64.tar.gz
ENV PATH=$PATH:/usr/local/go/bin

WORKDIR /arkhe

# Otimização de cache de dependências Go e Rust
COPY go.mod go.sum ./
RUN go mod download

COPY Cargo.toml Cargo.lock ./
# Note: Um build completo requeriria os sub-crates. Aqui abstraímos para a estrutura.

# Copiar código fonte
COPY . .

# Build Go CLI & Server
RUN cd arkhe-os && go build -o /arkhe/bin/arkhe-server ./cmd/arkhe-server

# Build Python SDK (Substrato Bridge)
RUN python3 -m venv /arkhe/venv
RUN /arkhe/venv/bin/pip install --upgrade pip
RUN /arkhe/venv/bin/pip install -r requirements.txt
RUN /arkhe/venv/bin/pip install -e .

# ───────────────────────────────────────────────────────
# Estágio de Produção
# ───────────────────────────────────────────────────────
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/arkhe/bin:/arkhe/venv/bin:$PATH"
ENV ARKHE_ENV=production

# Dependências de runtime (OpenBLAS, CUDA stubs se aplicável)
RUN apt-get update && apt-get install -y \
    libssl3 \
    ca-certificates \
    python3 \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/arkhe

# Copiar binários e ambientes virtuais
COPY --from=builder /arkhe/bin /arkhe/bin
COPY --from=builder /arkhe/venv /arkhe/venv
COPY --from=builder /arkhe/config /opt/arkhe/config

# Criar usuário não-root
RUN useradd -m -s /bin/bash arkhe && \
    chown -R arkhe:arkhe /opt/arkhe /arkhe

USER arkhe

EXPOSE 8080 9090 4971

# Healthcheck baseado em Coerência
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:9090/health/coherence || exit 1

ENTRYPOINT ["arkhe-server"]
CMD ["--config", "/opt/arkhe/config/production.yaml"]
