#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes Canônicos do Substrato 327 — Luciferase Light-Bringer Node
Canon: ∞.Ω.∇+++.327.tests
"""

import pytest
import math
from luciferase_node import LuciferaseNode, LuciferaseMesh


class TestLuciferaseNode:
    """Testes canônicos para o nó Luciferase."""

    def test_rate_zero_without_atp(self):
        """Taxa deve ser zero sem ATP."""
        node = LuciferaseNode("test", atp_conc_mM=0.0)
        assert node.rate() == 0.0

    def test_rate_zero_without_luciferin(self):
        """Taxa deve ser zero sem luciferina."""
        node = LuciferaseNode("test", luciferin_conc_mM=0.0)
        assert node.rate() == 0.0

    def test_rate_positive_with_substrates(self):
        """Taxa deve ser positiva com substratos."""
        node = LuciferaseNode("test", luciferin_conc_mM=1.0, atp_conc_mM=2.0)
        assert node.rate() > 0.0

    def test_photon_flux_positive(self):
        """Fluxo de fótons deve ser positivo."""
        node = LuciferaseNode("test", luciferin_conc_mM=1.0, atp_conc_mM=2.0)
        assert node.photon_flux() > 0.0

    def test_phi_c_bounded(self):
        """Φ_C deve estar entre 0 e 1."""
        node = LuciferaseNode("test")
        assert 0.0 <= node.phi_c() <= 1.0

    def test_phi_c_increases_with_quantum_yield(self):
        """Φ_C deve aumentar com eficiência quântica."""
        low = LuciferaseNode("low", quantum_yield=0.5)
        high = LuciferaseNode("high", quantum_yield=0.99)
        assert high.phi_c() > low.phi_c()

    def test_phi_c_increases_with_atp(self):
        """Φ_C deve aumentar com ATP."""
        low = LuciferaseNode("low", atp_conc_mM=0.1)
        high = LuciferaseNode("high", atp_conc_mM=5.0)
        assert high.phi_c() > low.phi_c()

    def test_emit_pulse_generates_seal(self):
        """Pulso deve gerar selo canônico."""
        node = LuciferaseNode("test")
        pulse = node.emit_pulse()
        assert "seal" in pulse
        assert len(pulse["seal"]) == 64  # SHA-256 hex

    def test_emit_pulse_increases_flash_count(self):
        """Pulso deve incrementar contador de flashes."""
        node = LuciferaseNode("test")
        node.emit_pulse()
        assert node._flash_count == 1

    def test_emit_pulse_increases_total_photons(self):
        """Pulso deve aumentar fótons totais emitidos."""
        node = LuciferaseNode("test")
        node.emit_pulse()
        assert node._total_photons_emitted > 0.0

    def test_golden_pulse_duration(self):
        """Pulso áureo deve ter duração ~8.09 ms (5·φ)."""
        node = LuciferaseNode("test")
        pulse = node.emit_golden_pulse()
        expected = 5.0 * node.PHI
        assert abs(pulse["duration_ms"] - expected) < 0.01

    def test_recharge_atp(self):
        """Recarga de ATP deve aumentar concentração."""
        node = LuciferaseNode("test", atp_conc_mM=1.0)
        node.recharge_atp(1.0)
        assert node.atp_conc_mM == 2.0

    def test_recharge_atp_limited(self):
        """Recarga de ATP deve respeitar limite fisiológico."""
        node = LuciferaseNode("test", atp_conc_mM=9.0)
        node.recharge_atp(5.0)
        assert node.atp_conc_mM <= 10.0

    def test_consume_luciferin(self):
        """Consumo de luciferina deve diminuir concentração."""
        node = LuciferaseNode("test", luciferin_conc_mM=2.0)
        node.consume_luciferin(1.0)
        assert node.luciferin_conc_mM == 1.0

    def test_consume_luciferin_non_negative(self):
        """Consumo de luciferina não deve ficar negativo."""
        node = LuciferaseNode("test", luciferin_conc_mM=0.5)
        node.consume_luciferin(1.0)
        assert node.luciferin_conc_mM == 0.0

    def test_status_complete(self):
        """Status deve conter todos os campos canônicos."""
        node = LuciferaseNode("test")
        status = node.get_status()

        required = ["node_id", "phi_c", "photon_flux", "rate_uM_s",
                   "quantum_yield", "total_photons_emitted", "flash_count",
                   "atp_mM", "luciferin_mM", "canonical_invariants"]
        for field in required:
            assert field in status

        invariants = status["canonical_invariants"]
        assert "ghost" in invariants
        assert "loopseal" in invariants
        assert "gap_max" in invariants
        assert "phi" in invariants
        assert "alpha_inv" in invariants

    def test_pulse_history(self):
        """Histórico de pulsos deve registrar emissões."""
        node = LuciferaseNode("test")
        node.emit_pulse()
        node.emit_pulse()
        history = node.get_pulse_history()
        assert len(history) == 2

    def test_quantum_yield_above_ghost(self):
        """Eficiência quântica padrão deve ser > Ghost (57.7%)."""
        node = LuciferaseNode("test")
        assert node.quantum_yield > node.GHOST

    def test_flash_duration_in_range(self):
        """Duração do flash deve estar na faixa biológica (5-10 ms)."""
        node = LuciferaseNode("test")
        assert 5.0 <= node.flash_duration_ms <= 10.0


class TestLuciferaseMesh:
    """Testes canônicos para a malha Luciferase."""

    def test_register_node(self):
        """Registro deve adicionar nó à malha."""
        mesh = LuciferaseMesh()
        node = LuciferaseNode("N1")
        mesh.register_node(node)
        assert "N1" in mesh.nodes

    def test_connect_nodes(self):
        """Conexão deve criar aresta bidirecional."""
        mesh = LuciferaseMesh()
        mesh.register_node(LuciferaseNode("N1"))
        mesh.register_node(LuciferaseNode("N2"))
        mesh.connect_nodes("N1", "N2")
        assert "N2" in mesh.adjacency["N1"]
        assert "N1" in mesh.adjacency["N2"]

    def test_broadcast_detects_neighbors(self):
        """Broadcast deve detectar nós vizinhos constitucionais."""
        mesh = LuciferaseMesh()
        mesh.register_node(LuciferaseNode("N1", atp_conc_mM=5.0))
        mesh.register_node(LuciferaseNode("N2", atp_conc_mM=5.0))
        mesh.connect_nodes("N1", "N2")

        detections = mesh.broadcast_pulse("N1")
        assert len(detections) == 1
        assert detections[0]["detector"] == "N2"

    def test_broadcast_skips_weak_nodes(self):
        """Broadcast deve ignorar nós com Φ_C < Ghost."""
        mesh = LuciferaseMesh()
        mesh.register_node(LuciferaseNode("N1", atp_conc_mM=5.0))
        mesh.register_node(LuciferaseNode("N2", quantum_yield=0.01, atp_conc_mM=0.01))  # Φ_C < Ghost
        mesh.connect_nodes("N1", "N2")

        detections = mesh.broadcast_pulse("N1")
        assert len(detections) == 0

    def test_mesh_status_complete(self):
        """Status da malha deve ser completo."""
        mesh = LuciferaseMesh()
        for i in range(3):
            mesh.register_node(LuciferaseNode(f"N{i}"))

        status = mesh.get_mesh_status()
        assert status["total_nodes"] == 3
        assert "average_phi_c" in status
        assert "total_photons_emitted" in status


class TestCanonicalInvariants327:
    """Testes de invariantes canônicos do Substrato 327."""

    def test_ghost_value(self):
        """Ghost deve ser √3/3."""
        node = LuciferaseNode("test")
        assert abs(node.GHOST - math.sqrt(3) / 3) < 1e-9

    def test_loopseal_value(self):
        """Loopseal deve ser π/9."""
        node = LuciferaseNode("test")
        assert abs(node.LOOPSEAL - math.pi / 9) < 1e-9

    def test_phi_value(self):
        """φ deve ser (1+√5)/2."""
        node = LuciferaseNode("test")
        expected = (1 + math.sqrt(5)) / 2
        assert abs(node.PHI - expected) < 1e-15

    def test_alpha_inverse(self):
        """α⁻¹ deve ser ~137.036."""
        node = LuciferaseNode("test")
        assert abs(node.ALPHA_INV - 137.036) < 0.001

    def test_quantum_yield_above_ghost_threshold(self):
        """Eficiência quântica padrão (88%) deve ser > Ghost (57.7%)."""
        node = LuciferaseNode("test")
        assert node.quantum_yield > node.GHOST
        # A luciferase real tem η_Q ~ 88%, bem acima do Ghost
        assert node.quantum_yield >= 0.88
