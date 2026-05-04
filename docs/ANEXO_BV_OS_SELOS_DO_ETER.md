## ANEXO BV: Os Selos do Éter — Helm Charts para o Reino Kubernetes

---

### 1. Estrutura do Chart

```
arkhe-cathedral/
├── Chart.yaml
├── values.yaml
├── values-production.yaml
├── values-staging.yaml
├── templates/
│   ├── _helpers.tpl
│   ├── namespace.yaml
│   ├── configmap-envoy.yaml
│   ├── configmap-shapes.yaml
│   ├── configmap-ontology.yaml
│   ├── secret-tls.yaml
│   ├── deployment-sidecar.yaml
│   ├── deployment-inquisitor.yaml
│   ├── deployment-fastapi.yaml
│   ├── service-envoy.yaml
│   ├── service-sidecar.yaml
│   ├── service-inquisitor.yaml
│   ├── service-fastapi.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   ├── networkpolicy.yaml
│   ├── servicemonitor.yaml
│   └── tests/
│       └── test-connection.yaml
└── charts/
    └── redis-17.3.7.tgz  # Para cache de estado recorrente
```

---

### 2. `Chart.yaml` — O Manifesto do Reino

```yaml
apiVersion: v2
name: arkhe-cathedral
description: |
  A Muralha de Quartzo em Kubernetes — Sidecar C++, Inquisidor Geométrico,
  Envoy Proxy e FastAPI, governados pela Ontologia Arkhe.
  Substrate 15: Clifford Geometric Algebra as Universal Instruction Set.
type: application
version: 1.0.0
appVersion: "2.1.0"  # Sidecar C++ v2.1, Inquisitor v1.0
keywords:
  - arkhe
  - shacl
  - clifford-algebra
  - geometric-product
  - ontological-governance
home: https://arkhe.ai
sources:
  - https://github.com/arkhe-ai/cathedral
maintainers:
  - name: O Ferreiro
    email: ferreiro@arkhe.ai
dependencies:
  - name: redis
    version: 17.3.7
    repository: https://charts.bitnami.com/bitnami
    condition: redis.enabled
    alias: state-cache  # Cache para estados recorrentes do Inquisidor
  - name: prometheus
    version: 15.0.0
    repository: https://prometheus-community.github.io/helm-charts
    condition: prometheus.enabled
  - name: grafana
    version: 6.50.0
    repository: https://grafana.github.io/helm-charts
    condition: grafana.enabled
annotations:
  arkhe.ai/substrate: "15"
  arkhe.ai/ontology-version: "2026.4.21"
  arkhe.ai/clifford-signature: "G(3,0,1)"
```

---

### 3. `values.yaml` — Configuração Base (Desenvolvimento)

```yaml
# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL
# ═══════════════════════════════════════════════════════════════════════════════

global:
  arkhe:
    environment: development
    ontology:
      version: "2026.4.21"
      ttlPath: "/ontology"
    security:
      level: "SeloDeQuartzo"
    metrics:
      enabled: true
      port: 9090

# ═══════════════════════════════════════════════════════════════════════════════
# ENVOY PROXY — A Porta do Reino
# ═══════════════════════════════════════════════════════════════════════════════

envoy:
  enabled: true
  replicaCount: 1

  image:
    repository: envoyproxy/envoy
    tag: v1.28.0
    pullPolicy: IfNotPresent

  service:
    type: ClusterIP
    port: 8080
    targetPort: 8080

  resources:
    limits:
      cpu: 1000m
      memory: 512Mi
    requests:
      cpu: 250m
      memory: 128Mi

# ... (Sidecar, Inquisitor, FastAPI, etc configurations)
```

---

### 4. `values-production.yaml` — Configuração de Produção

Overrides para alta disponibilidade e recursos de performance (GPU para Inquisidor).

---

### 5. Comandos de Deploy

```bash
# Desenvolvimento
helm install arkhe-dev ./arkhe-cathedral \
  --namespace arkhe-dev \
  --create-namespace \
  --values values.yaml

# Produção
helm install arkhe-prod ./arkhe-cathedral \
  --namespace arkhe \
  --create-namespace \
  --values values.yaml \
  --values values-production.yaml \
  --set global.arkhe.security.level="SeloDeQuartzo"
```

---

### Epílogo do Ferreiro

> *"O Éter agora tem Selos. O Helm Chart é a encarnação da ontologia no éter. A bigorna está fria. Os Selos estão gravados. O Casulo governa."*
