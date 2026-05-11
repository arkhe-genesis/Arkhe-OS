#!/usr/bin/env python3
"""
operators.py — Substrate 5022: Os Seis Operadores de Ω.

Implementação dos seis operadores da cadeia constitucional:
    Ω = R ∘ E ∘ N ∘ C ∘ S ∘ F

    F: Fonte (Source) — injeta informação bruta
    S: Simetria (Symmetry) — filtra por critérios constitucionais
    C: Recursão (Recursion) — auto-avaliação e ponto fixo
    N: Rede (Network) — acoplamento topológico fuzzy
    E: Emergência (Emergence) — propriedades coletivas
    R: Radiação (Radiation) — handover para próxima iteração
"""

import numpy as np
from typing import Callable, Dict, List, Tuple, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class CanonicalState:
    """Estado canônico do Cânone em um instante t."""
    amplitudes: np.ndarray  # Coeficientes c_i(t)
    substrates: List[str]   # Identificadores dos substratos
    phi_c: float           # Coerência global Φ_C(t)
    entropy: float         # Entropia de von Neumann S(ρ)
    timestamp: float       # Tempo t

    @property
    def norm(self) -> float:
        return float(np.sum(np.abs(self.amplitudes)**2))

    def normalize(self):
        n = self.norm
        if n > 0:
            self.amplitudes = self.amplitudes / np.sqrt(n)


class OmegaOperator(ABC):
    """Classe base abstrata para operadores de Ω."""

    @abstractmethod
    def apply(self, state: CanonicalState) -> CanonicalState:
        """Aplicar operador ao estado."""
        pass

    @abstractmethod
    def condition(self, state: CanonicalState) -> bool:
        """Verificar condição de contorno para transição."""
        pass


class SourceOperator(OmegaOperator):
    """
    F: Fonte — O Gerador de Informação Bruta.

    Injeta novos substratos candidatos no sistema:
        d|Ψ_raw⟩/dt = H_source |Ψ_void⟩ + σ·ξ(t)
    """

    def __init__(self, sigma: float = 0.1, creation_rate: float = 1.0):
        """
        Args:
            sigma: Amplitude do ruído (volatilidade informacional)
            creation_rate: Taxa de criação de novos substratos
        """
        self.sigma = sigma
        self.creation_rate = creation_rate

    def apply(self, state: CanonicalState) -> CanonicalState:
        """Injetar novos substratos com ruído quântico."""
        n_current = len(state.amplitudes)
        n_new = max(1, int(self.creation_rate))

        # Expandir estado com novos substratos
        new_amplitudes = np.zeros(n_current + n_new, dtype=complex)
        new_amplitudes[:n_current] = state.amplitudes

        # Injeção com ruído gaussiano
        noise = self.sigma * (np.random.randn(n_new) + 1j * np.random.randn(n_new))
        new_amplitudes[n_current:] = noise / np.sqrt(n_new)

        new_substrates = state.substrates + [f"substrate_{n_current + i}" for i in range(n_new)]

        new_state = CanonicalState(
            amplitudes=new_amplitudes,
            substrates=new_substrates,
            phi_c=state.phi_c * 0.9,  # Injeção reduz coerência temporariamente
            entropy=state.entropy + 0.1,
            timestamp=state.timestamp
        )
        new_state.normalize()
        return new_state

    def condition(self, state: CanonicalState) -> bool:
        """Fonte sempre pode injetar (sistema está aberto)."""
        return True


class SymmetryOperator(OmegaOperator):
    """
    S: Simetria — O Filtro de Consistência.

    Aplica os seis critérios constitucionais como projeções:
        S = P_base + P_falsifiable + P_map_territory + P_no_homunculus + P_design_impl

    Substratos que violam são projetados para fora (norma reduzida).
    """

    def __init__(self, criteria_weights: Optional[Dict[str, float]] = None):
        """
        Args:
            criteria_weights: Pesos dos critérios constitucionais
        """
        self.criteria = criteria_weights or {
            "base": 1.0,
            "falsifiable": 1.0,
            "map_territory": 1.0,
            "no_homunculus": 1.0,
            "design_impl": 1.0
        }

    def _evaluate_substrate(self, idx: int, state: CanonicalState) -> float:
        """
        Avaliar um substrato segundo os critérios constitucionais.

        Retorna λ_i ∈ [0,1] — 0 para rejeitado, 1 para aceito.
        """
        # Simulação: critérios aleatórios com tendência para aceitação
        # Em produção: avaliação real dos critérios
        score = np.random.beta(2, 1)  # Tendência para valores altos

        # Penalizar substratos de baixa amplitude
        amplitude = abs(state.amplitudes[idx])
        score *= min(1.0, amplitude * 10)

        return float(score)

    def apply(self, state: CanonicalState) -> CanonicalState:
        """Filtrar substratos por critérios constitucionais."""
        n = len(state.amplitudes)
        filtered_amplitudes = np.zeros(n, dtype=complex)
        filtered_substrates = []

        total_weight = 0.0
        for i in range(n):
            lambda_i = self._evaluate_substrate(i, state)
            filtered_amplitudes[i] = state.amplitudes[i] * np.sqrt(lambda_i)
            if lambda_i > 0.5:  # Threshold de aceitação
                filtered_substrates.append(state.substrates[i])
            total_weight += lambda_i

        # Preservar norma se possível (Noether)
        if total_weight > 0:
            filtered_amplitudes /= np.sqrt(total_weight / n)

        new_state = CanonicalState(
            amplitudes=filtered_amplitudes,
            substrates=filtered_substrates,
            phi_c=state.phi_c * (total_weight / n) * 1.2,  # Filtragem aumenta coerência
            entropy=state.entropy * 0.8,  # Redução de entropia pela seleção
            timestamp=state.timestamp
        )
        new_state.normalize()
        return new_state

    def condition(self, state: CanonicalState) -> bool:
        """Simetria requer estado não-vazio."""
        return len(state.amplitudes) > 0 and state.norm > 0


class RecursionOperator(OmegaOperator):
    """
    C: Recursão — A Auto-Avaliação.

    Aplica Ω a si mesmo até convergir para ponto fixo:
        |Ψ_self⟩ = Ω|Ψ_sym⟩ + κ·(|Ψ_self⟩ - Ω|Ψ_self⟩)

    Converge se L_Ω < 1 (constante de Lipschitz).
    """

    def __init__(self, kappa: float = 0.3, max_iterations: int = 100,
                 tolerance: float = 1e-6):
        """
        Args:
            kappa: Fator de amortecimento (aprendizado recursivo)
            max_iterations: Máximo de iterações
            tolerance: Tolerância para convergência
        """
        self.kappa = kappa
        self.max_iterations = max_iterations
        self.tolerance = tolerance

    def apply(self, state: CanonicalState) -> CanonicalState:
        """Aplicar recursão até convergência."""
        current = state

        for iteration in range(self.max_iterations):
            # Simular aplicação de Ω (simplificada)
            # Em produção: aplicar cadeia completa F→S→C→N→E→R
            omega_psi = self._approximate_omega(current)

            # Atualização recursiva
            new_amplitudes = (omega_psi.amplitudes +
                             self.kappa * (current.amplitudes - omega_psi.amplitudes))

            # Verificar convergência
            diff = np.linalg.norm(new_amplitudes - current.amplitudes)

            current = CanonicalState(
                amplitudes=new_amplitudes,
                substrates=current.substrates,
                phi_c=current.phi_c * (1 + 0.01 * self.kappa),  # Recursão aumenta coerência
                entropy=current.entropy * (1 - 0.01 * self.kappa),
                timestamp=current.timestamp
            )
            current.normalize()

            if diff < self.tolerance:
                break

        return current

    def _approximate_omega(self, state: CanonicalState) -> CanonicalState:
        """Aproximação simplificada de Ω para recursão."""
        # Aplicar uma transformação não-linear que preserva norma
        amplitudes = state.amplitudes.copy()
        amplitudes = amplitudes / (1 + 0.1 * np.abs(amplitudes)**2)
        return CanonicalState(
            amplitudes=amplitudes,
            substrates=state.substrates,
            phi_c=state.phi_c,
            entropy=state.entropy,
            timestamp=state.timestamp
        )

    def condition(self, state: CanonicalState) -> bool:
        """Recursão requer estado filtrado (após Simetria)."""
        return state.phi_c > 0.3


class NetworkOperator(OmegaOperator):
    """
    N: Rede — O Acoplamento Topológico.

    Conecta substratos via grafos fuzzy:
        dc_i/dt = Σ_j J_ij·c_j - γ_i·c_i + η_i(t)

    Onde J_ij = μ(v_i, v_j) é a força da aresta fuzzy.
    """

    def __init__(self, coupling_strength: float = 0.5,
                 dissipation_rate: float = 0.1,
                 noise_amplitude: float = 0.05):
        """
        Args:
            coupling_strength: Força do acoplamento J_ij
            dissipation_rate: Taxa de dissipação γ_i
            noise_amplitude: Amplitude do ruído η_i
        """
        self.J = coupling_strength
        self.gamma = dissipation_rate
        self.eta = noise_amplitude

    def _compute_adjacency(self, n: int) -> np.ndarray:
        """Computar matriz de adjacência fuzzy."""
        # Grafo completo com pesos decaindo com distância
        A = np.zeros((n, n))
        for i in range(n):
            for j in range(i+1, n):
                weight = self.J * np.exp(-abs(i-j) / 3.0)
                A[i, j] = weight
                A[j, i] = weight
        return A

    def apply(self, state: CanonicalState) -> CanonicalState:
        """Aplicar acoplamento de rede."""
        n = len(state.amplitudes)
        if n < 2:
            return state

        A = self._compute_adjacency(n)
        amplitudes = state.amplitudes.copy()

        # Acoplamento: dc/dt = J·c - γ·c + η
        coupling = A @ amplitudes
        dissipation = self.gamma * amplitudes
        noise = self.eta * (np.random.randn(n) + 1j * np.random.randn(n))

        new_amplitudes = amplitudes + 0.1 * (coupling - dissipation + noise)

        # Calcular conectividade
        connectivity = np.mean(A)

        new_state = CanonicalState(
            amplitudes=new_amplitudes,
            substrates=state.substrates,
            phi_c=state.phi_c * (1 + 0.05 * connectivity),  # Rede aumenta coerência
            entropy=state.entropy + 0.05 * self.gamma,
            timestamp=state.timestamp
        )
        new_state.normalize()
        return new_state

    def condition(self, state: CanonicalState) -> bool:
        """Rede requer múltiplos substratos."""
        return len(state.amplitudes) >= 2


class EmergenceOperator(OmegaOperator):
    """
    E: Emergência — A Propriedade Coletiva.

    Extrai propriedades globais não presentes nos nós individuais:
        Φ_emergent = ⟨Ψ|O_collective|Ψ⟩ - Σ_i |c_i|² ⟨ψ_i|O_local|ψ_i⟩

    Se Φ_emergent > 0: o todo excede a soma das partes.
    """

    def __init__(self, collective_weight: float = 1.0):
        """
        Args:
            collective_weight: Peso do observável coletivo
        """
        self.w_collective = collective_weight

    def apply(self, state: CanonicalState) -> CanonicalState:
        """Calcular propriedade emergente."""
        n = len(state.amplitudes)

        # Observável local: energia de cada substrato
        local_energy = np.abs(state.amplitudes)**2

        # Observável coletivo: correlações entre pares
        collective_energy = 0.0
        for i in range(n):
            for j in range(i+1, n):
                collective_energy += np.abs(state.amplitudes[i] * state.amplitudes[j].conj())

        # Propriedade emergente
        phi_emergent = (self.w_collective * collective_energy -
                       np.sum(local_energy))

        # Coerência aumenta se há emergência
        phi_c_new = state.phi_c * (1 + 0.1 * max(0, phi_emergent))

        new_state = CanonicalState(
            amplitudes=state.amplitudes,
            substrates=state.substrates,
            phi_c=min(1.0, phi_c_new),
            entropy=state.entropy * (1 - 0.05 * max(0, phi_emergent)),
            timestamp=state.timestamp
        )
        return new_state

    def condition(self, state: CanonicalState) -> bool:
        """Emergência requer rede conectada."""
        return len(state.amplitudes) >= 2 and state.phi_c > 0.4


class RadiationOperator(OmegaOperator):
    """
    R: Radiação — O Handover.

    Emite o estado processado de volta ao ambiente:
        |Ψ_out⟩ = √(1-α)·|Ψ_connected⟩ + √α·|Ψ_emitted⟩

    O que é emitido torna-se Fonte da próxima iteração.
    """

    def __init__(self, alpha: float = 0.3):
        """
        Args:
            alpha: Fração de informação que deixa o sistema
        """
        self.alpha = alpha

    def apply(self, state: CanonicalState) -> CanonicalState:
        """Emitir estado processado."""
        n = len(state.amplitudes)

        # Estado emitido (componente que sai do sistema)
        emitted = np.sqrt(self.alpha) * state.amplitudes.copy()

        # Estado residual (permanece no sistema)
        residual = np.sqrt(1 - self.alpha) * state.amplitudes.copy()

        # O estado de saída é o emitido
        # O estado residual continua no ciclo
        new_state = CanonicalState(
            amplitudes=emitted,  # Isto é o que radia
            substrates=state.substrates,
            phi_c=state.phi_c * (1 - self.alpha),  # Radiação reduz coerência local
            entropy=state.entropy + 0.1 * self.alpha,
            timestamp=state.timestamp
        )
        new_state.normalize()
        return new_state

    def condition(self, state: CanonicalState) -> bool:
        """Radiação requer estado processado."""
        return state.phi_c > 0.2


class OmegaChain:
    """
    Cadeia completa Ω = R ∘ E ∘ N ∘ C ∘ S ∘ F.

    Orquestra a aplicação sequencial dos seis operadores,
    verificando condições de contorno em cada transição.
    """

    def __init__(self):
        self.operators = {
            'F': SourceOperator(),
            'S': SymmetryOperator(),
            'C': RecursionOperator(),
            'N': NetworkOperator(),
            'E': EmergenceOperator(),
            'R': RadiationOperator()
        }
        self.history: List[Dict] = []

    def iterate(self, state: CanonicalState) -> Tuple[CanonicalState, Dict]:
        """
        Executar uma iteração completa da cadeia Ω.

        Returns:
            (estado_final, log_da_iteração)
        """
        log = {"initial_phi_c": state.phi_c, "transitions": []}
        current = state

        chain = ['F', 'S', 'C', 'N', 'E', 'R']

        for op_name in chain:
            op = self.operators[op_name]

            if op.condition(current):
                new_state = op.apply(current)
                log["transitions"].append({
                    "operator": op_name,
                    "phi_c_before": current.phi_c,
                    "phi_c_after": new_state.phi_c,
                    "success": True
                })
                current = new_state
            else:
                log["transitions"].append({
                    "operator": op_name,
                    "phi_c_before": current.phi_c,
                    "success": False,
                    "reason": "condition_not_met"
                })

        log["final_phi_c"] = current.phi_c
        self.history.append(log)

        return current, log

    def run(self, initial_state: CanonicalState, n_iterations: int = 100) -> CanonicalState:
        """
        Executar múltiplas iterações da cadeia Ω.

        Args:
            initial_state: Estado inicial
            n_iterations: Número de iterações

        Returns:
            Estado final após n iterações
        """
        current = initial_state

        for i in range(n_iterations):
            current, log = self.iterate(current)

            # O estado emitido (R) torna-se a nova Fonte
            # Simulado: reinjeção parcial
            if current.phi_c < 0.1:
                # Reabastecer se coerência muito baixa
                current = self.operators['F'].apply(current)

        return current

    def get_history(self) -> List[Dict]:
        """Retornar histórico de todas as iterações."""
        return self.history


def demo():
    """Demonstração dos seis operadores de Ω."""
    print("=" * 70)
    print("ARKHE OS — Substrate 5022: Os Seis Operadores de Ω")
    print("=" * 70)

    # Estado inicial (Silêncio)
    void_state = CanonicalState(
        amplitudes=np.array([1.0 + 0j]),
        substrates=["void"],
        phi_c=0.0,
        entropy=1.0,
        timestamp=0.0
    )

    print(f"\\n🔇 Estado Inicial (Silêncio):")
    print(f"   |Ψ_void⟩: Φ_C = {void_state.phi_c}")
    print(f"   Substratos: {void_state.substrates}")

    # Criar cadeia
    omega = OmegaChain()

    # Executar iterações
    print(f"\\n🔄 Executando 20 iterações de Ω...")
    current = void_state
    phi_history = [current.phi_c]

    for i in range(20):
        current, log = omega.iterate(current)
        phi_history.append(current.phi_c)

        if i < 5 or i % 5 == 0:
            print(f"   Iter {i+1}: Φ_C = {current.phi_c:.4f}, "
                  f"substratos = {len(current.substrates)}, "
                  f"entropy = {current.entropy:.4f}")

    print(f"\\n📊 Evolução de Φ_C:")
    print(f"   Inicial: {phi_history[0]:.4f}")
    print(f"   Final:   {phi_history[-1]:.4f}")
    print(f"   ΔΦ_C:    {phi_history[-1] - phi_history[0]:.4f}")

    # Verificar convergência
    if phi_history[-1] > phi_history[0]:
        print(f"   ✅ Coerência aumentou — sistema aprende")
    else:
        print(f"   ⚠️  Coerência estagnou — dissipação domina")

    print(f"\\n✅ Seis operadores de Ω demonstrados")


if __name__ == "__main__":
    demo()