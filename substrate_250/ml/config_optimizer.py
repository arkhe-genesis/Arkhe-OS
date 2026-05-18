#!/usr/bin/env python3
"""
ARKHE OS Substrate 250: ML-Based Configuration Optimizer
Canon: ∞.Ω.∇+++.250.ml_optimization

Otimização automática de parâmetros de configuração via aprendizado de máquina
baseado em histórico de Φ_C, com validação constitucional e rollback seguro.
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
import numpy as np

# Mock imports for ML libraries (in production: import sklearn, bayes_opt, etc.)
try:
    from sklearn.ensemble import RandomForestRegressor
except ImportError:
    RandomForestRegressor = None

try:
    from bayes_opt import BayesianOptimization
except ImportError:
    BayesianOptimization = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
logger = logging.getLogger(__name__)

# =============================================================================
# TIPOS CANÔNICOS DE OTIMIZAÇÃO
# =============================================================================

class OptimizationGoal(Enum):
    """Objetivo da otimização de configuração."""
    MAXIMIZE_PHI_C = "maximize_phi_c"          # Maximizar Φ_C composto
    STABILIZE_PHI_C = "stabilize_phi_c"        # Minimizar variância de Φ_C
    BALANCE = "balance"                        # Trade-off entre valor e estabilidade
    MINIMIZE_RESOURCE_USAGE = "minimize_resources"  # Otimizar custo computacional

@dataclass
class ConfigParameter:
    """Representação de um parâmetro de configuração otimizável."""
    registry_path: str          # Ex: "Network/BusPort"
    value_type: str             # "REG_DWORD", "REG_SZ", etc.
    current_value: Any          # Valor atual
    min_value: Optional[Any]    # Limite inferior (se numérico)
    max_value: Optional[Any]    # Limite superior (se numérico)
    allowed_values: Optional[List[Any]]  # Valores permitidos (se categórico)
    impact_on_phi_c: float      # Estimativa de impacto em Φ_C (0.0-1.0)
    constitutional_constraint: bool  # Se o parâmetro é protegido por P1-P7

    def is_numeric(self) -> bool:
        return self.value_type in ["REG_DWORD", "REG_QWORD"] and self.min_value is not None

    def normalize_value(self, value: Any) -> float:
        """Normaliza valor para [0, 1] para otimização."""
        if not self.is_numeric() or self.min_value is None or self.max_value is None:
            return 0.5  # Valor neutro para não-numéricos
        return (value - self.min_value) / (self.max_value - self.min_value)

@dataclass
class OptimizationRecommendation:
    """Recomendação de mudança de configuração gerada pelo ML."""
    recommendation_id: str
    timestamp: float
    parameter: ConfigParameter
    suggested_value: Any
    expected_phi_c_delta: float  # Mudança esperada em Φ_C
    confidence: float            # Confiança do modelo (0.0-1.0)
    rationale: str               # Explicação da recomendação (SHAP/LIME)
    constitutional_check: str    # "passed", "failed", "warning"
    risk_level: str              # "low", "medium", "high"
    requires_approval: bool      # Se requer aprovação humana
    rollback_plan: str           # Como reverter se necessário

    def to_dict(self) -> Dict:
        return {**asdict(self), "parameter": asdict(self.parameter)}

@dataclass
class OptimizationHistory:
    """Histórico de otimizações aplicadas."""
    recommendation: OptimizationRecommendation
    applied: bool
    applied_timestamp: Optional[float]
    phi_c_before: float
    phi_c_after: Optional[float]
    actual_phi_c_delta: Optional[float]
    rollback_triggered: bool
    temporal_chain_seal: Optional[str]

# =============================================================================
# COLETOR DE DADOS PARA TREINAMENTO
# =============================================================================

class PhiCDataCollector:
    """Coleta histórico de Φ_C e configurações para treinamento de ML."""

    def __init__(self, registry_root: str = r"SOFTWARE\ARKHE"):
        self.registry_root = registry_root
        self._phi_c_history: List[Dict] = []
        self._config_snapshots: List[Dict] = []

    def record_phi_c_sample(self, composite: float, layers: Dict[str, float],
                           context: Dict[str, Any]):
        """Registra amostra de Φ_C com contexto."""
        sample = {
            "timestamp": time.time(),
            "composite_phi_c": composite,
            "layer_phi_c": layers,
            "context": context  # workload, platform, time_of_day, etc.
        }
        self._phi_c_history.append(sample)

        # Manter apenas últimas 10k amostras para eficiência
        if len(self._phi_c_history) > 10000:
            self._phi_c_history = self._phi_c_history[-10000:]

    def record_config_snapshot(self, parameters: Dict[str, Any]):
        """Registra snapshot de configurações atuais."""
        snapshot = {
            "timestamp": time.time(),
            "parameters": parameters
        }
        self._config_snapshots.append(snapshot)

        if len(self._config_snapshots) > 1000:
            self._config_snapshots = self._config_snapshots[-1000:]

    def get_training_dataset(self, lookback_hours: int = 168) -> Tuple[np.ndarray, np.ndarray]:
        """Prepara dataset para treinamento: features → target (Φ_C)."""
        cutoff = time.time() - (lookback_hours * 3600)

        # Unir Φ_C samples com config snapshots mais próximos no tempo
        X, y = [], []
        for phi_sample in self._phi_c_history:
            if phi_sample["timestamp"] < cutoff:
                continue

            # Encontrar config snapshot mais próximo (within 5 min)
            closest_config = min(
                (s for s in self._config_snapshots
                 if abs(s["timestamp"] - phi_sample["timestamp"]) < 300),
                key=lambda s: abs(s["timestamp"] - phi_sample["timestamp"]),
                default=None
            )

            if closest_config:
                # Features: parâmetros normalizados + contexto temporal
                features = []
                for param_name, param_value in closest_config["parameters"].items():
                    if isinstance(param_value, (int, float)):
                        # Normalizar numéricos para [0, 1]
                        features.append(min(1.0, max(0.0, param_value / 1000)))
                    elif isinstance(param_value, bool):
                        features.append(1.0 if param_value else 0.0)
                    # Ignorar strings/categóricos por enquanto

                # Adicionar features temporais
                dt = datetime.fromtimestamp(phi_sample["timestamp"])
                features.extend([
                    dt.hour / 24,           # Hora do dia normalizada
                    dt.weekday() / 7,        # Dia da semana
                    phi_sample["context"].get("workload_intensity", 0.5)  # Contexto
                ])

                X.append(features)
                y.append(phi_sample["composite_phi_c"])

        return np.array(X) if X else np.empty((0, 0)), np.array(y) if y else np.empty(0)

# =============================================================================
# OTIMIZADOR DE CONFIGURAÇÃO BASEADO EM ML
# =============================================================================

class MLConfigOptimizer:
    """Motor de otimização de configuração usando aprendizado de máquina."""

    # Parâmetros otimizáveis (exemplo)
    OPTIMIZABLE_PARAMS = {
        "Network/BusPort": ConfigParameter(
            registry_path="Network/BusPort",
            value_type="REG_DWORD",
            current_value=8080,
            min_value=1024,
            max_value=65535,
            allowed_values=None,
            impact_on_phi_c=0.15,
            constitutional_constraint=False
        ),
        "Service/ThreadPoolSize": ConfigParameter(
            registry_path="Service/ThreadPoolSize",
            value_type="REG_DWORD",
            current_value=16,
            min_value=4,
            max_value=128,
            allowed_values=None,
            impact_on_phi_c=0.25,
            constitutional_constraint=False
        ),
        "PhiC/UpdateIntervalSec": ConfigParameter(
            registry_path="PhiC/UpdateIntervalSec",
            value_type="REG_DWORD",
            current_value=300,
            min_value=60,
            max_value=3600,
            allowed_values=None,
            impact_on_phi_c=0.10,
            constitutional_constraint=False
        ),
        # Parâmetros protegidos por constituição (não otimizáveis)
        "Security/FipsMode": ConfigParameter(
            registry_path="Security/FipsMode",
            value_type="REG_DWORD",
            current_value=1,
            min_value=None,
            max_value=None,
            allowed_values=[0, 1],
            impact_on_phi_c=0.0,
            constitutional_constraint=True  # P1: Verificação Formal
        ),
    }

    def __init__(self, goal: OptimizationGoal = OptimizationGoal.MAXIMIZE_PHI_C,
                 min_phi_c_threshold: float = 0.85):
        self.goal = goal
        self.min_phi_c_threshold = min_phi_c_threshold
        self.data_collector = PhiCDataCollector()
        self._model = None
        self._optimization_history: List[OptimizationHistory] = []

    async def train_model(self, force_retrain: bool = False) -> bool:
        """Treina ou atualiza o modelo de otimização."""
        if RandomForestRegressor is None:
            logger.warning("⚠️  ML libraries not available; using heuristic optimization")
            return False

        X, y = await asyncio.to_thread(self.data_collector.get_training_dataset)
        if len(X) < 100:
            logger.warning(f"⚠️  Insufficient training data: {len(X)} samples")
            return False

        if force_retrain or self._model is None:
            logger.info(f"🧠 Training model with {len(X)} samples...")
            self._model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            await asyncio.to_thread(self._model.fit, X, y)
            score = await asyncio.to_thread(self._model.score, X, y)
            logger.info(f"✅ Model trained: R² = {score:.3f}")
            return True
        else:
            # Incremental update (mock: em produção, usar partial_fit)
            logger.info("🔄 Incremental model update...")
            return True

    def generate_recommendations(self, top_n: int = 3) -> List[OptimizationRecommendation]:
        """Gera recomendações de otimização baseadas no modelo."""
        recommendations = []

        for param_key, param in self.OPTIMIZABLE_PARAMS.items():
            if param.constitutional_constraint:
                continue  # Pular parâmetros protegidos pela constituição

            # Simular impacto de diferentes valores
            best_value = param.current_value
            best_expected_delta = -float("inf")
            best_confidence = 0.0
            best_rationale = ""

            if param.is_numeric() and self._model and BayesianOptimization:
                # Bayesian optimization para encontrar melhor valor
                def phi_c_objective(**kwargs):
                    # Mock: avaliar modelo com valor proposto
                    normalized = param.normalize_value(kwargs["value"])
                    # Em produção: criar feature vector completo e prever Φ_C
                    return 0.90 + 0.10 * normalized  # Mock function

                try:
                    optimizer = BayesianOptimization(
                        f=phi_c_objective,
                        pbounds={"value": (0.0, 1.0)},
                        random_state=42,
                        verbose=0
                    )
                    optimizer.maximize(init_points=5, n_iter=10)
                    best_normalized = optimizer.max["params"]["value"]
                    best_value = param.min_value + best_normalized * (param.max_value - param.min_value)
                    best_expected_delta = optimizer.max["target"] - 0.90
                    best_confidence = 0.85  # Mock confidence
                    best_rationale = f"Bayesian optimization suggests {best_value:.0f} for max Φ_C"
                except Exception as e:
                    logger.warning(f"⚠️  Optimization failed for {param_key}: {e}")
                    continue
            else:
                # Heurística simples se modelo não disponível
                if param.impact_on_phi_c > 0.2:
                    best_value = param.max_value if hasattr(param, "max_value") else param.current_value
                    best_expected_delta = param.impact_on_phi_c * 0.5
                    best_confidence = 0.60
                    best_rationale = "Heuristic: increase value for higher Φ_C impact"

            # Verificação constitucional
            const_check = self._validate_constitutional(param, best_value)

            # Calcular nível de risco
            risk_level = self._assess_risk(param, best_value, best_expected_delta)

            rec = OptimizationRecommendation(
                recommendation_id=hashlib.sha3_256(f"{param_key}:{best_value}:{time.time()}".encode()).hexdigest()[:16],
                timestamp=time.time(),
                parameter=param,
                suggested_value=best_value,
                expected_phi_c_delta=best_expected_delta,
                confidence=best_confidence,
                rationale=best_rationale,
                constitutional_check=const_check,
                risk_level=risk_level,
                requires_approval=(risk_level == "high" or abs(best_expected_delta) > 0.05),
                rollback_plan=f"Restore {param_key} to {param.current_value} via Registry API"
            )
            recommendations.append(rec)

        # Ordenar por expected impact * confidence
        recommendations.sort(key=lambda r: r.expected_phi_c_delta * r.confidence, reverse=True)
        return recommendations[:top_n]

    def _validate_constitutional(self, param: ConfigParameter, value: Any) -> str:
        """Valida recomendação contra princípios constitucionais P1-P7."""
        # P1: Verificação Formal - Security/FipsMode não pode ser desabilitado
        if param.registry_path == "Security/FipsMode" and value == 0:
            return "failed"

        # P3: Gap Soberano - Φ_C não pode ser forçado a 1.0
        if "PhiC" in param.registry_path and value == 1.0:
            return "warning"

        # P7: Energia como Recurso - não permitir valores que causem waste excessivo
        if param.registry_path == "Service/ThreadPoolSize" and value > 64:
            return "warning"  # Pode causar waste de recursos

        return "passed"

    def _assess_risk(self, param: ConfigParameter, value: Any, expected_delta: float) -> str:
        """Avalia nível de risco da mudança proposta."""
        if param.impact_on_phi_c > 0.3 or abs(expected_delta) > 0.1:
            return "high"
        elif param.impact_on_phi_c > 0.15 or abs(expected_delta) > 0.05:
            return "medium"
        return "low"

    async def apply_recommendation(self, recommendation: OptimizationRecommendation,
                                 require_approval: bool = True) -> bool:
        """Aplica recomendação de otimização com validação e rollback capability."""
        if recommendation.constitutional_check == "failed":
            logger.error(f"❌ Cannot apply: constitutional check failed for {recommendation.parameter.registry_path}")
            return False

        if require_approval and recommendation.requires_approval:
            logger.warning(f"⚠️  Approval required for high-risk change: {recommendation.recommendation_id}")
            # Em produção: aguardar aprovação via API/dashboard
            return False

        # Backup do valor atual para rollback
        old_value = recommendation.parameter.current_value

        try:
            # Aplicar mudança via Registry API (mock)
            logger.info(f"🔧 Applying: {recommendation.parameter.registry_path} = {recommendation.suggested_value}")
            # registry_api.set_value(..., recommendation.suggested_value)

            # Aguardar estabilização e medir impacto
            await asyncio.sleep(30)  # Mock: aguardar Φ_C recalcular
            new_phi_c = self._measure_current_phi_c()  # Mock function

            # Registrar histórico
            phi_c_before_val = self._measure_current_phi_c()
            history = OptimizationHistory(
                recommendation=recommendation,
                applied=True,
                applied_timestamp=time.time(),
                phi_c_before=phi_c_before_val,
                phi_c_after=new_phi_c,
                actual_phi_c_delta=(new_phi_c or 0) - (phi_c_before_val or 0),
                rollback_triggered=False,
                temporal_chain_seal=None
            )

            # Verificar se Φ_C degradou além do threshold
            if new_phi_c and new_phi_c < self.min_phi_c_threshold:
                logger.warning(f"⚠️  Φ_C degraded to {new_phi_c:.3f}; triggering rollback")
                await self._rollback_change(recommendation, old_value)
                history.rollback_triggered = True
                history.actual_phi_c_delta = None

            # Ancorar na TemporalChain
            history.temporal_chain_seal = await self._anchor_optimization_event(history)
            self._optimization_history.append(history)

            return not history.rollback_triggered

        except Exception as e:
            logger.error(f"❌ Failed to apply recommendation: {e}")
            # Tentar rollback em caso de erro
            await self._rollback_change(recommendation, old_value)
            return False

    async def _rollback_change(self, recommendation: OptimizationRecommendation,
                            original_value: Any):
        """Reverte mudança de configuração para valor original."""
        logger.info(f"🔄 Rolling back: {recommendation.parameter.registry_path} → {original_value}")
        # registry_api.set_value(..., original_value)
        await asyncio.sleep(5)  # Mock: aguardar aplicação

    def _measure_current_phi_c(self) -> Optional[float]:
        """Mede Φ_C composto atual (mock: em produção, consultar API)."""
        # Mock: retornar valor simulado com ruído
        return 0.92 + np.random.normal(0, 0.02)

    async def _anchor_optimization_event(self, history: OptimizationHistory) -> str:
        """Ancora evento de otimização na TemporalChain."""
        payload = {
            "recommendation_id": history.recommendation.recommendation_id,
            "parameter": history.recommendation.parameter.registry_path,
            "old_value": history.recommendation.parameter.current_value,
            "new_value": history.recommendation.suggested_value,
            "phi_c_before": history.phi_c_before,
            "phi_c_after": history.phi_c_after,
            "rollback_triggered": history.rollback_triggered,
            "timestamp": time.time()
        }
        seal = hashlib.sha3_256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()
        logger.debug(f"🔗 Optimization anchored: {seal[:16]}...")
        return seal

    def get_optimization_stats(self) -> Dict:
        """Retorna estatísticas de otimizações aplicadas."""
        if not self._optimization_history:
            return {"total_recommendations": 0}

        applied = [h for h in self._optimization_history if h.applied]
        successful = [h for h in applied if not h.rollback_triggered and h.actual_phi_c_delta is not None]

        avg_delta = np.mean([h.actual_phi_c_delta for h in successful if h.actual_phi_c_delta is not None]) if successful else 0

        return {
            "total_recommendations": len(self._optimization_history),
            "applied_count": len(applied),
            "successful_count": len(successful),
            "rollback_count": sum(1 for h in applied if h.rollback_triggered),
            "avg_phi_c_delta": avg_delta,
            "last_recommendation": self._optimization_history[-1].recommendation.to_dict() if self._optimization_history else None
        }
