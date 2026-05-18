#!/usr/bin/env python3
"""
ARKHE OS Substrate 216: Prometheus Metrics Exporter for Uni‑Kernel
Canon: ∞.Ω.∇+++.216.monitoring.prometheus
Função: Exporta métricas do Uni‑Kernel Polyglot para Prometheus
via endpoint /metrics no formato exposition.
"""

from prometheus_client import start_http_server, Gauge, Counter, Histogram, Info
import time
import json
import hashlib
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# MÉTRICAS PROMETHEUS
# ═══════════════════════════════════════════════════════════════

# Gauges (valores instantâneos)
uni_kernel_phi_c = Gauge(
    'arkhe_uni_kernel_phi_c',
    'Coerência global do kernel Uni‑Kernel Polyglot',
    ['substrate_id']
)

uni_registered_languages = Gauge(
    'arkhe_uni_registered_languages',
    'Número de linguagens registradas no kernel',
    ['substrate_id']
)

uni_constructs_extracted = Gauge(
    'arkhe_uni_constructs_extracted',
    'Total de constructs extraídos por linguagem',
    ['substrate_id', 'language']
)

# Counters (valores acumulativos)
uni_parse_attempts = Counter(
    'arkhe_uni_parse_attempts_total',
    'Total de tentativas de parse',
    ['substrate_id', 'language', 'parse_mode']  # kernel/user/hybrid
)

uni_parse_success = Counter(
    'arkhe_uni_parse_success_total',
    'Total de parses bem-sucedidos',
    ['substrate_id', 'language', 'parse_mode']
)

uni_security_violations = Counter(
    'arkhe_uni_security_violations_total',
    'Total de violações de segurança detectadas',
    ['substrate_id', 'language', 'violation_type', 'severity']
)

uni_tokens_generated = Counter(
    'arkhe_uni_tokens_generated_total',
    'Total de Tokens Arkhe gerados',
    ['substrate_id', 'language', 'construct_type']
)

uni_bus_messages_published = Counter(
    'arkhe_uni_bus_messages_published_total',
    'Total de mensagens publicadas no Bus V3',
    ['substrate_id', 'channel']
)

uni_bus_messages_consumed = Counter(
    'arkhe_uni_bus_messages_consumed_total',
    'Total de mensagens consumidas do Bus V3',
    ['substrate_id', 'channel']
)

# Histograms (distribuições)
uni_parse_duration = Histogram(
    'arkhe_uni_parse_duration_seconds',
    'Duração do parsing em segundos',
    ['substrate_id', 'language', 'parse_mode'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

uni_token_generation_duration = Histogram(
    'arkhe_uni_token_generation_duration_seconds',
    'Duração da geração de tokens em segundos',
    ['substrate_id', 'language'],
    buckets=[0.0001, 0.0005, 0.001, 0.0025, 0.005, 0.01, 0.025]
)

# Info (metadados)
uni_kernel_info = Info(
    'arkhe_uni_kernel_info',
    'Metadados do kernel Uni‑Kernel Polyglot',
    ['substrate_id', 'kernel_version', 'module_version']
)

# ═══════════════════════════════════════════════════════════════
# EXPORTADOR DE MÉTRICAS
# ═══════════════════════════════════════════════════════════════

class UniKernelMetricsExporter:
    """Exporta métricas do Uni‑Kernel para Prometheus."""

    def __init__(self, substrate_id: str = "216-KM", port: int = 9091):
        self.substrate_id = substrate_id
        self.port = port
        self._last_kernel_stats: Optional[Dict] = None

        # Inicializar info do kernel
        uni_kernel_info.labels(
            substrate_id=substrate_id,
            kernel_version="6.8",
            module_version="216-KM-v1.0.0"
        ).info({
            "canonical_seal": "d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5",
            "supported_languages": "19",
            "supported_engines": "tree-sitter,antlr4,regex"
        })

    def start_server(self):
        """Inicia servidor HTTP para métricas Prometheus."""
        start_http_server(self.port)
        logger.info(f"📊 Prometheus metrics server started on port {self.port}")

    def update_kernel_stats(self, stats: Dict):
        """Atualiza métricas a partir de stats do kernel."""
        self._last_kernel_stats = stats

        # Atualizar gauges
        uni_kernel_phi_c.labels(substrate_id=self.substrate_id).set(
            stats.get("kernel_phi_c", 1.0)
        )
        uni_registered_languages.labels(substrate_id=self.substrate_id).set(
            stats.get("languages_registered", 0)
        )

        # Atualizar constructs por linguagem
        for lang, count in stats.get("constructs_by_language", {}).items():
            uni_constructs_extracted.labels(
                substrate_id=self.substrate_id,
                language=lang
            ).set(count)

    def record_parse_attempt(
        self,
        language: str,
        parse_mode: str,
        success: bool,
        duration_seconds: float,
        phi_c: float,
        constructs: int,
        violations: int,
        tokens: int
    ):
        """Registra métricas de uma tentativa de parse."""
        # Incrementar counters de tentativas/sucesso
        uni_parse_attempts.labels(
            substrate_id=self.substrate_id,
            language=language,
            parse_mode=parse_mode
        ).inc()

        if success:
            uni_parse_success.labels(
                substrate_id=self.substrate_id,
                language=language,
                parse_mode=parse_mode
            ).inc()

        # Registrar duração do histogram
        uni_parse_duration.labels(
            substrate_id=self.substrate_id,
            language=language,
            parse_mode=parse_mode
        ).observe(duration_seconds)

        # Registrar violações por tipo (mock: distribuir igualmente)
        for i in range(violations):
            violation_type = f"type_{i % 5}"
            severity = ["critical", "high", "medium", "low"][i % 4]
            uni_security_violations.labels(
                substrate_id=self.substrate_id,
                language=language,
                violation_type=violation_type,
                severity=severity
            ).inc()

        # Registrar tokens por tipo de construct (mock)
        construct_types = ["function", "transaction", "query", "api_call", "crypto_op"]
        for i in range(tokens):
            ct = construct_types[i % len(construct_types)]
            uni_tokens_generated.labels(
                substrate_id=self.substrate_id,
                language=language,
                construct_type=ct
            ).inc()

    def record_bus_message(self, channel: str, published: bool = True):
        """Registra mensagem do Bus V3."""
        if published:
            uni_bus_messages_published.labels(
                substrate_id=self.substrate_id,
                channel=channel
            ).inc()
        else:
            uni_bus_messages_consumed.labels(
                substrate_id=self.substrate_id,
                channel=channel
            ).inc()

    def record_token_generation(self, language: str, duration_seconds: float):
        """Registra duração da geração de tokens."""
        uni_token_generation_duration.labels(
            substrate_id=self.substrate_id,
            language=language
        ).observe(duration_seconds)

# ═══════════════════════════════════════════════════════════════
# DEMONSTRAÇÃO
# ═══════════════════════════════════════════════════════════════

def demonstrate_metrics():
    """Demonstra exportação de métricas para Prometheus."""
    print(f"\n📊 Demonstrando Exportador de Métricas Prometheus")
    print(f"   Substrate 216: Uni‑Kernel Polyglot\n")

    # Iniciar servidor de métricas
    exporter = UniKernelMetricsExporter(substrate_id="216-KM", port=9091)
    exporter.start_server()

    # Simular atualizações de métricas
    print("🔄 Simulando atualizações de métricas...")

    # Stats do kernel
    kernel_stats = {
        "kernel_phi_c": 0.9992,
        "languages_registered": 19,
        "constructs_by_language": {
            "python": 1247, "cobol": 892, "javascript": 2156,
            "java": 1834, "rust": 567
        }
    }
    exporter.update_kernel_stats(kernel_stats)

    # Simular parses
    import random
    languages = ["python", "cobol", "javascript", "java", "rust"]
    parse_modes = ["kernel", "user"]

    for _ in range(20):
        lang = random.choice(languages)
        mode = random.choice(parse_modes)
        success = random.random() > 0.05  # 95% success rate
        duration = random.expovariate(100)  # ~10ms average
        phi_c = 0.90 + random.random() * 0.10
        constructs = random.randint(5, 50)
        violations = random.randint(0, 3)
        tokens = random.randint(10, 100)

        exporter.record_parse_attempt(
            language=lang,
            parse_mode=mode,
            success=success,
            duration_seconds=duration,
            phi_c=phi_c,
            constructs=constructs,
            violations=violations,
            tokens=tokens
        )

    # Simular mensagens do Bus V3
    for channel in ["phi_c_metrics", "security_violations", "uni_kernel_tokens"]:
        exporter.record_bus_message(channel, published=True)
        exporter.record_bus_message(channel, published=False)

    # Simular geração de tokens
    for lang in ["python", "cobol"]:
        duration = random.expovariate(1000)  # ~1ms average
        exporter.record_token_generation(lang, duration)

    print(f"✅ Métricas atualizadas")
    print(f"🔗 Acesse: http://localhost:9091/metrics")
    print(f"📊 Grafana: Configure datasource Prometheus em http://localhost:9091")

    # Manter servidor rodando por alguns segundos para demonstração
    print(f"\n⏳ Servidor de métricas rodando... (Ctrl+C para parar)")
    try:
        import time
        time.sleep(10)
    except KeyboardInterrupt:
        print(f"\n🛑 Servidor parado")

if __name__ == "__main__":
    demonstrate_metrics()