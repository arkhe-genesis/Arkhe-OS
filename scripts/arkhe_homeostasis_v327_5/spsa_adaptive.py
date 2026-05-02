#!/usr/bin/env python3
"""
spsa_adaptive.py
SPSA com modos adaptativos: convergência estável vs. choque para escapar de platôs.
"""
import numpy as np
from typing import Literal, Tuple, Optional

class AdaptiveSPSA:
    """
    SPSA com modos adaptativos para navegação em paisagens de otimização complexas.

    Modos:
    - 'stable': a=0.1, c=0.05 (convergência suave)
    - 'aggressive': a=0.4, c=0.2 (choque para escapar de platôs)
    - 'adaptive': troca automática baseado em progresso
    """

    def __init__(self,
                 param_bounds: list,
                 mode: Literal['stable', 'aggressive', 'adaptive'] = 'adaptive',
                 plateau_threshold: int = 5,
                 min_improvement: float = 0.01):
        self.param_bounds = param_bounds
        self.mode = mode
        self.plateau_threshold = plateau_threshold
        self.min_improvement = min_improvement

        # Hiperparâmetros por modo
        self.hyperparams = {
            'stable': {'a': 0.1, 'c': 0.05},
            'aggressive': {'a': 0.4, 'c': 0.2},  # Choque de parâmetros
            'adaptive': {'a': 0.1, 'c': 0.05}  # Começa estável
        }

        self.current_params = self.hyperparams['adaptive'].copy()
        self.stagnation_counter = 0
        self.best_score = -np.inf
        self.history = []

    def _apply_shock_if_needed(self, current_score: float) -> bool:
        """Verifica se deve aplicar choque de parâmetros."""
        if self.mode != 'adaptive':
            return self.mode == 'aggressive'

        # Atualizar melhor histórico
        if current_score > self.best_score + self.min_improvement:
            self.best_score = current_score
            self.stagnation_counter = 0
            return False

        self.stagnation_counter += 1

        # Aplicar choque após estagnação prolongada
        if self.stagnation_counter >= self.plateau_threshold:
            print(f"   ⚡ PLATÔ DETECTADO ({self.stagnation_counter} epochs) — Aplicando choque de parâmetros!")
            self.current_params = self.hyperparams['aggressive'].copy()
            self.stagnation_counter = 0
            return True

        return False

    def step(self, evaluate_fn, epoch: int, current_theta: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Executa um passo do SPSA com parâmetros adaptativos.

        Args:
            evaluate_fn: função que retorna score para dados parâmetros
            epoch: número da iteração atual
            current_theta: vetor de parâmetros atuais

        Returns:
            new_theta: parâmetros atualizados
            score: score do ponto atual
        """
        # Avaliar ponto atual
        current_score = evaluate_fn(current_theta)
        self.history.append(current_score)

        # Verificar necessidade de choque
        shock_applied = self._apply_shock_if_needed(current_score)

        # Obter hiperparâmetros atuais
        a = self.current_params['a']
        c = self.current_params['c']

        # Gerar vetor de perturbação aleatória (±1)
        delta = np.random.choice([-1, 1], size=len(current_theta))

        # Avaliar pontos perturbados
        theta_plus = np.clip(current_theta + c * delta,
                            [b[0] for b in self.param_bounds],
                            [b[1] for b in self.param_bounds])
        theta_minus = np.clip(current_theta - c * delta,
                             [b[0] for b in self.param_bounds],
                             [b[1] for b in self.param_bounds])

        score_plus = evaluate_fn(theta_plus)
        score_minus = evaluate_fn(theta_minus)

        # Estimar gradiente
        grad_est = (score_plus - score_minus) / (2 * c * delta + 1e-10)

        # Atualização com learning rate decrescente
        ak = a / (epoch ** 0.602)
        new_theta = current_theta + ak * grad_est # Note that here we are maximizing, so +
        new_theta = np.clip(new_theta,
                           [b[0] for b in self.param_bounds],
                           [b[1] for b in self.param_bounds])

        # Log de diagnóstico
        if shock_applied:
            print(f"   📈 Choque aplicado: a={a}, c={c} → score: {current_score:.4f}")

        return new_theta, current_score
