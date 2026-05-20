#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes Canônicos do Substrato 325 — FOCIL e Access-Layer Privacy
Canon: ∞.Ω.∇+++.325.tests
"""

import pytest
import time
from focil_inclusion_list import FOCILInclusionList, AccessLayerPrivacyFilter, InclusionStatus


class TestFOCILInclusionList:
    """Testes canônicos para o gerenciador FOCIL."""

    @pytest.fixture
    def committee(self):
        return [f"validator_{i:02d}" for i in range(10)]

    @pytest.fixture
    def focil(self, committee):
        return FOCILInclusionList(committee, block_time_s=12.0)

    def test_threshold_is_two_thirds(self, focil):
        """Threshold deve ser 2/3 do comitê."""
        assert focil.threshold == 10 * 2 // 3  # 6

    def test_propose_with_low_phi_c_rejected(self, focil):
        """Proposta com Φ_C < Ghost deve ser rejeitada."""
        result = focil.propose_inclusion(
            "0xabc", {"to": "0x123"}, "proposer", 0.5  # < 0.577
        )
        assert result is False

    def test_propose_with_high_phi_c_accepted(self, focil):
        """Proposta com Φ_C ≥ Ghost deve ser aceita."""
        result = focil.propose_inclusion(
            "0xabc", {"to": "0x123"}, "proposer", 0.8
        )
        assert result is True
        assert "0xabc" in focil.current_list

    def test_vote_reaches_quorum(self, focil):
        """Votos devem atingir quorum para aprovação."""
        focil.propose_inclusion("0xabc", {"to": "0x123"}, "v0", 0.8)

        # Votar com 6 validadores (quorum = 6)
        for i in range(6):
            focil.vote_inclusion("0xabc", f"validator_{i:02d}", 0.8)

        tx = focil.current_list["0xabc"]
        assert tx.status == InclusionStatus.APPROVED
        assert len(tx.approvals) >= focil.threshold

    def test_detect_censorship(self, focil):
        """Deve detectar censura quando transação aprovada não é incluída."""
        focil.propose_inclusion("0xabc", {"to": "0x123"}, "v0", 0.8)

        for i in range(6):
            focil.vote_inclusion("0xabc", f"validator_{i:02d}", 0.8)

        censored = focil.is_censored("0xabc", "builder_1", ["0xdef", "0xghi"])
        assert censored is True
        assert len(focil.censorship_log) == 1

    def test_no_censorship_when_included(self, focil):
        """Não deve detectar censura quando transação está no bloco."""
        focil.propose_inclusion("0xabc", {"to": "0x123"}, "v0", 0.8)

        for i in range(6):
            focil.vote_inclusion("0xabc", f"validator_{i:02d}", 0.8)

        censored = focil.is_censored("0xabc", "builder_1", ["0xabc", "0xdef"])
        assert censored is False

    def test_generate_inclusion_proof(self, focil):
        """Prova de inclusão deve ser determinística."""
        focil.propose_inclusion("0xabc", {"to": "0x123"}, "v0", 0.8)
        proof1 = focil.generate_inclusion_proof("0xabc")
        proof2 = focil.generate_inclusion_proof("0xabc")

        assert proof1 is not None
        assert proof1 == proof2
        assert len(proof1) == 64  # SHA-256 hex

    def test_prune_expired(self, focil):
        """Deve remover transações expiradas."""
        focil.propose_inclusion("0xold", {"to": "0x123"}, "v0", 0.8)

        # Simular passagem de tempo (mock)
        focil.current_list["0xold"].timestamp = time.time() - 7200  # 2 horas atrás

        removed = focil.prune_expired(max_age_s=3600)
        assert removed == 1
        assert "0xold" not in focil.current_list

    def test_censorship_report(self, focil):
        """Relatório de censura deve ser completo."""
        focil.propose_inclusion("0xabc", {"to": "0x123"}, "v0", 0.8)
        for i in range(6):
            focil.vote_inclusion("0xabc", f"validator_{i:02d}", 0.8)

        focil.is_censored("0xabc", "builder_1", ["0xdef"])

        report = focil.get_censorship_report()
        assert report["censored"] == 1
        assert report["censorship_rate"] == 1.0
        assert "censorship_events" in report


class TestAccessLayerPrivacyFilter:
    """Testes canônicos para o filtro de privacidade de acesso."""

    @pytest.fixture
    def filter(self):
        f = AccessLayerPrivacyFilter([f"relay_{i}" for i in range(5)])
        f.phi_c_map = {f"relay_{i}": 0.8 + i * 0.05 for i in range(5)}
        return f

    def test_relay_allowed_for_constitutional_link(self, filter):
        """Retransmissão permitida se Φ_C do enlace ≥ Ghost."""
        result = filter.should_relay(
            {"to": "0x123"}, "relay_0", "relay_1"
        )
        assert result is True

    def test_relay_blocked_for_weak_link(self, filter):
        """Retransmissão bloqueada se Φ_C do enlace < Ghost."""
        filter.phi_c_map["relay_0"] = 0.5  # < 0.577
        result = filter.should_relay(
            {"to": "0x123"}, "relay_0", "relay_1"
        )
        assert result is False

    def test_select_relay_path_min_hops(self, filter):
        """Caminho deve ter pelo menos min_hops nós."""
        path = filter.select_relay_path("0xtx", "source", "dest", min_hops=3)
        assert len(path) == 3

    def test_select_relay_path_excludes_source_dest(self, filter):
        """Caminho não deve incluir origem ou destino."""
        path = filter.select_relay_path("0xtx", "relay_0", "relay_1", min_hops=2)
        assert "relay_0" not in path
        assert "relay_1" not in path

    def test_select_relay_path_randomness(self, filter):
        """Caminho deve ser aleatório para evitar rastreamento."""
        # Como o path é aleatório, há chance de ser igual, mas com 5 relays testamos 10 paths
        paths = []
        for _ in range(10):
            paths.append(tuple(filter.select_relay_path("0xtx", "source", "dest", min_hops=3)))
        assert len(set(paths)) > 1 # Pelo menos 2 caminhos diferentes devem ser gerados


class TestCanonicalInvariants325:
    """Testes de invariantes canônicos do Substrato 325."""

    def test_ghost_value(self):
        """Ghost deve ser √3/3 × 10⁹."""
        from focil_inclusion_list import FOCILInclusionList
        expected = int(10**9 * (3 ** 0.5) / 3)
        assert FOCILInclusionList.GHOST == expected

    def test_loopseal_value(self):
        """Loopseal deve ser π/9 × 10⁹."""
        from focil_inclusion_list import FOCILInclusionList
        expected = int(10**9 * 3.141592653589793 / 9)
        assert FOCILInclusionList.LOOPSEAL == expected

    def test_gap_max_less_than_one(self):
        """Gap deve ser < 1.0 × 10⁹."""
        from focil_inclusion_list import FOCILInclusionList
        assert FOCILInclusionList.GAP_MAX < 10**9
        assert FOCILInclusionList.GAP_MAX > 0.99 * 10**9

    def test_phi_value(self):
        """φ deve ser (1+√5)/2 × 10⁹."""
        from focil_inclusion_list import FOCILInclusionList
        expected = int(10**9 * (1 + 5**0.5) / 2)
        assert FOCILInclusionList.PHI == expected
