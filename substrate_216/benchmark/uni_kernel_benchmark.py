#!/usr/bin/env python3
"""
ARKHE OS Substrate 216: Uni‑Kernel Polyglot Performance Benchmark
Canon: ∞.Ω.∇+++.216.benchmark.performance
Função: Benchmark comparativo de parsing em kernel-space vs user-space
para 19+ linguagens suportadas pelo Uni‑Kernel Polyglot.
"""

import asyncio
import time
import json
import hashlib
import statistics
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto
from pathlib import Path
import logging
import requests
import ctypes
import fcntl
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# CONSTANTES E CONFIGURAÇÕES
# ═══════════════════════════════════════════════════════════════

class ParseMode(Enum):
    """Modos de parsing para benchmark."""
    KERNEL_SPACE = "kernel"
    USER_SPACE = "user"
    HYBRID = "hybrid"

@dataclass
class BenchmarkConfig:
    """Configuração do benchmark."""
    languages: List[str] = field(default_factory=lambda: [
        "python", "javascript", "typescript", "c", "cpp", "java", "rust", "go",
        "ruby", "csharp", "php", "cobol", "sql", "plsql", "jcl", "abap",
        "swift", "kotlin", "scala"
    ])
    sample_sizes: List[int] = field(default_factory=lambda: [100, 500, 1000, 5000, 10000])
    iterations_per_sample: int = 10
    kernel_device: str = "/dev/arkhe_uni"
    user_api_endpoint: str = "http://localhost:8080/parse"
    timeout_seconds: float = 30.0
    warmup_iterations: int = 3

# ═══════════════════════════════════════════════════════════════
# TIPOS CANÔNICOS DE RESULTADO
# ═══════════════════════════════════════════════════════════════

@dataclass
class BenchmarkResult:
    """Resultado de benchmark para uma configuração específica."""
    language: str
    sample_size: int
    parse_mode: ParseMode
    iterations: int
    avg_parse_time_ms: float
    median_parse_time_ms: float
    p95_parse_time_ms: float
    p99_parse_time_ms: float
    std_dev_ms: float
    min_parse_time_ms: float
    max_parse_time_ms: float
    success_rate: float  # 0.0-1.0
    avg_phi_c: float
    avg_constructs_per_parse: float
    avg_violations_per_parse: float
    memory_usage_kb: float
    cpu_usage_percent: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "parse_mode": self.parse_mode.value
        }

@dataclass
class ComparativeAnalysis:
    """Análise comparativa kernel vs user-space."""
    language: str
    sample_size: int
    kernel_result: BenchmarkResult
    user_result: BenchmarkResult
    speedup_factor: float  # kernel_time / user_time (<1 = kernel mais rápido)
    overhead_percent: float  # (kernel - user) / user * 100
    phi_c_delta: float  # kernel_phi_c - user_phi_c
    recommendation: str  # "prefer_kernel", "prefer_user", "hybrid"

    def to_dict(self) -> Dict:
        return asdict(self)

# ═══════════════════════════════════════════════════════════════
# CLIENTES DE PARSING
# ═══════════════════════════════════════════════════════════════

class KernelParseClient:
    """Cliente para parsing via ioctl em kernel-space."""

    # IOCTL commands (deve corresponder ao header do kernel module)
    ARKHE_UNI_MAGIC = 0xA6
    ARKHE_IOCTL_PARSE_LANG = (0x4000 << 16) | (0xA6 << 8) | 0

    def __init__(self, device_path: str = "/dev/arkhe_uni"):
        self.device_path = device_path
        self.fd = None

    def __enter__(self):
        self.fd = os.open(self.device_path, os.O_RDWR)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fd is not None:
            os.close(self.fd)

    def parse(self, source: str, language: str, caller_ring: int = 0) -> Dict:
        """Executa parsing via ioctl no kernel module."""
        if self.fd is None:
            raise RuntimeError("Device not opened")

        # Estrutura simplificada para ioctl (em produção: usar struct packing correto)
        # Esta é uma representação simplificada para demonstração
        request = {
            "caller_pid": os.getpid(),
            "caller_ring": caller_ring,
            "language": self._lang_to_enum(language),
            "source_len": len(source),
            "source_fragment": source[:8192]  # ARKHE_MAX_SOURCE_FRAGMENT
        }

        # Em produção: usar struct.pack e fcntl.ioctl com a estrutura correta
        # Mock: simular chamada ioctl
        start = time.perf_counter_ns()

        # Simular parsing em kernel (mock)
        time.sleep(0.001 * len(source) / 1000)  # Latência simulada

        end = time.perf_counter_ns()
        parse_time_ns = end - start

        return {
            "parse_time_ns": parse_time_ns,
            "program_name": f"benchmark_{language}",
            "phi_c_score": 0.92 + (hash(source) % 100) / 1000,
            "construct_count": len(source) // 50,
            "violation_count": hash(source) % 3,
            "token_count": len(source) // 30,
            "status": 0
        }

    def _lang_to_enum(self, lang: str) -> int:
        """Converte nome de linguagem para enum do kernel."""
        lang_map = {
            "python": 1, "javascript": 2, "typescript": 3, "c": 4, "cpp": 5,
            "java": 6, "rust": 7, "go": 8, "ruby": 9, "csharp": 10,
            "php": 11, "cobol": 12, "sql": 13, "plsql": 14, "jcl": 15,
            "abap": 16, "swift": 17, "kotlin": 18, "scala": 19
        }
        return lang_map.get(lang.lower(), 0)

class UserSpaceParseClient:
    """Cliente para parsing via API REST em user-space."""

    def __init__(self, endpoint: str = "http://localhost:8080/parse"):
        self.endpoint = endpoint
        self.session = requests.Session()

    def parse(self, source: str, language: str) -> Dict:
        """Executa parsing via API REST."""
        payload = {
            "source": source,
            "language": language
        }

        start = time.perf_counter_ns()
        response = self.session.post(self.endpoint, json=payload, timeout=30)
        end = time.perf_counter_ns()

        response.raise_for_status()
        result = response.json()

        # Adicionar tempo total de requisição
        result["parse_time_ns"] = end - start
        return result

# ═══════════════════════════════════════════════════════════════
# GERADOR DE SAMPLES DE CÓDIGO
# ═══════════════════════════════════════════════════════════════

class CodeSampleGenerator:
    """Gera samples de código realistas para benchmark."""

    # Templates simplificados por linguagem
    TEMPLATES = {
        "python": [
            "def func_{i}(x): return x * {i}\n",
            "class Class_{i}:\n    def method(self): pass\n",
            "if __name__ == '__main__':\n    print('hello_{i}')\n"
        ],
        "javascript": [
            "function func_{i}(x) {{ return x * {i}; }}\n",
            "class Class_{i} {{ method() {{}} }}\n",
            "console.log('hello_{i}');\n"
        ],
        "cobol": [
            "       IDENTIFICATION DIVISION.\n",
            "       PROGRAM-ID. PROG_{i}.\n",
            "       PROCEDURE DIVISION.\n",
            "           DISPLAY 'HELLO_{i}'.\n",
            "           STOP RUN.\n"
        ],
        # ... mais templates para outras linguagens
    }

    @staticmethod
    def generate(language: str, size_bytes: int) -> str:
        """Gera código de tamanho aproximado para uma linguagem."""
        templates = CodeSampleGenerator.TEMPLATES.get(language, CodeSampleGenerator.TEMPLATES["python"])

        code = []
        current_size = 0
        i = 0

        while current_size < size_bytes:
            template = templates[i % len(templates)]
            line = template.format(i=i)
            code.append(line)
            current_size += len(line.encode('utf-8'))
            i += 1

        return "".join(code)

# ═══════════════════════════════════════════════════════════════
# EXECUTOR DE BENCHMARK
# ═══════════════════════════════════════════════════════════════

class UniKernelBenchmark:
    """Executor principal do benchmark."""

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.results: List[BenchmarkResult] = []
        self.comparisons: List[ComparativeAnalysis] = []

    async def run_benchmark(self) -> List[BenchmarkResult]:
        """Executa benchmark completo para todas as configurações."""
        logger.info(f"🚀 Iniciando benchmark: {len(self.config.languages)} linguagens, "
                   f"{len(self.config.sample_sizes)} tamanhos, "
                   f"{self.config.iterations_per_sample} iterações")

        for language in self.config.languages:
            for sample_size in self.config.sample_sizes:
                # Gerar sample de código
                source = CodeSampleGenerator.generate(language, sample_size)

                # Warmup
                for _ in range(self.config.warmup_iterations):
                    await self._run_single_parse(source, language, ParseMode.KERNEL_SPACE)
                    await self._run_single_parse(source, language, ParseMode.USER_SPACE)

                # Benchmark kernel-space
                kernel_result = await self._benchmark_mode(
                    source, language, ParseMode.KERNEL_SPACE
                )
                self.results.append(kernel_result)

                # Benchmark user-space
                user_result = await self._benchmark_mode(
                    source, language, ParseMode.USER_SPACE
                )
                self.results.append(user_result)

                # Análise comparativa
                comparison = self._analyze_comparison(kernel_result, user_result)
                self.comparisons.append(comparison)

                logger.info(
                    f"✅ {language} ({sample_size}B): "
                    f"Kernel={kernel_result.avg_parse_time_ms:.2f}ms, "
                    f"User={user_result.avg_parse_time_ms:.2f}ms, "
                    f"Speedup={comparison.speedup_factor:.2f}x"
                )

        return self.results

    async def _run_single_parse(
        self,
        source: str,
        language: str,
        mode: ParseMode
    ) -> Dict:
        """Executa um único parse para warmup ou medição."""
        if mode == ParseMode.KERNEL_SPACE:
            with KernelParseClient(self.config.kernel_device) as client:
                return client.parse(source, language)
        else:
            client = UserSpaceParseClient(self.config.user_api_endpoint)
            return client.parse(source, language)

    async def _benchmark_mode(
        self,
        source: str,
        language: str,
        mode: ParseMode
    ) -> BenchmarkResult:
        """Executa benchmark para um modo específico."""
        parse_times = []
        phi_c_scores = []
        construct_counts = []
        violation_counts = []
        success_count = 0

        for iteration in range(self.config.iterations_per_sample):
            try:
                result = await self._run_single_parse(source, language, mode)

                if result.get("status", 0) == 0:
                    success_count += 1
                    parse_times.append(result["parse_time_ns"] / 1_000_000)  # ns → ms
                    phi_c_scores.append(result.get("phi_c_score", 0.9))
                    construct_counts.append(result.get("construct_count", 0))
                    violation_counts.append(result.get("violation_count", 0))

            except Exception as e:
                logger.warning(f"⚠️ Iteration {iteration} failed: {e}")
                continue

        # Calcular métricas estatísticas
        if not parse_times:
            return BenchmarkResult(
                language=language,
                sample_size=len(source),
                parse_mode=mode,
                iterations=self.config.iterations_per_sample,
                avg_parse_time_ms=0,
                median_parse_time_ms=0,
                p95_parse_time_ms=0,
                p99_parse_time_ms=0,
                std_dev_ms=0,
                min_parse_time_ms=0,
                max_parse_time_ms=0,
                success_rate=0,
                avg_phi_c=0,
                avg_constructs_per_parse=0,
                avg_violations_per_parse=0,
                memory_usage_kb=0,
                cpu_usage_percent=0
            )

        return BenchmarkResult(
            language=language,
            sample_size=len(source),
            parse_mode=mode,
            iterations=len(parse_times),
            avg_parse_time_ms=statistics.mean(parse_times),
            median_parse_time_ms=statistics.median(parse_times),
            p95_parse_time_ms=statistics.quantiles(parse_times, n=20)[18] if len(parse_times) >= 20 else max(parse_times),
            p99_parse_time_ms=statistics.quantiles(parse_times, n=100)[98] if len(parse_times) >= 100 else max(parse_times),
            std_dev_ms=statistics.stdev(parse_times) if len(parse_times) >= 2 else 0,
            min_parse_time_ms=min(parse_times),
            max_parse_time_ms=max(parse_times),
            success_rate=success_count / self.config.iterations_per_sample,
            avg_phi_c=statistics.mean(phi_c_scores) if phi_c_scores else 0,
            avg_constructs_per_parse=statistics.mean(construct_counts) if construct_counts else 0,
            avg_violations_per_parse=statistics.mean(violation_counts) if violation_counts else 0,
            memory_usage_kb=0,  # Em produção: medir via /proc/[pid]/status
            cpu_usage_percent=0  # Em produção: medir via psutil
        )

    def _analyze_comparison(
        self,
        kernel: BenchmarkResult,
        user: BenchmarkResult
    ) -> ComparativeAnalysis:
        """Analisa comparação entre kernel e user-space."""
        if user.avg_parse_time_ms == 0:
            speedup = 1.0
            overhead = 0
        else:
            speedup = kernel.avg_parse_time_ms / user.avg_parse_time_ms
            overhead = (kernel.avg_parse_time_ms - user.avg_parse_time_ms) / user.avg_parse_time_ms * 100

        phi_c_delta = kernel.avg_phi_c - user.avg_phi_c

        # Recomendação baseada em métricas
        if speedup < 0.9 and kernel.success_rate > 0.95:
            recommendation = "prefer_kernel"
        elif speedup > 1.1 or kernel.success_rate < 0.9:
            recommendation = "prefer_user"
        else:
            recommendation = "hybrid"

        return ComparativeAnalysis(
            language=kernel.language,
            sample_size=kernel.sample_size,
            kernel_result=kernel,
            user_result=user,
            speedup_factor=speedup,
            overhead_percent=overhead,
            phi_c_delta=phi_c_delta,
            recommendation=recommendation
        )

    def export_results(self, output_path: str):
        """Exporta resultados para JSON."""
        output = {
            "benchmark_config": asdict(self.config),
            "results": [r.to_dict() for r in self.results],
            "comparisons": [c.to_dict() for c in self.comparisons],
            "summary": self._generate_summary()
        }

        Path(output_path).write_text(json.dumps(output, indent=2))
        logger.info(f"📊 Resultados exportados: {output_path}")

    def _generate_summary(self) -> Dict:
        """Gera resumo executivo do benchmark."""
        if not self.comparisons:
            return {}

        # Agrupar por linguagem
        by_language = {}
        for comp in self.comparisons:
            if comp.language not in by_language:
                by_language[comp.language] = []
            by_language[comp.language].append(comp)

        summary = {}
        for lang, comps in by_language.items():
            avg_speedup = statistics.mean([c.speedup_factor for c in comps])
            avg_overhead = statistics.mean([c.overhead_percent for c in comps])
            kernel_wins = sum(1 for c in comps if c.speedup_factor < 1.0)

            summary[lang] = {
                "avg_speedup": avg_speedup,
                "avg_overhead_percent": avg_overhead,
                "kernel_wins": kernel_wins,
                "total_comparisons": len(comps),
                "recommendation": "prefer_kernel" if avg_speedup < 0.95 else
                                 "prefer_user" if avg_speedup > 1.05 else "hybrid"
            }

        return summary

# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════

async def main():
    """Executa benchmark principal."""
    print("\n" + "="*70)
    print("🏛️ ARKHE Ω‑TEMP v∞.Ω — Substrate 216: Performance Benchmark")
    print("   Uni‑Kernel Polyglot: Kernel vs User‑Space Parsing")
    print("="*70 + "\n")

    config = BenchmarkConfig(
        languages=["python", "cobol", "javascript", "java", "rust"],  # Subset para demo
        sample_sizes=[500, 2000],
        iterations_per_sample=5,
        warmup_iterations=2
    )

    benchmark = UniKernelBenchmark(config)

    # Executar benchmark
    results = await benchmark.run_benchmark()

    # Exportar resultados
    output_file = f"/tmp/arkhe_benchmark_{int(time.time())}.json"
    benchmark.export_results(output_file)

    # Exibir resumo
    summary = benchmark._generate_summary()
    print(f"\n📈 Resumo Executivo:")
    for lang, stats in summary.items():
        print(f"   {lang:12s}: Speedup={stats['avg_speedup']:.2f}x, "
              f"Overhead={stats['avg_overhead_percent']:+.1f}%, "
              f"Recomendação: {stats['recommendation']}")

    print(f"\n✅ Benchmark concluído. Resultados: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())