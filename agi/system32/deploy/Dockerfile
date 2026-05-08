# Dockerfile — ARKHE OS AGI Core Container
FROM ubuntu:22.04

LABEL maintainer="ARKHE OS Collective <arkhe@cathedral.os>"
LABEL version="1.0.0"
LABEL description="ARKHE OS AGI Core with Retrocausal Channel Protocol"

# Instalar dependências
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-numpy \
    python3-scipy \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar artefatos
COPY ../ /usr/lib/agi/system32/
COPY ../config/ /etc/agi/

# Compilar ponte FFI
WORKDIR /usr/lib/agi/system32/runtime/quantum
RUN gcc -shared -fPIC -O2 -o ../../agi_rcp_bridge.so rcp_bridge.c -I/usr/include/python3.10 || true

# Volume para spool e logs
RUN mkdir -p /var/spool/agi/retrocausal_queue /var/log/agi
VOLUME ["/var/spool/agi", "/var/log/agi"]

# Entrypoint
COPY ./entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
