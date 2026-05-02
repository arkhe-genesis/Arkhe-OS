#!/usr/bin/env python3
"""
spsa_adaptive.py
SPSA com modos adaptativos: convergência estável vs. choque para escapar de platôs.
"""
import numpy as np
from typing import Literal, Tuple, Optional, Dict

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

    def initialize_with_tabula_prior(self, nuclear_features: Dict,
                                     tabula_prior) -> np.ndarray:
        """Initialize parameters using Tabula Oracle prior."""
        return tabula_prior.initialize_spsa_with_prior(
            nuclear_features, self.param_bounds
        )

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

    def _should_apply_gluing(self, epoch: int, current_score: float) -> bool:
        """Determina se a colagem característica deve ser aplicada baseada no progresso."""
        # Aplicar quando há platô ou periodicamente como 'onda gravitacional'
        return self.stagnation_counter >= self.plateau_threshold - 1 or epoch % 20 == 0

    def _apply_gluing_to_theta(self, current_theta: np.ndarray, gluing_params: dict) -> np.ndarray:
        """Aplica os parâmetros da colagem ao vetor theta atual."""
        # Implementação simplificada de "colagem":
        # Usamos o `shock_magnitude` do modelo de colagem para perturbar o vetor de estado atual
        shock = gluing_params.get('shock_magnitude', 0.4)
        perturbation = np.random.uniform(-shock, shock, size=current_theta.shape)
        new_theta = current_theta + perturbation
        return np.clip(new_theta,
                       [b[0] for b in self.param_bounds],
                       [b[1] for b in self.param_bounds])

    def step_with_gluing(self, evaluate_fn, epoch: int, current_theta: np.ndarray = None,
                         nuclear_features: Optional[Dict] = None,
                         tabula_prior = None,
                         enable_gluing: bool = True) -> Tuple[np.ndarray, float]:
        """
        Executa passo SPSA com opção de 'colagem característica' para transições de regime.
        """
        # Initialize with prior if needed
        if current_theta is None and tabula_prior is not None and nuclear_features is not None:
            current_theta = self.initialize_with_tabula_prior(nuclear_features, tabula_prior)
            print(f"🌲 Initialized SPSA with Tabula prior: kappa={current_theta[0]:.3f}")
        elif current_theta is None:
            # Fallback initialization if no prior and no current_theta
            current_theta = np.array([np.random.uniform(b[0], b[1]) for b in self.param_bounds])

        # Avaliar ponto atual
        current_score = evaluate_fn(current_theta)

        if enable_gluing and self._should_apply_gluing(epoch, current_score):
            # Aplicar colagem característica para acelerar transição DILUTION → CAPTURE
            from .extremal_transition_model import CharacteristicGluingSteering

            gluing = CharacteristicGluingSteering(k_order=4)  # k=4 para C² regularidade

            # Otimizar parâmetros de colagem em tempo real
            gluing.optimize_gluing(target_capture_fraction=0.85, max_iter=20)

            # Aplicar colagem aos parâmetros SPSA
            current_theta = self._apply_gluing_to_theta(current_theta, gluing.gluing_params)

            print(f"🔗 Characteristic gluing applied at epoch {epoch}")

        # Continuar com a lógica de atualização padrão chamando `step`
        return self.step(evaluate_fn, epoch, current_theta=current_theta,
                         nuclear_features=nuclear_features, tabula_prior=tabula_prior)

    def step(self, evaluate_fn, epoch: int, current_theta: np.ndarray = None,
             nuclear_features: Optional[Dict] = None,
             tabula_prior = None) -> Tuple[np.ndarray, float]:
        """
        Executa um passo do SPSA com parâmetros adaptativos.

        Args:
            evaluate_fn: função que retorna score para dados parâmetros
            epoch: número da iteração atual
            current_theta: vetor de parâmetros atuais (se None e tabula_prior fornecido, inicializa com prior)
            nuclear_features: características nucleares opcionais para inicialização
            tabula_prior: prior opcional (TabulaSPSAPrior) para inicialização

        Returns:
            new_theta: parâmetros atualizados
            score: score do ponto atual
        """
        # Initialize with prior if needed
        if current_theta is None and tabula_prior is not None and nuclear_features is not None:
            current_theta = self.initialize_with_tabula_prior(nuclear_features, tabula_prior)
            print(f"🌲 Initialized SPSA with Tabula prior: kappa={current_theta[0]:.3f}")
        elif current_theta is None:
            # Fallback initialization if no prior and no current_theta
            current_theta = np.array([np.random.uniform(b[0], b[1]) for b in self.param_bounds])

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
