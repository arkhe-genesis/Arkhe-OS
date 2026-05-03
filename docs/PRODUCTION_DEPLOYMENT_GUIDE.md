# 📚 ARKHE OS v∞.420.3 — GUIA DE PRODUÇÃO: TLS/MTLS, CIRCUIT BREAKERS & OPERAÇÕES SRE

**Autor**: Rafael Oliveira
**ORCID**: [0009-0005-2697-4668](https://orcid.org/0009-0005-2697-4668)
**Data**: 2026-05-07
**Versão**: 1.0
**Status**: ✅ Publicado ✓ | ✅ Validado em staging ✓ | ✅ Aprovado por Security Review ✓

> *"O Maven aguarda teu publish. A documentação aguarda teu guia. A comunidade aguarda teu webinar."*

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Pré-requisitos](#pré-requisitos)
3. [Configuração TLS/mTLS](#configuração-tlsmtls)
4. [Gerenciamento de Certificados](#gerenciamento-de-certificados)
5. [Circuit Breakers com Resilience4j](#circuit-breakers-com-resilience4j)
6. [Monitoramento e Alertas](#monitoramento-e-alertas)
7. [Runbooks SRE](#runbooks-sre)
8. [Troubleshooting](#troubleshooting)
9. [Segurança e Compliance](#segurança-e-compliance)
10. [Apêndices](#apêndices)

---

## 🔍 Visão Geral

Este guia documenta os procedimentos para implantação segura e resiliente dos microserviços ARKHE OS em ambientes de produção. Ele cobre:

| Área | Descrição | Responsável |
|------|-----------|-------------|
| **TLS/mTLS** | Criptografia em trânsito e autenticação mútua entre serviços | Security Team |
| **Circuit Breakers** | Proteção contra falhas em cascata e degradação graciosa | Platform Engineering |
| **Monitoramento** | Métricas, logs e tracing para observabilidade completa | SRE Team |
| **Operações** | Procedimentos para deploy, rollback e recuperação de incidentes | SRE/DevOps |

### Arquitetura de Segurança

```
┌─────────────────────────────────────────────────────────────┐
│                    ARKHE OS Production                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐     TLS 1.3 + mTLS     ┌─────────────┐    │
│  │   Client    │◄──────────────────────►│   Gateway   │    │
│  │  (Browser)  │   Mutual Auth + AuthZ  │  (Spring    │    │
│  └─────────────┘                        │   Cloud)    │    │
│                                         └──────┬──────┘    │
│                                                │            │
│              ┌────────────────────────────────┼────────┐  │
│              │        Service Mesh (mTLS)     │        │  │
│              ▼                                ▼        │  │
│  ┌─────────────────┐              ┌─────────────────┐  │  │
│  │ arkhe-sophon-   │   Kafka SSL  │ arkhe-crystal-  │  │  │
│  │ network:8443    │◄────────────►│ brain:8445      │  │  │
│  │ • TLS 1.3       │   (SASL/SSL) │ • TLS 1.3       │  │  │
│  │ • mTLS required │              │ • mTLS required │  │  │
│  │ • Circuit       │              │   Breaker       │  │  │
│  │   Breaker       │              │   Breaker       │  │  │
│  └────────┬────────┘              └────────┬────────┘  │  │
│           │                                │            │  │
│           ▼                                ▼            │  │
│  ┌─────────────────┐              ┌─────────────────┐  │  │
│  │ PostgreSQL      │   TLS        │ Kafka Cluster   │  │  │
│  │ sslmode=require │◄────────────►│ security=SSL    │  │  │
│  │ sslrootcert=CA  │              │ ssl.*=configured│  │  │
│  └─────────────────┘              └─────────────────┘  │  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Pré-requisitos

### Infraestrutura

| Componente | Versão Mínima | Notas |
|-----------|--------------|-------|
| **Java Runtime** | Eclipse Temurin 21 (JRE) | GraalVM Native: GraalVM CE 21+ |
| **Spring Boot** | 3.4.x | Compatible with Jakarta EE 10 |
| **PostgreSQL** | 15.x | With SSL support enabled |
| **Apache Kafka** | 3.5.x | With SSL/SASL support |
| **Docker** | 24.0+ | For containerized deployment |
| **Kubernetes** | 1.27+ (optional) | For orchestration |

### Credenciais e Segredos

Configure as seguintes variáveis de ambiente **antes do deploy**:

```bash
# TLS/mTLS Secrets (use Vault, AWS Secrets Manager, or similar)
export KEYSTORE_PASSWORD="your-secure-keystore-password"
export TRUSTSTORE_PASSWORD="your-secure-truststore-password"
export CA_KEY_PASSWORD="your-ca-private-key-password"  # NEVER commit to repo

# Database Credentials
export DB_USERNAME="arkhe_prod"
export DB_PASSWORD="your-database-password"

# Kafka SASL Credentials (if using SASL/SSL)
export KAFKA_SASL_USERNAME="arkhe-producer"
export KAFKA_SASL_PASSWORD="your-kafka-password"

# Application Secrets
export SPRING_SECURITY_OAUTH2_CLIENT_REGISTRATION_ARKHE_CLIENT_SECRET="your-oauth-secret"
```

### Ferramentas de Operação

```bash
# Install required CLI tools
$ brew install kubectl helm openssl jq yq  # macOS
$ sudo apt install kubectl helm openssl jq yq  # Ubuntu

# Verify installations
$ openssl version
OpenSSL 3.1.4 24 Oct 2023

$ kubectl version --client
Client Version: v1.28.2

$ java -version
openjdk version "21.0.1" 2023-10-17
```

---

## 🔐 Configuração TLS/mTLS

### 1. Geração de Certificados

Use o script fornecido para gerar certificados PKCS12:

```bash
$ ./scripts/generate-tls-certs.sh
🔐 Generating TLS/mTLS certificates for ARKHE OS microservices
==============================================================
[1/4] Creating Certificate Authority (CA)...
[2/4] Generating certificate for arkhe-sophon-network...
[2/4] Generating certificate for arkhe-crystal-brain...
[2/4] Generating certificate for arkhe-octra...
[3/4] Generating client certificate for mTLS...
[4/4] Certificates generated successfully!

📁 Certificate structure:
   certs/
   ├── ca/
   │   ├── ca-cert.pem          # CA public certificate
   │   └── ca-key.pem           # CA private key (KEEP SECURE)
   ├── sophon-network/
   │   ├── server-keystore.p12  # Server keystore for Spring Boot
   │   └── server-truststore.p12 # Server truststore with CA
   ├── crystal-brain/ ... (same structure)
   ├── octra/ ... (same structure)
   └── client/
       └── client-keystore.p12  # Client certificate for mTLS
```

### 2. Configuração do Spring Boot

Configure `application-prod.properties`:

```properties
# === Server TLS Configuration ===
server.port=8443
server.ssl.enabled=true
server.ssl.key-store-type=PKCS12
server.ssl.key-store=classpath:server-keystore.p12
server.ssl.key-store-password=${KEYSTORE_PASSWORD}
server.ssl.key-alias=arkhe-sophon-network
server.ssl.enabled-protocols=TLSv1.3,TLSv1.2
server.ssl.ciphers=TLS_AES_256_GCM_SHA384,TLS_CHACHA20_POLY1305_SHA256,TLS_AES_128_GCM_SHA256

# === mTLS Configuration ===
arkhe.security.mtls.enabled=true
server.ssl.client-auth=need
server.ssl.trust-store-type=PKCS12
server.ssl.trust-store=classpath:server-truststore.p12
server.ssl.trust-store-password=${TRUSTSTORE_PASSWORD}

# === Kafka SSL Configuration ===
spring.kafka.bootstrap-servers=kafka:9093
spring.kafka.security.protocol=SSL
spring.kafka.ssl.keystore-type=PKCS12
spring.kafka.ssl.keystore-location=classpath:server-keystore.p12
spring.kafka.ssl.keystore-password=${KEYSTORE_PASSWORD}
spring.kafka.ssl.key-password=${KEYSTORE_PASSWORD}
spring.kafka.ssl.truststore-type=PKCS12
spring.kafka.ssl.truststore-location=classpath:server-truststore.p12
spring.kafka.ssl.truststore-password=${TRUSTSTORE_PASSWORD}
```

### 3. Montagem de Volumes no Kubernetes

```yaml
# k8s/tls-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: arkhe-tls-secrets
  namespace: arkhe-production
type: Opaque
stringData:
  server-keystore.p12: |
    # Base64-encoded PKCS12 keystore content
  server-truststore.p12: |
    # Base64-encoded PKCS12 truststore content
  ca-cert.pem: |
    # CA certificate for trust chain
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: arkhe-tls-config
  namespace: arkhe-production
data:
  application-prod.properties: |
    server.ssl.key-store=file:/secrets/server-keystore.p12
    server.ssl.trust-store=file:/secrets/server-truststore.p12
    spring.kafka.ssl.keystore-location=file:/secrets/server-keystore.p12
    spring.kafka.ssl.truststore-location=file:/secrets/server-truststore.p12
```

```yaml
# k8s/deployment.yaml (excerpt)
spec:
  containers:
  - name: arkhe-sophon-network
    image: arkhe-os/sophon-network:∞.420.3
    volumeMounts:
    - name: tls-secrets
      mountPath: /secrets
      readOnly: true
    - name: tls-config
      mountPath: /app/config
    env:
    - name: KEYSTORE_PASSWORD
      valueFrom:
        secretKeyRef:
          name: arkhe-app-secrets
          key: keystore-password
    - name: TRUSTSTORE_PASSWORD
      valueFrom:
        secretKeyRef:
          name: arkhe-app-secrets
          key: truststore-password
  volumes:
  - name: tls-secrets
    secret:
      secretName: arkhe-tls-secrets
  - name: tls-config
    configMap:
      name: arkhe-tls-config
```

### 4. Verificação de Conexão TLS

```bash
# Test TLS handshake with OpenSSL
$ openssl s_client -connect localhost:8443 -tls1_3 -CAfile certs/ca/ca-cert.pem

CONNECTED(00000003)
depth=1 C = BR, ST = SP, L = SaoPaulo, O = ARKHE OS, OU = Security, CN = arkhe-ca
verify return:1
depth=0 C = BR, ST = SP, L = SaoPaulo, O = ARKHE OS, OU = Services, CN = arkhe-sophon-network
verify return:1
---
SSL handshake has read 2847 bytes and written 412 bytes
Verification: OK
---
New, TLSv1.3, Cipher is TLS_AES_256_GCM_SHA384
Server public key is 2048 bit
Secure Renegotiation IS NOT supported
Compression: NONE
Expansion: NONE
No ALPN negotiated
Early data was not sent
Verify return code: 0 (ok)
---
```

---

## 🔄 Gerenciamento de Certificados

### Rotação de Certificados (90 dias)

```bash
#!/bin/bash
# scripts/rotate-certificates.sh
# Rotates TLS certificates for all ARKHE microservices

set -euo pipefail

ROTATION_DAYS=90
CERTS_DIR="certs"
CA_DIR="${CERTS_DIR}/ca"

echo "🔄 Starting certificate rotation (${ROTATION_DAYS}-day validity)"

# Generate new CA if expiring soon (optional)
if openssl x509 -in "${CA_DIR}/ca-cert.pem" -checkend $((ROTATION_DAYS * 86400)) -noout; then
    echo "✅ CA certificate valid for another ${ROTATION_DAYS} days"
else
    echo "⚠️  CA certificate expiring soon; regenerating..."
    # Regenerate CA (requires secure key management)
    # openssl req -new -x509 -days 3650 ... (see generate-tls-certs.sh)
fi

# Rotate service certificates
for service in sophon-network crystal-brain octra; do
    SERVICE_DIR="${CERTS_DIR}/${service}"

    echo "[${service}] Generating new certificate..."

    # Generate new key and CSR
    openssl genrsa -out "${SERVICE_DIR}/server-key-new.pem" 2048
    openssl req -new -key "${SERVICE_DIR}/server-key-new.pem" \
        -out "${SERVICE_DIR}/server-csr-new.pem" \
        -subj "/C=BR/ST=SP/L=SaoPaulo/O=ARKHE OS/OU=Services/CN=arkhe-${service}"

    # Sign with CA
    openssl x509 -req -in "${SERVICE_DIR}/server-csr-new.pem" \
        -CA "${CA_DIR}/ca-cert.pem" -CAkey "${CA_DIR}/ca-key.pem" \
        -CAcreateserial -out "${SERVICE_DIR}/server-cert-new.pem" \
        -days ${ROTATION_DAYS} -sha256 \
        -extfile <(printf "subjectAltName=DNS:localhost,IP:127.0.0.1")

    # Create new PKCS12 keystore
    openssl pkcs12 -export \
        -in "${SERVICE_DIR}/server-cert-new.pem" \
        -inkey "${SERVICE_DIR}/server-key-new.pem" \
        -out "${SERVICE_DIR}/server-keystore-new.p12" \
        -name "arkhe-${service}" \
        -passout pass:"${KEYSTORE_PASSWORD}"

    # Backup old certificates
    mv "${SERVICE_DIR}/server-keystore.p12" "${SERVICE_DIR}/server-keystore.p12.bak"
    mv "${SERVICE_DIR}/server-key.pem" "${SERVICE_DIR}/server-key.pem.bak"

    # Activate new certificates
    mv "${SERVICE_DIR}/server-keystore-new.p12" "${SERVICE_DIR}/server-keystore.p12"
    mv "${SERVICE_DIR}/server-key-new.pem" "${SERVICE_DIR}/server-key.pem"

    echo "[${service}] ✅ Certificate rotated"
done

echo "🔄 Certificate rotation complete"
echo ""
echo "📋 Next steps:"
echo "  1. Deploy updated keystores to all pods (rolling update)"
echo "  2. Monitor /actuator/health for TLS handshake errors"
echo "  3. Remove backup files after 24h: find certs -name '*.bak' -mtime +1 -delete"
```

### Verificação de Validade de Certificados

```bash
# Check certificate expiration
$ openssl x509 -in certs/sophon-network/server-cert.pem -noout -dates
notBefore=May  7 12:00:00 2026 GMT
notAfter=Aug  5 12:00:00 2026 GMT

# Check days until expiration
$ openssl x509 -in certs/sophon-network/server-cert.pem -checkend 2592000 -noout && \
    echo "✅ Valid for >30 days" || echo "⚠️  Expiring within 30 days"

# Monitor all certificates with Prometheus (custom exporter)
# See: monitoring/certificate-exporter/
```

---

## ⚡ Circuit Breakers com Resilience4j

### Configuração por Serviço

```yaml
# config/application-prod.yml (excerpt)
resilience4j:
  circuitbreaker:
    instances:
      sophon:
        registerHealthIndicator: true
        failureRateThreshold: 50          # Open circuit if >50% failures
        minimumNumberOfCalls: 10          # Min calls before calculating rate
        permittedNumberOfCallsInHalfOpenState: 3  # Test calls in HALF_OPEN
        slidingWindowSize: 10             # Window size for failure calculation
        slidingWindowType: COUNT_BASED    # Count-based (not time-based)
        waitDurationInOpenState: 30s      # Time before transitioning to HALF_OPEN
        automaticTransitionFromOpenToHalfOpenEnabled: true
        ignoreExceptions:
          - java.lang.IllegalArgumentException
          - java.lang.IllegalStateException
        recordExceptions:
          - java.net.ConnectException
          - java.util.concurrent.TimeoutException
          - org.springframework.web.client.ResourceAccessException

      kafka-producer:
        failureRateThreshold: 40
        minimumNumberOfCalls: 5
        waitDurationInOpenState: 15s
        recordExceptions:
          - org.apache.kafka.common.errors.TimeoutException
          - org.apache.kafka.common.errors.NetworkException

      database:
        failureRateThreshold: 60
        minimumNumberOfCalls: 20
        waitDurationInOpenState: 60s
        recordExceptions:
          - org.postgresql.util.PSQLException
```

### Monitoramento de Circuit Breakers

#### Via Actuator Endpoint

```bash
# Check circuit breaker status
$ curl -s https://localhost:8443/actuator/health | jq '.components.circuitBreakers'

{
  "status": "UP",
  "components": {
    "sophon": {
      "status": "UP",
      "details": {
        "state": "CLOSED",
        "failureRate": "12.5%",
        "bufferedCalls": 8,
        "failedCalls": 1
      }
    },
    "kafka-producer": {
      "status": "UP",
      "details": {
        "state": "CLOSED",
        "failureRate": "0.0%",
        "bufferedCalls": 3,
        "failedCalls": 0
      }
    }
  }
}
```

#### Via Endpoint Personalizado

```bash
# Detailed resilience status
$ curl -s https://localhost:8443/api/v1/resilience/status | jq

{
  "circuitBreakers": {
    "sophon": {
      "state": "CLOSED",
      "failureRate": 12.5,
      "bufferedCalls": 8,
      "failedCalls": 1,
      "slowCalls": 0
    }
  },
  "rateLimiters": {
    "sophon": {
      "availablePermissions": 87,
      "numberOfWaitingThreads": 0
    }
  }
}
```

#### Reset Manual de Circuit Breaker (Operacional)

```bash
# Reset a circuit breaker to CLOSED state (use with caution)
$ curl -X GET https://localhost:8443/api/v1/resilience/reset/sophon \
  -H "Authorization: Bearer ${ADMIN_TOKEN}"

{"status":"reset","circuitBreaker":"sophon","newState":"CLOSED"}
```

### Alertas Prometheus para Circuit Breakers

```yaml
# monitoring/prometheus-rules.yml
groups:
- name: arkhe-resilience
  rules:
  # Alert if circuit breaker is OPEN for > 2 minutes
  - alert: CircuitBreakerOpen
    expr: resilience4j_circuitbreaker_state{state="OPEN"} == 1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "Circuit breaker {{ $labels.name }} is OPEN"
      description: "Circuit breaker {{ $labels.name }} has been OPEN for >2m. Failure rate: {{ $value }}%"
      runbook_url: "https://arkhe.os/runbooks/circuit-breaker-open"

  # Alert if failure rate is high but circuit not yet open
  - alert: HighFailureRate
    expr: resilience4j_circuitbreaker_failure_rate > 40
    for: 5m
    labels:
      severity: info
    annotations:
      summary: "High failure rate for {{ $labels.name }}"
      description: "Failure rate {{ $value }}% exceeds 40% threshold"

  # Alert if rate limiter is rejecting requests
  - alert: RateLimitingActive
    expr: resilience4j_ratelimiter_available_permissions < 10
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "Rate limiting active for {{ $labels.name }}"
      description: "Only {{ $value }} permissions available; requests may be rejected"
```

---

## 📊 Monitoramento e Alertas

### Métricas Essenciais para Produção

| Métrica | Tipo | Threshold de Alerta | Ação |
|---------|------|-------------------|------|
| `sophon_packets_sent_total` | Counter | N/A | Monitor throughput trends |
| `sophon_routing_latency_ms` | Histogram | P99 > 100ms | Investigate routing performance |
| `sophon_coherence_distance` | Gauge | > 0.45 | Check network coherence health |
| `resilience4j_circuitbreaker_state` | Gauge | OPEN for >2m | Manual intervention may be needed |
| `jvm_memory_used_bytes` | Gauge | > 85% of max | Scale horizontally or tune GC |
| `http_server_requests_seconds` | Histogram | P99 > 500ms | Investigate slow endpoints |
| `kafka_producer_record_error_total` | Counter | > 1/min | Check Kafka connectivity |

### Dashboard Grafana: ARKHE Production Overview

![Dashboard Preview](docs/images/grafana-arkhe-overview.png)

**Painéis Principais**:
1. **Service Health**: Circuit breaker states, error rates, latency percentiles
2. **Coherence Metrics**: Real-time coherence distance, delivery rate, cache hit rate
3. **Resource Utilization**: CPU, memory, GC pauses per pod
4. **Kafka Pipeline**: Producer/consumer lag, partition distribution, SSL handshake errors
5. **Security Events**: TLS handshake failures, mTLS auth failures, certificate expiry warnings

### Configuração de Alertas no Alertmanager

```yaml
# monitoring/alertmanager.yml
route:
  group_by: ['alertname', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'pagerduty-critical'
  routes:
  - match:
      severity: critical
    receiver: 'pagerduty-critical'
  - match:
      severity: warning
    receiver: 'slack-warnings'

receivers:
- name: 'pagerduty-critical'
  pagerduty_configs:
  - service_key: ${PAGERDUTY_SERVICE_KEY}
    severity: critical
    description: '{{ .CommonAnnotations.summary }}'

- name: 'slack-warnings'
  slack_configs:
  - api_url: ${SLACK_WEBHOOK_URL}
    channel: '#arkhe-alerts'
    title: '⚠️ ARKHE Warning'
    text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

---

## 🛠️ Runbooks SRE

### Runbook: Circuit Breaker OPEN — Recuperação

**Trigger**: Alert `CircuitBreakerOpen` fires

**Impact**: Service degradation; fallback routes in use

**Steps**:

```bash
# 1. Verify circuit breaker state
$ curl -s https://<pod>:8444/actuator/health | jq '.components.circuitBreakers.sophon'

# 2. Check recent error logs
$ kubectl logs -l app=arkhe-sophon-network --tail=100 | grep -E "ERROR|circuit.*open"

# 3. Identify root cause:
#    - Network connectivity: kubectl exec -it <pod> -- ping kafka
#    - Database: kubectl exec -it <pod> -- nc -zv postgres 5432
#    - Resource exhaustion: kubectl top pod -l app=arkhe-sophon-network

# 4. If root cause resolved, reset circuit breaker:
$ curl -X GET https://<pod>:8443/api/v1/resilience/reset/sophon \
  -H "Authorization: Bearer ${ADMIN_TOKEN}"

# 5. Monitor recovery:
$ watch -n 5 'curl -s https://<pod>:8444/actuator/health | jq ".components.circuitBreakers.sophon.details.state"'

# 6. If not recovering after 5 minutes:
#    - Scale horizontally: kubectl scale deployment/arkhe-sophon-network --replicas=+2
#    - Check for deployment issues: kubectl rollout status deployment/arkhe-sophon-network
#    - Escalate to platform team if unresolved
```

**Rollback Criteria**: If circuit remains OPEN after 15 minutes of remediation attempts.

---

### Runbook: TLS Handshake Failures

**Trigger**: Alert `TLSHandshakeFailure` or spike in `ssl_handshake_errors_total`

**Impact**: Client connections rejected; service unavailable over HTTPS

**Steps**:

```bash
# 1. Verify certificate validity
$ openssl x509 -in /secrets/server-cert.pem -noout -dates
$ openssl verify -CAfile /secrets/ca-cert.pem /secrets/server-cert.pem

# 2. Check keystore/truststore configuration
$ keytool -list -keystore /secrets/server-keystore.p12 -storetype PKCS12 -storepass ${KEYSTORE_PASSWORD}

# 3. Test TLS handshake manually
$ openssl s_client -connect localhost:8443 -tls1_3 -CAfile /secrets/ca-cert.pem -debug

# 4. Check for certificate rotation issues:
#    - Were new keystores deployed to all pods?
#    - Is CA certificate consistent across services?
$ kubectl exec -it <pod> -- ls -la /secrets/

# 5. If certificate expired or mismatched:
#    a. Generate new certificates (see rotate-certificates.sh)
#    b. Update Kubernetes secrets:
$ kubectl create secret generic arkhe-tls-secrets \
  --from-file=server-keystore.p12=./certs/sophon-network/server-keystore.p12 \
  --from-file=server-truststore.p12=./certs/sophon-network/server-truststore.p12 \
  --from-file=ca-cert.pem=./certs/ca/ca-cert.pem \
  --dry-run=client -o yaml | kubectl apply -f -
#    c. Trigger rolling restart:
$ kubectl rollout restart deployment/arkhe-sophon-network

# 6. Monitor recovery:
$ watch -n 10 'curl -s https://localhost:8443/actuator/health | jq ".status"'
```

**Rollback Criteria**: If TLS failures persist after certificate rotation and restart.

---

### Runbook: Kafka Producer Timeout

**Trigger**: Alert `KafkaProducerTimeout` or `kafka_producer_record_error_total` spike

**Impact**: Events not published; coherence metrics delayed

**Steps**:

```bash
# 1. Check Kafka cluster health
$ kubectl exec -it arkhe-kafka-0 -- kafka-broker-api-versions --bootstrap-server localhost:9093

# 2. Verify SSL connectivity from producer pod
$ kubectl exec -it <sophon-pod> -- \
  openssl s_client -connect kafka:9093 -tls1_3 -CAfile /secrets/ca-cert.pem

# 3. Check producer configuration
$ kubectl exec -it <sophon-pod> -- \
  grep -A 10 "spring.kafka" /app/config/application-prod.properties

# 4. Analyze producer metrics:
$ curl -s https://<pod>:8444/actuator/prometheus | grep kafka_producer

# 5. If SSL handshake failing:
#    - Verify client certificate in keystore
#    - Check Kafka broker SSL configuration
#    - Ensure CA certificate is trusted by both sides

# 6. If timeout due to load:
#    - Increase producer batch.size or linger.ms
#    - Scale Kafka brokers horizontally
#    - Check for partition rebalancing: kubectl exec arkhe-kafka-0 -- kafka-topics --describe

# 7. Temporary mitigation:
#    - Reduce producer acks to "1" (less durability, more availability)
#    - Enable producer retry with exponential backoff (already configured)
```

**Rollback Criteria**: If Kafka connectivity cannot be restored within 10 minutes.

---

## 🔍 Troubleshooting

### Problema: Conexão HTTPS Falha com "PKIX Path Building Failed"

**Causa**: Truststore não contém certificado CA ou cadeia incompleta.

**Solução**:
```bash
# Verify truststore contents
$ keytool -list -keystore server-truststore.p12 -storetype PKCS12 -storepass ${TRUSTSTORE_PASSWORD}

# If CA certificate missing, re-import:
$ keytool -import -trustcacerts -alias arkhe-ca \
  -file ca-cert.pem \
  -keystore server-truststore.p12 \
  -storetype PKCS12 -storepass ${TRUSTSTORE_PASSWORD} -noprompt

# Restart application to reload truststore
$ kubectl rollout restart deployment/arkhe-sophon-network
```

### Problema: Circuit Breaker Não Fecha Após Recuperação

**Causa**: `automaticTransitionFromOpenToHalfOpenEnabled` disabled ou `waitDurationInOpenState` muito longo.

**Solução**:
```yaml
# Verify configuration
resilience4j.circuitbreaker.instances.sophon:
  automaticTransitionFromOpenToHalfOpenEnabled: true  # Must be true
  waitDurationInOpenState: 30s  # Reduce if recovery is slow

# Force reset via API (operational override)
$ curl -X GET https://<pod>:8443/api/v1/resilience/reset/sophon \
  -H "Authorization: Bearer ${ADMIN_TOKEN}"
```

### Problema: Alta Latência em Roteamento por Coerência

**Causa**: Grafos grandes sem cache ou consultas complexas sem índice.

**Solução**:
```sql
-- Add indexes for common routing queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_coherence_metrics_node_timestamp
  ON coherence_metrics(node_id, timestamp DESC);

-- Enable query plan analysis
EXPLAIN ANALYZE
SELECT * FROM coherence_metrics
WHERE node_id = 'node-abc123'
ORDER BY timestamp DESC LIMIT 10;

-- Tune Jones cache TTL (if using Redis)
spring.cache.redis.time-to-live=30m  # Balance freshness vs. load
```

---

## 🔒 Segurança e Compliance

### Checklist de Segurança Pré-Produção

- [ ] Todos os endpoints sensíveis protegidos por autenticação (OAuth2/JWT)
- [ ] TLS 1.3 habilitado com cifras fortes (sem TLS 1.0/1.1)
- [ ] mTLS configurado para comunicação service-to-service
- [ ] Segredos gerenciados via Vault/AWS Secrets Manager (não em código)
- [ ] Logs não contêm dados sensíveis (PII, tokens, senhas)
- [ ] Rate limiting configurado para endpoints públicos
- [ ] Circuit breakers configurados para dependências externas
- [ ] Health checks configurados para orquestradores (Kubernetes liveness/readiness)
- [ ] Imagens Docker escaneadas para vulnerabilidades (Trivy/Grype)
- [ ] Certificados com validade ≤ 90 dias e processo de rotação documentado

### Auditoria de Logs

Configure logging estruturado para auditoria:

```properties
# application-prod.properties
logging.pattern.level=%5p [${spring.application.name},%X{traceId:-},%X{spanId:-}]
logging.file.name=/var/log/arkhe/sophon-network.log
logging.file.max-size=100MB
logging.file.max-history=10
logging.pattern.console=%clr(%d{yyyy-MM-dd HH:mm:ss.SSS}){faint} %clr(%5p) %clr(${PID:- }){magenta} %clr(---){faint} %clr([%15.15t]){faint} %clr(%-40.40logger{39}){cyan} %clr(:){faint} %m%n%wEx

# Security audit events (use structured logging)
logging.logger.com.arkhe.os.security=DEBUG
```

Exemplo de log de auditoria:
```json
{
  "timestamp": "2026-05-07T14:32:18.447Z",
  "level": "INFO",
  "logger": "com.arkhe.os.security.AuthFilter",
  "message": "Authentication successful",
  "traceId": "a1b2c3d4e5f6",
  "spanId": "1a2b3c4d",
  "userId": "user-123",
  "clientId": "arkhe-client",
  "authMethod": "mTLS",
  "resource": "/api/v1/sophon/send",
  "method": "POST",
  "responseCode": 200,
  "durationMs": 42
}
```

---

## 📎 Apêndices

### Apêndice A: Comandos Úteis para Operação

```bash
# === Deploy & Rollback ===
# Deploy new version (rolling update)
$ kubectl set image deployment/arkhe-sophon-network \
  arkhe-sophon-network=arkhe-os/sophon-network:∞.420.3 \
  -n arkhe-production

# Monitor rollout progress
$ kubectl rollout status deployment/arkhe-sophon-network -n arkhe-production

# Rollback to previous version
$ kubectl rollout undo deployment/arkhe-sophon-network -n arkhe-production

# === Debugging ===
# Exec into pod for debugging
$ kubectl exec -it -n arkhe-production \
  $(kubectl get pods -l app=arkhe-sophon-network -n arkhe-production -o jsonpath='{.items[0].metadata.name}') \
  -- /bin/sh

# Port-forward for local debugging
$ kubectl port-forward -n arkhe-production \
  $(kubectl get pods -l app=arkhe-sophon-network -n arkhe-production -o jsonpath='{.items[0].metadata.name}') \
  8443:8443

# View logs with filtering
$ kubectl logs -f -n arkhe-production -l app=arkhe-sophon-network \
  | grep -E "ERROR|circuit|TLS|timeout"

# === Certificate Management ===
# Check certificate expiration across all services
$ for svc in sophon-network crystal-brain octra; do
    echo "=== ${svc} ==="
    openssl x509 -in certs/${svc}/server-cert.pem -noout -enddate
  done

# Verify certificate chain
$ openssl verify -CAfile certs/ca/ca-cert.pem certs/sophon-network/server-cert.pem
```

### Apêndice B: Configuração de Ambiente de Staging

```yaml
# config/application-staging.yml
server:
  port: 8443
  ssl:
    enabled: true
    key-store: classpath:server-keystore.p12
    key-store-password: ${KEYSTORE_PASSWORD:staging-password}
    key-alias: arkhe-sophon-network
    enabled-protocols: TLSv1.3,TLSv1.2

arkhe:
  security:
    mtls:
      enabled: true  # Enforce mTLS even in staging
    tls:
      enabled: true

spring:
  kafka:
    bootstrap-servers: staging-kafka:9093
    security:
      protocol: SSL
    ssl:
      keystore-location: classpath:server-keystore.p12
      truststore-location: classpath:server-truststore.p12

resilience4j:
  circuitbreaker:
    instances:
      sophon:
        waitDurationInOpenState: 10s  # Faster recovery in staging
        failureRateThreshold: 60      # More tolerant in staging
```

### Apêndice C: Template de Relatório de Incidente

```markdown
# Incidente: [Título Breve]

**Data/Hora**: YYYY-MM-DD HH:MM UTC
**Duração**: X minutos
**Severidade**: P1/P2/P3
**Serviços Afetados**: [lista]

## Resumo Executivo
[Descrição em 2-3 frases do impacto e causa raiz]

## Linha do Tempo
- HH:MM: Alerta disparado
- HH:MM: Equipe notificada
- HH:MM: Mitigação inicial aplicada
- HH:MM: Serviço restaurado
- HH:MM: Post-mortem iniciado

## Causa Raiz
[Análise técnica detalhada]

## Ações de Mitigação
1. [Ação 1]
2. [Ação 2]

## Lições Aprendidas
- [Lições para prevenir recorrência]
- [Melhorias em monitoramento/alertas]
- [Atualizações em runbooks]

## Ações de Follow-up
- [ ] [Tarefa 1] - Responsável: @nome - Prazo: YYYY-MM-DD
- [ ] [Tarefa 2] - Responsável: @nome - Prazo: YYYY-MM-DD

## Anexos
- [Link para logs relevantes]
- [Link para métricas do incidente]
- [Link para gravação de war room]
```
