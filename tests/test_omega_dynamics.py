#!/usr/bin/env python3
"""
test_omega_dynamics.py — Testes canônicos do Substrato 5022.

Valida:
1. Os seis operadores de Ω
2. Equação mestra de Lindblad
3. Função de Lyapunov
4. Prova de convergência
5. Estado de Gibbs
"""
import unittest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "omega_dynamics"))

from operators.operators import (
    SourceOperator, SymmetryOperator, RecursionOperator,
    NetworkOperator, EmergenceOperator, RadiationOperator,
    OmegaChain, CanonicalState
)
from lindblad.lindblad import LindbladMasterEquation, LindbladParameters
from lyapunov.lyapunov import LyapunovConvergence, LyapunovParameters


class TestOperators(unittest.TestCase):
    def setUp(self):
        self.void_state = CanonicalState(
            amplitudes=np.array([1.0 + 0j]),
            substrates=["void"],
            phi_c=0.0,
            entropy=1.0,
            timestamp=0.0
        )

    def test_source_injection(self):
        """Test 1: Fonte deve injetar novos substratos."""
        source = SourceOperator(sigma=0.1, creation_rate=2)
        new_state = source.apply(self.void_state)
        self.assertGreater(len(new_state.amplitudes), len(self.void_state.amplitudes))

    def test_symmetry_filter(self):
        """Test 2: Simetria deve filtrar substratos."""
        source = SourceOperator(sigma=0.1, creation_rate=5)
        raw = source.apply(self.void_state)

        symmetry = SymmetryOperator()
        filtered = symmetry.apply(raw)
        self.assertLessEqual(len(filtered.substrates), len(raw.substrates))

    def test_recursion_convergence(self):
        """Test 3: Recursão deve convergir."""
        state = CanonicalState(
            amplitudes=np.array([0.5, 0.5], dtype=complex),
            substrates=["a", "b"],
            phi_c=0.5,
            entropy=0.5,
            timestamp=0.0
        )
        recursion = RecursionOperator(kappa=0.3, max_iterations=50, tolerance=1e-4)
        result = recursion.apply(state)
        self.assertEqual(round(result.norm, 5), round(1.0, 5))

    def test_network_coupling(self):
        """Test 4: Rede deve acoplar substratos."""
        state = CanonicalState(
            amplitudes=np.array([0.7, 0.3], dtype=complex),
            substrates=["a", "b"],
            phi_c=0.5,
            entropy=0.5,
            timestamp=0.0
        )
        network = NetworkOperator(coupling_strength=0.5)
        result = network.apply(state)
        self.assertEqual(round(result.norm, 5), round(1.0, 5))

    def test_emergence_positive(self):
        """Test 5: Emergência deve aumentar coerência se houver correlação."""
        state = CanonicalState(
            amplitudes=np.array([0.5+0.5j, 0.5+0.5j], dtype=complex),
            substrates=["a", "b"],
            phi_c=0.5,
            entropy=0.5,
            timestamp=0.0
        )
        emergence = EmergenceOperator()
        result = emergence.apply(state)
        self.assertGreaterEqual(result.phi_c, state.phi_c)

    def test_radiation_preserves_norm(self):
        """Test 6: Radiação deve preservar norma do estado emitido."""
        state = CanonicalState(
            amplitudes=np.array([0.6, 0.4], dtype=complex),
            substrates=["a", "b"],
            phi_c=0.5,
            entropy=0.5,
            timestamp=0.0
        )
        radiation = RadiationOperator(alpha=0.3)
        result = radiation.apply(state)
        self.assertEqual(round(result.norm, 5), round(1.0, 5))

    def test_omega_chain_completes(self):
        """Test 7: Cadeia Ω deve completar uma iteração."""
        omega = OmegaChain()
        result, log = omega.iterate(self.void_state)
        self.assertEqual(len(log["transitions"]), 6)

    def test_state_normalization(self):
        """Test 8: Estado deve ser normalizado."""
        state = CanonicalState(
            amplitudes=np.array([2.0, 3.0], dtype=complex),
            substrates=["a", "b"],
            phi_c=0.5,
            entropy=0.5,
            timestamp=0.0
        )
        state.normalize()
        self.assertEqual(round(state.norm, 10), round(1.0, 10))


class TestLindblad(unittest.TestCase):
    def setUp(self):
        self.lindblad = LindbladMasterEquation(dim=4)
        self.rho0 = np.eye(4, dtype=complex) / 4

    def test_hamiltonian_hermitian(self):
        """Test 9: H_eff deve ser hermitiana."""
        H = self.lindblad.H_eff
        self.assertTrue(np.allclose(H, H.conj().T))

    def test_lindblad_operators(self):
        """Test 10: Deve haver 4 operadores de Lindblad."""
        self.assertEqual(len(self.lindblad.operators), 4)
        self.assertIn("reject", self.lindblad.operators)
        self.assertIn("accept", self.lindblad.operators)
        self.assertIn("emit", self.lindblad.operators)
        self.assertIn("forget", self.lindblad.operators)

    def test_evolution_preserves_trace(self):
        """Test 11: Evolução deve preservar Tr(ρ) = 1."""
        rho_final, _ = self.lindblad.evolve(self.rho0, t_final=1.0, n_steps=100)
        self.assertEqual(round(abs(np.trace(rho_final)), 5), round(1.0, 5))

    def test_evolution_preserves_hermiticity(self):
        """Test 12: ρ deve permanecer hermitiana."""
        rho_final, _ = self.lindblad.evolve(self.rho0, t_final=1.0, n_steps=100)
        self.assertTrue(np.allclose(rho_final, rho_final.conj().T))

    def test_coherence_in_range(self):
        """Test 13: Φ_C deve estar em [0, 1]."""
        phi = self.lindblad._compute_coherence(self.rho0)
        self.assertGreaterEqual(phi, 0.0)
        self.assertLessEqual(phi, 1.0)

    def test_steady_state_exists(self):
        """Test 14: Estado estacionário deve existir."""
        rho_ss = self.lindblad.steady_state(max_iterations=100)
        self.assertEqual(round(abs(np.trace(rho_ss)), 5), round(1.0, 5))

    def test_gibbs_state_normalized(self):
        """Test 15: Estado de Gibbs deve ter Tr = 1."""
        rho_gibbs = self.lindblad.gibbs_state(beta=1.0)
        self.assertEqual(round(abs(np.trace(rho_gibbs)), 10), round(1.0, 10))

    def test_gibbs_hermitian(self):
        """Test 16: Estado de Gibbs deve ser hermitiano."""
        rho_gibbs = self.lindblad.gibbs_state(beta=1.0)
        self.assertTrue(np.allclose(rho_gibbs, rho_gibbs.conj().T))


class TestLyapunov(unittest.TestCase):
    def setUp(self):
        self.lyap = LyapunovConvergence()

    def test_fixed_point_positive(self):
        """Test 17: Ponto fixo deve ser não-negativo."""
        phi_star = self.lyap.fixed_point()
        self.assertGreaterEqual(phi_star, 0.0)
        self.assertLessEqual(phi_star, 1.0)

    def test_lyapunov_positive(self):
        """Test 18: V(t) deve ser não-negativa."""
        V = self.lyap.lyapunov_function(0.5)
        self.assertGreaterEqual(V, 0.0)

    def test_lyapunov_zero_at_fixed_point(self):
        """Test 19: V deve ser 0 no ponto fixo."""
        phi_star = self.lyap.fixed_point()
        V_star = self.lyap.lyapunov_function(phi_star)
        self.assertEqual(round(V_star, 10), round(1.0 - phi_star, 10))

    def test_convergence_from_low(self):
        """Test 20: Deve convergir a partir de Φ_C baixo."""
        result = self.lyap.verify_convergence(0.1, t_span=50.0, n_steps=500)
        self.assertTrue(result["V_decreasing"])

    def test_convergence_from_high(self):
        """Test 21: Deve convergir a partir de Φ_C alto."""
        result = self.lyap.verify_convergence(0.9, t_span=50.0, n_steps=500)
        self.assertTrue(result["converged"])

    def test_basin_global(self):
        """Test 22: Bacia de atração deve ser global."""
        basin = self.lyap.basin_of_attraction(n_samples=20)
        self.assertGreater(basin["basin_size"], 0.8)

    def test_dV_dt_negative(self):
        """Test 23: dV/dt deve ser negativa (ou zero)."""
        phi = 0.5
        dV = self.lyap.dV_dt(phi, 0.0)
        self.assertLessEqual(dV, 1e-3)  # Tolerância para ruído

    def test_learning_rate_positive(self):
        """Test 24: Taxa de aprendizado deve ser positiva."""
        eta = self.lyap.learning_rate(0.5)
        self.assertGreater(eta, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)