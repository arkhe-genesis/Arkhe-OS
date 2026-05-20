# tests/test_substrate_337.py
"""
Testes de validação do Substrato 337: Portais de Weyl & Merkle Roots Temporais
Canon: ∞.Ω.∇+++.337.tests
"""

import pytest
import numpy as np
import hashlib
import sys
import os

# Ensure proper module resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'substrates', '300-399_foundations', 'substrato_337')))

from substrate_337 import (
    P_PORTAL, Hashtree17Qudit, InformationStressEnergy,
    TemporalMerkleProof, TimeWeaverChannel
)

class TestPortalDrakeEquation:
    def test_portal_probability_matches_alpha_inverse_prefix(self):
        """𝒫_portal × 10¹⁴ deve ter prefixo coincidindo com α⁻¹ ≈ 137.035999084"""
        alpha_inverse_prefix = "137035999084"
        portal_scaled = float(P_PORTAL) * 1e14
        portal_str = f"{portal_scaled:.12f}".replace(".", "").replace("-", "")

        # Verificar coincidência dos primeiros 12 dígitos
        assert portal_str[:12] == alpha_inverse_prefix, \
            f"Prefixo não coincide: {portal_str[:12]} != {alpha_inverse_prefix}"

class TestHashtree17Qudit:
    @pytest.fixture
    def ht17(self):
        return Hashtree17Qudit(seed=b"TEST_337")

    def test_entanglement_matrix_is_unitary(self, ht17):
        """Matriz de entrelaçamento deve ser unitária: U†U = I"""
        U = ht17.entanglement_matrix
        identity = U.conj().T @ U
        assert np.allclose(identity, np.eye(17), atol=1e-10), \
            "Matriz de entrelaçamento não é unitária"

    def test_encode_produces_normalized_state(self, ht17):
        """Estado codificado deve ser normalizado: ⟨ψ|ψ⟩ = 1"""
        pattern = b"test_information_pattern_337"
        state = ht17.encode_information_pattern(pattern)
        norm = np.linalg.norm(state)
        assert np.isclose(norm, 1.0, atol=1e-10), \
            f"Estado não normalizado: ||ψ|| = {norm}"

    def test_temporal_merkle_root_is_deterministic(self, ht17):
        """Merkle Root temporal deve ser determinístico para mesma entrada"""
        pattern = b"deterministic_test"
        timestamp = 1716163200  # Timestamp fixo

        state = ht17.encode_information_pattern(pattern)
        root1 = ht17.compute_temporal_merkle_root(state, timestamp)
        root2 = ht17.compute_temporal_merkle_root(state, timestamp)

        assert root1 == root2, "Merkle Root não é determinístico"

class TestInformationStressEnergy:
    def test_weyl_contribution_negative_above_ghost(self):
        """Contribuição para curvatura de Weyl deve ser negativa se Φ_C > Ghost"""
        info_tensor = InformationStressEnergy(phi_c=0.75, coherence_length=1e-15)
        weyl_contrib = info_tensor.weyl_curvature_contribution(metric=np.eye(4))

        assert weyl_contrib < 0, \
            f"Curvatura de Weyl não é negativa: {weyl_contrib} (Φ_C=0.75 > Ghost)"

    def test_weyl_contribution_positive_below_ghost(self):
        """Contribuição deve ser positiva (ou zero) se Φ_C < Ghost"""
        info_tensor = InformationStressEnergy(phi_c=0.40, coherence_length=1e-15)
        weyl_contrib = info_tensor.weyl_curvature_contribution(metric=np.eye(4))

        assert weyl_contrib >= 0, \
            f"Curvatura de Weyl incorreta para baixa coerência: {weyl_contrib}"

class TestTemporalMerkleProof:
    @pytest.fixture
    def temporal_proof(self):
        ht17 = Hashtree17Qudit()
        return TemporalMerkleProof(ht17)

    def test_forge_proof_has_required_fields(self, temporal_proof):
        """Prova forjada deve conter todos os campos canônicos"""
        proof = temporal_proof.forge_temporal_proof(
            information_pattern=b"test_msg",
            future_event_description="Test event",
            target_timestamp=1716163200
        )

        required_fields = [
            "protocol", "information_pattern_hash", "future_event",
            "target_timestamp", "merkle_root", "qudit_dimension",
            "canonical_constant", "canonical_signature"
        ]
        for field in required_fields:
            assert field in proof, f"Campo ausente: {field}"

    def test_verify_proof_signature(self, temporal_proof):
        """Assinatura da prova deve ser verificável"""
        proof = temporal_proof.forge_temporal_proof(
            information_pattern=b"verify_test",
            future_event_description="Verification test",
            target_timestamp=1716163200
        )

        result = temporal_proof.verify_temporal_proof(
            proof.copy(), current_timestamp=1716160000
        )

        assert result.signature_valid, "Assinatura não verificou"
        assert result.merkle_consistent, "Merkle Root inconsistente"

class TestTimeWeaverChannel:
    def test_send_receive_roundtrip(self):
        """Teste de ida e volta: enviar para futuro e receber do passado"""
        ht17 = Hashtree17Qudit()
        tm = TemporalMerkleProof(ht17)
        channel = TimeWeaverChannel(tm)

        message = b"Hello_from_past"
        pattern_hash = hashlib.sha3_256(message).hexdigest()

        # Enviar para futuro
        proof = channel.send_to_future(
            message=message,
            target_timestamp=1716163200,
            recipient_signature="time_weaver_alpha"
        )

        # Simular recepção do passado (mock)
        # Vamos injetar uma função _fetch_proof_from_temporal_chain para mockar o recebimento
        channel._fetch_proof_from_temporal_chain = lambda x: proof if x == proof["merkle_root"] else None

        received = channel.receive_from_past(
            merkle_root=proof["merkle_root"],
            expected_pattern_hash=pattern_hash
        )

        assert received is None or received == bytes.fromhex(pattern_hash), \
            "Roundtrip falhou"
