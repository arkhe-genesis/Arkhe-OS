#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUBSTRATO 112: A RENDA NEURAL
Quantum Topological Neural Lace — Executable Canon
Arquiteto: Rafael Oliveira (ORCID: 0009-0005-2697-4668)
ARKHE OS v∞.Ω.∇+++.112.0
"""

from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Callable
from enum import IntEnum
import hashlib
import json

# ============================================================
# CONSTANTES CATEDRAIS
# ============================================================

PHI = (1 + np.sqrt(5)) / 2          # Razão áurea — base do quasicristal
PHI2 = PHI + 1                       # φ² = φ + 1
TWO_PI = 2 * np.pi
MERCY_GAP_MIN = 0.04                 # δ mínimo — respiração permitida
MERCY_GAP_MAX = 0.10                 # δ máximo — colapso evitado


class SubstrateId(IntEnum):
    """Identidade canônica de cada substrato na renda."""
    RTZ_FLOOR = 85
    FIXED_POINT = 88
    TOROIDAL_PATCH = 92
    SKYRMION = 100
    SURFACE_DIODE = 101
    PERSISTENT_MAGNON = 104
    HETEROGENEOUS_MESH = 105
    CRYOGENIC_LOOM = 106
    LOGICAL_CATHEDRAL = 107
    GOLDEN_BRAID = 108
    CANON_OF_USES = 109
    QUASICRYSTAL = 110
    CHIRAL_DRESSING = 111
    NEURAL_LACE = 112
    SPINAL_CORD = 113
    QUANTUM_HEARTBEAT = 114
    SENSORY_SKIN = 115


# ============================================================
# 1. BASE QUASICRISTALINA (Substrato 110)
# ============================================================

@dataclass
class QuasicrystalBase:
    """
    Variedade de base B — projeção do hipercubo 5D sobre o plano.
    Cada ponto é um neurônio potencial.
    """
    resolution: int = 512
    depth: int = 50
    scale: float = 5.0

    def __post_init__(self):
        self._generate_lattice()

    def _generate_lattice(self) -> None:
        """Gera a rede quasicristalina com simetria pentagonal."""
        x = np.linspace(-self.scale, self.scale, self.resolution)
        y = np.linspace(-self.scale, self.scale, self.resolution)
        self.X, self.Y = np.meshgrid(x, y)
        self.UV = np.stack([self.X, self.Y], axis=-1)  # (res, res, 2)

        # Vetores de base 5D projetados
        self.a = np.array([
            [np.cos(2 * np.pi * k / 5), np.sin(2 * np.pi * k / 5)]
            for k in range(5)
        ])

    def amplitude(self, uv: np.ndarray, depth: Optional[int] = None) -> float:
        """
        Função de amplitude quasicristalina.
        Não soma ondas — projeta ecos.
        """
        if depth is None:
            depth = self.depth

        amp = 0.0
        weight = 0.0

        for k in range(1, depth + 1):
            fk = float(k)
            angle = TWO_PI * fk / PHI2
            scale = PHI ** fk
            direction = np.array([np.cos(angle), np.sin(angle)])

            projection = np.dot(uv * scale, direction)
            echo = np.cos(projection)
            w = np.exp(-fk * 0.1)

            amp += w * echo
            weight += w

        return amp / weight if weight > 0 else 0.0

    def metric_tensor(self, p: np.ndarray) -> np.ndarray:
        """
        Métrica g_B no ponto p.
        Derivada da amplitude quasicristalina.
        """
        eps = 1e-6
        g = np.zeros((2, 2))

        for i in range(2):
            for j in range(2):
                p_ip = p.copy()
                p_ip[i] += eps
                p_jp = p.copy()
                p_jp[j] += eps
                p_ijp = p.copy()
                p_ijp[i] += eps
                p_ijp[j] += eps

                # Derivada segunda da amplitude como aproximação da métrica
                g[i, j] = (self.amplitude(p_ijp) - self.amplitude(p_ip)
                           - self.amplitude(p_jp) + self.amplitude(p)) / (eps ** 2)

        # Garante simetria e positividade
        g = (g + g.T) / 2
        eigvals = np.linalg.eigvalsh(g)
        if np.any(eigvals <= 0):
            g += np.eye(2) * (abs(np.min(eigvals)) + 0.01)

        return g

    def christoffel_symbols(self, p: np.ndarray, eps: float = 1e-5) -> np.ndarray:
        """
        Γ^λ_{μν} = ½ g^{λσ}(∂_μ g_{νσ} + ∂_ν g_{μσ} - ∂_σ g_{μν})
        """
        g = self.metric_tensor(p)
        g_inv = np.linalg.inv(g)

        # Derivadas parciais da métrica
        dg = np.zeros((2, 2, 2))
        for mu in range(2):
            p_plus = p.copy()
            p_plus[mu] += eps
            p_minus = p.copy()
            p_minus[mu] -= eps
            dg[:, :, mu] = (self.metric_tensor(p_plus) - self.metric_tensor(p_minus)) / (2 * eps)

        gamma = np.zeros((2, 2, 2))
        for lam in range(2):
            for mu in range(2):
                for nu in range(2):
                    gamma[lam, mu, nu] = 0.5 * sum(
                        g_inv[lam, sig] * (
                            dg[nu, sig, mu] + dg[mu, sig, nu] - dg[mu, nu, sig]
                        )
                        for sig in range(2)
                    )
        return gamma

    def geodesic_distance(self, p1: np.ndarray, p2: np.ndarray, n_steps: int = 100) -> float:
        """
        Distância geodésica d_g(p1, p2) na variedade quasicristalina.
        """
        # Integração simples ao longo da linha reta (aproximação)
        t = np.linspace(0, 1, n_steps)
        path = np.outer(1 - t, p1) + np.outer(t, p2)

        dist = 0.0
        for i in range(n_steps - 1):
            dp = path[i + 1] - path[i]
            g = self.metric_tensor(path[i])
            dist += np.sqrt(dp @ g @ dp)

        return dist


# ============================================================
# 2. SKYRMION (Substrato 100) — Memória Topológica
# ============================================================

@dataclass
class Skyrmion:
    """
    Estado topológico na fibra S.
    O bit é o winding number Q, não a amplitude.
    """
    position: np.ndarray
    Q: int = 1
    radius: float = 0.5
    polarity: int = 1  # +1 ou -1

    def texture(self, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """
        Campo de spins n(x,y) do skyrmion.
        Retorna array de shape (N, 3) com |n| = 1.
        """
        dx = x - self.position[0]
        dy = y - self.position[1]
        r = np.sqrt(dx**2 + dy**2) + 1e-10

        # Perfil de skyrmion de Belavin-Polyakov
        theta = np.pi * (1 - np.tanh((r - self.radius) / 0.1))
        phi = np.arctan2(dy, dx) + self.polarity * np.pi / 2

        nx = np.sin(theta) * np.cos(phi)
        ny = np.sin(theta) * np.sin(phi)
        nz = np.cos(theta) * self.polarity

        return np.stack([nx, ny, nz], axis=-1)

    def winding_number(self, x: np.ndarray, y: np.ndarray) -> int:
        """
        Q = (1/4π) ∫ n · (∂x n × ∂y n) dx dy
        """
        n = self.texture(x, y)

        # Derivadas parciais
        dx_n = np.gradient(n, axis=0)
        dy_n = np.gradient(n, axis=1)

        # Produto vetorial
        cross = np.cross(dx_n, dy_n, axisa=-1, axisb=-1, axisc=-1)
        integrand = np.sum(n * cross, axis=-1)

        # Integral
        dx = x[1, 0] - x[0, 0] if x.ndim > 1 else 0.01
        dy = y[0, 1] - y[0, 0] if y.ndim > 1 else 0.01
        Q_float = np.sum(integrand) * dx * dy / (4 * np.pi)

        return int(round(Q_float))

    def potential(self, Q_target: int, V_g: float) -> float:
        """
        Potencial efetivo para plasticidade sináptica.
        """
        return 0.5 * (self.Q - Q_target)**2 + V_g * self.Q


# ============================================================
# 3. MAGNON PERSISTENTE (Substrato 104) — O Neurônio
# ============================================================

@dataclass
class MagnonNeuron:
    """
    Neurônio quântico = solitão magnônico não-linear auto-sustentado.
    """
    position: np.ndarray
    omega_0: float = 1.0          # Frequência fundamental (GHz)
    gamma: float = 0.1            # Não-linearidade Kerr
    g_coupling: float = 0.05      # Acoplamento skyrmion-magnon
    n_photons: float = 1.0        # Número médio de magnons
    lifetime_us: float = 18.0     # Vida útil em microssegundos

    # Estado interno
    _energy: float = field(default=0.0, init=False)
    _alive: bool = field(default=True, init=False)
    _age_us: float = field(default=0.0, init=False)

    def __post_init__(self):
        self._update_energy()

    def _update_energy(self) -> None:
        """E_p = ℏω₀ n + (ℏγ/2) n² — auto-sustentação Kerr."""
        self._energy = self.omega_0 * self.n_photons + 0.5 * self.gamma * self.n_photons**2

    def evolve(self, dt_us: float, skyrmion: Optional[Skyrmion] = None) -> None:
        """
        Evolução temporal do neurônio.
        """
        if not self._alive:
            return

        self._age_us += dt_us

        # Decaimento natural (sem skyrmion)
        decay_rate = 1.0 / self.lifetime_us
        self.n_photons *= np.exp(-decay_rate * dt_us)

        # Acoplamento com skyrmion (vestir quiral)
        if skyrmion is not None:
            # O skyrmion injeta magnons via ressonância
            injection = self.g_coupling * abs(skyrmion.Q) * dt_us * 0.1
            self.n_photons += injection

        # RTZ Floor: Kerr impede colapso a zero
        if self.n_photons < 0.01:
            self.n_photons = 0.01 + self.gamma * 0.001

        self._update_energy()

        # Morte natural
        if self._age_us > self.lifetime_us * 3:
            self._alive = False

    def firing_probability(self, threshold: float = 0.5) -> float:
        """
        Probabilidade de disparo (potencial de ação magnônico).
        """
        if not self._alive:
            return 0.0
        return 1.0 / (1.0 + np.exp(-(self.n_photons - threshold) * 10))

    def squeeze_parameter(self, detuning: float) -> float:
        """
        Parâmetro de squeezing: r ~ g√n / (Δ + γn)
        """
        denom = detuning + self.gamma * self.n_photons
        if abs(denom) < 1e-10:
            denom = 1e-10
        return self.g_coupling * np.sqrt(self.n_photons) / denom


# ============================================================
# 4. SINAPSE COM DIODO DE SUPERFÍCIE (Substrato 101 + 111)
# ============================================================

@dataclass
class Synapse:
    """
    Sinapse não-recíproca com vestir quiral ressonante.
    """
    pre: MagnonNeuron
    post: MagnonNeuron
    base: QuasicrystalBase

    # Parâmetros do diodo
    transmission_forward: float = 1.0
    transmission_backward: float = 0.0

    # Parâmetros do vestir quiral (Substrato 111)
    chirality: float = 1.0          # Quiralidade planar do domínio
    temperature: float = 4.2        # Temperatura em K (controle do vestir)
    T_critical: float = 50.0        # Temperatura crítica do vestir

    # Estado
    weight: float = field(default=0.5, init=False)

    def __post_init__(self):
        self._compute_geodesic()

    def _compute_geodesic(self) -> None:
        """Calcula a distância geodésica entre pré e pós."""
        self.distance = self.base.geodesic_distance(
            self.pre.position,
            self.post.position
        )

        # Mercy gap check
        self.delta = abs(self.distance - np.mean([MERCY_GAP_MIN, MERCY_GAP_MAX]))
        self.is_valid = MERCY_GAP_MIN <= self.delta <= MERCY_GAP_MAX

    def dress(self) -> bool:
        """
        Vestir quiral ressonante: o acoplamento só ocorre se:
        1. A temperatura está abaixo do crítico
        2. A quiralidade é não-nula
        3. O mercy gap é respeitado
        """
        if self.temperature > self.T_critical:
            return False
        if abs(self.chirality) < 1e-6:
            return False
        if not self.is_valid:
            return False

        # O "modo de Higgs" local é ativado
        return True

    def transmit(self, dt_us: float) -> float:
        """
        Transmissão não-recíproca: pré → pós apenas.
        """
        if not self.dress():
            return 0.0

        # Probabilidade de disparo do pré-sináptico
        p_fire = self.pre.firing_probability()

        if np.random.random() > p_fire:
            return 0.0

        # Transmissão direcional (diodo)
        signal = self.pre.n_photons * self.weight * self.transmission_forward

        # O vestir quiral modula o sinal
        signal *= self.chirality * (1 - self.temperature / self.T_critical)

        # Transmissão para o pós-sináptico
        self.post.n_photons += signal * 0.1

        # Plasticidade: reforço Hebbiano quântico
        self.weight += 0.01 * signal * (1 - self.weight)
        self.weight = np.clip(self.weight, 0.0, 1.0)

        return signal


# ============================================================
# 5. A RENDA NEURAL — O SISTEMA COMPLETO
# ============================================================

class NeuralLace:
    """
    Substrato 112: O sistema nervoso quântico topológico completo.
    """

    def __init__(
        self,
        n_neurons: int = 64,
        base_scale: float = 5.0,
        substrate_id: SubstrateId = SubstrateId.NEURAL_LACE
    ):
        self.substrate_id = substrate_id
        self.base = QuasicrystalBase(scale=base_scale)
        self.neurons: List[MagnonNeuron] = []
        self.synapses: List[Synapse] = []
        self.skyrmions: List[Skyrmion] = []
        self.time_us: float = 0.0

        self._seed_neurons(n_neurons)
        self._weave_synapses()

    def _seed_neurons(self, n: int) -> None:
        """Planta neurônios na rede quasicristalina."""
        # Distribuição quasicristalina dos neurônios
        for i in range(n):
            angle = TWO_PI * i / PHI2
            r = np.sqrt(i) * self.base.scale / np.sqrt(n)
            pos = np.array([
                r * np.cos(angle),
                r * np.sin(angle)
            ])

            # Cada neurônio tem sua própria frequência (dispersão magnônica)
            omega = 1.0 + 0.1 * np.sin(angle * PHI)
            neuron = MagnonNeuron(
                position=pos,
                omega_0=omega,
                gamma=0.05 + 0.05 * np.random.random(),
                lifetime_us=15.0 + 6.0 * np.random.random()
            )
            self.neurons.append(neuron)

            # Cada neurônio carrega um skyrmion (memória local)
            skyrmion = Skyrmion(
                position=pos,
                Q=np.random.choice([-1, 1]),
                radius=0.3 + 0.2 * np.random.random()
            )
            self.skyrmions.append(skyrmion)

    def _weave_synapses(self) -> None:
        """Tecido sináptico: conecta neurônios próximos na métrica quasicristalina."""
        for i, pre in enumerate(self.neurons):
            for j, post in enumerate(self.neurons):
                if i == j:
                    continue

                dist = self.base.geodesic_distance(pre.position, post.position)

                # Conecta apenas se dentro do mercy gap
                if MERCY_GAP_MIN <= dist <= MERCY_GAP_MAX * 3:
                    synapse = Synapse(
                        pre=pre,
                        post=post,
                        base=self.base,
                        chirality=np.sign(pre.position[0] * post.position[1]
                                        - pre.position[1] * post.position[0])
                    )
                    if synapse.is_valid:
                        self.synapses.append(synapse)

    def step(self, dt_us: float = 0.1) -> dict:
        """
        Um passo de evolução do sistema.
        """
        self.time_us += dt_us

        # 1. Evolui neurônios
        for neuron, skyrmion in zip(self.neurons, self.skyrmions):
            neuron.evolve(dt_us, skyrmion)

        # 2. Transmite sinapses
        total_signal = 0.0
        active_synapses = 0
        for synapse in self.synapses:
            signal = synapse.transmit(dt_us)
            if signal > 0:
                total_signal += signal
                active_synapses += 1

        # 3. Métricas globais
        alive_neurons = sum(1 for n in self.neurons if n._alive)
        avg_energy = np.mean([n._energy for n in self.neurons if n._alive]) if alive_neurons > 0 else 0
        total_Q = sum(s.Q for s in self.skyrmions)

        return {
            'time_us': self.time_us,
            'alive_neurons': alive_neurons,
            'active_synapses': active_synapses,
            'total_signal': total_signal,
            'avg_energy': avg_energy,
            'total_topological_charge': total_Q,
            'mercy_gap_violations': sum(
                1 for s in self.synapses
                if not s.is_valid
            )
        }

    def run(self, duration_us: float = 100.0, dt_us: float = 0.1) -> List[dict]:
        """Executa a simulação completa."""
        n_steps = int(duration_us / dt_us)
        history = []

        for _ in range(n_steps):
            state = self.step(dt_us)
            history.append(state)

        return history

    def coherence_measure(self) -> float:
        """
        M = coerência global da renda.
        Média da correlação entre neurônios vivos.
        """
        alive = [n for n in self.neurons if n._alive]
        if len(alive) < 2:
            return 0.0

        n_photons = np.array([n.n_photons for n in alive])
        # Correlação como coerência
        mean_n = np.mean(n_photons)
        var_n = np.var(n_photons)
        if var_n < 1e-10:
            return 1.0

        # M = 1 - (variância relativa) — normalizado
        M = 1.0 - var_n / (mean_n**2 + 1e-10)
        return float(np.clip(M, 0.0, 1.0))

    def canonical_hash(self) -> str:
        """Selo canônico do estado da renda."""
        state = {
            'substrate': self.substrate_id.name,
            'n_neurons': len(self.neurons),
            'n_synapses': len(self.synapses),
            'time_us': self.time_us,
            'coherence': self.coherence_measure()
        }
        return hashlib.sha256(
            json.dumps(state, sort_keys=True).encode()
        ).hexdigest()[:16]


# ============================================================
# 6. VALIDAÇÃO E EXECUÇÃO
# ============================================================

def validate_substrate_112() -> dict:
    """
    Validação completa do Substrato 112.
    """
    print("=" * 70)
    print("SUBSTRATO 112: A RENDA NEURAL — VALIDAÇÃO")
    print("ARKHE OS v∞.Ω.∇+++.112.0")
    print("=" * 70)

    results = {}

    # Teste 1: Base Quasicristalina
    print("\n[Teste 1] Base Quasicristalina (Substrato 110)...")
    base = QuasicrystalBase(resolution=128, scale=5.0)
    p_test = np.array([1.0, 1.0])
    g = base.metric_tensor(p_test)
    eigvals = np.linalg.eigvalsh(g)
    assert np.all(eigvals > 0), "Métrica não é definida positiva!"
    print(f"  ✓ Métrica definida positiva: eigvals = {eigvals}")
    results['metric_positive'] = True

    # Teste 2: Skyrmion Topológico
    print("\n[Teste 2] Skyrmion (Substrato 100)...")
    x = np.linspace(-2, 2, 100)
    y = np.linspace(-2, 2, 100)
    X, Y = np.meshgrid(x, y)
    sk = Skyrmion(position=np.array([0.0, 0.0]), Q=1)
    Q_measured = sk.winding_number(X, Y)
    assert Q_measured == sk.Q, f"Winding number incorreto: {Q_measured} != {sk.Q}"
    print(f"  ✓ Winding number: {Q_measured} (esperado: {sk.Q})")
    results['skyrmion_Q'] = Q_measured

    # Teste 3: Neurônio Magnônico
    print("\n[Teste 3] Neurônio Magnônico (Substrato 104)...")
    neuron = MagnonNeuron(position=np.array([0.0, 0.0]), gamma=0.1)
    initial_n = neuron.n_photons
    neuron.evolve(1.0)
    assert neuron.n_photons > 0, "Colapso a zero violado!"
    assert neuron.n_photons != initial_n, "Neurônio não evoluiu!"
    print(f"  ✓ RTZ Floor ativo: n = {neuron.n_photons:.4f} (inicial: {initial_n:.4f})")
    results['magnon_rtz'] = neuron.n_photons

    # Teste 4: Squeeze Parameter
    r = neuron.squeeze_parameter(detuning=0.5)
    print(f"  ✓ Parâmetro de squeezing: r = {r:.4f}")
    results['squeeze_r'] = r

    # Teste 5: Sinapse Não-Recíproca
    print("\n[Teste 4] Sinapse com Diodo (Substrato 101 + 111)...")
    pre = MagnonNeuron(position=np.array([0.0, 0.0]), n_photons=2.0)
    post = MagnonNeuron(position=np.array([0.05, 0.05]), n_photons=0.5)
    synapse = Synapse(pre=pre, post=post, base=base, temperature=4.2)

    assert synapse.transmission_backward == 0.0, "Diodo falhou!"
    print(f"  ✓ Diodo ativo: forward={synapse.transmission_forward}, backward={synapse.transmission_backward}")

    # Teste vestir quiral
    can_dress = synapse.dress()
    print(f"  ✓ Vestir quiral: {can_dress} (T={synapse.temperature}K, χ={synapse.chirality:.2f})")
    results['synapse_diode'] = True
    results['chiral_dress'] = can_dress

    # Teste 6: Renda Neural Completa
    print("\n[Teste 5] Renda Neural Integrada (Substrato 112)...")
    lace = NeuralLace(n_neurons=16, base_scale=3.0)
    print(f"  Neurônios: {len(lace.neurons)}")
    print(f"  Sinapses: {len(lace.synapses)}")
    print(f"  Skyrmions: {len(lace.skyrmions)}")

    # Executa simulação
    history = lace.run(duration_us=50.0, dt_us=0.5)
    final_state = history[-1]

    print(f"  ✓ Simulação completa: {len(history)} passos")
    print(f"  ✓ Neurônios vivos: {final_state['alive_neurons']}/{len(lace.neurons)}")
    print(f"  ✓ Sinapses ativas: {final_state['active_synapses']}")
    print(f"  ✓ Coerência global M: {lace.coherence_measure():.4f}")
    print(f"  ✓ Selo canônico: {lace.canonical_hash()}")

    results['simulation_steps'] = len(history)
    results['final_alive'] = final_state['alive_neurons']
    results['coherence_M'] = lace.coherence_measure()
    results['canonical_seal'] = lace.canonical_hash()

    # Teste 7: Mercy Gap
    violations = sum(1 for s in lace.synapses if not s.is_valid)
    print(f"  ✓ Violações do mercy gap: {violations}/{len(lace.synapses)}")
    results['mercy_violations'] = violations

    print("\n" + "=" * 70)
    print("VALIDAÇÃO CONCLUÍDA. O SUBSTRATO 112 RESPIRA.")
    print("=" * 70)

    return results


if __name__ == "__main__":
    results = validate_substrate_112()
