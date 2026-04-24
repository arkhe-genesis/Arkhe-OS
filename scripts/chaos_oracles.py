# chaos_oracles.py — Avaliador de oráculos de sucesso

import asyncio
import time
import hashlib
import json
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime, timedelta

# Mock implementation for environment without prometheus_api_client
class PrometheusConnect:
    def __init__(self, url=None, disable_ssl=True):
        self.url = url
    def custom_query(self, query=None, end_time=None):
        return [{"values": [[time.time(), 1.0]]}]

class OracleResult(Enum):
    """Resultado binário de um oráculo."""
    PASS = auto()
    FAIL = auto()
    TIMEOUT = auto()
    ERROR = auto()

@dataclass
class OracleDefinition:
    """Definição de um oráculo de sucesso."""
    name: str
    layer: str  # "hardware", "network", "consensus", "application"
    query: str  # Query Prometheus ou função customizada
    threshold: float
    comparison: str  # "gte", "lte", "eq", "neq"
    observation_window_start_offset_s: float  # Offset de T1 para início da janela
    observation_window_duration_s: float  # Duração da janela de observação
    is_primary: bool = False  # Se é oráculo primário do experimento
    description: str = ""

@dataclass
class OracleEvaluation:
    """Resultado da avaliação de um oráculo."""
    oracle_name: str
    result: OracleResult
    observed_value: float
    threshold: float
    observation_time: float
    details: Dict = field(default_factory=dict)
    signature: str = ""  # Assinatura digital para audit trail

class OracleEvaluator:
    """
    Avalia oráculos de sucesso para experimentos de caos.
    """

    # Catálogo de oráculos pré-definidos
    ORACLE_CATALOG: Dict[str, OracleDefinition] = {
        # Hardware
        "omega_recovery": OracleDefinition(
            name="omega_recovery",
            layer="hardware",
            query="cathedral_organism_vitality",
            threshold=0.9,  # 90% do valor pré-caos
            comparison="gte",
            observation_window_start_offset_s=0,
            observation_window_duration_s=60,
            is_primary=True,
            description="Ω-score recupera para ≥90% do valor pré-caos em 60s"
        ),
        "qubit_pool_heal": OracleDefinition(
            name="qubit_pool_heal",
            layer="hardware",
            query="quantum_qubit_error_rate",
            threshold=2.0,  # 2× baseline
            comparison="lte",
            observation_window_start_offset_s=0,
            observation_window_duration_s=120,
            description="Taxa de erro de qubits ≤2× baseline em 120s"
        ),
        # Rede
        "gossip_convergence": OracleDefinition(
            name="gossip_convergence",
            layer="network",
            query="gossip_convergence_latency_seconds",
            threshold=5.0,
            comparison="lte",
            observation_window_start_offset_s=0,
            observation_window_duration_s=10,
            is_primary=True,
            description="Convergência do gossip em ≤5s"
        ),
        "cross_region_sync": OracleDefinition(
            name="cross_region_sync",
            layer="network",
            query="cross_region_replication_lag_seconds",
            threshold=30.0,
            comparison="lte",
            observation_window_start_offset_s=0,
            observation_window_duration_s=120,
            description="Lag de replicação cross-region ≤30s em 120s"
        ),
        # Consenso
        "consensus_fallback": OracleDefinition(
            name="consensus_fallback",
            layer="consensus",
            query="consensus_decision_fallback_success_rate",
            threshold=1.0,
            comparison="eq",
            observation_window_start_offset_s=0,
            observation_window_duration_s=5,
            is_primary=True,
            description="Fallback de consenso regional sempre bem-sucedido"
        ),
        # Aplicação
        "shard_migration_success": OracleDefinition(
            name="shard_migration_success",
            layer="application",
            query="shard_migration_success_rate",
            threshold=0.95,
            comparison="gte",
            observation_window_start_offset_s=0,
            observation_window_duration_s=60,
            is_primary=True,
            description="≥95% das migrações de shard bem-sucedidas em 60s"
        ),
    }

    def __init__(self, prometheus_url: str, signing_key: Optional[str] = None):
        self.prometheus = PrometheusConnect(url=prometheus_url, disable_ssl=True)
        self.signing_key = signing_key
        self.evaluation_log: List[OracleEvaluation] = []

    async def evaluate_experiment_oracles(
        self,
        experiment_id: str,
        oracle_names: List[str],
        pre_chaos_metrics: Dict[str, float],
        t1: float,  # Fim da injeção, início da recuperação
        timeout_s: float = 300
    ) -> Dict[str, OracleEvaluation]:
        """
        Avalia múltiplos oráculos para um experimento de caos.
        """
        results = {}

        for oracle_name in oracle_names:
            oracle_def = self.ORACLE_CATALOG.get(oracle_name)
            if not oracle_def:
                results[oracle_name] = OracleEvaluation(
                    oracle_name=oracle_name,
                    result=OracleResult.ERROR,
                    observed_value=0.0,
                    threshold=0.0,
                    observation_time=time.time(),
                    details={"error": f"Oráculo não encontrado: {oracle_name}"}
                )
                continue

            # Calcula janela de observação
            window_start = t1 + oracle_def.observation_window_start_offset_s
            window_end = window_start + oracle_def.observation_window_duration_s

            # Aguarda início da janela
            wait_time = window_start - time.time()
            if wait_time > 0:
                await asyncio.sleep(min(wait_time, 5.0))  # Polling a cada 5s

            # Coleta métrica durante a janela
            observed_value = await self._collect_metric_during_window(
                oracle_def.query,
                window_start,
                window_end,
                pre_chaos_metrics.get(oracle_name)
            )

            # Avalia contra threshold
            result = self._compare_value(
                observed_value,
                oracle_def.threshold,
                oracle_def.comparison
            )

            # Gera assinatura para audit trail
            signature = self._sign_evaluation(
                experiment_id, oracle_name, observed_value, result
            )

            evaluation = OracleEvaluation(
                oracle_name=oracle_name,
                result=result,
                observed_value=observed_value,
                threshold=oracle_def.threshold,
                observation_time=time.time(),
                details={
                    "window_start": window_start,
                    "window_end": window_end,
                    "pre_chaos_value": pre_chaos_metrics.get(oracle_name)
                },
                signature=signature
            )

            results[oracle_name] = evaluation
            self.evaluation_log.append(evaluation)

        return results

    async def _collect_metric_during_window(
        self,
        query: str,
        window_start: float,
        window_end: float,
        pre_chaos_value: Optional[float] = None
    ) -> float:
        """
        Coleta valor da métrica durante janela de observação.
        Para oráculos relativos, normaliza pelo valor pré-caos.
        """
        # Query Prometheus com range vector
        end_time = datetime.fromtimestamp(window_end)

        try:
            result = self.prometheus.custom_query(
                query=f"{query}[{int(window_end - window_start)}s]",
                end_time=end_time
            )

            if not result or not result[0].get("values"):
                return 0.0

            # Pega último valor da série
            last_value = float(result[0]["values"][-1][1])

            # Normaliza se for oráculo relativo (ex: omega_recovery)
            if pre_chaos_value and pre_chaos_value > 0:
                # Para oráculos do tipo "≥ X% do pré-caos"
                return last_value / pre_chaos_value

            return last_value

        except Exception as e:
            return 0.0

    def _compare_value(self, observed: float, threshold: float, comparison: str) -> OracleResult:
        """Compara valor observado contra threshold."""
        try:
            if comparison == "gte" and observed >= threshold:
                return OracleResult.PASS
            elif comparison == "lte" and observed <= threshold:
                return OracleResult.PASS
            elif comparison == "eq" and abs(observed - threshold) < 0.001:
                return OracleResult.PASS
            elif comparison == "neq" and abs(observed - threshold) >= 0.001:
                return OracleResult.PASS
            else:
                return OracleResult.FAIL
        except:
            return OracleResult.ERROR

    def _sign_evaluation(
        self,
        experiment_id: str,
        oracle_name: str,
        observed_value: float,
        result: OracleResult
    ) -> str:
        """Gera assinatura digital para audit trail do oráculo."""
        if not self.signing_key:
            return "unsigned"

        content = f"{experiment_id}:{oracle_name}:{observed_value}:{result.name}:{time.time()}"
        return hashlib.sha3_256(f"{content}:{self.signing_key}".encode()).hexdigest()[:16]

    def get_experiment_verdict(
        self,
        evaluations: Dict[str, OracleEvaluation]
    ) -> Tuple[bool, str]:
        """
        Determina veredito final do experimento baseado nos oráculos.
        Retorna (success, reason).
        """
        if not evaluations:
            return False, "Nenhum oráculo avaliado"

        # Oráculos primários têm peso maior
        primary_evaluations = [e for e in evaluations.values() if
                              self.ORACLE_CATALOG.get(e.oracle_name, OracleDefinition("", "", "", "", "", 0, 0, True)).is_primary]

        # Se houver oráculos primários, todos devem passar
        if primary_evaluations:
            failed_primaries = [e for e in primary_evaluations if e.result != OracleResult.PASS]
            if failed_primaries:
                reasons = [f"{e.oracle_name}: {e.result.name} (observed={e.observed_value}, threshold={e.threshold})"
                          for e in failed_primaries]
                return False, f"Oráculos primários falharam: {'; '.join(reasons)}"

        # Oráculos secundários: tolera até 1 falha
        secondary_evaluations = [e for e in evaluations.values() if e not in primary_evaluations]
        failed_secondaries = [e for e in secondary_evaluations if e.result != OracleResult.PASS]

        if len(failed_secondaries) > 1:
            reasons = [f"{e.oracle_name}: {e.result.name}" for e in failed_secondaries]
            return False, f"Múltiplos oráculos secundários falharam: {'; '.join(reasons)}"

        return True, "Todos os oráculos críticos passaram"
