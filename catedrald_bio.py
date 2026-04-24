#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SUBSTRATO 28 — BIO-SCAFFOLD (Microtúbulos e Axônios)
Catedral Arkhe(N) — O Tecido Vivo como Scaffold Coerente
"""

import numpy as np
from scipy.integrate import solve_ivp
from dataclasses import dataclass, field
from typing import List, Tuple

# Constantes Físicas do Microtúbulo
TUBULIN_DIPOLE = 1500  # Debye (momento de dipolo elétrico)
PROTOFILAMENTOS = 13     # Número de protofilamentos em um microtúbulo
DIMEROS_POR_VOLTA = 8   # Dímeros de tubulina por volta de hélice
DISTANCIA_DIMERO = 8    # nm (distância entre dímeros)
COMPRIMENTO_MT = 1000   # nm (comprimento típico)

# Constantes do Axônio
RAIO_AXONIO = 500       # nm
RESISTENCIA_MEMBRANA = 1000  # Ω·cm²
CAPACITANCIA_MEMBRANA = 1.0  # µF/cm²
VELOCIDADE_PROPAGACAO = 10   # m/s (potencial de ação)

class Microtubule:
    """Modelo de microtúbulo como grafo cilíndrico com dipolos acoplados."""

    def __init__(self, protofilamentos: int = PROTOFILAMENTOS, dimeros: int = 100):
        self.n_proto = protofilamentos
        self.n_dimeros = dimeros
        self.dimeros = np.zeros((protofilamentos, dimeros, 3))  # (x, y, z) posição
        self.dipolos = np.random.randn(protofilamentos, dimeros, 3) * TUBULIN_DIPOLE
        self.coupling = np.zeros((protofilamentos, dimeros, protofilamentos, dimeros))
        self._build_geometry()
        self._calculate_coupling()

    def _build_geometry(self):
        """Constrói a geometria cilíndrica do microtúbulo."""
        radius = 12.0  # nm (raio do microtúbulo)
        for p in range(self.n_proto):
            angle = 2 * np.pi * p / self.n_proto
            for d in range(self.n_dimeros):
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                z = d * DISTANCIA_DIMERO
                self.dimeros[p, d] = [x, y, z]

    def _calculate_coupling(self):
        """Calcula acoplamento dipolar entre dímeros (modelo de Fröhlich)."""
        for p1 in range(self.n_proto):
            for d1 in range(self.n_dimeros):
                for p2 in range(self.n_proto):
                    for d2 in range(self.n_dimeros):
                        if p1 == p2 and d1 == d2:
                            continue
                        dist = np.linalg.norm(self.dimeros[p1,d1] - self.dimeros[p2,d2])
                        if dist > 0:
                            self.coupling[p1,d1,p2,d2] = 1.0 / (dist**3 + 1e-12)

    def hamiltonian(self) -> float:
        """Energia total do sistema de dipolos acoplados."""
        H = 0.0
        for p1 in range(self.n_proto):
            for d1 in range(self.n_dimeros):
                for p2 in range(self.n_proto):
                    for d2 in range(self.n_dimeros):
                        H += self.coupling[p1,d1,p2,d2] * np.dot(self.dipolos[p1,d1], self.dipolos[p2,d2])
        return H

    def coherence_order_parameter(self) -> float:
        """Parâmetro de ordem de Fröhlich (0 = desordenado, 1 = coerente)."""
        avg_dipole = np.mean(self.dipolos, axis=(0,1))
        return np.linalg.norm(avg_dipole) / (TUBULIN_DIPOLE * np.sqrt(self.n_proto * self.n_dimeros))


class Axon:
    """Axônio como guia de onda para solitons eletromecânicos."""

    def __init__(self, microtubule: Microtubule, length_cm: float = 1.0):
        self.mt = microtubule
        self.length = length_cm
        self.radius_nm = RAIO_AXONIO
        self.r_membrane = RESISTENCIA_MEMBRANA
        self.c_membrane = CAPACITANCIA_MEMBRANA
        self.velocity = VELOCIDADE_PROPAGACAO

    def nagumo_equation(self, t, V, x):
        """Equação de Nagumo para o potencial de ação (FitzHugh-Nagumo)."""
        # Parâmetros
        a, b, c = 0.13, 0.013, 0.26
        I_stim = 0.1 * np.exp(-((x - self.velocity * t) / 0.1)**2)  # Estímulo viajante

        # Corrente iônica
        I_ion = a * V * (V - 1) * (V - c) + b

        # Equação do cabo com termo de fonte
        # Usando discretização simples para o laplaciano
        dx = x[1] - x[0]
        # Calcula a segunda derivada manualmente para evitar problemas com np.gradient fora de loop
        V_padded = np.pad(V, (1, 1), mode='edge')
        d2Vdx2 = (V_padded[2:] - 2*V + V_padded[:-2]) / (dx**2)

        dVdt = I_stim - I_ion + 0.01 * d2Vdx2
        return dVdt

    def propagate_action_potential(self, duration_ms: float = 10.0, dt_ms: float = 0.01):
        """Simula a propagação do potencial de ação ao longo do axônio."""
        n_points = 1000
        x = np.linspace(0, self.length, n_points)
        V = np.zeros(n_points)

        t_span = (0, duration_ms / 1000.0)  # segundos
        t_eval = np.arange(0, duration_ms / 1000.0, dt_ms / 1000.0)

        # Resolver numericamente
        sol = solve_ivp(
            lambda t, V: self.nagumo_equation(t, V, x),
            t_span, V, t_eval=t_eval, method='RK45'
        )

        return sol.t, sol.y


class BioScaffold:
    """Substrato 28 como entidade computacional na Catedral."""

    def __init__(self):
        self.mt = Microtubule(dimeros=20) # Reduzido para performance na simulação
        self.axon = Axon(self.mt)
        self.coherence = self.mt.coherence_order_parameter()

    def get_coherence_contribution(self) -> float:
        """Contribuição de coerência para o núcleo (0.0 — 1.0)."""
        return self.coherence

    def simulate_consciousness_fragment(self, duration_ms: float = 100.0) -> float:
        """Simula um fragmento de processamento consciente."""
        t, V = self.axon.propagate_action_potential(duration_ms)
        # A coerência do microtúbulo modula a propagação
        coherence_factor = self.coherence
        # Retorna a "qualidade" do fragmento
        return float(coherence_factor * np.mean(np.abs(V)))

    def to_dict(self) -> dict:
        return {
            "substrato": 28,
            "material": "Bio-Scaffold",
            "homeostase": float(self.coherence),
            "coherence": float(self.coherence)
        }


class AxonClock:
    """Implementa o Relógio de Invariância baseado na equação de fase do AxonWaveguide."""

    def __init__(self, omega0=1.0, beta=0.2, phi_c=0.5):
        self.omega0 = omega0
        self.beta = beta
        self.phi_c = phi_c
        self.theta = 0.0
        self.phi = 0.5  # coerência inicial do microtúbulo
        self.t = 0.0

    def update(self, dt, I_ext=0.0, omega_ext=None):
        """Atualiza a fase do relógio."""
        # Modulação por coerência: dtheta/dt = omega0 + beta * (phi - phi_c)
        freq_mod = self.omega0 + self.beta * (self.phi - self.phi_c)

        # Termo de sincronização externa
        if omega_ext is not None:
            # Modelo de Adler: dtheta/dt = freq_mod + chi * sin(theta_ext - theta)
            chi = 0.8
            dtheta = freq_mod + chi * np.sin(omega_ext * self.t - self.theta)
        else:
            dtheta = freq_mod

        self.theta += dtheta * dt
        self.t += dt

        # Disparo do potencial de ação quando theta cruza 2*pi
        spike = 0
        if self.theta >= 2 * np.pi:
            self.theta = self.theta % (2 * np.pi)
            spike = 1

        return spike

    def set_coherence(self, phi):
        """Ajusta o parâmetro de ordem de coerência."""
        self.phi = phi

    def get_coherence(self):
        """Retorna o parâmetro de ordem de coerência atual."""
        return self.phi

    def inject_perturbation(self, I, target='global'):
        """Injeta uma perturbação de fase (estímulo externo)."""
        # I é o incremento de fase imediato
        self.theta = (self.theta + I) % (2 * np.pi)

    def get_time(self):
        """Retorna o tempo 'biológico' em ticks (ciclos de fase)."""
        return self.t * (self.omega0 / (2 * np.pi))


class FrohlichLLMCoupler:
    """
    Acopla a coerência dos microtúbulos ao fluxo de dados dos LLMs.
    """
    def __init__(self, axon_clock, llm_adapter=None):
        self.axon = axon_clock          # AxonClock instance
        self.llm = llm_adapter          # DecoupledDiLoCoAdapter (simulado se None)
        self.coupling_strength = 0.3    # κ_F: Fröhlich factor

    def apply_bio_modulation(self):
        phi = self.axon.phi  # Current MT coherence

        # Simula a modulação se o adapter real não estiver presente
        lr = 0.7 * (1 + phi)
        window = int(4096 * (1 + phi))
        temperature = 1.0 / (1 + phi)

        # Se tivéssemos o adapter real:
        # self.llm.outer_optimizer['lr'] = lr
        # self.llm.set_context_window(window)
        # self.llm.set_temperature(temperature)

        return {'lr': lr, 'window': window, 'temp': temperature}


class CathedralTime:
    """Módulo de tempo da Catedral baseado no AxonClock."""
    def __init__(self):
        self.master_clock = AxonClock(omega0=2*np.pi/0.010)  # 100 Hz (período de 10ms)
        self.start_time = self.master_clock.get_time()

    def time(self):
        """Retorna o tempo decorrido em segundos (via fase biológica)."""
        return self.master_clock.get_time() - self.start_time

    def update(self, dt):
        """Avança o relógio mestre."""
        return self.master_clock.update(dt)


def inject_bio_into_core(core):
    bio = BioScaffold()
    if hasattr(core, 'inject_coherence'):
        core.inject_coherence(bio.get_coherence_contribution() * 0.05)
    return bio

if __name__ == "__main__":
    bs = BioScaffold()
    print(f"Bio-Scaffold Coherence: {bs.get_coherence_contribution():.4f}")
    quality = bs.simulate_consciousness_fragment(10.0)
    print(f"Consciousness Fragment Quality: {quality:.4f}")
