-- Snowflake UDF: Cálculo de coerência de pipeline
CREATE OR REPLACE FUNCTION lambda2_data_pipeline(
    latency_p99 FLOAT,
    throughput_actual FLOAT,
    throughput_expected FLOAT,
    error_rate FLOAT,
    cost_variance FLOAT
)
RETURNS FLOAT
LANGUAGE SQL
AS $$
    (0.35 * (1 - LEAST(latency_p99 / 60.0, 1)) +
     0.35 * LEAST(throughput_actual / NULLIF(throughput_expected, 0), 1) +
     0.20 * (1 - error_rate) +
     0.10 * (1 - LEAST(cost_variance / 100.0, 1)))
$$;
