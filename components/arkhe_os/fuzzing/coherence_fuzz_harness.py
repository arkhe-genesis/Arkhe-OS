# arkhe_os/fuzzing/coherence_fuzz_harness.py
"""
Substrato 274: Harness de Fuzzing Guiado por Coerência
Integra AFL++/libFuzzer com métricas de coerência do ARKHE OS.
"""
import subprocess
import json
import hashlib
import time
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from enum import Enum

class FuzzMode(Enum):
    AFL_PLUS_PLUS = "afl++"
    LIBFUZZER = "libfuzzer"
    HONGGFUZZ = "honggfuzz"

@dataclass
class FuzzFinding:
    """Registro de descoberta do fuzzing com contexto de coerência."""
    finding_id: str
    input_hash: str
    input_path: Path
    crash_type: str  # "segfault", "timeout", "assert", "coherence_drop"
    target_function: str
    coherence_before: float
    coherence_after: float
    coherence_delta: float
    stack_trace: Optional[str]
    timestamp: float
    metadata: Dict[str, any] = field(default_factory=dict)

    def to_canonical_dict(self) -> Dict:
        return {
            "finding_id": self.finding_id,
            "input_hash": self.input_hash,
            "crash_type": self.crash_type,
            "target": self.target_function,
            "phi_before": round(self.coherence_before, 4),
            "phi_after": round(self.coherence_after, 4),
            "delta_phi": round(self.coherence_delta, 4),
            "severity": self._compute_severity(),
            "stack_trace": self.stack_trace[:1000] if self.stack_trace else None,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    def _compute_severity(self) -> str:
        if self.crash_type in ("segfault", "assert"):
            return "critical"
        elif self.coherence_delta < -0.3:
            return "high"
        elif self.coherence_delta < -0.1:
            return "medium"
        return "low"

class CoherenceFuzzHarness:
    """Harness que executa fuzzing e avalia coerência dos resultados."""

    def __init__(
        self,
        target_binary: str,
        work_dir: Path,
        coherence_evaluator: Callable[[bytes], float],
        mode: FuzzMode = FuzzMode.AFL_PLUS_PLUS,
    ):
        self.target = target_binary
        self.work_dir = work_dir
        self.evaluate_coherence = coherence_evaluator
        self.mode = mode
        self.findings: List[FuzzFinding] = []
        self._finding_counter = 0

        # Configurações do fuzzing
        self.timeout_sec = 30  # timeout por input
        self.min_coherence_drop = 0.1  # threshold para registrar finding

    def run_campaign(self, duration_sec: int = 3600, corpus_dir: Optional[Path] = None) -> Dict:
        """Executa campanha de fuzzing com monitoramento de coerência."""
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # Preparar diretórios
        input_dir = corpus_dir or (self.work_dir / "corpus")
        output_dir = self.work_dir / "output"
        crashes_dir = output_dir / "crashes"
        input_dir.mkdir(parents=True, exist_ok=True)
        crashes_dir.mkdir(parents=True, exist_ok=True)

        # Comando base do fuzzing
        cmd = self._build_fuzz_command(input_dir, output_dir, crashes_dir, duration_sec)

        print(f"🚀 Iniciando fuzzing ({self.mode.value}) por {duration_sec}s...")
        print(f"   Target: {self.target}")
        print(f"   Output: {output_dir}")

        # Executar fuzzing em subprocesso com monitoramento
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        start_time = time.time()
        last_check = start_time

        while process.poll() is None:
            current_time = time.time()

            # Verificar novos inputs a cada 60s
            if current_time - last_check >= 60:
                new_findings = self._scan_for_findings(output_dir, crashes_dir)
                if new_findings:
                    print(f"   🎯 {len(new_findings)} novos findings detectados")
                    self.findings.extend(new_findings)
                    self._submit_findings_to_hypermesh(new_findings)
                last_check = current_time

            # Verificar timeout da campanha
            if current_time - start_time >= duration_sec:
                process.terminate()
                break

            time.sleep(1)

        process.wait()

        # Scan final
        final_findings = self._scan_for_findings(output_dir, crashes_dir)
        self.findings.extend(f for f in final_findings if f not in self.findings)

        return self._generate_campaign_report(duration_sec)

    def _build_fuzz_command(self, input_dir: Path, output_dir: Path, crashes_dir: Path, duration: int) -> List[str]:
        """Constrói comando do fuzzing baseado no modo."""
        if self.mode == FuzzMode.AFL_PLUS_PLUS:
            return [
                "afl-fuzz",
                "-i", str(input_dir),
                "-o", str(output_dir),
                "-V", str(duration),
                "-t", str(self.timeout_sec * 1000),  # timeout em ms
                "-m", "none",  # sem limite de memória
                "--", self.target, "@@"
            ]
        elif self.mode == FuzzMode.LIBFUZZER:
            return [
                self.target,
                f"-max_total_time={duration}",
                f"-timeout={self.timeout_sec}",
                f"-artifact_prefix={crashes_dir}/",
                str(input_dir)
            ]
        else:
            raise ValueError(f"Modo não suportado: {self.mode}")

    def _scan_for_findings(self, output_dir: Path, crashes_dir: Path) -> List[FuzzFinding]:
        """Varre diretórios de output em busca de novos findings."""
        new_findings = []

        # Processar crashes
        if crashes_dir.exists():
            for crash_file in crashes_dir.glob("id:*"):
                if self._is_new_finding(crash_file):
                    finding = self._analyze_crash(crash_file)
                    if finding:
                        new_findings.append(finding)

        # Processar inputs que causaram drop significativo de coerência
        queue_dir = output_dir / "queue"
        if queue_dir.exists():
            for input_file in queue_dir.glob("id:*"):
                if input_file.suffix == ".state":
                    continue
                coherence = self._evaluate_input_coherence(input_file)
                if coherence < 0.5:  # Threshold para baixa coerência
                    finding = self._analyze_coherence_drop(input_file, coherence)
                    if finding:
                        new_findings.append(finding)

        return new_findings

    def _is_new_finding(self, file_path: Path) -> bool:
        """Verifica se finding já foi processado."""
        processed_file = self.work_dir / ".processed_findings"
        if not processed_file.exists():
            return True

        processed = set(processed_file.read_text().splitlines())
        file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()[:16]
        return file_hash not in processed

    def _mark_as_processed(self, file_path: Path):
        """Marca finding como processado."""
        processed_file = self.work_dir / ".processed_findings"
        file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()[:16]
        with open(processed_file, "a") as f:
            f.write(file_hash + "\n")

    def _analyze_crash(self, crash_file: Path) -> Optional[FuzzFinding]:
        """Analisa arquivo de crash e gera finding."""
        try:
            # Executar target com input do crash para coletar contexto
            result = subprocess.run(
                [self.target, str(crash_file)],
                capture_output=True,
                timeout=self.timeout_sec
            )

            # Calcular coerência do estado pós-crash (se aplicável)
            coherence_after = 0.0  # Crash implica coerência zero
            coherence_before = self._evaluate_input_coherence(crash_file)

            self._finding_counter += 1
            finding = FuzzFinding(
                finding_id=f"crash-{self._finding_counter:04d}",
                input_hash=hashlib.sha256(crash_file.read_bytes()).hexdigest()[:16],
                input_path=crash_file,
                crash_type=self._classify_crash(result),
                target_function=self._extract_target_function(result.stderr.decode() if result.stderr else ""),
                coherence_before=coherence_before,
                coherence_after=coherence_after,
                coherence_delta=coherence_after - coherence_before,
                stack_trace=result.stderr.decode() if result.stderr else None,
                timestamp=time.time(),
                metadata={"exit_code": result.returncode, "afl_stats": self._read_afl_stats()},
            )

            self._mark_as_processed(crash_file)
            return finding

        except subprocess.TimeoutExpired:
            return None
        except Exception as e:
            print(f"⚠️ Erro ao analisar crash {crash_file}: {e}")
            return None

    def _analyze_coherence_drop(self, input_file: Path, coherence: float) -> Optional[FuzzFinding]:
        """Analisa input que causou drop significativo de coerência."""
        self._finding_counter += 1
        return FuzzFinding(
            finding_id=f"coherence-drop-{self._finding_counter:04d}",
            input_hash=hashlib.sha256(input_file.read_bytes()).hexdigest()[:16],
            input_path=input_file,
            crash_type="coherence_drop",
            target_function="unknown",
            coherence_before=0.95,  # Baseline assumido
            coherence_after=coherence,
            coherence_delta=coherence - 0.95,
            stack_trace=None,
            timestamp=time.time(),
            metadata={"input_size": input_file.stat().st_size},
        )

    def _evaluate_input_coherence(self, input_file: Path) -> float:
        """Avalia coerência do target ao processar input."""
        try:
            result = subprocess.run(
                [self.target, str(input_file)],
                capture_output=True,
                timeout=self.timeout_sec
            )
            if result.returncode != 0:
                return 0.0
            return self.evaluate_coherence(result.stdout)
        except:
            return 0.0

    def _classify_crash(self, result: subprocess.CompletedProcess) -> str:
        """Classifica tipo de crash baseado no resultado."""
        if result.returncode < 0:
            return "segfault"
        elif result.returncode == 124:  # timeout
            return "timeout"
        elif result.stderr and b"assert" in result.stderr.lower():
            return "assert"
        return "unknown"

    def _extract_target_function(self, stderr: str) -> str:
        """Extrai nome da função do stack trace."""
        # Placeholder: em produção, parsear stack trace real
        import re
        match = re.search(r'in (\\w+)', stderr)
        return match.group(1) if match else "unknown"

    def _read_afl_stats(self) -> Dict:
        """Lê estatísticas do AFL++ se disponíveis."""
        stats_file = self.work_dir / "output" / "fuzzer_stats"
        if stats_file.exists():
            stats = {}
            for line in stats_file.read_text().splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    stats[key.strip()] = val.strip()
            return stats
        return {}

    def _submit_findings_to_hypermesh(self, findings: List[FuzzFinding]):
        """Submete findings ao canal de coerência."""
        payload = {
            "source": f"fuzzing-{self.mode.value}",
            "target": self.target,
            "findings": [f.to_canonical_dict() for f in findings],
            "summary": {
                "total_findings": len(findings),
                "critical": sum(1 for f in findings if f._compute_severity() == "critical"),
                "avg_coherence_delta": sum(f.coherence_delta for f in findings) / len(findings),
            },
            "timestamp": time.time(),
        }

        # Em produção: enviar via qhttp_client
        output_file = self.work_dir / f"fuzz_findings_{int(time.time())}.json"
        output_file.write_text(json.dumps(payload, indent=2, default=str))
        print(f"   📤 {len(findings)} findings submetidos: {output_file}")

    def _generate_campaign_report(self, duration_sec: int) -> Dict:
        """Gera relatório final da campanha."""
        return {
            "campaign_id": hashlib.sha256(f"{self.target}{time.time()}".encode()).hexdigest()[:12],
            "target": self.target,
            "mode": self.mode.value,
            "duration_sec": duration_sec,
            "total_findings": len(self.findings),
            "findings_by_severity": {
                "critical": sum(1 for f in self.findings if f._compute_severity() == "critical"),
                "high": sum(1 for f in self.findings if f._compute_severity() == "high"),
                "medium": sum(1 for f in self.findings if f._compute_severity() == "medium"),
                "low": sum(1 for f in self.findings if f._compute_severity() == "low"),
            },
            "avg_coherence_delta": sum(f.coherence_delta for f in self.findings) / len(self.findings) if self.findings else 0,
            "findings": [f.to_canonical_dict() for f in self.findings],
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ARKHE Fuzz Harness")
    parser.add_argument("--target", required=True, help="Target binary to fuzz")
    parser.add_argument("--mode", default="afl++", help="Fuzzing mode (afl++, libfuzzer)")
    parser.add_argument("--duration", type=int, default=3600, help="Fuzzing duration in seconds")
    parser.add_argument("--corpus", help="Directory with corpus")
    parser.add_argument("--output", required=True, help="Directory for output")
    args = parser.parse_args()

    def dummy_evaluator(b): return 0.5

    mode = FuzzMode(args.mode)
    harness = CoherenceFuzzHarness(
        target_binary=args.target,
        work_dir=Path(args.output),
        coherence_evaluator=dummy_evaluator,
        mode=mode
    )
    harness.run_campaign(args.duration, Path(args.corpus) if args.corpus else None)
