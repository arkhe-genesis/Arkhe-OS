#!/usr/bin/env python3
"""
ARKHE OS Substrate 263: Performance Benchmark & Optimization Engine
Canon: ∞.Ω.∇+++.263.performance_benchmark

Motor de benchmark, profiling e otimização de performance do Arkhe-OS.
Cobre: micronúcleo IPC, runtime WASM, criptografia PQC híbrida,
pipeline de verificação formal (Kani/TLA+), e sistema de build (Cargo/LTO).
"""

import asyncio
import hashlib
import json
import time
import statistics
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Callable
from collections import deque
import math

# ── Data Models ──

@dataclass
class BenchmarkResult:
    """Resultado de uma execução de benchmark."""
    benchmark_id: str
    subsystem: str
    metric: str
    value: float
    unit: str
    iterations: int
    samples: List[float]
    mean: float
    median: float
    stddev: float
    p95: float
    p99: float
    baseline: Optional[float]
    improvement_pct: Optional[float]
    timestamp: float

@dataclass
class OptimizationStrategy:
    """Estratégia de otimização para um subsistema."""
    strategy_id: str
    subsystem: str
    target_metric: str
    technique: str
    expected_gain_pct: float
    implementation_complexity: str  # low / medium / high
    risk_level: str  # low / medium / high
    applied: bool

@dataclass
class PerformanceProfile:
    """Perfil de performance de um subsistema."""
    profile_id: str
    subsystem: str
    bottleneck: str
    hotspot_function: Optional[str]
    cpu_utilization_pct: float
    memory_pressure_mb: float
    ipc_latency_us: Optional[float]
    throughput_ops_sec: Optional[float]
    recommendations: List[str] = field(default_factory=list)

@dataclass
class RegressionAlert:
    """Alerta de regressão de performance."""
    alert_id: str
    subsystem: str
    metric: str
    baseline_value: float
    current_value: float
    regression_pct: float
    severity: str  # critical / warning / info
    timestamp: float

@dataclass
class CanonicalBenchmark:
    """Relatório canônico de benchmark."""
    benchmark_id: str
    total_subsystems: int
    total_benchmarks: int
    total_optimizations: int
    total_regressions: int
    overall_phi_c: float
    seal: str
    timestamp: float

# ── Engine ──

class ArkhePerformanceEngine:
    """Motor de benchmark e otimização de performance do Arkhe-OS."""

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.profiles: List[PerformanceProfile] = []
        self.strategies: List[OptimizationStrategy] = []
        self.alerts: List[RegressionAlert] = []
        self._baseline_store: Dict[str, float] = {}

    def _hash(self, text: str) -> str:
        return hashlib.sha3_256(text.encode()).hexdigest()[:16]

    def _percentile(self, data: List[float], p: float) -> float:
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * p / 100
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_data[int(k)]
        return sorted_data[int(f)] * (c - k) + sorted_data[int(c)] * (k - f)

    # ═══════════════════════════════════════════════════════════
    # KERNEL IPC BENCHMARKS
    # ═══════════════════════════════════════════════════════════

    async def benchmark_kernel_ipc_latency(self, iterations: int = 10000) -> BenchmarkResult:
        """Benchmark: latência de IPC no micronúcleo multikernel."""
        samples = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            # Simulação: message-passing entre 2 cores (Barrelfish-style)
            msg = {"src": 0, "dst": 1, "payload": b"x" * 64}
            await asyncio.sleep(0)  # yield para simular context switch
            t1 = time.perf_counter()
            samples.append((t1 - t0) * 1e6)  # microseconds

        baseline = self._baseline_store.get("kernel_ipc_latency", 2.5)
        mean = statistics.mean(samples)
        improvement = ((baseline - mean) / baseline * 100) if baseline else None

        result = BenchmarkResult(
            benchmark_id=self._hash("ipc_latency"),
            subsystem="kernel",
            metric="ipc_latency",
            value=mean,
            unit="us",
            iterations=iterations,
            samples=samples[:100],
            mean=mean,
            median=statistics.median(samples),
            stddev=statistics.stdev(samples) if len(samples) > 1 else 0.0,
            p95=self._percentile(samples, 95),
            p99=self._percentile(samples, 99),
            baseline=baseline,
            improvement_pct=improvement,
            timestamp=time.time()
        )
        self.results.append(result)
        return result

    async def benchmark_kernel_ipc_throughput(self, iterations: int = 5000) -> BenchmarkResult:
        """Benchmark: throughput de mensagens IPC por segundo."""
        t0 = time.perf_counter()
        for _ in range(iterations):
            await asyncio.sleep(0)
        t1 = time.perf_counter()
        throughput = iterations / (t1 - t0)

        baseline = self._baseline_store.get("kernel_ipc_throughput", 100000)
        improvement = ((throughput - baseline) / baseline * 100) if baseline else None

        result = BenchmarkResult(
            benchmark_id=self._hash("ipc_throughput"),
            subsystem="kernel",
            metric="ipc_throughput",
            value=throughput,
            unit="msg/sec",
            iterations=iterations,
            samples=[throughput],
            mean=throughput,
            median=throughput,
            stddev=0.0,
            p95=throughput,
            p99=throughput,
            baseline=baseline,
            improvement_pct=improvement,
            timestamp=time.time()
        )
        self.results.append(result)
        return result

    # ═══════════════════════════════════════════════════════════
    # WASM RUNTIME BENCHMARKS
    # ═══════════════════════════════════════════════════════════

    async def benchmark_wasm_compile_time(self, module_size_kb: int = 1024) -> BenchmarkResult:
        """Benchmark: tempo de compilação WASM (wasm-bindgen target)."""
        # Simulação: compilação proporcional ao tamanho do módulo
        compile_time_ms = module_size_kb * 0.8 + (module_size_kb ** 0.5) * 2
        await asyncio.sleep(compile_time_ms / 1000)

        baseline = self._baseline_store.get("wasm_compile_time", 1200.0)
        improvement = ((baseline - compile_time_ms) / baseline * 100) if baseline else None

        result = BenchmarkResult(
            benchmark_id=self._hash("wasm_compile"),
            subsystem="wasm_runtime",
            metric="compile_time",
            value=compile_time_ms,
            unit="ms",
            iterations=1,
            samples=[compile_time_ms],
            mean=compile_time_ms,
            median=compile_time_ms,
            stddev=0.0,
            p95=compile_time_ms,
            p99=compile_time_ms,
            baseline=baseline,
            improvement_pct=improvement,
            timestamp=time.time()
        )
        self.results.append(result)
        return result

    async def benchmark_wasm_execution_overhead(self, iterations: int = 50000) -> BenchmarkResult:
        """Benchmark: overhead de execução WASM vs nativo."""
        # Simulação: overhead típico de 15-25% sobre nativo
        native_time_us = 0.05
        wasm_overhead_factor = 1.18
        wasm_time_us = native_time_us * wasm_overhead_factor

        samples = [wasm_time_us * (1 + (i % 5) * 0.02) for i in range(min(iterations, 100))]
        mean = statistics.mean(samples)

        baseline = self._baseline_store.get("wasm_overhead", 1.35)
        improvement = ((baseline - wasm_overhead_factor) / baseline * 100) if baseline else None

        result = BenchmarkResult(
            benchmark_id=self._hash("wasm_overhead"),
            subsystem="wasm_runtime",
            metric="execution_overhead",
            value=wasm_overhead_factor,
            unit="ratio",
            iterations=iterations,
            samples=samples,
            mean=mean,
            median=statistics.median(samples),
            stddev=statistics.stdev(samples) if len(samples) > 1 else 0.0,
            p95=self._percentile(samples, 95),
            p99=self._percentile(samples, 99),
            baseline=baseline,
            improvement_pct=improvement,
            timestamp=time.time()
        )
        self.results.append(result)
        return result

    async def benchmark_zkwasm_proof_generation(self, circuit_size: int = 1000) -> BenchmarkResult:
        """Benchmark: geração de provas zkWASM (Groth16/Bulletproofs)."""
        # Simulação: tempo quadrático no tamanho do circuito
        proof_time_ms = circuit_size * 2.5 + (circuit_size ** 1.5) * 0.1
        await asyncio.sleep(proof_time_ms / 1000)

        baseline = self._baseline_store.get("zkwasm_proof_time", 3500.0)
        improvement = ((baseline - proof_time_ms) / baseline * 100) if baseline else None

        result = BenchmarkResult(
            benchmark_id=self._hash("zkwasm_proof"),
            subsystem="wasm_runtime",
            metric="proof_generation_time",
            value=proof_time_ms,
            unit="ms",
            iterations=1,
            samples=[proof_time_ms],
            mean=proof_time_ms,
            median=proof_time_ms,
            stddev=0.0,
            p95=proof_time_ms,
            p99=proof_time_ms,
            baseline=baseline,
            improvement_pct=improvement,
            timestamp=time.time()
        )
        self.results.append(result)
        return result

    # ═══════════════════════════════════════════════════════════
    # PQC CRYPTO BENCHMARKS
    # ═══════════════════════════════════════════════════════════

    async def benchmark_ed25519_sign(self, iterations: int = 10000) -> BenchmarkResult:
        """Benchmark: assinatura Ed25519 (IPC local)."""
        samples = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            # Simulação: ~50us por assinatura Ed25519
            await asyncio.sleep(0.00005)
            t1 = time.perf_counter()
            samples.append((t1 - t0) * 1e6)

        mean = statistics.mean(samples)
        baseline = self._baseline_store.get("ed25519_sign", 65.0)
        improvement = ((baseline - mean) / baseline * 100) if baseline else None

        result = BenchmarkResult(
            benchmark_id=self._hash("ed25519_sign"),
            subsystem="crypto",
            metric="sign_latency",
            value=mean,
            unit="us",
            iterations=iterations,
            samples=samples[:100],
            mean=mean,
            median=statistics.median(samples),
            stddev=statistics.stdev(samples) if len(samples) > 1 else 0.0,
            p95=self._percentile(samples, 95),
            p99=self._percentile(samples, 99),
            baseline=baseline,
            improvement_pct=improvement,
            timestamp=time.time()
        )
        self.results.append(result)
        return result

    async def benchmark_mldsa44_sign(self, iterations: int = 100) -> BenchmarkResult:
        """Benchmark: assinatura ML-DSA-44 (governança blockchain)."""
        samples = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            # Simulação: ~2ms por assinatura ML-DSA-44
            await asyncio.sleep(0.002)
            t1 = time.perf_counter()
            samples.append((t1 - t0) * 1e3)

        mean = statistics.mean(samples)
        baseline = self._baseline_store.get("mldsa44_sign", 3.5)
        improvement = ((baseline - mean) / baseline * 100) if baseline else None

        result = BenchmarkResult(
            benchmark_id=self._hash("mldsa44_sign"),
            subsystem="crypto",
            metric="sign_latency",
            value=mean,
            unit="ms",
            iterations=iterations,
            samples=samples[:100],
            mean=mean,
            median=statistics.median(samples),
            stddev=statistics.stdev(samples) if len(samples) > 1 else 0.0,
            p95=self._percentile(samples, 95),
            p99=self._percentile(samples, 99),
            baseline=baseline,
            improvement_pct=improvement,
            timestamp=time.time()
        )
        self.results.append(result)
        return result

    async def benchmark_hybrid_verify(self, iterations: int = 500) -> BenchmarkResult:
        """Benchmark: verificação híbrida Ed25519 + ML-DSA-44."""
        samples = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            # Simulação: ~1.2ms para verificação híbrida
            await asyncio.sleep(0.0012)
            t1 = time.perf_counter()
            samples.append((t1 - t0) * 1e3)

        mean = statistics.mean(samples)
        baseline = self._baseline_store.get("hybrid_verify", 2.0)
        improvement = ((baseline - mean) / baseline * 100) if baseline else None

        result = BenchmarkResult(
            benchmark_id=self._hash("hybrid_verify"),
            subsystem="crypto",
            metric="verify_latency",
            value=mean,
            unit="ms",
            iterations=iterations,
            samples=samples[:100],
            mean=mean,
            median=statistics.median(samples),
            stddev=statistics.stdev(samples) if len(samples) > 1 else 0.0,
            p95=self._percentile(samples, 95),
            p99=self._percentile(samples, 99),
            baseline=baseline,
            improvement_pct=improvement,
            timestamp=time.time()
        )
        self.results.append(result)
        return result

    # ═══════════════════════════════════════════════════════════
    # FORMAL VERIFICATION PIPELINE BENCHMARKS
    # ═══════════════════════════════════════════════════════════

    async def benchmark_kani_verify(self, proof_count: int = 50) -> BenchmarkResult:
        """Benchmark: execução do Kani Rust Verifier."""
        # Simulação: ~30s por proof em média
        total_time_s = proof_count * 25 + (proof_count ** 0.5) * 5
        await asyncio.sleep(total_time_s / 100)  # scaled down for test

        baseline = self._baseline_store.get("kani_verify", 1800.0)
        improvement = ((baseline - total_time_s) / baseline * 100) if baseline else None

        result = BenchmarkResult(
            benchmark_id=self._hash("kani_verify"),
            subsystem="verification",
            metric="verification_time",
            value=total_time_s,
            unit="s",
            iterations=proof_count,
            samples=[total_time_s],
            mean=total_time_s,
            median=total_time_s,
            stddev=0.0,
            p95=total_time_s,
            p99=total_time_s,
            baseline=baseline,
            improvement_pct=improvement,
            timestamp=time.time()
        )
        self.results.append(result)
        return result

    async def benchmark_tla_model_check(self, state_space_size: int = 100000) -> BenchmarkResult:
        """Benchmark: TLC Model Checker (TLA+)."""
        # Simulação: BFS traversal time
        check_time_s = math.log10(state_space_size) * 8 + state_space_size / 50000
        await asyncio.sleep(check_time_s / 100)

        baseline = self._baseline_store.get("tla_check", 45.0)
        improvement = ((baseline - check_time_s) / baseline * 100) if baseline else None

        result = BenchmarkResult(
            benchmark_id=self._hash("tla_check"),
            subsystem="verification",
            metric="model_check_time",
            value=check_time_s,
            unit="s",
            iterations=1,
            samples=[check_time_s],
            mean=check_time_s,
            median=check_time_s,
            stddev=0.0,
            p95=check_time_s,
            p99=check_time_s,
            baseline=baseline,
            improvement_pct=improvement,
            timestamp=time.time()
        )
        self.results.append(result)
        return result

    # ═══════════════════════════════════════════════════════════
    # BUILD SYSTEM BENCHMARKS
    # ═══════════════════════════════════════════════════════════

    async def benchmark_cargo_build_full(self, crate_count: int = 50) -> BenchmarkResult:
        """Benchmark: build completo do workspace Cargo."""
        # Simulação: tempo proporcional ao número de crates
        build_time_s = crate_count * 12 + (crate_count ** 0.7) * 20
        await asyncio.sleep(build_time_s / 100)

        baseline = self._baseline_store.get("cargo_build_full", 900.0)
        improvement = ((baseline - build_time_s) / baseline * 100) if baseline else None

        result = BenchmarkResult(
            benchmark_id=self._hash("cargo_build"),
            subsystem="build",
            metric="full_build_time",
            value=build_time_s,
            unit="s",
            iterations=1,
            samples=[build_time_s],
            mean=build_time_s,
            median=build_time_s,
            stddev=0.0,
            p95=build_time_s,
            p99=build_time_s,
            baseline=baseline,
            improvement_pct=improvement,
            timestamp=time.time()
        )
        self.results.append(result)
        return result

    async def benchmark_lto_link_time(self, binary_size_mb: int = 50) -> BenchmarkResult:
        """Benchmark: tempo de linkagem com LTO=fat."""
        # Simulação: LTO fat é O(n^1.5) no tamanho do binário
        link_time_s = binary_size_mb ** 1.5 * 0.3 + 5
        await asyncio.sleep(link_time_s / 100)

        baseline = self._baseline_store.get("lto_link", 120.0)
        improvement = ((baseline - link_time_s) / baseline * 100) if baseline else None

        result = BenchmarkResult(
            benchmark_id=self._hash("lto_link"),
            subsystem="build",
            metric="link_time",
            value=link_time_s,
            unit="s",
            iterations=1,
            samples=[link_time_s],
            mean=link_time_s,
            median=link_time_s,
            stddev=0.0,
            p95=link_time_s,
            p99=link_time_s,
            baseline=baseline,
            improvement_pct=improvement,
            timestamp=time.time()
        )
        self.results.append(result)
        return result

    # ═══════════════════════════════════════════════════════════
    # OPTIMIZATION STRATEGIES
    # ═══════════════════════════════════════════════════════════

    def generate_optimization_strategies(self) -> List[OptimizationStrategy]:
        """Gera estratégias de otimização para cada subsistema."""
        strategies = [
            OptimizationStrategy(
                strategy_id="OPT-K01", subsystem="kernel",
                target_metric="ipc_latency", technique="Batch message passing + ring buffers",
                expected_gain_pct=35.0, implementation_complexity="medium", risk_level="low",
                applied=False
            ),
            OptimizationStrategy(
                strategy_id="OPT-K02", subsystem="kernel",
                target_metric="ipc_throughput", technique="Lock-free queues (crossbeam)",
                expected_gain_pct=50.0, implementation_complexity="high", risk_level="medium",
                applied=False
            ),
            OptimizationStrategy(
                strategy_id="OPT-W01", subsystem="wasm_runtime",
                target_metric="compile_time", technique="Incremental compilation + wasmtime AOT cache",
                expected_gain_pct=40.0, implementation_complexity="medium", risk_level="low",
                applied=False
            ),
            OptimizationStrategy(
                strategy_id="OPT-W02", subsystem="wasm_runtime",
                target_metric="execution_overhead", technique="Wasmtime Cranelift tiering + SIMD",
                expected_gain_pct=25.0, implementation_complexity="high", risk_level="medium",
                applied=False
            ),
            OptimizationStrategy(
                strategy_id="OPT-W03", subsystem="wasm_runtime",
                target_metric="proof_generation_time", technique="GPU-accelerated Groth16 (CUDA)",
                expected_gain_pct=80.0, implementation_complexity="high", risk_level="high",
                applied=False
            ),
            OptimizationStrategy(
                strategy_id="OPT-C01", subsystem="crypto",
                target_metric="sign_latency", technique="Ed25519 assembly optimizations (AVX2)",
                expected_gain_pct=30.0, implementation_complexity="medium", risk_level="low",
                applied=False
            ),
            OptimizationStrategy(
                strategy_id="OPT-C02", subsystem="crypto",
                target_metric="sign_latency", technique="ML-DSA precomputed NTT tables",
                expected_gain_pct=45.0, implementation_complexity="high", risk_level="medium",
                applied=False
            ),
            OptimizationStrategy(
                strategy_id="OPT-C03", subsystem="crypto",
                target_metric="verify_latency", technique="Batch verification (BLS-style aggregation)",
                expected_gain_pct=60.0, implementation_complexity="high", risk_level="medium",
                applied=False
            ),
            OptimizationStrategy(
                strategy_id="OPT-V01", subsystem="verification",
                target_metric="verification_time", technique="Parallel Kani proofs (rayon)",
                expected_gain_pct=55.0, implementation_complexity="medium", risk_level="low",
                applied=False
            ),
            OptimizationStrategy(
                strategy_id="OPT-V02", subsystem="verification",
                target_metric="model_check_time", technique="Distributed TLC (cloud workers)",
                expected_gain_pct=70.0, implementation_complexity="high", risk_level="medium",
                applied=False
            ),
            OptimizationStrategy(
                strategy_id="OPT-B01", subsystem="build",
                target_metric="full_build_time", technique="Sccache + incremental builds",
                expected_gain_pct=35.0, implementation_complexity="low", risk_level="low",
                applied=False
            ),
            OptimizationStrategy(
                strategy_id="OPT-B02", subsystem="build",
                target_metric="link_time", technique="ThinLTO fallback + mold linker",
                expected_gain_pct=40.0, implementation_complexity="medium", risk_level="low",
                applied=False
            ),
        ]
        self.strategies = strategies
        return strategies

    # ═══════════════════════════════════════════════════════════
    # PERFORMANCE PROFILES
    # ═══════════════════════════════════════════════════════════

    def generate_performance_profiles(self) -> List[PerformanceProfile]:
        """Gera perfis de performance por subsistema."""
        profiles = [
            PerformanceProfile(
                profile_id="PROF-K01", subsystem="kernel",
                bottleneck="Cache-line invalidation on IPC",
                hotspot_function="message_pass_channel_send",
                cpu_utilization_pct=12.0, memory_pressure_mb=48.0,
                ipc_latency_us=2.1, throughput_ops_sec=450000,
                recommendations=["Switch to lock-free ring buffers", "Batch small messages"]
            ),
            PerformanceProfile(
                profile_id="PROF-W01", subsystem="wasm_runtime",
                bottleneck="JIT compilation warm-up",
                hotspot_function="cranelift_compile_function",
                cpu_utilization_pct=45.0, memory_pressure_mb=256.0,
                ipc_latency_us=None, throughput_ops_sec=8500,
                recommendations=["Enable AOT caching", "Precompile hot modules"]
            ),
            PerformanceProfile(
                profile_id="PROF-C01", subsystem="crypto",
                bottleneck="ML-DSA polynomial multiplication",
                hotspot_function="polyvec_ntt",
                cpu_utilization_pct=78.0, memory_pressure_mb=512.0,
                ipc_latency_us=None, throughput_ops_sec=420,
                recommendations=["Precompute NTT tables", "Use AVX-512 if available"]
            ),
            PerformanceProfile(
                profile_id="PROF-V01", subsystem="verification",
                bottleneck="SMT solver backtracking (Z3)",
                hotspot_function="smt_check_assertions",
                cpu_utilization_pct=95.0, memory_pressure_mb=2048.0,
                ipc_latency_us=None, throughput_ops_sec=2,
                recommendations=["Parallel proof decomposition", "Smaller proof harnesses"]
            ),
            PerformanceProfile(
                profile_id="PROF-B01", subsystem="build",
                bottleneck="LTO fat link-time optimization",
                hotspot_function="llvm_lto_optimize",
                cpu_utilization_pct=88.0, memory_pressure_mb=4096.0,
                ipc_latency_us=None, throughput_ops_sec=None,
                recommendations=["Switch to ThinLTO for dev builds", "Use mold linker"]
            ),
        ]
        self.profiles = profiles
        return profiles

    # ═══════════════════════════════════════════════════════════
    # REGRESSION DETECTION
    # ═══════════════════════════════════════════════════════════

    def detect_regressions(self, threshold_pct: float = 5.0) -> List[RegressionAlert]:
        """Detecta regressões de performance contra baseline."""
        alerts = []
        for result in self.results:
            if result.baseline is None or result.improvement_pct is None:
                continue
            if result.improvement_pct < -threshold_pct:
                regression_pct = abs(result.improvement_pct)
                severity = "critical" if regression_pct > 20 else "warning" if regression_pct > 10 else "info"
                alert = RegressionAlert(
                    alert_id=self._hash(f"reg_{result.benchmark_id}"),
                    subsystem=result.subsystem,
                    metric=result.metric,
                    baseline_value=result.baseline,
                    current_value=result.value,
                    regression_pct=regression_pct,
                    severity=severity,
                    timestamp=time.time()
                )
                alerts.append(alert)
        self.alerts = alerts
        return alerts

    # ═══════════════════════════════════════════════════════════
    # CANONIZATION
    # ═══════════════════════════════════════════════════════════

    async def run_full_benchmark_suite(self) -> List[BenchmarkResult]:
        """Executa suite completa de benchmarks."""
        await self.benchmark_kernel_ipc_latency()
        await self.benchmark_kernel_ipc_throughput()
        await self.benchmark_wasm_compile_time()
        await self.benchmark_wasm_execution_overhead()
        await self.benchmark_zkwasm_proof_generation()
        await self.benchmark_ed25519_sign()
        await self.benchmark_mldsa44_sign()
        await self.benchmark_hybrid_verify()
        await self.benchmark_kani_verify()
        await self.benchmark_tla_model_check()
        await self.benchmark_cargo_build_full()
        await self.benchmark_lto_link_time()
        return self.results

    async def canonize(self) -> CanonicalBenchmark:
        """Executa pipeline completo de benchmark e canonização."""
        # Calculate timestamp ONCE before executing benchmarks to avoid hash-mismatches and race conditions
        seal_timestamp = time.time()

        await self.run_full_benchmark_suite()
        self.generate_optimization_strategies()
        self.generate_performance_profiles()
        self.detect_regressions()

        # Calculate overall Φ_C based on improvement percentages
        improvements = [r.improvement_pct for r in self.results if r.improvement_pct is not None]
        phi_c = (sum(improvements) / len(improvements) / 100 + 1) / 2 if improvements else 0.5
        phi_c = max(0.0, min(1.0, phi_c))

        seal_input = json.dumps({
            'benchmarks': len(self.results),
            'optimizations': len(self.strategies),
            'regressions': len(self.alerts),
            'phi_c': round(phi_c, 6),
            'timestamp': seal_timestamp,
        }, sort_keys=True)
        seal = hashlib.sha3_256(seal_input.encode()).hexdigest()

        benchmark = CanonicalBenchmark(
            benchmark_id=self._hash("perf_suite_v1"),
            total_subsystems=len(set(r.subsystem for r in self.results)),
            total_benchmarks=len(self.results),
            total_optimizations=len(self.strategies),
            total_regressions=len(self.alerts),
            overall_phi_c=phi_c,
            seal=seal,
            timestamp=seal_timestamp
        )
        return benchmark

    def export_json(self, benchmark: CanonicalBenchmark, path: str):
        """Exporta relatório de benchmark como JSON."""
        data = {
            'canonical_benchmark': asdict(benchmark),
            'results': [asdict(r) for r in self.results],
            'profiles': [asdict(p) for p in self.profiles],
            'strategies': [asdict(s) for s in self.strategies],
            'alerts': [asdict(a) for a in self.alerts],
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# ── Bus Interface ──

class ArkhePerformanceBusInterface:
    """Interface de publicação no Bus V3 da Catedral."""

    def __init__(self, engine: ArkhePerformanceEngine):
        self.engine = engine

    async def publish_to_bus(self, benchmark: CanonicalBenchmark) -> Tuple[bool, str]:
        """Publica métricas de performance no Bus V3."""
        bus_payload = {
            'substrate': '263',
            'canon': '∞.Ω.∇+++.263.performance_benchmark',
            'benchmark_id': benchmark.benchmark_id,
            'seal': benchmark.seal,
            'phi_c': benchmark.overall_phi_c,
            'subsystems': list(set(r.subsystem for r in self.engine.results)),
            'regression_count': benchmark.total_regressions,
            'top_bottleneck': self.engine.profiles[0].bottleneck if self.engine.profiles else None,
        }
        bus_seal = hashlib.sha3_256(
            json.dumps(bus_payload, sort_keys=True).encode()
        ).hexdigest()
        return True, bus_seal