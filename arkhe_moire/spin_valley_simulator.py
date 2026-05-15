#!/usr/bin/env python3
"""
Substrato 9041 — Simulador de Canais Spin‑Valley
Modela a propagação de modos coletivos spin‑valley em heteroestruturas
moiré, com acoplamento ao campo atratora Φ_C.
"""

import numpy as np
from scipy.linalg import expm
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from .materials_2d_db import MoireMaterial, MATERIALS_2D_CATALOG

@dataclass
class SpinValleyState:
    """Estado spin‑valley em um ponto da rede moiré."""
    position: Tuple[float, float]     # (x, y) na supercélula moiré
    spin: complex                     # Amplitude de spin (↑ ou ↓)
    valley: complex                   # Amplitude de valley (K ou K')
    coherence: float                  # Φ_C local
    energy_ev: float                  # Energia do estado (eV)

class SpinValleySimulator:
    """
    Simulador de dinâmica spin‑valley em materiais moiré.

    Modela:
    • Hamiltoniano de acoplamento spin‑órbita + valley
    • Propagação de modos coletivos (spin‑valley waves)
    • Interação com campo atratora Φ_C
    • Efeitos de temperatura e campo externo
    """

    def __init__(self, material: MoireMaterial, angle_degrees: float = 1.1):
        self.material = material
        self.angle = angle_degrees
        self.phi_c = material.compute_phi_c_at_angle(angle_degrees)

        # Constantes físicas
        self.hbar = 6.582119569e-16  # eV·s
        self.k_B = 8.617333262e-5     # eV/K

        # Construir Hamiltoniano base
        self.H0 = self._build_hamiltonian()

    def _build_hamiltonian(self) -> np.ndarray:
        """
        Constrói Hamiltoniano de 4 bandas (spin ⊗ valley).

        Base: |K↑⟩, |K↓⟩, |K'↑⟩, |K'↓⟩

        H = H_valley + H_soc + H_moire

        Onde:
        • H_valley = Δ * τ_z ⊗ I  (gap valley)
        • H_soc = λ * τ_z ⊗ σ_z  (acoplamento spin-órbita)
        • H_moire = V(r) * I ⊗ I  (potencial moiré periódico)
        """
        # Matrizes de Pauli para valley (τ) e spin (σ)
        tau_z = np.array([[1, 0], [0, -1]])  # Valley: K/K'
        sigma_z = np.array([[1, 0], [0, -1]])  # Spin: ↑/↓
        I = np.eye(2)

        # Parâmetros do material
        Delta = self.material.monolayer_bandgap_ev  # Gap valley
        lamb = self.material.spin_orbit_coupling_ev  # SOC

        # Construir Hamiltoniano via produto de Kronecker
        H_valley = Delta * np.kron(tau_z, I)           # τ_z ⊗ I
        H_soc = lamb * np.kron(tau_z, sigma_z)         # τ_z ⊗ σ_z

        # Potencial moiré periódico (aproximação de primeira harmônica)
        V0 = 0.05  # Amplitude do potencial moiré (eV) — típico para TMDs
        # Para simplicidade, usamos um potencial efetivo na diagonal
        H_moire = V0 * np.cos(self.angle * np.pi / 180) * np.eye(4)

        return H_valley + H_soc + H_moire

    def compute_spin_valley_dispersion(self, k_points: np.ndarray) -> np.ndarray:
        """
        Calcula a relação de dispersão E(k) para os modos spin‑valley.

        Args:
            k_points: Array de momentos cristalinos (N × 2) em unidades de π/a

        Returns:
            Energias para cada ponto k (N × 4 bandas)
        """
        energies = np.zeros((len(k_points), 4))

        for i, k in enumerate(k_points):
            # Hamiltoniano com termo cinético
            kx, ky = k
            # Termo de hopping (aproximação de massa efetiva)
            m_eff = 0.35  # Massa efetiva típica para TMDs (em unidades de m_e)
            kinetic = (self.hbar**2 / (2 * m_eff)) * (kx**2 + ky**2)

            H_k = self.H0 + kinetic * np.eye(4)
            eigenvalues = np.linalg.eigvalsh(H_k)
            energies[i] = np.sort(eigenvalues)

        return energies

    def simulate_propagation(
        self,
        initial_state: SpinValleyState,
        time_steps: int = 100,
        dt_fs: float = 1.0,  # passo temporal em femtossegundos
    ) -> List[SpinValleyState]:
        """
        Simula propagação temporal de um estado spin‑valley.

        Resolve a equação de Schrödinger dependente do tempo:
        iℏ * d|ψ⟩/dt = H|ψ⟩

        via operador de evolução U(t) = exp(-iHt/ℏ)
        """
        dt_s = dt_fs * 1e-15  # Converter fs para segundos
        dt_ev = dt_s / self.hbar  # Converter para unidades de eV⁻¹

        # Operador de evolução
        U = expm(-1j * self.H0 * dt_ev / self.hbar)

        # Vetor de estado inicial (4 componentes)
        psi = np.array([
            initial_state.spin * initial_state.valley,   # |K↑⟩
            initial_state.spin * (1 - initial_state.valley),  # |K↓⟩ (simplificado)
            (1 - initial_state.spin) * initial_state.valley,  # |K'↑⟩
            (1 - initial_state.spin) * (1 - initial_state.valley),  # |K'↓⟩
        ])
        psi = psi / np.linalg.norm(psi)

        states = [initial_state]
        current = initial_state

        for t in range(time_steps):
            psi = U @ psi
            psi = psi / np.linalg.norm(psi)

            # Extrair observáveis
            spin_up_prob = abs(psi[0])**2 + abs(psi[1])**2
            valley_K_prob = abs(psi[0])**2 + abs(psi[2])**2

            # Calcular coerência Φ_C local
            # Φ_C ∝ pureza do estado reduzido
            rho_spin = np.array([
                [abs(psi[0])**2 + abs(psi[1])**2, psi[0]*np.conj(psi[2]) + psi[1]*np.conj(psi[3])],
                [psi[2]*np.conj(psi[0]) + psi[3]*np.conj(psi[1]), abs(psi[2])**2 + abs(psi[3])**2],
            ])
            purity = np.trace(rho_spin @ rho_spin).real
            coherence = purity * self.phi_c

            state = SpinValleyState(
                position=current.position,  # Posição fixa para simulação simples
                spin=complex(spin_up_prob, 0),
                valley=complex(valley_K_prob, 0),
                coherence=float(coherence),
                energy_ev=float(np.real(np.conj(psi).T @ self.H0 @ psi)),
            )
            states.append(state)

        return states

    def find_critical_angles(self, angle_range: Tuple[float, float] = (0.0, 5.0),
                           n_points: int = 100) -> List[float]:
        """
        Encontra ângulos críticos que maximizam Φ_C.

        Varre o intervalo de ângulos e calcula Φ_C para cada um.
        """
        angles = np.linspace(angle_range[0], angle_range[1], n_points)
        phi_c_values = np.zeros(n_points)

        for i, angle in enumerate(angles):
            temp_material = MoireMaterial(
                name="temp",
                formula="temp",
                material_class=self.material.material_class,
                lattice_constant_a=self.material.lattice_constant_a,
                monolayer_bandgap_ev=self.material.monolayer_bandgap_ev,
                spin_orbit_coupling_ev=self.material.spin_orbit_coupling_ev,
                critical_angles=self.material.critical_angles,
                phi_c_peak=self.material.phi_c_peak,
                valley_coherence_time_ps=self.material.valley_coherence_time_ps,
                spin_coherence_time_ps=self.material.spin_coherence_time_ps,
            )
            phi_c_values[i] = temp_material.compute_phi_c_at_angle(angle)

        # Encontrar picos locais
        peaks = []
        for i in range(1, n_points - 1):
            if phi_c_values[i] > phi_c_values[i-1] and phi_c_values[i] > phi_c_values[i+1]:
                peaks.append(round(float(angles[i]), 2))

        return sorted(peaks)

    def optimize_critical_angles_qnc(self, angle_range: Tuple[float, float] = (0.0, 5.0),
                           n_points: int = 100,
                           epochs: int = 50) -> List[float]:
        """
        Usa o QNC (Quantum Neural Coding) para otimizar a descoberta de ângulos
        críticos que maximizam a coerência Φ_C via aprendizado de máquina.
        """
        try:
            from arkp_qnc.quantum_layers import QuantumDenseLayer, QuantumDenseConfig
            qnc_available = True
        except ImportError:
            qnc_available = False

        if not qnc_available:
            # Fallback
            return self.find_critical_angles(angle_range, n_points)

        angles = np.linspace(angle_range[0], angle_range[1], n_points)

        config = QuantumDenseConfig(input_dim=len(angles), output_dim=len(angles))
        qnc_layer = QuantumDenseLayer(config)

        phi_c_values = np.zeros(n_points)

        for i, angle in enumerate(angles):
            temp_material = MoireMaterial(
                name="temp",
                formula="temp",
                material_class=self.material.material_class,
                lattice_constant_a=self.material.lattice_constant_a,
                monolayer_bandgap_ev=self.material.monolayer_bandgap_ev,
                spin_orbit_coupling_ev=self.material.spin_orbit_coupling_ev,
                critical_angles=self.material.critical_angles,
                phi_c_peak=self.material.phi_c_peak,
                valley_coherence_time_ps=self.material.valley_coherence_time_ps,
                spin_coherence_time_ps=self.material.spin_coherence_time_ps,
            )
            phi_c_values[i] = temp_material.compute_phi_c_at_angle(angle)


        density_matrix = np.outer(phi_c_values, phi_c_values)
        trace = np.trace(density_matrix)
        if trace > 0:
            density_matrix /= trace

        for _ in range(epochs):
            density_matrix = qnc_layer.forward(density_matrix)

        # extrair probabilidades ao longo da diagonal
        optimized_phi_c = np.real(np.diag(density_matrix))

        peaks = []
        for i in range(1, n_points - 1):
            if optimized_phi_c[i] > optimized_phi_c[i-1] and optimized_phi_c[i] > optimized_phi_c[i+1]:
                peaks.append(round(float(angles[i]), 2))

        # QNC pode encontrar picos que não estão no modelo base simplificado de phi_c, ou refinar os existentes
        # Aqui, vamos mesclar os resultados do QNC com os ângulos originais para obter resultados robustos
        base_peaks = self.find_critical_angles(angle_range, n_points)

        all_peaks = set(base_peaks + peaks)

        return sorted(list(all_peaks))

    def generate_coherence_map(self, temperature_range: Tuple[float, float] = (1.0, 100.0),
                              n_points: int = 50) -> Dict:
        """
        Gera mapa de coerência Φ_C(θ, T) para o material.

        Returns:
            Dict com arrays de ângulos, temperaturas e matriz Φ_C
        """
        angles = np.linspace(0.0, 5.0, n_points)
        temps = np.linspace(temperature_range[0], temperature_range[1], n_points)
        coherence_map = np.zeros((len(temps), len(angles)))

        for i, T in enumerate(temps):
            for j, angle in enumerate(angles):
                coherence_map[i, j] = self.material.compute_phi_c_at_angle(angle, T)

        return {
            "angles": angles.tolist(),
            "temperatures": temps.tolist(),
            "coherence_matrix": coherence_map.tolist(),
            "material": self.material.name,
            "phi_c_peak": float(self.material.phi_c_peak),
            "critical_angles": self.material.critical_angles,
        }


# ============================================================================
# FERRAMENTA DE MAPEAMENTO DE MATERIAIS
# ============================================================================

class MaterialsMapper:
    """
    Mapeia materiais 2D existentes para o ecossistema Arkhe.
    Identifica os melhores candidatos para cada aplicação.
    """

    def __init__(self):
        self.catalog = MATERIALS_2D_CATALOG

    def find_best_for_application(self, application: str, min_phi_c: float = 0.95,
                                  max_temperature_k: float = 4.2) -> List[Tuple[str, float]]:
        """Encontra os melhores materiais para uma aplicação específica."""
        candidates = []

        for key, material in self.catalog.items():
            if application in material.applications:
                phi_c = material.compute_phi_c_at_angle(
                    material.critical_angles[0] if material.critical_angles else 0.0,
                    max_temperature_k
                )
                if phi_c >= min_phi_c:
                    candidates.append((material.name, phi_c))

        return sorted(candidates, key=lambda x: x[1], reverse=True)

    def find_by_phi_c_range(self, min_phi_c: float = 0.99,
                          max_phi_c: float = 1.0) -> List[Tuple[str, float]]:
        """Encontra materiais que atingem um determinado intervalo de Φ_C."""
        results = []
        for key, material in self.catalog.items():
            if min_phi_c <= material.phi_c_peak <= max_phi_c:
                results.append((material.name, material.phi_c_peak))
        return sorted(results, key=lambda x: x[1], reverse=True)

    def find_by_coherence_time(self, min_time_ps: float = 100.0,
                              mode: str = "spin") -> List[Tuple[str, float]]:
        """Encontra materiais com tempo de coerência mínimo."""
        results = []
        for key, material in self.catalog.items():
            time_ps = material.spin_coherence_time_ps if mode == "spin" else material.valley_coherence_time_ps
            if time_ps >= min_time_ps:
                results.append((material.name, time_ps))
        return sorted(results, key=lambda x: x[1], reverse=True)
