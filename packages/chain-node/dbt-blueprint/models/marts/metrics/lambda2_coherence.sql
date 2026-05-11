-- models/marts/metrics/lambda2_coherence.sql
-- Cálculo de λ₂ para todos os pipelines críticos

WITH pipeline_metrics AS (
  SELECT
    pipeline_id,
    DATE_TRUNC('hour', execution_time) as window_time,
    AVG(duration_seconds) as avg_latency,
    STDDEV(duration_seconds) as std_latency,
    COUNT(*) as throughput,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) / COUNT(*) as error_rate,
    MAX(credits_used) as max_cost,
    MIN(credits_used) as min_cost,
    MAX(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_successful_load))) as freshness_seconds
  FROM {{ ref('pipeline_audit') }}
  WHERE execution_time >= CURRENT_TIMESTAMP - INTERVAL '7 days'
  GROUP BY 1, 2
),

coherence_calc AS (
  SELECT
    pipeline_id,
    window_time,
    -- Componentes normalizados
    (1 - LEAST(std_latency / NULLIF(avg_latency, 0), 1)) as latency_stability,
    (1 - LEAST(error_rate, 1)) as reliability,
    (1 - LEAST((max_cost - min_cost) / NULLIF(AVG(credits_used), 0), 1)) as cost_efficiency,
    (1 - LEAST(freshness_seconds / 300, 1)) as freshness_score,

    -- λ₂-data final (ponderação ajustável por domínio)
    (0.30 * (1 - LEAST(std_latency / NULLIF(avg_latency, 0), 1)) +
     0.30 * LEAST(throughput / 1000, 1) +
     0.20 * (1 - LEAST(error_rate, 1)) +
     0.10 * (1 - LEAST((max_cost - min_cost) / NULLIF(AVG(credits_used), 0), 1)) +
     0.10 * (1 - LEAST(freshness_seconds / 300, 1))) as lambda2_score

  FROM pipeline_metrics
)

SELECT
  *,
  CASE
    WHEN lambda2_score >= 0.95 THEN 'COHERENT'
    WHEN lambda2_score >= 0.85 THEN 'CRITICAL'
    ELSE 'DECOHERENT'
  END as coherence_state,
  CASE
    WHEN lambda2_score >= 0.95 THEN '🟢'
    WHEN lambda2_score >= 0.85 THEN '🟡'
    ELSE '🔴'
  END as coherence_emoji
FROM coherence_calc
