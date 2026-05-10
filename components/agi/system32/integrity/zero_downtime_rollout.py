#!/usr/bin/env python3
"""
zero_downtime_rollout.py — Estratégia de deploy sem downtime
com rollback automático baseado em coerência.
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class DeploymentState:
    version: str
    status: str  # 'deploying', 'active', 'rollback', 'failed'
    phi_c: float
    health_checks_passed: bool

class ZeroDowntimeRollout:
    """Gerencia rollouts sem downtime baseados em coerência."""

    def __init__(self, min_phi_c: float = 0.7):
        self.min_phi_c = min_phi_c
        self.active_deployment: DeploymentState = None
        self.history: list = []

    def start_deployment(self, version: str) -> DeploymentState:
        """Inicia um novo deployment em paralelo (Blue/Green)."""
        new_dep = DeploymentState(
            version=version,
            status='deploying',
            phi_c=0.0,
            health_checks_passed=False
        )
        return new_dep

    def evaluate_deployment(self, deployment: DeploymentState, current_phi_c: float, health_passed: bool) -> str:
        """Avalia se o deployment atual deve ser promovido ou sofrer rollback."""
        deployment.phi_c = current_phi_c
        deployment.health_checks_passed = health_passed

        if not health_passed:
            deployment.status = 'failed'
            return 'rollback'

        if current_phi_c < self.min_phi_c:
            deployment.status = 'rollback'
            return 'rollback'

        # Se passar nos checks e tiver coerência suficiente, promove
        deployment.status = 'active'
        if self.active_deployment:
            self.history.append(self.active_deployment)
        self.active_deployment = deployment
        return 'success'

    def trigger_rollback(self) -> bool:
        """Aciona rollback automático para a última versão estável."""
        if not self.history:
            return False

        # Pega o último deployment bem sucedido
        last_stable = None
        for dep in reversed(self.history):
            if dep.status == 'active':
                last_stable = dep
                break

        if last_stable:
            self.active_deployment = last_stable
            return True

        return False
