# Runbook: TLS Handshake Failures

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
