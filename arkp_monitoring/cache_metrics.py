#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cache_metrics.py — Métricas em tempo real do cache de dependências

Exporta métricas para Prometheus/Grafana:
• cache_hit_rate
• cache_eviction_rate
• avg_compression_ratio
• temporal_anchor_success_rate
• qip_influence_distribution
"""

from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# Métricas Prometheus
CACHE_REQUESTS = Counter(
    'arkhe_cache_requests_total',
    'Total cache requests',
    ['operation', 'result']  # get/put, hit/miss/evict
)

CACHE_SIZE = Gauge(
    'arkhe_cache_size_bytes',
    'Current cache size in bytes'
)

CACHE_COMPRESSION = Histogram(
    'arkhe_cache_compression_ratio',
    'Compression ratio achieved',
    buckets=[1.0, 1.5, 2.0, 3.0, 5.0, 10.0]
)

TEMPORAL_ANCHORS = Counter(
    'arkhe_temporal_anchors_total',
    'TemporalChain anchors created',
    ['status']  # success/failure
)

QIP_INFLUENCE = Histogram(
    'arkhe_qip_influence_score',
    'QIP influence score distribution',
    buckets=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
)

def record_cache_hit():
    CACHE_REQUESTS.labels(operation='get', result='hit').inc()

def record_cache_miss():
    CACHE_REQUESTS.labels(operation='get', result='miss').inc()

def record_eviction(count: int):
    CACHE_REQUESTS.labels(operation='evict', result='evicted').inc(count)

def record_compression(ratio: float):
    CACHE_COMPRESSION.observe(ratio)

def record_temporal_anchor(success: bool):
    status = 'success' if success else 'failure'
    TEMPORAL_ANCHORS.labels(status=status).inc()

def record_qip_influence(score: float):
    QIP_INFLUENCE.observe(score)

def start_metrics_server(port: int = 9091):
    """Inicia servidor de métricas Prometheus."""
    start_http_server(port)
    print(f"📊 Metrics server started on port {port}")
