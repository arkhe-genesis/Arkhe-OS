# Runbook: Circuit Breaker OPEN — Recuperação

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
