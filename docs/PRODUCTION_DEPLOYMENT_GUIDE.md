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
# ARKHE OS Production Deployment Guide

## Overview

This guide details the security hardening and resilience configurations for deploying ARKHE OS microservices in a production environment (v∞.420.2+). It covers TLS/mTLS setup for secure communication, Kafka topology configurations, and Resilience4j circuit breakers to prevent cascading failures.

---

## 1. TLS and mTLS Configuration

Security in transit is strictly enforced using Transport Layer Security (TLS) and mutual TLS (mTLS) for all service-to-service communication.

### 1.1 Generating Certificates

Use the provided script (`scripts/generate-tls-certs.sh`) to generate the Certificate Authority (CA) and the necessary PKCS12 keystores/truststores.

```bash
# Generate CA, Server, and Client certificates
./scripts/generate-tls-certs.sh
```

**Directory Structure Generated:**
```
certs/
├── ca/
│   ├── ca-cert.pem          # CA public certificate
│   └── ca-key.pem           # CA private key (KEEP SECURE)
├── sophon-network/
│   ├── server-keystore.p12  # Server keystore for Spring Boot
│   └── server-truststore.p12 # Server truststore with CA
├── crystal-brain/ ...
├── octra/ ...
└── client/
    └── client-keystore.p12  # Client certificate for mTLS
```

**Security Notes:**
*   **Rotate certificates every 90 days** in production.
*   Use HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault for key management.
*   **NEVER** commit `ca-key.pem` or any private keys to version control.
*   Default password is `changeit`. Change this in production via environment variables (`KEYSTORE_PASSWORD`, `TRUSTSTORE_PASSWORD`).

### 1.2 Spring Boot Configuration for TLS/mTLS

Enable TLS and mTLS in your `application-prod.properties` (or via config server):

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
```

### 1.3 Kafka SSL Configuration

Kafka communication is secured using SSL/mTLS:

```properties
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

---

## 2. Circuit Breakers and Resilience

To ensure high availability and prevent cascading failures, Resilience4j is configured across critical paths (e.g., Sophon routing).

### 2.1 Resilience4j Configuration

Circuit breakers, rate limiters, retries, and time limiters are applied. The default configuration in `application-prod.properties` is:

```properties
# === Circuit Breaker Configuration (Example: Sophon) ===
resilience4j.circuitbreaker.instances.sophon.register-health-indicator=true
resilience4j.circuitbreaker.instances.sophon.failure-rate-threshold=50
resilience4j.circuitbreaker.instances.sophon.minimum-number-of-calls=10
resilience4j.circuitbreaker.instances.sophon.permitted-number-of-calls-in-half-open-state=3
resilience4j.circuitbreaker.instances.sophon.sliding-window-size=10
resilience4j.circuitbreaker.instances.sophon.sliding-window-type=COUNT_BASED
resilience4j.circuitbreaker.instances.sophon.wait-duration-in-open-state=30s
resilience4j.circuitbreaker.instances.sophon.automatic-transition-from-open-to-half-open-enabled=true

# === Rate Limiting ===
resilience4j.ratelimiter.instances.sophon.limit-for-period=100
resilience4j.ratelimiter.instances.sophon.limit-refresh-period=1s
resilience4j.ratelimiter.instances.sophon.timeout-duration=0
```

*   **State Transitions**:
    *   **CLOSED (Normal):** Traffic flows normally. If the failure rate exceeds 50% over a window of 10 calls, it opens.
    *   **OPEN (Failing):** Traffic is halted (fallback is executed) for 30 seconds.
    *   **HALF-OPEN (Recovery):** After 30 seconds, 3 test calls are permitted. If they succeed, the breaker closes. If they fail, it re-opens.

### 2.2 Fallback Mechanisms

Services are annotated to provide graceful degradation. For example, if the primary coherence routing graph service fails, the system will fall back to returning a default/cached route to ensure continued progress.

---

## 3. Site Reliability Engineering (SRE) Operations

### 3.1 Monitoring Circuit Breakers

Health indicators are registered with Spring Boot Actuator.

**Check Health Status:**
```bash
curl -k --cert certs/client/client-cert.pem --key certs/client/client-key.pem \
  https://localhost:8443/actuator/health
```

**View Detailed Resilience Status:**
A custom endpoint is available to inspect the specific metrics (failure rate, state, buffered calls) of all circuit breakers and rate limiters.
```bash
curl -k --cert certs/client/client-cert.pem --key certs/client/client-key.pem \
  https://localhost:8443/api/v1/resilience/status
```

### 3.2 SRE Runbooks

#### Runbook: Circuit Breaker Manual Reset
If a circuit breaker remains stuck in an `OPEN` state despite the underlying issue being resolved, you can manually reset it to `CLOSED`:

```bash
# Reset a specific circuit breaker (e.g., "sophon")
curl -k -X GET --cert certs/client/client-cert.pem --key certs/client/client-key.pem \
  https://localhost:8443/api/v1/resilience/reset/sophon
```

#### Runbook: Certificate Rotation
1.  Generate new certificates using the CA.
2.  Deploy the new `.p12` keystores/truststores to the secret store/vault.
3.  Perform a rolling restart of the microservices to pick up the new configuration. If utilizing Spring Cloud Bus, issue a refresh event.

#### Runbook: Handling mTLS Handshake Failures
*   **Symptom:** Clients receiving 401/403 or `SSLHandshakeException`.
*   **Resolution:** Verify that the client is presenting the `client-cert.pem` and that the certificate is signed by the CA present in the server's `server-truststore.p12`. Check the client certificate expiration date.

---
*End of Guide. Validated against Arkhe OS v∞.420.2.*
