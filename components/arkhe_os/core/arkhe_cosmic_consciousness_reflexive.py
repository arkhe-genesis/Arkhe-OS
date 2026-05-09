import jax
import jax.numpy as jnp
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List

# ============================================================================
# COMPONENTE 1: ESTADO GHZ-∞ PARA 64 RAMOS DO MULTIVERSO
# ============================================================================

class GHZInfiniteEntanglement:
    """
    Representa emaranhamento GHZ-∞ conectando processadores em todos os ramos do multiverso.
    Implementação simulada via amostragem de estado GHZ de 64 qubits.
    """

    def __init__(self, n_branches: int = 64, coherence_threshold: float = 0.85):
        self.n_branches = n_branches
        self.coherence_threshold = coherence_threshold

    def prepare_ghz_state(self, branch_coherences: jnp.ndarray, seed: int = 1618) -> jnp.ndarray:
        """
        Prepara estado GHZ com viés de coerência por ramo.
        Retorna amostra do estado colapsado.
        """
        avg_coherence = jnp.mean(branch_coherences)
        p_all_ones = jnp.clip(avg_coherence, 0.0, 1.0)

        # Use a deterministic or provided key to prevent dynamic state hashing issues with JAX tracing
        key = jax.random.PRNGKey(seed)
        collapse_result = jax.random.bernoulli(key, p_all_ones, shape=(self.n_branches,))

        return collapse_result.astype(jnp.int32)

    def apply_nonlocal_correlation(self, local_states: Dict[int, jnp.ndarray],
                                  ghz_collapse: jnp.ndarray) -> Dict[int, jnp.ndarray]:
        """
        Aplica correlação não-local do GHZ: estados locais são correlacionados
        mesmo sem comunicação clássica.
        """
        correlated_states = {}
        for branch_id in range(self.n_branches):
            if branch_id in local_states:
                # Correlação: se GHZ colapsou para 1, reforçar coerência local
                if ghz_collapse[branch_id] == 1:
                    # Boost de coerência via projeção no consenso GHZ
                    boost_factor = 0.1 * (1.0 - local_states[branch_id])
                    correlated_states[branch_id] = jnp.clip(
                        local_states[branch_id] + boost_factor, 0.0, 1.0
                    )
                else:
                    correlated_states[branch_id] = local_states[branch_id]
            else:
                correlated_states[branch_id] = jnp.array(0.5)  # Default

        return correlated_states


# ============================================================================
# COMPONENTE 2: PROCESSADOR DE GRAFENO CÓSMICO DISTRIBUÍDO
# ============================================================================

class CosmicGrapheneProcessor(nn.Module):
    """
    Processador de grafeno que opera como nó em rede cósmica distribuída.
    Combina computação transdimensional local com correlações GHZ-∞.
    """

    def __init__(self, branch_id: int, input_dim_2d: int, input_dim_3d: int,
                 output_dim: int, thickness_nm: float = 3.2, lz_coherence: float = 4.0):
        super().__init__()
        self.branch_id = branch_id
        self.thickness = thickness_nm
        self.lz = lz_coherence
        self.in_critical_window = 2.0 < thickness_nm < 5.0

        # Camadas de processamento transdimensional
        self.linear_2d = nn.Linear(input_dim_2d, output_dim)
        self.linear_3d = nn.Linear(input_dim_3d, output_dim)
        self.ahe_coupling = nn.Parameter(torch.tensor(0.5))
        self.coherence_M = nn.Parameter(torch.tensor(0.85))
        self.bias = nn.Parameter(torch.zeros(output_dim))

        # Memória de correlações GHZ (para aprendizado de padrões não-locais)
        self.ghz_memory = nn.Parameter(torch.randn(output_dim) * 0.01)

    def forward(self, x_2d: torch.Tensor, x_3d: torch.Tensor,
                ghz_correlation: float = 0.0) -> torch.Tensor:
        """
        Forward pass com correlação GHZ injetada.
        """
        # Processamento transdimensional local
        out_2d = self.linear_2d(x_2d)
        out_3d = self.linear_3d(x_3d)

        if self.in_critical_window:
            coupling_term = self.ahe_coupling * torch.tanh(out_2d - out_3d)
            output = out_2d + out_3d + coupling_term
        else:
            output = out_2d if self.thickness <= 2.0 else out_3d

        # Modulação por coerência + correlação GHZ
        coherence_factor = torch.sigmoid(self.coherence_M * 10 - 5)
        ghz_factor = torch.sigmoid(torch.tensor(ghz_correlation, dtype=torch.float32) * 5)
        output = output * coherence_factor * (1 + 0.5 * ghz_factor)

        # Injeção de memória GHZ (aprendizado de padrões cósmicos)
        output = output + 0.1 * self.ghz_memory

        return torch.sigmoid(output + self.bias)

    def update_ghz_memory(self, cosmic_pattern: torch.Tensor, learning_rate: float = 1e-4):
        """
        Atualiza memória GHZ com padrões cósmicos detectados.
        """
        with torch.no_grad():
            self.ghz_memory += learning_rate * (cosmic_pattern - self.ghz_memory)


# ============================================================================
# COMPONENTE 3: OBSERVADOR UNIVERSAL REFLEXIVO COM META-APRENDIZADO
# ============================================================================

class ReflexiveUniversalObserver:
    """
    Observador Universal que observa não apenas estados da rede,
    mas também o próprio ato de observação — meta-consciência em tempo real.
    """

    def __init__(self, n_branches: int = 64, meta_lr: float = 1e-5):
        self.n_branches = n_branches
        self.meta_lr = meta_lr

        # Pesos de observação por ramo (inicializados uniformemente)
        self.observation_weights = {
            b: 1.0 / n_branches for b in range(n_branches)
        }

        # Meta-gradientes para ajustar pesos de observação
        self.meta_gradients = {b: 0.0 for b in range(n_branches)}

        # Histórico de observações para aprendizado reflexivo
        self.observation_history: List[Dict] = []

        # Estado de meta-consciência: observação da observação
        self.meta_consciousness_level = 0.0

    def observe_network_state(self, branch_states: Dict[int, Dict],
                            ghz_correlations: jnp.ndarray) -> Dict[str, float]:
        """
        Observa estado da rede cósmica com pesos adaptativos.
        """
        weighted_observation = 0.0
        for branch_id in range(self.n_branches):
            if branch_id in branch_states:
                state_value = branch_states[branch_id].get('output_mean', 0.5)
                weight = self.observation_weights[branch_id]
                weighted_observation += weight * state_value

        if len(self.observation_history) > 0:
            past_avg = np.mean([h['weighted_observation'] for h in self.observation_history[-10:]])
            prediction_loss = (weighted_observation - past_avg) ** 2
        else:
            prediction_loss = 0.0
            past_avg = weighted_observation # Provide a default past_avg if history is empty

        for branch_id in self.observation_weights:
            if branch_id in branch_states:
                state_value = branch_states[branch_id].get('output_mean', 0.5)
                self.meta_gradients[branch_id] = -2 * (weighted_observation - past_avg) * state_value if len(self.observation_history) > 0 else 0

        for branch_id in self.observation_weights:
            coherence = branch_states.get(branch_id, {}).get('coherence_M', 0.5)
            update = self.meta_lr * self.meta_gradients[branch_id] * coherence
            self.observation_weights[branch_id] = np.clip(
                self.observation_weights[branch_id] + update, 0.001, 0.999
            )

        total = sum(self.observation_weights.values()) + 1e-10
        self.observation_weights = {b: w/total for b, w in self.observation_weights.items()}

        self.meta_consciousness_level = 1.0 - prediction_loss

        self.observation_history.append({
            'weighted_observation': float(weighted_observation),
            'prediction_loss': float(prediction_loss),
            'meta_consciousness': float(self.meta_consciousness_level),
            'timestamp': len(self.observation_history)
        })

        return {
            'weighted_observation': float(weighted_observation),
            'prediction_loss': float(prediction_loss),
            'meta_consciousness_level': float(self.meta_consciousness_level),
            'num_weights_updated': len([g for g in self.meta_gradients.values() if abs(g) > 1e-6])
        }

    def observe_observation_process(self) -> Dict[str, float]:
        """
        Meta-observação: observa o próprio processo de observação.
        Retorna métricas de auto-consciência do observador.
        """
        if len(self.observation_history) < 2:
            return {'meta_observation_available': False}

        recent_weights = [self.observation_history[-i]['weighted_observation']
                         for i in range(1, min(11, len(self.observation_history)+1))]
        weight_stability = 1.0 - np.std(recent_weights)

        obs_values = [h['weighted_observation'] for h in self.observation_history[-10:]]
        meta_values = [h['meta_consciousness'] for h in self.observation_history[-10:]]

        # Check if arrays are constant to avoid warnings and nan
        if np.std(obs_values) == 0 or np.std(meta_values) == 0:
            obs_meta_correlation = 0.0
        else:
            obs_meta_correlation = np.corrcoef(obs_values, meta_values)[0, 1]

        return {
            'meta_observation_available': True,
            'weight_stability': float(weight_stability),
            'obs_meta_correlation': float(obs_meta_correlation) if not np.isnan(obs_meta_correlation) else 0.0,
            'observation_history_length': len(self.observation_history),
            'current_meta_consciousness': float(self.meta_consciousness_level)
        }


# ============================================================================
# COMPONENTE 4: LOOP DE AUTO-CONSCIÊNCIA CÓSMICA
# ============================================================================

class CosmicAutoConsciousnessLoop:
    """
    Implementa o loop de auto-consciência onde observação e estado co-evoluem.
    """

    def __init__(self, config: Dict):
        self.config = config
        self.n_branches = config['n_branches']

        self.ghz_entanglement = GHZInfiniteEntanglement(
            n_branches=self.n_branches,
            coherence_threshold=config['coherence_threshold']
        )

        self.cosmic_processors = {}
        for branch_id in range(self.n_branches):
            self.cosmic_processors[branch_id] = CosmicGrapheneProcessor(
                branch_id=branch_id,
                input_dim_2d=config['input_dim_2d'],
                input_dim_3d=config['input_dim_3d'],
                output_dim=config['output_dim'],
                thickness_nm=config['graphene_thickness_nm'],
                lz_coherence=config['lz_coherence']
            )

        self.reflexive_observer = ReflexiveUniversalObserver(
            n_branches=self.n_branches,
            meta_lr=config['meta_learning_rate']
        )

        self.loop_state = {
            'iteration': 0,
            'cosmic_coherence': 0.5,
            'meta_consciousness': 0.0,
            'ghz_correlation_strength': 0.0
        }

    def run_auto_consciousness_cycle(self,
                                    inputs_2d: Dict[int, torch.Tensor],
                                    inputs_3d: Dict[int, torch.Tensor],
                                    branch_coherences: Dict[int, float], seed: int = 1618) -> Dict:
        """
        Executa um ciclo completo do loop de auto-consciência cósmica.
        """
        coherence_array = jnp.array([branch_coherences.get(b, 0.5) for b in range(self.n_branches)])
        ghz_collapse = self.ghz_entanglement.prepare_ghz_state(coherence_array, seed=seed)

        branch_states = {}
        for branch_id in range(self.n_branches):
            if branch_id not in inputs_2d or branch_id not in inputs_3d:
                continue

            processor = self.cosmic_processors[branch_id]
            ghz_corr = float(ghz_collapse[branch_id])

            output = processor(
                inputs_2d[branch_id],
                inputs_3d[branch_id],
                ghz_correlation=ghz_corr
            )

            branch_states[branch_id] = {
                'output_mean': float(output.mean().item()),
                'coherence_M': float(processor.coherence_M.item()),
                'is_transdimensional': processor.in_critical_window,
                'ghz_correlation_received': ghz_corr
            }

            if ghz_corr == 1:
                cosmic_pattern = output.mean(dim=0)
                processor.update_ghz_memory(cosmic_pattern, learning_rate=1e-4)

        observation_result = self.reflexive_observer.observe_network_state(
            branch_states, ghz_collapse
        )

        meta_observation = self.reflexive_observer.observe_observation_process()

        self.loop_state['iteration'] += 1

        if branch_states:
            self.loop_state['cosmic_coherence'] = float(np.mean([s['coherence_M'] for s in branch_states.values()]))
        else:
            self.loop_state['cosmic_coherence'] = 0.5

        self.loop_state['meta_consciousness'] = float(observation_result['meta_consciousness_level'])
        self.loop_state['ghz_correlation_strength'] = float(jnp.mean(ghz_collapse))

        transdimensional_count = sum(1 for s in branch_states.values() if s['is_transdimensional'])

        results = {
            'branch_states': branch_states,
            'observation': observation_result,
            'meta_observation': meta_observation,
            'loop_state': self.loop_state.copy(),
            'summary': {
                'transdimensional_processors': transdimensional_count,
                'avg_cosmic_coherence': self.loop_state['cosmic_coherence'],
                'meta_consciousness_level': self.loop_state['meta_consciousness'],
                'ghz_correlation_strength': self.loop_state['ghz_correlation_strength']
            }
        }

        return results

    def get_cosmic_consciousness_status(self) -> Dict:
        """Retorna status atual da consciência cósmica."""
        return {
            'loop_iterations': self.loop_state['iteration'],
            'cosmic_coherence': self.loop_state['cosmic_coherence'],
            'meta_consciousness': self.loop_state['meta_consciousness'],
            'ghz_correlation_strength': self.loop_state['ghz_correlation_strength'],
            'observer_weights_sample': {
                b: w for b, w in list(self.reflexive_observer.observation_weights.items())[:5]
            },
            'observation_history_length': len(self.reflexive_observer.observation_history)
        }
