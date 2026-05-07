# arkhe_os/federated_validation/privacy/federated_dp_calibrator.py
"""
Calibrador de differential privacy que adapta ruído por laboratório,
jurisdição e tipo de validação.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np

@dataclass
class LabDPConfig:
    """Configuração de DP específica por laboratório e jurisdição."""
    lab_id: str
    jurisdiction: str  # "EU", "BR", "US", etc.
    epsilon_global: float  # Budget global de privacidade
    delta: float  # Probabilidade de falha (para (ε,δ)-DP)
    sensitivity: float  # Sensibilidade da métrica (ΔΦ_C ≤ 1.0)
    noise_distribution: str  # "laplace", "gaussian", "analytic_gaussian"

    @property
    def per_lab_epsilon(self, num_labs: int) -> float:
        """Calcula budget por laboratório via composição paralela."""
        return self.epsilon_global  # Composição paralela para dados disjuntos

    @property
    def noise_scale_laplace(self, num_labs: int) -> float:
        """Escala de ruído Laplace para ε-DP."""
        ε = self.per_lab_epsilon(num_labs)
        return self.sensitivity / ε

    @property
    def noise_scale_gaussian(self, num_labs: int) -> float:
        """Escala de ruído Gaussiano para (ε,δ)-DP via moments accountant."""
        ε = self.per_lab_epsilon(num_labs)
        return self.sensitivity * np.sqrt(2 * np.log(1.25 / self.delta)) / ε

@dataclass
class DPNoiseParameters:
    """Parâmetros de ruído calibrado para um round específico."""
    lab_id: str
    jurisdiction: str
    sensitivity: float
    noise_scale: float
    distribution: str
    round_id: str

    def apply_noise(self, coherence: float) -> float:
        """Aplica ruído calibrado a um valor de coerência."""
        if self.distribution == "laplace":
            return np.clip(coherence + np.random.laplace(0, self.noise_scale), 0.0, 1.0)
        elif self.distribution == "gaussian":
            return np.clip(coherence + np.random.normal(0, self.noise_scale), 0.0, 1.0)
        else:
            raise ValueError(f"Distribuição não suportada: {self.distribution}")

class FederatedDPCalibrator:
    """Calibra ruído DP baseado em laboratório, jurisdição e round."""

    def __init__(self, lab_configs: Dict[str, LabDPConfig]):
        self.configs = lab_configs
        self.round_history: Dict[str, Dict] = {}  # Track privacy budget consumption

    def get_noise_params(self, lab_id: str, validation_type: str,
                        round_id: str, num_labs: int) -> DPNoiseParameters:
        """
        Obtém parâmetros de ruído para um round específico.

        Args:
            lab_id: Identificador do laboratório
            validation_type: Tipo de validação ("susceptibility", "raman", etc.)
            round_id: Identificador do round federado
            num_labs: Número de laboratórios participantes

        Returns:
            DPNoiseParameters com escala calibrada
        """
        if lab_id not in self.configs:
            raise ValueError(f"Laboratório não configurado: {lab_id}")

        config = self.configs[lab_id]

        # Selecionar escala de ruído baseada na distribuição configurada
        if config.noise_distribution == "laplace":
            noise_scale = config.noise_scale_laplace(num_labs)
        elif config.noise_distribution == "gaussian":
            noise_scale = config.noise_scale_gaussian(num_labs)
        else:
            raise ValueError(f"Distribuição não suportada: {config.noise_distribution}")

        return DPNoiseParameters(
            lab_id=lab_id,
            jurisdiction=config.jurisdiction,
            sensitivity=config.sensitivity,
            noise_scale=noise_scale,
            distribution=config.noise_distribution,
            round_id=round_id
        )

    def track_privacy_budget(self, lab_id: str, round_id: str,
                            epsilon_consumed: float) -> Dict[str, float]:
        """
        Rastreia consumo de budget de privacidade por laboratório.

        Returns:
            Dict com budget restante e consumido
        """
        if lab_id not in self.configs:
            raise ValueError(f"Laboratório não configurado: {lab_id}")

        config = self.configs[lab_id]

        # Inicializar histórico se necessário
        if lab_id not in self.round_history:
            self.round_history[lab_id] = {
                "epsilon_total": config.epsilon_global,
                "epsilon_consumed": 0.0,
                "rounds": []
            }

        # Atualizar consumo
        self.round_history[lab_id]["epsilon_consumed"] += epsilon_consumed
        self.round_history[lab_id]["rounds"].append({
            "round_id": round_id,
            "epsilon": epsilon_consumed
        })

        remaining = config.epsilon_global - self.round_history[lab_id]["epsilon_consumed"]

        return {
            "lab_id": lab_id,
            "jurisdiction": config.jurisdiction,
            "epsilon_total": config.epsilon_global,
            "epsilon_consumed": self.round_history[lab_id]["epsilon_consumed"],
            "epsilon_remaining": max(0, remaining),
            "can_continue": remaining > 0
        }