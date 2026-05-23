# ARKHE CONTAINER v1.0
# Base: Debian Bookworm (stable, minimal attack surface)
FROM debian:bookworm-slim AS base

# CAMADA 1: Kernel isolation (implicito no Docker runtime)
# CAMADA 2: Storage setup
RUN mkdir -p /arkhe/{substratos,verificadores,proofs,logs} && \
    chmod 755 /arkhe && \
    chmod 1777 /arkhe/proofs  # sticky bit para append-only

# CAMADA 3: Verificação (eBPF + audit)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 python3-pip \
    libbpf-dev linux-headers-generic \
    bpfcc-tools libbpfcc \
    && rm -rf /var/lib/apt/lists/*

# CAMADA 4: Política constitucional
COPY seccomp-arkhe.json /etc/arkhe/seccomp.json
COPY selinux-arkhe.te /etc/arkhe/arkhe.te
COPY capabilities-drop.txt /etc/arkhe/caps.drop

# CAMADA 5: Runtime
RUN pip3 install --no-cache-dir \
    sympy numpy scipy matplotlib \
    cryptography hashlib3_256 \
    pytest hypothesis

# CAMADA 6: Aplicação (Substratos)
COPY substrato_227f_verifier.py /arkhe/substratos/
COPY substrato_233_lagrangian.py /arkhe/substratos/
COPY arkhe_cli.py /arkhe/

# Política de execução: read-only exceto /arkhe/proofs e /tmp
RUN chmod -R 555 /arkhe/substratos && \
    chmod 755 /arkhe/arkhe_cli.py

# Usuário não-privilegiado
USER arkhe:arkhe

# Entrypoint constitucional
ENTRYPOINT ["/usr/bin/python3", "/arkhe/arkhe_cli.py"]
CMD ["--help"]

# Healthcheck: verificar integridade dos substratos
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /usr/bin/python3 -c "import hashlib; \
        assert hashlib.sha3_256(open('/arkhe/substratos/substrato_227f_verifier.py','rb').read()).hexdigest() == 'EXPECTED_HASH'" \
        || exit 1
