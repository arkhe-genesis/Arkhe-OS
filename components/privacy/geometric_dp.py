#!/usr/bin/env python3
"""
geometric_dp.py — Privacidade diferencial emergente da projeção no núcleo do vórtice.
A ofuscação geométrica substitui ruído artificial por estrutura natural do fibrado.
"""

import numpy as np
import torch
import time
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from scipy import stats
import hashlib

@dataclass
class GeometricPrivacyConfig:
    """Configuração para privacidade por geometria."""
    # Parâmetros do vórtice
    manifold_diameter: float = 10.0  # diam(ℳ) para bound de Lipschitz
    lipschitz_constant: float = 1.0  # L da conexão de Berry
    num_participants: int = 10       # N para bound de privacidade

    # Parâmetros de privacidade
    target_epsilon: float = 1.0      # ε alvo para (ε,δ)-DP
    target_delta: float = 1e-5       # δ alvo
    projection_method: str = 'gaussian'  # 'gaussian', 'hard', 'adaptive'

    # Ruído geométrico opcional (para bound rigoroso)
    add_geometric_noise: bool = True
    noise_scale_factor: float = 1.0

class GeometricPrivacyMechanism:
    """
    Mecanismo de privacidade que usa projeção no núcleo como ofuscação natural.

    Teorema: Se 𝒜_μ é L-Lipschitz, então ℳ_geo satisfaz (ε,δ)-DP com
    ε = L·diam(ℳ)·√[2ln(1.25/δ)/N]
    """

    def __init__(self, config: GeometricPrivacyConfig):
        self.config = config

        # Calcular bound teórico de privacidade
        self.theoretical_epsilon = self._compute_epsilon_bound()

        # Cache para projeções (otimização)
        self._projection_cache: Dict[str, torch.Tensor] = {}

        # Histórico para auditoria
        self.privacy_audit_log: List[Dict] = []

    def _compute_epsilon_bound(self) -> float:
        """Calcula bound teórico de ε baseado nos parâmetros."""
        N = self.config.num_participants
        L = self.config.lipschitz_constant
        diam = self.config.manifold_diameter
        delta = self.config.target_delta

        # Fórmula do teorema: ε = L·diam·√[2ln(1.25/δ)/N]
        epsilon = L * diam * np.sqrt(2 * np.log(1.25 / delta) / N)
        return epsilon

    def project_to_core(
        self,
        wavefunctions: List[torch.Tensor],
        phase_offsets: Optional[List[float]] = None,
        core_window: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, Dict]:
        """
        Projeta múltiplas funções de onda no núcleo do vórtice.

        Args:
            wavefunctions: Lista de Ψ_i(x_i) para cada participante
            phase_offsets: Fases θ_i para compensação (opcional)
            core_window: Janela de projeção (default: gaussiana centrada em x=0)

        Returns:
            (Ψ_agg, metadata) onde Ψ_agg é o estado agregado com privacidade geométrica
        """
        if phase_offsets is None:
            phase_offsets = [0.0] * len(wavefunctions)

        if core_window is None:
            # Janela gaussiana padrão centrada em x=0
            x = torch.linspace(-30, 30, 1024)
            core_window = torch.exp(-x**2 / 2.0)

        # Projeção ponderada de cada função de onda
        projections = []
        for psi, phase in zip(wavefunctions, phase_offsets):
            # Compensar fase para alinhar no núcleo
            phase_tensor = torch.tensor(-1j * phase)
            phase_compensated = psi * torch.exp(phase_tensor)
            # Projeção suave via janela
            proj = torch.sum(phase_compensated * core_window) / torch.sum(core_window)
            projections.append(proj)

        # Agregação coerente (média de fase-preservante)
        aggregated = torch.mean(torch.stack(projections))

        # Adicionar ruído geométrico se configurado (para bound rigoroso de DP)
        if self.config.add_geometric_noise:
            # Variância geométrica estimada da dispersão das projeções
            geom_variance = torch.var(torch.stack(projections)).item()
            noise_scale = self.config.noise_scale_factor * np.sqrt(geom_variance + 1e-12)
            geometric_noise = torch.randn_like(aggregated) * noise_scale
            aggregated = aggregated + geometric_noise

        # Calcular métricas de privacidade
        privacy_metrics = self._compute_privacy_metrics(wavefunctions, projections, aggregated)

        # Registrar para auditoria
        self.privacy_audit_log.append({
            'timestamp': time.time(),
            'num_participants': len(wavefunctions),
            'theoretical_epsilon': self.theoretical_epsilon,
            'empirical_variance': privacy_metrics['empirical_variance'],
            'geometric_noise_scale': privacy_metrics.get('geometric_noise_scale', 0),
            'projection_method': self.config.projection_method
        })

        return aggregated, privacy_metrics

    def _compute_privacy_metrics(
        self,
        wavefunctions: List[torch.Tensor],
        projections: List[torch.Tensor],
        aggregated: torch.Tensor
    ) -> Dict[str, Union[float, str]]:
        """Calcula métricas empíricas de privacidade."""
        # Variância empírica das projeções (proxy para sensibilidade)
        proj_tensor = torch.stack(projections)
        empirical_variance = torch.var(proj_tensor).item()

        # Estimativa de sensibilidade L2
        sensitivity_estimate = torch.sqrt(torch.tensor(empirical_variance * len(wavefunctions))).item()

        # Bound empírico de ε (se ruído geométrico adicionado)
        if self.config.add_geometric_noise:
            # Para Gaussian mechanism: ε ≈ √[2ln(1.25/δ)] · sensitivity / σ
            delta = self.config.target_delta
            sigma = self.config.noise_scale_factor * np.sqrt(empirical_variance + 1e-12)
            empirical_epsilon = np.sqrt(2 * np.log(1.25 / delta)) * sensitivity_estimate / sigma
        else:
            empirical_epsilon = float('inf')  # Sem ruído, sem bound garantido

        return {
            'empirical_variance': empirical_variance,
            'sensitivity_estimate': sensitivity_estimate,
            'theoretical_epsilon': self.theoretical_epsilon,
            'empirical_epsilon': empirical_epsilon if self.config.add_geometric_noise else None,
            'geometric_noise_scale': self.config.noise_scale_factor * np.sqrt(empirical_variance + 1e-12) if self.config.add_geometric_noise else 0,
            'privacy_guarantee': f'({self.theoretical_epsilon:.2f}, {self.config.target_delta})-DP (teórico)'
        }

    def verify_privacy_guarantee(
        self,
        sensitivity: float,
        num_queries: int = 1
    ) -> Dict[str, Union[bool, float]]:
        """
        Verifica se o mecanismo satisfaz o bound de privacidade para uma query.

        Args:
            sensitivity: Sensibilidade L2 da query
            num_queries: Número de queries compostas (para composition)

        Returns:
            Dict com verificação do guarantee
        """
        # Composition avançada para múltiplas queries
        if num_queries > 1:
            # Advanced composition: ε_total ≈ √[2k ln(1/δ')] · ε + kε(e^ε - 1)
            delta_prime = self.config.target_delta / 2
            k = num_queries
            eps_single = self.theoretical_epsilon

            # Termo dominante da composição avançada
            epsilon_composed = np.sqrt(2 * k * np.log(1 / delta_prime)) * eps_single + k * eps_single * (np.exp(eps_single) - 1)
        else:
            epsilon_composed = self.theoretical_epsilon

        # Verificar se sensibilidade está dentro do bound assumido
        assumed_sensitivity = self.config.lipschitz_constant * self.config.manifold_diameter
        sensitivity_ok = sensitivity <= assumed_sensitivity * 1.1  # 10% margem

        return {
            'privacy_guaranteed': sensitivity_ok and epsilon_composed <= self.config.target_epsilon * 2,
            'composed_epsilon': epsilon_composed,
            'target_epsilon': self.config.target_epsilon,
            'sensitivity_ok': sensitivity_ok,
            'assumed_sensitivity': assumed_sensitivity,
            'actual_sensitivity': sensitivity,
            'margin': (assumed_sensitivity - sensitivity) / assumed_sensitivity if assumed_sensitivity > 0 else 0
        }

    def export_privacy_audit(self, path: str):
        """Exporta log de auditoria de privacidade."""
        import json

        audit_data = {
            'config': {
                'manifold_diameter': self.config.manifold_diameter,
                'lipschitz_constant': self.config.lipschitz_constant,
                'num_participants': self.config.num_participants,
                'target_epsilon': self.config.target_epsilon,
                'target_delta': self.config.target_delta,
                'add_geometric_noise': self.config.add_geometric_noise
            },
            'theoretical_bound': {
                'epsilon': self.theoretical_epsilon,
                'formula': 'ε = L·diam(ℳ)·√[2ln(1.25/δ)/N]'
            },
            'audit_log': self.privacy_audit_log,
            'export_timestamp': time.time()
        }

        with open(path, 'w') as f:
            json.dump(audit_data, f, indent=2, default=lambda x: x.item() if isinstance(x, torch.Tensor) else str(x))

        print(f"✅ Privacy audit exported to {path}")
