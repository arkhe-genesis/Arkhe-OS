# Runbook: Kafka Producer Timeout

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
