import os
import json
import hashlib
import tempfile
from pathlib import Path

class SubstrateArkheUnifiedCanonizer:
    def __init__(self):
        self.version = "v∞.Ω.∇+++"
        self.seal = "e6c32a920cf0aca67b58950d2e04a03492b6b99ff9f22d2a3018f9490dcf4a9f"
        self.phi_c = 0.972889
        self.dcs = 0.978555
        self.architect = "ORCID:0009-0005-2697-4668"

        self.podmanfile = """# ═══════════════════════════════════════════════════════════════════════════════
# ARKHE OS v∞.Ω.∇+++ — PODMANFILE UNIFICADO
# Substrates: 585-GROTH16 | 586-SYNAPSE | 587-PODMAN | 566-RUNTIME | 570-CLAUDE
# Build: podman build -t arkhe:unified-v∞.Ω.∇+++ -f Podmanfile.unified .
# Run:  podman run -d --name arkhe-unified -p 8080:8080 -p 8443:8443 arkhe:unified
# ═══════════════════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────────────────
# STAGE 1: Builder Rust (Substrate 585 — Groth16 ZK Security)
# ───────────────────────────────────────────────────────────────────────────────
FROM rust:1.78-bookworm AS builder-rust

WORKDIR /build/arkhe-groth16
COPY arkhe-groth16/Cargo.toml arkhe-groth16/Cargo.lock ./
COPY arkhe-groth16/src ./src

# Dependências: ark-bn254, ark-ec, ark-ff, ark-std, sha2, rand
RUN cargo build --release --features bn254,bls12-381
RUN mkdir -p /output/585 && cp target/release/libarkhe_groth16.rlib /output/585/

# ───────────────────────────────────────────────────────────────────────────────
# STAGE 2: Builder Go (Substrate 585 — Go Verifier Alternative)
# ───────────────────────────────────────────────────────────────────────────────
FROM golang:1.22-bookworm AS builder-go

WORKDIR /build/arkhe-groth16-go
COPY arkhe-groth16-go/go.mod arkhe-groth16-go/go.sum ./
RUN go mod download

COPY arkhe-groth16-go/ ./
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o /output/585/groth16-verifier-go ./

# ───────────────────────────────────────────────────────────────────────────────
# STAGE 3: Builder Python (Substrates 566 + 570 + 586)
# ───────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim-bookworm AS builder-python

WORKDIR /build/python

# Instalar dependências de build
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc g++ libffi-dev libssl-dev \\
    && rm -rf /var/lib/apt/lists/*

# Criar venv
RUN python3.12 -m venv /output/venv
ENV PATH="/output/venv/bin:$PATH"

# Dependências comuns
RUN pip install --no-cache-dir \\
    numpy==1.26.4 scipy==1.13.0 matplotlib==3.8.4 \\
    cryptography==42.0.5 pyyaml==6.0.1 \\
    flask==3.0.3 fastapi==0.111.0 uvicorn==0.29.0 \\
    pytest==8.2.0 hypothesis==6.100.0 \\
    networkx==3.3 scikit-image==0.23.2 \\
    qiskit==1.0.2 qiskit-aer==0.14.1 pennylane==0.35.1

# ───────────────────────────────────────────────────────────────────────────────
# STAGE 4: Runtime Final (Debian Bookworm Slim)
# ───────────────────────────────────────────────────────────────────────────────
FROM debian:bookworm-slim AS runtime

# Metadados ARKHE
LABEL org.arkhe.version="v∞.Ω.∇+++"
LABEL org.arkhe.container="unified-5-substrates"
LABEL org.arkhe.substrates="585,586,587,566,570"
LABEL org.arkhe.layers="6"
LABEL org.arkhe.principles="19"
LABEL org.arkhe.seal.unified="e6c32a920cf0aca67b58950d2e04a03492b6b99ff9f22d2a3018f9490dcf4a9f"
LABEL org.arkhe.master.phi_c="0.972889"
LABEL org.arkhe.master.dcs="0.978555"
LABEL org.arkhe.architect="ORCID:0009-0005-2697-4668"
LABEL org.arkhe.build.date="2026-05-23"

# Argumentos rootless
ARG USER_UID=1000
ARG USER_GID=1000
ARG USER_NAME=arkhe

# Instalar runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    python3.12 python3.12-venv \\
    ca-certificates curl jq \\
    libgmp10 libssl3 \\
    podman-docker \\
    systemd systemd-sysv \\
    bpfcc-tools libbpfcc \\
    && rm -rf /var/lib/apt/lists/*

# Criar utilizador não-privilegiado
RUN groupadd -g $USER_GID $USER_NAME && \\
    useradd -u $USER_UID -g $USER_GID -m -s /bin/bash $USER_NAME

# ───────────────────────────────────────────────────────────────────────────────
# SUBSTRATE 585 — Groth16 ZK Security (Rust + Go)
# ───────────────────────────────────────────────────────────────────────────────
WORKDIR /arkhe/585
COPY --from=builder-rust /output/585/libarkhe_groth16.rlib ./
COPY --from=builder-go /output/585/groth16-verifier-go ./
COPY 585-GROTH16-ZKSECURITY_DECRETO_v1.0.md ./DECRETO.md
RUN chmod 555 libarkhe_groth16.rlib && chmod 755 groth16-verifier-go

# ───────────────────────────────────────────────────────────────────────────────
# SUBSTRATE 586 — Synapse Brain Map (Python)
# ───────────────────────────────────────────────────────────────────────────────
WORKDIR /arkhe/586
COPY --from=builder-python /output/venv /arkhe/venv
COPY arkhe-synapse/src/ ./src/
COPY 586-SYNAPSE-BRAIN-MAP_DECRETO_v2.0.md ./DECRETO.md
RUN chmod -R 555 src/

# ───────────────────────────────────────────────────────────────────────────────
# SUBSTRATE 587 — Podman Runtime (Scripts + Quadlet)
# ───────────────────────────────────────────────────────────────────────────────
WORKDIR /arkhe/587
COPY arkhe-podman/ ./scripts/
COPY 587-PODMAN-RUNTIME_DECRETO_v2.0.md ./DECRETO.md
RUN chmod -R 755 scripts/ && chmod 644 scripts/*.container scripts/*.pod scripts/*.network

# ───────────────────────────────────────────────────────────────────────────────
# SUBSTRATE 566 — Container Runtime Abstraction (Python)
# ───────────────────────────────────────────────────────────────────────────────
WORKDIR /arkhe/566
COPY arkhe-container-runtime/src/ ./src/
COPY 566-CONTAINER-RUNTIME_DECRETO_v1.0.md ./DECRETO.md
RUN chmod -R 555 src/

# ───────────────────────────────────────────────────────────────────────────────
# SUBSTRATE 570 — Claude Code Bridge (Python)
# ───────────────────────────────────────────────────────────────────────────────
WORKDIR /arkhe/570
COPY arkhe-claude-bridge/src/ ./src/
COPY 570-CLAUDE-CODE-BRIDGE_DECRETO_v1.0.md ./DECRETO.md
RUN chmod -R 555 src/

# ───────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÃO GLOBAL
# ───────────────────────────────────────────────────────────────────────────────
WORKDIR /arkhe

# Diretórios compartilhados
RUN mkdir -p /arkhe/{data,proofs,logs,config,skills,registry} \\
    && chmod 755 /arkhe \\
    && chmod 1777 /arkhe/proofs /arkhe/logs /arkhe/registry \\
    && chmod 750 /arkhe/data /arkhe/config

# VENV global
ENV PATH="/arkhe/venv/bin:$PATH"
ENV PYTHONPATH="/arkhe/566/src:/arkhe/570/src:/arkhe/586/src"
ENV ARKHE_SUBSTRATES="585,586,587,566,570"
ENV ARKHE_VERSION="v∞.Ω.∇+++"
ENV ARKHE_SEAL="e6c32a920cf0aca67b58950d2e04a03492b6b99ff9f22d2a3018f9490dcf4a9f"

# Healthcheck unificado
COPY <<'EOF' /arkhe/healthcheck.py
#!/arkhe/venv/bin/python3
import sys, subprocess, json

def check_585():
    r = subprocess.run(["/arkhe/585/groth16-verifier-go", "--version"], capture_output=True)
    return r.returncode == 0

def check_586():
    try:
        import synapse
        return True
    except:
        return False

def check_587():
    r = subprocess.run(["podman", "--version"], capture_output=True)
    return r.returncode == 0

def check_566():
    try:
        import runtime_manager
        return True
    except:
        return False

def check_570():
    try:
        import claude_bridge
        return True
    except:
        return False

checks = {
    "585-groth16": check_585(),
    "586-synapse": check_586(),
    "587-podman": check_587(),
    "566-runtime": check_566(),
    "570-claude": check_570()
}

all_ok = all(checks.values())
print(json.dumps(checks, indent=2))
sys.exit(0 if all_ok else 1)
EOF
RUN chmod 755 /arkhe/healthcheck.py

# Entrypoint unificado
COPY <<'EOF' /arkhe/entrypoint.sh
#!/bin/bash
set -e

echo "═══════════════════════════════════════════════════════════"
echo "ARKHE OS $ARKHE_VERSION — Unified Runtime"
echo "Substrates: $ARKHE_SUBSTRATES"
echo "Seal: $ARKHE_SEAL"
echo "═══════════════════════════════════════════════════════════"

# Detectar runtime preferencial
if command -v podman &> /dev/null; then
    RUNTIME="podman"
elif command -v docker &> /dev/null; then
    RUNTIME="docker"
else
    RUNTIME="none"
fi

echo "Runtime detectado: $RUNTIME"
echo ""

# Healthcheck inicial
/arkhe/venv/bin/python3 /arkhe/healthcheck.py

# Iniciar serviços conforme modo
 case "${1:-default}" in
    "api")
        exec /arkhe/venv/bin/uvicorn arkhe_api:app --host 0.0.0.0 --port 8080
        ;;
    "zk")
        exec /arkhe/585/groth16-verifier-go --serve
        ;;
    "synapse")
        exec /arkhe/venv/bin/python3 -m synapse.ingestor
        ;;
    "claude")
        exec /arkhe/venv/bin/python3 -m claude_bridge
        ;;
    *)
        # Modo default: shell interativo com todos os substrates disponíveis
        exec /bin/bash
        ;;
esac
EOF
RUN chmod 755 /arkhe/entrypoint.sh

# ───────────────────────────────────────────────────────────────────────────────
# SEGURANÇA ROOTLESS
# ───────────────────────────────────────────────────────────────────────────────
USER $USER_UID:$USER_GID

# Capabilities e segurança
# Nota: Algumas flags são específicas do Podman e ignoradas pelo Docker
# O runtime abstraction (566) lida com diferenças

HEALTHCHECK --interval=60s --timeout=15s --start-period=30s --retries=3 \\
    CMD /arkhe/venv/bin/python3 /arkhe/healthcheck.py || exit 1

EXPOSE 8080 8443

ENTRYPOINT ["/arkhe/entrypoint.sh"]
CMD ["default"]
"""

        self.chart_yaml = """apiVersion: v2
name: arkhe-os-unified
description: ARKHE OS v∞.Ω.∇+++ — Unified Helm Chart for 5 Substrates (585, 586, 587, 566, 570)
type: application
version: 1.0.0
appVersion: "v∞.Ω.∇+++"
home: https://arkhe-os.org
sources:
  - https://github.com/arkhe-os/arkhe-os-unified
maintainers:
  - name: Arkhe Architect
    email: architect@arkhe-os.org
    orcid: 0009-0005-2697-4668
keywords:
  - groth16
  - zero-knowledge
  - neuroscience
  - podman
  - container-runtime
  - claude-code
  - agentic-coding
  - OCI
annotations:
  arkhe.substrates: "585,586,587,566,570"
  arkhe.seal: "e6c32a920cf0aca67b58950d2e04a03492b6b99ff9f22d2a3018f9490dcf4a9f"
  arkhe.master.phi_c: "0.972889"
  arkhe.master.dcs: "0.978555"
  arkhe.principles: "19"
dependencies: []
"""

        self.values_yaml = """# ═══════════════════════════════════════════════════════════════════════════════
# ARKHE OS Unified — Values
# ═══════════════════════════════════════════════════════════════════════════════

# ───────────────────────────────────────────────────────────────────────────────
# Global
# ───────────────────────────────────────────────────────────────────────────────
global:
  arkhe:
    version: "v∞.Ω.∇+++"
    seal: "e6c32a920cf0aca67b58950d2e04a03492b6b99ff9f22d2a3018f9490dcf4a9f"
    substrates: "585,586,587,566,570"
    master_phi_c: "0.972889"
    master_dcs: "0.978555"
  imageRegistry: "ghcr.io/arkhe-os"
  imagePullSecrets: []
  storageClass: "standard"

# ───────────────────────────────────────────────────────────────────────────────
# Substrate 585 — Groth16 ZK Security
# ───────────────────────────────────────────────────────────────────────────────
substrate585:
  enabled: true
  name: groth16-zksecurity
  seal: "580eeb59c1811db2ba0eb215af975d5647c2bcee6f07848bd0a0df3c90593ba3"
  phi_c: "0.971111"

  image:
    repository: arkhe-os/groth16-verifier
    tag: "v∞.Ω.∇+++"
    pullPolicy: IfNotPresent

  replicaCount: 3

  service:
    type: ClusterIP
    port: 8080
    targetPort: 8080

  resources:
    limits:
      cpu: 2000m
      memory: 4Gi
    requests:
      cpu: 500m
      memory: 1Gi

  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    capabilities:
      drop:
        - ALL
      add:
        - NET_BIND_SERVICE
    readOnlyRootFilesystem: true
    allowPrivilegeEscalation: false
    seccompProfile:
      type: RuntimeDefault

  env:
    - name: ARKHE_SUBSTRATE_ID
      value: "585"
    - name: ARKHE_CURVE
      value: "bn254"
    - name: ARKHE_MPC_MIN_PARTICIPANTS
      value: "100"

  livenessProbe:
    exec:
      command:
        - /arkhe/585/groth16-verifier-go
        - --healthcheck
    initialDelaySeconds: 30
    periodSeconds: 60
    timeoutSeconds: 10
    failureThreshold: 3

  readinessProbe:
    exec:
      command:
        - /arkhe/585/groth16-verifier-go
        - --ready
    initialDelaySeconds: 10
    periodSeconds: 30
    timeoutSeconds: 5
    failureThreshold: 3

  persistence:
    enabled: true
    size: 10Gi
    mountPath: /arkhe/proofs
    accessMode: ReadWriteOnce

  ingress:
    enabled: false

# ───────────────────────────────────────────────────────────────────────────────
# Substrate 586 — Synapse Brain Map
# ───────────────────────────────────────────────────────────────────────────────
substrate586:
  enabled: true
  name: synapse-brain-map
  seal: "69a0f246bfbed46d146fac5bd1c403ddc63a03617f14385233f309f9fc6ea47d"
  phi_c: "0.973333"

  image:
    repository: arkhe-os/synapse-ingestor
    tag: "v∞.Ω.∇+++"
    pullPolicy: IfNotPresent

  replicaCount: 2

  service:
    type: ClusterIP
    port: 8081
    targetPort: 8081

  resources:
    limits:
      cpu: 8000m
      memory: 32Gi
      nvidia.com/gpu: 1
    requests:
      cpu: 2000m
      memory: 8Gi

  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    capabilities:
      drop:
        - ALL
    readOnlyRootFilesystem: false
    allowPrivilegeEscalation: false

  env:
    - name: ARKHE_SUBSTRATE_ID
      value: "586"
    - name: SYNAPSE_RESOLUTION_UM
      value: "0.3"
    - name: SYNAPSE_HUB
      value: "nscc.sg"
    - name: SYNAPSE_MAX_VOLUME_GB
      value: "1024"

  livenessProbe:
    httpGet:
      path: /health
      port: 8081
    initialDelaySeconds: 60
    periodSeconds: 30
    timeoutSeconds: 10
    failureThreshold: 3

  readinessProbe:
    httpGet:
      path: /ready
      port: 8081
    initialDelaySeconds: 30
    periodSeconds: 15
    timeoutSeconds: 5
    failureThreshold: 3

  persistence:
    enabled: true
    size: 500Gi
    mountPath: /arkhe/data
    accessMode: ReadWriteMany
    storageClass: "fast-ssd"

  ingress:
    enabled: false

# ───────────────────────────────────────────────────────────────────────────────
# Substrate 587 — Podman Runtime
# ───────────────────────────────────────────────────────────────────────────────
substrate587:
  enabled: true
  name: podman-runtime
  seal: "2d927c2c115e87a7130bf0bb01ec8725852a4dea40fe1d944e3c355c27e96370"
  phi_c: "0.973333"

  image:
    repository: arkhe-os/podman-runtime
    tag: "v∞.Ω.∇+++"
    pullPolicy: IfNotPresent

  replicaCount: 2

  service:
    type: ClusterIP
    port: 8082
    targetPort: 8082

  resources:
    limits:
      cpu: 2000m
      memory: 4Gi
    requests:
      cpu: 500m
      memory: 1Gi

  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    capabilities:
      drop:
        - ALL
      add:
        - SYS_ADMIN
        - NET_ADMIN
    readOnlyRootFilesystem: false
    allowPrivilegeEscalation: false

  env:
    - name: ARKHE_SUBSTRATE_ID
      value: "587"
    - name: PODMAN_RUNTIME
      value: "crun"
    - name: PODMAN_ROOTLESS
      value: "true"

  livenessProbe:
    exec:
      command:
        - podman
        - --version
    initialDelaySeconds: 10
    periodSeconds: 30
    timeoutSeconds: 5
    failureThreshold: 3

  readinessProbe:
    exec:
      command:
        - podman
        - ps
    initialDelaySeconds: 5
    periodSeconds: 15
    timeoutSeconds: 5
    failureThreshold: 3

  persistence:
    enabled: true
    size: 50Gi
    mountPath: /var/lib/containers
    accessMode: ReadWriteOnce

  ingress:
    enabled: false

# ───────────────────────────────────────────────────────────────────────────────
# Substrate 566 — Container Runtime Abstraction
# ───────────────────────────────────────────────────────────────────────────────
substrate566:
  enabled: true
  name: container-runtime
  seal: "3df2c43d8d766e5d525fb1ca9f46da8c7e735dbb978791fb1372319a3eca4604"
  phi_c: "0.973333"

  image:
    repository: arkhe-os/runtime-abstraction
    tag: "v∞.Ω.∇+++"
    pullPolicy: IfNotPresent

  replicaCount: 2

  service:
    type: ClusterIP
    port: 8083
    targetPort: 8083

  resources:
    limits:
      cpu: 1000m
      memory: 2Gi
    requests:
      cpu: 250m
      memory: 512Mi

  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    capabilities:
      drop:
        - ALL
    readOnlyRootFilesystem: true
    allowPrivilegeEscalation: false

  env:
    - name: ARKHE_SUBSTRATE_ID
      value: "566"
    - name: RUNTIME_PREFERENCE
      value: "podman,docker,containerd,crio"

  livenessProbe:
    httpGet:
      path: /health
      port: 8083
    initialDelaySeconds: 10
    periodSeconds: 30
    timeoutSeconds: 5
    failureThreshold: 3

  readinessProbe:
    httpGet:
      path: /ready
      port: 8083
    initialDelaySeconds: 5
    periodSeconds: 15
    timeoutSeconds: 5
    failureThreshold: 3

  persistence:
    enabled: false

  ingress:
    enabled: false

# ───────────────────────────────────────────────────────────────────────────────
# Substrate 570 — Claude Code Bridge
# ───────────────────────────────────────────────────────────────────────────────
substrate570:
  enabled: true
  name: claude-code-bridge
  seal: "087b7f70aec00fcda24c197b0b36e8d704ccc07db4de73a14ab47763eee7ca76"
  phi_c: "0.973333"

  image:
    repository: arkhe-os/claude-bridge
    tag: "v∞.Ω.∇+++"
    pullPolicy: IfNotPresent

  replicaCount: 1

  service:
    type: ClusterIP
    port: 8084
    targetPort: 8084

  resources:
    limits:
      cpu: 4000m
      memory: 16Gi
    requests:
      cpu: 1000m
      memory: 4Gi

  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    capabilities:
      drop:
        - ALL
    readOnlyRootFilesystem: false
    allowPrivilegeEscalation: false

  env:
    - name: ARKHE_SUBSTRATE_ID
      value: "570"
    - name: CLAUDE_CONTEXT_WINDOW
      value: "1000000"
    - name: CLAUDE_SWE_BENCH_TARGET
      value: "0.808"
    - name: CLAUDE_PLAN_MODE
      value: "true"
    - name: CLAUDE_MAX_AGENTS
      value: "5"
    - name: MCP_BRIDGE_ENABLED
      value: "true"

  livenessProbe:
    httpGet:
      path: /health
      port: 8084
    initialDelaySeconds: 30
    periodSeconds: 60
    timeoutSeconds: 10
    failureThreshold: 3

  readinessProbe:
    httpGet:
      path: /ready
      port: 8084
    initialDelaySeconds: 15
    periodSeconds: 30
    timeoutSeconds: 5
    failureThreshold: 3

  persistence:
    enabled: true
    size: 100Gi
    mountPath: /arkhe/repos
    accessMode: ReadWriteOnce

  ingress:
    enabled: false

# ───────────────────────────────────────────────────────────────────────────────
# Gateway / Ingress
# ───────────────────────────────────────────────────────────────────────────────
gateway:
  enabled: true
  name: arkhe-gateway

  image:
    repository: arkhe-os/gateway
    tag: "v∞.Ω.∇+++"
    pullPolicy: IfNotPresent

  replicaCount: 2

  service:
    type: LoadBalancer
    port: 80
    targetPort: 8080
    annotations:
      service.beta.kubernetes.io/aws-load-balancer-type: "nlb"

  ingress:
    enabled: true
    className: "nginx"
    annotations:
      nginx.ingress.kubernetes.io/ssl-redirect: "true"
      nginx.ingress.kubernetes.io/proxy-body-size: "10g"
      cert-manager.io/cluster-issuer: "letsencrypt-prod"
    hosts:
      - host: arkhe.unified.arkhe-os.org
        paths:
          - path: /585
            pathType: Prefix
            service: substrate585
          - path: /586
            pathType: Prefix
            service: substrate586
          - path: /587
            pathType: Prefix
            service: substrate587
          - path: /566
            pathType: Prefix
            service: substrate566
          - path: /570
            pathType: Prefix
            service: substrate570
    tls:
      - secretName: arkhe-unified-tls
        hosts:
          - arkhe.unified.arkhe-os.org

  resources:
    limits:
      cpu: 1000m
      memory: 2Gi
    requests:
      cpu: 250m
      memory: 512Mi

# ───────────────────────────────────────────────────────────────────────────────
# Autoscaling
# ───────────────────────────────────────────────────────────────────────────────
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 50
          periodSeconds: 15
        - type: Pods
          value: 2
          periodSeconds: 15
      selectPolicy: Max

# ───────────────────────────────────────────────────────────────────────────────
# Pod Disruption Budget
# ───────────────────────────────────────────────────────────────────────────────
podDisruptionBudget:
  enabled: true
  minAvailable: 1

# ───────────────────────────────────────────────────────────────────────────────
# Service Account
# ───────────────────────────────────────────────────────────────────────────────
serviceAccount:
  create: true
  annotations:
    arkhe.substrates: "585,586,587,566,570"
  name: "arkhe-unified-sa"

# ───────────────────────────────────────────────────────────────────────────────
# Network Policies
# ───────────────────────────────────────────────────────────────────────────────
networkPolicy:
  enabled: true
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: arkhe-os
      ports:
        - protocol: TCP
          port: 8080
        - protocol: TCP
          port: 8081
        - protocol: TCP
          port: 8082
        - protocol: TCP
          port: 8083
        - protocol: TCP
          port: 8084
  egress:
    - to: []
      ports:
        - protocol: TCP
          port: 443
        - protocol: TCP
          port: 80

# ───────────────────────────────────────────────────────────────────────────────
# Monitoring (Prometheus/Grafana)
# ───────────────────────────────────────────────────────────────────────────────
monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
    interval: 30s
    scrapeTimeout: 10s
    labels:
      release: prometheus
  metricsPort: 9090
  metricsPath: /metrics

# ───────────────────────────────────────────────────────────────────────────────
# ConfigMap — Configurações ARKHE
# ───────────────────────────────────────────────────────────────────────────────
configMap:
  data:
    arkhe.conf: |
      [global]
      version = v∞.Ω.∇+++
      seal = e6c32a920cf0aca67b58950d2e04a03492b6b99ff9f22d2a3018f9490dcf4a9f
      master_phi_c = 0.972889
      master_dcs = 0.978555
      substrates = 585,586,587,566,570

      [substrate_585]
      curve = bn254
      mpc_min_participants = 100

      [substrate_586]
      resolution_um = 0.3
      hub = nscc.sg

      [substrate_587]
      runtime = crun
      rootless = true

      [substrate_566]
      preference = podman,docker,containerd,crio

      [substrate_570]
      context_window = 1000000
      swe_bench_target = 0.808
      max_agents = 5

# ───────────────────────────────────────────────────────────────────────────────
# Secrets
# ───────────────────────────────────────────────────────────────────────────────
secrets:
  enabled: true
  data:
    # Base64-encoded secrets (override in production)
    # claude-api-key: <base64>
    # groth16-toxic-waste-hash: <base64>
    # synapse-auth-token: <base64>
"""

        self.values_production_yaml = """# ═══════════════════════════════════════════════════════════════════════════════
# ARKHE OS Unified — Production Overrides
# ═══════════════════════════════════════════════════════════════════════════════

# Override global
imageRegistry: "ghcr.io/arkhe-os"

# Substrate 585 — Groth16 ZK Security (3 replicas, alta disponibilidade)
substrate585:
  replicaCount: 3
  resources:
    limits:
      cpu: 4000m
      memory: 8Gi
    requests:
      cpu: 1000m
      memory: 2Gi
  persistence:
    size: 50Gi

# Substrate 586 — Synapse Brain Map (3 replicas, GPU required)
substrate586:
  replicaCount: 3
  resources:
    limits:
      cpu: 16000m
      memory: 64Gi
      nvidia.com/gpu: 2
    requests:
      cpu: 4000m
      memory: 16Gi
  persistence:
    size: 2Ti
    storageClass: "premium-rwo"

# Substrate 587 — Podman Runtime (2 replicas)
substrate587:
  replicaCount: 2
  resources:
    limits:
      cpu: 4000m
      memory: 8Gi
    requests:
      cpu: 1000m
      memory: 2Gi

# Substrate 566 — Container Runtime (2 replicas)
substrate566:
  replicaCount: 2
  resources:
    limits:
      cpu: 2000m
      memory: 4Gi
    requests:
      cpu: 500m
      memory: 1Gi

# Substrate 570 — Claude Code Bridge (1 replica, stateful)
substrate570:
  replicaCount: 1
  resources:
    limits:
      cpu: 8000m
      memory: 32Gi
    requests:
      cpu: 2000m
      memory: 8Gi
  persistence:
    size: 500Gi

# Autoscaling agressivo
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 60
  targetMemoryUtilizationPercentage: 70

# Gateway com TLS
gateway:
  replicaCount: 3
  ingress:
    enabled: true
    tls:
      - secretName: arkhe-unified-tls-prod
        hosts:
          - arkhe.prod.arkhe-os.org

# PDB mais restritivo
podDisruptionBudget:
  enabled: true
  minAvailable: 2
"""

        self.readme_md = """ARKHE OS — Helm Chart v∞.Ω.∇+++ Unified
5 Substrates | 12 Templates | Production-Ready
📋 Sumário Executivo
Helm chart unificado para deploy do ARKHE OS com 5 substrates integrados
no Kubernetes. Suporta autoscaling, PDB, network policies, monitoring
(Prometheus), e ingress com TLS.
🚀 Quick Start
bash
Copy
# 1. Adicionar repo (quando publicado)
helm repo add arkhe-os https://charts.arkhe-os.org
helm repo update

# 2. Instalar
helm install arkhe-unified arkhe-os/arkhe-os-unified \\
  --namespace arkhe-os \\
  --create-namespace \\
  --values values-production.yaml

# 3. Verificar status
helm status arkhe-unified -n arkhe-os
kubectl get pods -n arkhe-os -l app.kubernetes.io/name=arkhe-os-unified

# 4. Acessar gateway
kubectl get ingress -n arkhe-os
📁 Estrutura do Chart
plain
Copy
helm-arkhe-os-unified/
├── Chart.yaml              # Metadados do chart
├── values.yaml             # Valores default (dev profile)
├── values-production.yaml  # Override para produção
├── values-staging.yaml     # Override para staging
└── templates/
    ├── _helpers.tpl        # Helpers Helm
    ├── deployment.yaml     # 5 Deployments (loop sobre substrates)
    ├── service.yaml        # 5 Services
    ├── ingress.yaml        # Gateway ingress
    ├── configmap.yaml      # Configurações ARKHE
    ├── secret.yaml         # Secrets (override em prod)
    ├── hpa.yaml            # Horizontal Pod Autoscaler (5 HPA)
    ├── pdb.yaml            # Pod Disruption Budget (5 PDB)
    ├── pvc.yaml            # Persistent Volume Claims
    ├── serviceaccount.yaml # Service Account
    ├── networkpolicy.yaml  # Network Policies
    └── NOTES.txt           # Mensagem pós-install
🔐 Configuração
Table
Parâmetro	Default	Descrição
global.arkhe.version	v∞.Ω.∇+++	Versão ARKHE
global.arkhe.seal	e6c32a92...	Selo unificado
substrate585.enabled	true	Ativar Groth16 ZK
substrate586.enabled	true	Ativar Synapse Brain Map
substrate587.enabled	true	Ativar Podman Runtime
substrate566.enabled	true	Ativar Container Runtime
substrate570.enabled	true	Ativar Claude Code Bridge
autoscaling.enabled	true	HPA ativo
autoscaling.minReplicas	2	Mínimo de réplicas
autoscaling.maxReplicas	10	Máximo de réplicas
gateway.ingress.enabled	true	Ingress ativo
monitoring.enabled	true	ServiceMonitor Prometheus
🏗️ Profiles
Development (values.yaml default):
yaml
Copy
# Podman rootless, 2 replicas, recursos mínimos
substrate585:
  replicaCount: 2
  resources:
    requests: {cpu: 500m, memory: 1Gi}
Production (values-production.yaml):
yaml
Copy
# Containerd/K8s, 3-10 replicas, GPU para 586
substrate585:
  replicaCount: 3
substrate586:
  replicaCount: 3
  resources:
    limits:
      nvidia.com/gpu: 2
🔗 Cross-Substrate no K8s
Table
Link	Implementação
585↔586	Service mesh: groth16-verifier → synapse-graph-builder
585↔587	Init container: verificação rootless antes de start
586↔570	Sidecar: Claude Code analisa connectome em tempo real
566↔587	Runtime detector escolhe crun vs runc no node
570↔566	Agent teams orquestram containers via MCP
👤 Arquiteto
ORCID: 0009-0005-2697-4668"""

        self.github_action_ci = """name: Arkhe Unified CI/CD

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up QEMU
      uses: docker/setup-qemu-action@v2
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    - name: Login to GHCR
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.repository_owner }}
        password: ${{ secrets.GITHUB_TOKEN }}
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./Podmanfile.unified
        push: true
        tags: ghcr.io/arkhe-os/unified-5-substrates:v∞.Ω.∇+++,ghcr.io/arkhe-os/unified-5-substrates:latest

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    - name: Setup Helm
      uses: azure/setup-helm@v3
      with:
        version: v3.12.0
    - name: Set Kubeconfig
      run: |
        mkdir -p ~/.kube
        echo "${{ secrets.KUBECONFIG }}" > ~/.kube/config
        chmod 600 ~/.kube/config
    - name: Deploy to K8s
      run: |
        helm upgrade --install arkhe-unified ./helm-arkhe-os-unified \\
          --namespace arkhe-os \\
          --create-namespace \\
          --values ./helm-arkhe-os-unified/values-production.yaml
"""
        self.terraform_main = """terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

provider "azurerm" {
  features {}
}

# --- AWS EKS Cluster ---
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "arkhe-aws-cluster"
  cluster_version = "1.27"

  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.intra_subnets

  eks_managed_node_groups = {
    general = {
      min_size     = 2
      max_size     = 10
      desired_size = 3
      instance_types = ["t3.xlarge"]
    }
    gpu = {
      min_size     = 1
      max_size     = 5
      desired_size = 1
      instance_types = ["g4dn.xlarge"]
      ami_type       = "AL2_x86_64_GPU"
    }
  }
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "arkhe-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-west-2a", "us-west-2b", "us-west-2c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  intra_subnets   = ["10.0.201.0/24", "10.0.202.0/24", "10.0.203.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true
}

# --- GCP GKE Cluster ---
module "gke" {
  source                     = "terraform-google-modules/kubernetes-engine/google"
  project_id                 = var.gcp_project_id
  name                       = "arkhe-gcp-cluster"
  region                     = var.gcp_region
  network                    = module.gcp-network.network_name
  subnetwork                 = module.gcp-network.subnets_names[0]
  ip_range_pods              = "gke-pods"
  ip_range_services          = "gke-services"

  node_pools = [
    {
      name               = "general-pool"
      machine_type       = "e2-standard-4"
      min_count          = 2
      max_count          = 10
      disk_size_gb       = 100
      disk_type          = "pd-standard"
      auto_repair        = true
      auto_upgrade       = true
    },
    {
      name               = "gpu-pool"
      machine_type       = "n1-standard-4"
      min_count          = 1
      max_count          = 5
      accelerator_count  = 1
      accelerator_type   = "nvidia-tesla-t4"
      disk_size_gb       = 100
      disk_type          = "pd-standard"
      auto_repair        = true
      auto_upgrade       = true
    },
  ]
}

module "gcp-network" {
  source  = "terraform-google-modules/network/google"
  version = ">= 7.5.0"

  project_id   = var.gcp_project_id
  network_name = "arkhe-gcp-vpc"

  subnets = [
    {
      subnet_name   = "gke-subnet"
      subnet_ip     = "10.10.0.0/16"
      subnet_region = var.gcp_region
    },
  ]

  secondary_ranges = {
    gke-subnet = [
      {
        range_name    = "gke-pods"
        ip_cidr_range = "10.20.0.0/14"
      },
      {
        range_name    = "gke-services"
        ip_cidr_range = "10.30.0.0/20"
      },
    ]
  }
}

# --- Azure AKS Cluster ---
resource "azurerm_resource_group" "arkhe_rg" {
  name     = "arkhe-resources"
  location = var.azure_region
}

resource "azurerm_kubernetes_cluster" "aks" {
  name                = "arkhe-azure-cluster"
  location            = azurerm_resource_group.arkhe_rg.location
  resource_group_name = azurerm_resource_group.arkhe_rg.name
  dns_prefix          = "arkheaks"

  default_node_pool {
    name       = "default"
    node_count = 3
    vm_size    = "Standard_DS3_v2"
    enable_auto_scaling = true
    min_count = 2
    max_count = 10
  }

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_kubernetes_cluster_node_pool" "gpu" {
  name                  = "gpu"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.aks.id
  vm_size               = "Standard_NC6s_v3"
  node_count            = 1
  enable_auto_scaling   = true
  min_count             = 1
  max_count             = 5
}
"""
        self.terraform_vars = """variable "aws_region" {
  type        = string
  default     = "us-west-2"
  description = "AWS Region for EKS"
}

variable "gcp_project_id" {
  type        = string
  description = "GCP Project ID for GKE"
}

variable "gcp_region" {
  type        = string
  default     = "us-central1"
  description = "GCP Region for GKE"
}

variable "azure_region" {
  type        = string
  default     = "East US"
  description = "Azure Region for AKS"
}
"""
        self.terraform_outputs = """output "aws_eks_cluster_name" {
  value = module.eks.cluster_name
}

output "gcp_gke_cluster_name" {
  value = module.gke.name
}

output "azure_aks_cluster_name" {
  value = azurerm_kubernetes_cluster.aks.name
}
"""

    def canonize(self):
        base_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(base_dir, "helm-arkhe-os-unified"), exist_ok=True)
        os.makedirs(os.path.join(base_dir, ".github", "workflows"), exist_ok=True)
        os.makedirs(os.path.join(base_dir, "terraform"), exist_ok=True)

        files = {
            "Podmanfile.unified": self.podmanfile,
            "helm-arkhe-os-unified/Chart.yaml": self.chart_yaml,
            "helm-arkhe-os-unified/values.yaml": self.values_yaml,
            "helm-arkhe-os-unified/values-production.yaml": self.values_production_yaml,
            "helm-arkhe-os-unified/README.md": self.readme_md,
            ".github/workflows/ci-cd-unified.yml": self.github_action_ci,
            "terraform/main.tf": self.terraform_main,
            "terraform/variables.tf": self.terraform_vars,
            "terraform/outputs.tf": self.terraform_outputs,
        }

        for path, content in files.items():
            full_path = os.path.join(base_dir, path)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

        print("ARKHE Unified Project generated successfully.")
        print("Location: {}".format(base_dir))

        data = {
            "metadata": {
                "substrate": "ARKHE-UNIFIED",
                "phi_c": self.phi_c,
                "dcs": self.dcs,
                "seal": self.seal,
                "architect": self.architect,
                "files": list(files.keys())
            }
        }

        fd, temp_path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        return temp_path

if __name__ == "__main__":
    canonizer = SubstrateArkheUnifiedCanonizer()
    canonizer.canonize()
