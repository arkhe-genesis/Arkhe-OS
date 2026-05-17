# .github/runners/arm64-hsm/Dockerfile
FROM ubuntu:22.04-arm64

# Instalar dependências base
RUN apt-get update && apt-get install -y \
    python3.11 python3-pip git curl wget \
    build-essential libssl-dev pkg-config \
    softhsm2 libp11-kit-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar liboqs para PQC
RUN pip3 install liboqs-python cryptography

# Configurar SoftHSM para emulação PKCS#11
RUN mkdir -p /etc/softhsm /var/lib/softhsm/tokens
COPY softhsm2.conf /etc/softhsm/
RUN softhsm2-util --init-token --slot 0 --label "arkhe-ci-hsm" --pin 1234 --so-pin 1234

# Instalar runner GitHub Actions
ARG RUNNER_VERSION=2.311.0
RUN curl -L -o actions-runner-linux-arm64-${RUNNER_VERSION}.tar.gz \
    https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-arm64-${RUNNER_VERSION}.tar.gz \
    && tar xzf actions-runner-linux-arm64-${RUNNER_VERSION}.tar.gz -C /opt/actions \
    && rm actions-runner-linux-arm64-${RUNNER_VERSION}.tar.gz

# Script de entrada
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
