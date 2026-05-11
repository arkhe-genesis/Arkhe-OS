#!/usr/bin/env python3
"""
expanded_parameter_space.py
Espaço de parâmetros expandido para otimização conjunta via SPSA e busca em grade.
"""
import numpy as np

def multi_objective_score(classification_result, model_complexity_penalty=0.01):
    """
    Função objetivo que balanceia CAPTURE fraction com complexidade do modelo.

    Args:
        classification_result: saída do pipeline Ising
        model_complexity_penalty: peso para penalizar embedding_dim alto

    Returns:
        score: valor escalar a ser maximizado
    """
    capture_frac = classification_result['capture_fraction']

    # Penalizar dimensionalidade excessiva (Occam's razor geométrico)
    avg_dim = np.mean([
        info.get('manifold_dim', 3)
        for info in classification_result['community_details'].values()
        if info['regime'] == 'CAPTURE'
    ]) if any(info['regime'] == 'CAPTURE' for info in classification_result['community_details'].values()) else 0

    complexity_penalty = model_complexity_penalty * avg_dim

    # Bonus por coesão média das comunidades CAPTURE
    capture_cohesion = np.mean([
        abs(info['rho'])
        for info in classification_result['community_details'].values()
        if info['regime'] == 'CAPTURE'
    ]) if any(info['regime'] == 'CAPTURE'
              for info in classification_result['community_details'].values()) else 0
    cohesion_bonus = 0.1 * capture_cohesion

    return capture_frac - complexity_penalty + cohesion_bonus


class AdaptiveParameterOptimizer:
    """Otimizador que combina SPSA com busca em grade adaptativa para espaço expandido."""

    def __init__(self, param_ranges, initial_point,
                 spsa_params={'a': 0.4, 'c': 0.2},
                 grid_refinement_interval=5):
        """
        Args:
            param_ranges: dict {param_name: (min, max)}
            initial_point: dict {param_name: initial_value}
            spsa_params: hiperparâmetros para SPSA
            grid_refinement_interval: a cada N epochs, refinar busca local
        """
        self.param_names = list(param_ranges.keys())
        self.bounds = [param_ranges[name] for name in self.param_names]
        self.theta = np.array([initial_point[name] for name in self.param_names], dtype=float)
        self.a, self.c = spsa_params['a'], spsa_params['c']
        self.grid_interval = grid_refinement_interval
        self.best_score = -np.inf
        self.best_params = self.theta.copy()

    def refine_with_grid_search(self, evaluate_fn, radius=0.1, steps_per_dim=3):
        """Busca em grade local ao redor dos melhores parâmetros atuais."""
        center = self.best_params
        grid_points = []

        # Gerar grade multidimensional
        for i, (name, (min_val, max_val)) in enumerate(zip(self.param_names, self.bounds)):
            center_val = center[i]
            # Limitar raio aos bounds
            low = max(min_val, center_val - radius * (max_val - min_val))
            high = min(max_val, center_val + radius * (max_val - min_val))
            grid_points.append(np.linspace(low, high, steps_per_dim))

        # Avaliar todos os pontos da grade
        best_local_score = -np.inf
        best_local_params = center.copy()

        from itertools import product
        for point in product(*grid_points):
            point_array = np.array(point)
            score = evaluate_fn(point_array)
            if score > best_local_score:
                best_local_score = score
                best_local_params = point_array

        return best_local_params, best_local_score

    def optimize(self, evaluate_fn, max_epochs=50):
        """
        Loop principal de otimização.

        Args:
            evaluate_fn: função que recebe array de parâmetros e retorna score
            max_epochs: número total de iterações

        Returns:
            history: lista de registros por epoch
        """
        history = []

        for k in range(1, max_epochs + 1):
            # Avaliar ponto atual
            current_score = evaluate_fn(self.theta)

            # Refinamento com grade a intervalos regulares
            if k % self.grid_interval == 0 and current_score > self.best_score:
                print(f"  🔍 Epoch {k}: Refinando com busca em grade...")
                refined_params, refined_score = self.refine_with_grid_search(evaluate_fn)
                if refined_score > current_score:
                    self.theta = refined_params
                    current_score = refined_score
                    print(f"     ✓ Refinamento melhorou score: {current_score:.4f}")

            # Atualizar melhor histórico
            if current_score > self.best_score:
                self.best_score = current_score
                self.best_params = self.theta.copy()

            # SPSA: estimar gradiente
            delta = np.random.choice([-1, 1], size=len(self.param_names))
            theta_plus = np.clip(self.theta + self.c * delta, *zip(*self.bounds))
            theta_minus = np.clip(self.theta - self.c * delta, *zip(*self.bounds))

            score_plus = evaluate_fn(theta_plus)
            score_minus = evaluate_fn(theta_minus)
            grad_est = (score_plus - score_minus) / (2 * self.c * delta)

            # Atualização
            ak = self.a / (k ** 0.602)
            self.theta = self.theta + ak * grad_est # Maximize
            self.theta = np.clip(self.theta, *zip(*self.bounds))

            # Registrar
            record = {
                'epoch': k,
                'params': {name: float(val) for name, val in zip(self.param_names, self.theta)},
                'score': float(current_score),
                'best_score': float(self.best_score),
                'grid_refinement': (k % self.grid_interval == 0)
            }
            history.append(record)

            print(f"Epoch {k:2d}: score={current_score:.4f}, best={self.best_score:.4f}, "
                  f"params={dict(zip(self.param_names, [f'{v:.3f}' for v in self.theta]))}")

        return history, self.best_params.copy(), self.best_score
