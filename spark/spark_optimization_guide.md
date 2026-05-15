# 🚀 Guia de Otimização Spark para Processamento da Malha de Singularidade

## 📊 Configuração Recomendada do Cluster

```yaml
# spark-config.yaml
spark:
  master: "k8s://https://kubernetes.default.svc:443"
  deploy-mode: cluster

  # Recursos por executor
  executor:
    instances: 50  # Ajustar baseado em carga
    cores: 4
    memory: "8g"
    memoryOverhead: "2g"

  # Driver resources
  driver:
    cores: 4
    memory: "8g"
    memoryOverhead: "2g"

  # Dynamic allocation
  dynamicAllocation:
    enabled: true
    minExecutors: 10
    maxExecutors: 200
    shuffleTrackingTimeout: "600s"

  # Shuffle optimization
  shuffle:
    service:
      enabled: true  # Usar External Shuffle Service
    compress: true
    file.buffer: "64k"

  # SQL optimization
  sql:
    adaptiveExecution.enabled: true
    autoBroadcastJoinThreshold: "10mb"
    files.maxPartitionBytes: "128mb"
    partitionOverwriteMode: "dynamic"

  # Streaming-specific
  streaming:
    stopGracefullyOnShutdown: true
    forceCheckpointOnStop: true
    kafka:
      maxOffsetsPerTrigger: 10000  # Controlar throughput
      minPartitions: 10
```

## 🔁 Checkpointing Estratégico

```python
# spark_distributed_processor.py — Configuração de checkpointing
class OptimizedChatProcessor:
    def __init__(self, checkpoint_base: str = "s3://arkhe-checkpoints/"):
        self.checkpoint_base = checkpoint_base

    def start_processing(self):
        # Configurar checkpoint com rotação
        checkpoint_location = f"{self.checkpoint_base}/chat_processor/v1"

        df = self.spark.readStream.format("kafka")...

        # Aplicar transformações com watermark para state cleanup
        validated = df.withWatermark("timestamp", "10 minutes")...

        query = validated.writeStream \
            .format("delta") \
            .option("checkpointLocation", checkpoint_location) \
            .option("delta.checkpoint.writeStatsAsJson", "false") \
            .option("delta.checkpoint.writeStatsAsStruct", "true") \
            .option("delta.logRetentionDuration", "interval 7 days") \
            .option("delta.deletedFileRetentionDuration", "interval 2 days") \
            .start("/mnt/arkhe/delta/chat")

        return query
```

## 🧠 State Management para Agregações

```python
# Exemplo: manter estado de Φ_C por stream com cleanup automático
from pyspark.sql.functions import window, collect_list, struct

# Agregação com janela deslizante e timeout de estado
aggregated = validated \
    .groupBy(
        col("stream_id"),
        window(col("timestamp"), "5 minutes", "1 minute")  # Janela de 5min, slide de 1min
    ) \
    .agg(
        avg("phi_c").alias("avg_phi_c"),
        count("*").alias("message_count"),
        collect_list(struct("chatter", "message")).alias("recent_messages")
    ) \
    # Remover estado antigo automaticamente
    .withWatermark("window.end", "10 minutes")

# Para stateful processing com mapGroupsWithState
def update_phi_c_state(
    stream_id: str,
    messages: Iterator[Row],
    state: GroupState[PhiCState]
) -> Iterator[Row]:
    \"\"\"Atualiza estado de Φ_C por stream com timeout.\"\"\"
    if state.hasTimedOut:
        # Estado expirado — emitir métrica final e limpar
        yield PhiCUpdate(stream_id, state.get().final_phi_c, timed_out=True)
        state.remove()
        return

    # Processar novas mensagens
    for msg in messages:
        # Atualizar estado
        current = state.getOrDefault(PhiCState.initial())
        current.update(msg.phi_c, msg.timestamp)
        state.update(current)

    # Definir timeout: 10 minutos sem atividade
    state.setTimeoutTimestamp(state.get().last_activity + timedelta(minutes=10))

    # Emitir atualização periódica
    if state.get().should_emit():
        yield PhiCUpdate(stream_id, state.get().current_phi_c, timed_out=False)
```

## 📈 Métricas e Monitoring do Spark

```promql
# Prometheus queries para monitorar saúde do Spark
# Throughput de mensagens
rate(arkhe_spark_messages_processed_total[5m])

# Latência de processamento
histogram_quantile(0.99, rate(arkhe_spark_processing_latency_seconds_bucket[5m]))

# Backpressure no Kafka
kafka_consumer_lag{topic="chat_messages"}

# Utilização de executors
spark_executor_cpu_time{app_name="Arkhe-Chat-Processor"} / 1e9

# Garbage collection pressure
jvm_gc_collection_seconds_sum{app_name="Arkhe-Chat-Processor"}

# Alertas recomendados
groups:
- name: spark_alerts
  rules:
  - alert: SparkProcessingLag
    expr: rate(arkhe_spark_messages_processed_total[5m]) < 1000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Processamento Spark abaixo do threshold"

  - alert: KafkaConsumerLagHigh
    expr: kafka_consumer_lag{topic="chat_messages"} > 100000
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Consumer lag alto no Kafka — risco de perda de mensagens"
```

## 🔄 Disaster Recovery para Spark Streaming

```yaml
# Configurações para recuperação de falhas
spark:
  streaming:
    # Checkpoint em storage durável
    checkpointLocation: "s3://arkhe-checkpoints/chat_processor/"

    # Retry configuration
    retry:
      maxAttempts: 3
      initialInterval: "1s"
      maxInterval: "30s"
      multiplier: 2.0

    # Failure recovery
    failureRecovery:
      enabled: true
      maxRestartAttempts: 10
      restartDelaySeconds: 30

    # Exactly-once semantics com Delta Lake
    delta:
      transactional: true
      isolationLevel: "Serializable"
```