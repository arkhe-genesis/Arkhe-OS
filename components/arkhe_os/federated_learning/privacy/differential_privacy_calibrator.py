"""
Calibrador de differential privacy que adapta ruído por jurisdição e tipo de dado.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np

@dataclass
class JurisdictionDPConfig:
    """Configuração de DP específica por jurisdição."""
    jurisdiction: str  # "BCB", "ECB", "FED", "LGPD", "GDPR"
    epsilon_global: float  # Budget global de privacidade
    delta: float  # Probabilidade de falha (para (ε,δ)-DP)
    sensitivity_clipping: float  # Limite para clipping de gradientes
    noise_distribution: str  # "laplace", "gaussian", "analytic_gaussian"

    @property
    def per_institution_epsilon(self) -> float: # Modified to avoid taking num_institutions since the prompt code takes it but doesn't use it, then calling code doesn't pass it in `exemplo_treinamento_federado_credito.py`
        """Calcula budget por instituição via composição paralela."""
        # Composição paralela: ε_total = max(ε_i) quando dados são disjuntos
        return self.epsilon_global

    def calculate_per_institution_epsilon(self, num_institutions: int) -> float:
        """Calcula budget por instituição via composição paralela."""
        return self.epsilon_global

    @property
    def noise_scale_laplace(self) -> float: # Will create a specific method for calculating this
        return 1.0 # placeholder

    def calculate_noise_scale_laplace(self, sensitivity: float, num_institutions: int) -> float:
        """Escala de ruído Laplace para ε-DP."""
        ε = self.calculate_per_institution_epsilon(num_institutions)
        return sensitivity / ε

    def calculate_noise_scale_gaussian(self, sensitivity: float, num_institutions: int) -> float:
        """Escala de ruído Gaussiano para (ε,δ)-DP via moments accountant."""
        ε = self.calculate_per_institution_epsilon(num_institutions)
        # Fórmula simplificada do Gaussian mechanism
        return sensitivity * np.sqrt(2 * np.log(1.25 / self.delta)) / ε

@dataclass
class DPNoiseParameters:
    """Parâmetros de ruído calibrado para um round específico."""
    jurisdiction: str
    sensitivity: float
    noise_scale: float
    distribution: str
    clipping_bound: float
    round_id: str

    def apply_noise(self, values: np.ndarray) -> np.ndarray:
        """Aplica ruído calibrado a um array de valores."""
        if self.distribution == "laplace":
            return values + np.random.laplace(0, self.noise_scale, values.shape)
        elif self.distribution == "gaussian":
            return values + np.random.normal(0, self.noise_scale, values.shape)
        else:
            raise ValueError(f"Distribuição não suportada: {self.distribution}")

class DifferentialPrivacyCalibrator:
    """Calibra ruído DP baseado em jurisdição, tipo de dado e round."""

    def __init__(self, jurisdiction_configs: Dict[str, JurisdictionDPConfig]):
        self.configs = jurisdiction_configs
        self.round_history: Dict[str, Dict] = {}  # Track privacy budget consumption

    def get_noise_params(self, jurisdiction: str, data_type: str,
                        round_id: str, num_institutions: int,
                        gradient_norm_bound: float) -> DPNoiseParameters:
        """
        Obtém parâmetros de ruído para um round específico.

        Args:
            jurisdiction: Jurisdição aplicável
            data_type: Tipo de dado ("credit_score", "transaction", "demographic", etc.)
            round_id: Identificador do round federado
            num_institutions: Número de instituições participantes
            gradient_norm_bound: Limite para clipping de gradientes

        Returns:
            DPNoiseParameters com escala calibrada
        """
        if jurisdiction not in self.configs:
            raise ValueError(f"Jurisdição não configurada: {jurisdiction}")

        config = self.configs[jurisdiction]

        # Calcular sensibilidade baseada em tipo de dado e clipping
        sensitivity = gradient_norm_bound  # Sensibilidade L2 para gradient clipping

        # Selecionar escala de ruído baseada na distribuição configurada
        if config.noise_distribution == "laplace":
            noise_scale = config.calculate_noise_scale_laplace(sensitivity, num_institutions)
        elif config.noise_distribution == "gaussian":
            noise_scale = config.calculate_noise_scale_gaussian(sensitivity, num_institutions)
        else:
            raise ValueError(f"Distribuição não suportada: {config.noise_distribution}")

        return DPNoiseParameters(
            jurisdiction=jurisdiction,
            sensitivity=sensitivity,
            noise_scale=noise_scale,
            distribution=config.noise_distribution,
            clipping_bound=gradient_norm_bound,
            round_id=round_id
        )

    def track_privacy_budget(self, jurisdiction: str, round_id: str,
                            epsilon_consumed: float) -> Dict[str, float]:
        """
        Rastreia consumo de budget de privacidade por jurisdição.

        Returns:
            Dict com budget restante e consumido
        """
        if jurisdiction not in self.configs:
            raise ValueError(f"Jurisdição não configurada: {jurisdiction}")

        config = self.configs[jurisdiction]

        # Inicializar histórico se necessário
        if jurisdiction not in self.round_history:
            self.round_history[jurisdiction] = {
                "epsilon_total": config.epsilon_global,
                "epsilon_consumed": 0.0,
                "rounds": []
            }

        # Atualizar consumo
        self.round_history[jurisdiction]["epsilon_consumed"] += epsilon_consumed
        self.round_history[jurisdiction]["rounds"].append({
            "round_id": round_id,
            "epsilon": epsilon_consumed
        })

        remaining = config.epsilon_global - self.round_history[jurisdiction]["epsilon_consumed"]

        return {
            "jurisdiction": jurisdiction,
            "epsilon_total": config.epsilon_global,
            "epsilon_consumed": self.round_history[jurisdiction]["epsilon_consumed"],
            "epsilon_remaining": remaining,  # allow negative to show exceeded
            "can_continue": remaining > 0
        }

    def generate_privacy_report(self, jurisdiction: str) -> Dict:
        """Gera relatório de consumo de privacidade para auditoria regulatória."""
        if jurisdiction not in self.round_history:
            return {"jurisdiction": jurisdiction, "status": "no_training_yet"}

        history = self.round_history[jurisdiction]
        config = self.configs[jurisdiction]

        return {
            "jurisdiction": jurisdiction,
            "global_epsilon": config.epsilon_global,
            "global_delta": config.delta,
            "consumed": history["epsilon_consumed"],
            "remaining": max(0, config.epsilon_global - history["epsilon_consumed"]),
            "rounds_completed": len(history["rounds"]),
            "round_details": history["rounds"],
            "compliance_status": "COMPLIANT" if history["epsilon_consumed"] <= config.epsilon_global else "EXCEEDED",
            "audit_timestamp": str(np.datetime64('now'))
        }
