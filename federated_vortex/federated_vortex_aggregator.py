#!/usr/bin/env python3
"""
federated_vortex_aggregator.py — Agregação federada via ressonância de vórtice.
Sem troca de bits clássicos: a agregação ocorre por projeção no núcleo compartilhado.
"""

import numpy as np
import torch
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import hashlib
import time

from vortex_entanglement.multi_particle_vortex import MultiParticleVortex, VortexFiberConfig

@dataclass
class VortexFederatedConfig:
    """Configuração para agregação federada por vórtice."""
    # Parâmetros do vórtice
    num_particles: int
    fiber_configs: List[VortexFiberConfig]
    manifold_dim: int = 1
    hbar: float = 1.0
    beta_nonlinear: float = 0.5

    # Parâmetros de aprendizado
    learning_rate: float = 0.01
    aggregation_window: int = 10  # passos entre agregações
    projection_method: str = 'gaussian'  # 'gaussian', 'hard', 'adaptive'

    # Privacidade (opcional)
    add_dp_noise: bool = False
    epsilon_dp: float = 1.0
    delta_dp: float = 1e-5

class VortexFederatedAggregator:
    """
    Agregador federado que usa o núcleo do vórtice como canal de agregação.
    Nenhuma comunicação clássica é necessária: a sincronização ocorre via geometria.
    """

    def __init__(self, config: VortexFederatedConfig):
        self.config = config

        # Instanciar modelo de vórtice multipartícula
        self.vortex = MultiParticleVortex(
            num_particles=config.num_particles,
            fiber_configs=config.fiber_configs,
            manifold_dim=config.manifold_dim,
            hbar=config.hbar,
            beta_nonlinear=config.beta_nonlinear
        )

        # Buffer para gradientes locais (simula "computação local")
        self.local_gradient_buffer: Dict[str, List[np.ndarray]] = defaultdict(list)

        # Histórico de agregações para auditoria
        self.aggregation_history: List[Dict] = []

        # Contador de rounds federados
        self.federation_round = 0

    def submit_local_gradient(
        self,
        participant_id: str,
        gradient: np.ndarray,
        loss_value: float,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Submete gradiente local para agregação futura.
        Em produção: isso seria computado localmente no dispositivo quântico.
        """
        # Armazenar gradiente no buffer
        self.local_gradient_buffer[participant_id].append({
            'gradient': gradient,
            'loss': loss_value,
            'timestamp': time.time(),
            'metadata': metadata or {}
        })

        # Gerar ID único para rastreamento
        grad_hash = hashlib.sha256(
            f"{participant_id}_{time.time()}_{np.sum(gradient)}".encode()
        ).hexdigest()[:12]

        return grad_hash

    def _apply_dp_noise(self, gradient: np.ndarray) -> np.ndarray:
        """Aplica ruído diferencial de privacidade se configurado."""
        if not self.config.add_dp_noise:
            return gradient

        # Gaussian mechanism para (ε, δ)-DP
        sensitivity = np.linalg.norm(gradient)  # L2 sensitivity
        sigma = sensitivity * np.sqrt(2 * np.log(1.25 / self.config.delta_dp)) / self.config.epsilon_dp
        noise = np.random.randn(*gradient.shape) * sigma
        return gradient + noise

    def _project_to_tangent_space(self, gradient: np.ndarray, psi: np.ndarray) -> np.ndarray:
        """Projeta gradiente no espaço tangente da fibra U(1)."""
        # Para U(1): componente imaginária da fase relativa
        # ⟨ψ|∇L⟩_imag = Im(ψ* · ∇L)
        tangent = np.imag(np.conj(psi) * gradient)
        return tangent

    def perform_vortex_aggregation(self) -> Dict[str, any]:
        """
        Executa agregação federada via projeção no núcleo do vórtice.
        Retorna métricas da agregação.
        """
        # Verificar se há gradientes suficientes
        active_participants = [
            pid for pid, grads in self.local_gradient_buffer.items()
            if len(grads) > 0
        ]

        if len(active_participants) < 2:
            return {'status': 'insufficient_participants', 'active_count': len(active_participants)}

        # Coletar gradientes mais recentes de cada participante
        recent_gradients = {}
        for pid in active_participants:
            latest = self.local_gradient_buffer[pid][-1]
            grad = self._apply_dp_noise(latest['gradient'])
            recent_gradients[pid] = {
                'gradient': grad,
                'loss': latest['loss'],
                'timestamp': latest['timestamp']
            }

        # Evoluir vórtice para sincronizar fases
        t_evolve = 1.0  # tempo de evolução para sincronização
        for pid in active_participants:
            self.vortex.evolve_particle(pid, t_final=t_evolve)

        # Calcular projeção no núcleo (agregação geométrica)
        psi_aggregated = self.vortex.compute_core_projection()

        # Atualizar conexão de Berry via gradientes projetados
        tangent_gradients = {
            pid: self._project_to_tangent_space(data['gradient'], self.vortex.psi_states[pid])
            for pid, data in recent_gradients.items()
        }

        update_result = self.vortex.update_berry_connection(
            local_gradients=tangent_gradients,
            learning_rate=self.config.learning_rate
        )

        # Calcular métricas de qualidade da agregação
        entanglement_metrics = self.vortex.get_entanglement_metrics()

        # Registrar histórico
        self.aggregation_history.append({
            'round': self.federation_round,
            'timestamp': time.time(),
            'active_participants': active_participants,
            'phase_update': update_result['phase_update'],
            'avg_loss': np.mean([d['loss'] for d in recent_gradients.values()]),
            'entanglement_fidelity': np.mean([
                v for k, v in entanglement_metrics.items() if 'fidelity' in k
            ]),
            'bell_violations': sum(1 for k, v in entanglement_metrics.items()
                                 if 'bell_S' in k and v > 2.0)
        })

        # Limpar buffer de gradientes processados
        for pid in active_participants:
            if self.local_gradient_buffer[pid]:
                self.local_gradient_buffer[pid].pop()

        self.federation_round += 1

        return {
            'status': 'success',
            'round': self.federation_round,
            'phase_update': update_result['phase_update'],
            'entanglement_metrics': entanglement_metrics,
            'aggregation_quality': {
                'avg_fidelity': np.mean([v for k, v in entanglement_metrics.items() if 'fidelity' in k]),
                'num_bell_violations': sum(1 for k, v in entanglement_metrics.items() if 'bell_S' in k and v > 2.0),
                'coherence_norm': np.linalg.norm(psi_aggregated)
            }
        }

    def get_aggregated_model_state(self) -> Dict[str, np.ndarray]:
        """
        Retorna o estado agregado do modelo (projeção no núcleo).
        Pode ser usado para inferência distribuída sem comunicação.
        """
        psi_agg = self.vortex.compute_core_projection()
        return {
            'aggregated_wavefunction': psi_agg,
            'core_amplitude': psi_agg[self.vortex.nx // 2],  # valor em x=0
            'federation_round': self.federation_round,
            'entanglement_verified': any(
                v > 2.0 for k, v in self.vortex.get_entanglement_metrics().items()
                if 'bell_S' in k
            )
        }

    def export_audit_log(self, path: str):
        """Exporta log de agregações para auditoria externa."""
        import json
        audit_data = {
            'config': {
                'num_particles': self.config.num_particles,
                'learning_rate': self.config.learning_rate,
                'dp_enabled': self.config.add_dp_noise,
                'epsilon': self.config.epsilon_dp if self.config.add_dp_noise else None
            },
            'aggregation_history': self.aggregation_history,
            'final_entanglement_metrics': self.vortex.get_entanglement_metrics(),
            'export_timestamp': time.time()
        }

        with open(path, 'w') as f:
            json.dump(audit_data, f, indent=2, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else str(x))

        print(f"✅ Audit log exportado para {path}")
