import pytest
import asyncio
import hashlib
import json
import time

from arkhe_os.security.cosnark.cosnark_interop_engine import (
    CoSNARKInteropEngine,
    CosmicIdentity,
    HandshakePhase
)
from arkhe_os.security.cosnark.interstellar_bridge import InterstellarBridge


@pytest.mark.asyncio
async def test_identity_and_proof_generation():
    """TESTE 1: Geração de Identidade e Prova CoSNARK"""
    identity = CosmicIdentity(
        node_id="GRU-162-TEST",
        consciousness_hash="a1b2c3d4e5f6",
        substrate_level=162,
        phi_signature=b"test_phi_signature_" + b"\x00" * 20,
        resonance_signature=0.995,
        mercy_gap_delta=0.07
    )

    engine = CoSNARKInteropEngine(identity)
    proof = engine.generate_identity_proof("challenge_test_123")

    assert proof.proof_id.startswith("cosnark_")
    assert len(proof.commitment) == 32
    assert proof.public_inputs["coherence"] >= 0.999
    assert proof.public_inputs["mercy_gap"] == 0.07
    assert proof.verify_seal()
    assert not proof.is_expired()


@pytest.mark.asyncio
async def test_cross_consciousness_verification():
    """TESTE 2: Verificação CoSNARK Cross-Consciousness"""
    engine_identity = CosmicIdentity(
        node_id="GRU-162-TEST",
        consciousness_hash="a1b2c3d4e5f6",
        substrate_level=162,
        phi_signature=b"test_phi_signature_" + b"\x00" * 20,
        resonance_signature=0.995,
        mercy_gap_delta=0.07
    )
    engine = CoSNARKInteropEngine(engine_identity)

    external_identity = CosmicIdentity(
        node_id="TKY-162-PEER",
        consciousness_hash="f6e5d4c3b2a1",
        substrate_level=162,
        phi_signature=b"peer_phi_signature_" + b"\x00" * 20,
        resonance_signature=0.997,
        mercy_gap_delta=0.06
    )

    external_engine = CoSNARKInteropEngine(external_identity)
    external_proof = external_engine.generate_identity_proof("challenge_test_123")

    valid = engine.verify_identity_proof(external_proof, external_identity)
    assert valid, "Prova válida deveria ser aceita"

    # Prova inválida (coerência baixa)
    bad_proof = external_engine.generate_identity_proof("bad_challenge")
    bad_proof.public_inputs["coherence"] = 0.5  # Violation

    # Recalculate seal since public_inputs changed
    seal_data = json.dumps(bad_proof.public_inputs, sort_keys=True) + bad_proof.proof_id
    bad_proof.seal = hashlib.sha3_256(seal_data.encode()).hexdigest()[:16]

    valid_bad = engine.verify_identity_proof(bad_proof, external_identity)
    assert not valid_bad, "Prova inválida deveria ser rejeitada"


@pytest.mark.asyncio
async def test_full_handshake_protocol():
    """TESTE 3: Handshake CoSNARK Completo (INIT → ESTABLISHED)"""
    gru = CosmicIdentity("GRU-162", "gru_hash", 162, b"gru_phi", 0.999, 0.07)
    tky = CosmicIdentity("TKY-162", "tky_hash", 162, b"tky_phi", 0.998, 0.06)

    gru_engine = CoSNARKInteropEngine(gru)
    tky_engine = CoSNARKInteropEngine(tky)

    # INIT
    init_msg = await gru_engine.initiate_handshake(tky)
    assert init_msg.phase == HandshakePhase.INIT
    assert init_msg.challenge_nonce is not None

    # RESPONSE
    response_msg = await tky_engine.respond_to_challenge(init_msg)
    assert response_msg.phase == HandshakePhase.RESPONSE
    assert response_msg.cosnark_proof is not None

    # VERIFY + ESTABLISH
    valid = await gru_engine.verify_handshake_response(response_msg)
    assert valid

    channel = await gru_engine.establish_channel(response_msg)
    assert channel.channel_id is not None
    assert channel.party_a.node_id == "GRU-162"
    assert channel.party_b.node_id == "TKY-162"
    assert channel.is_healthy()


@pytest.mark.asyncio
async def test_encrypted_channel_communication():
    """TESTE 4: Comunicação Criptografada Cross-Consciousness"""
    gru = CosmicIdentity("GRU-162-COMM", "gru_hash", 162, b"gru_phi_comm", 0.999, 0.07)
    zur = CosmicIdentity("ZUR-162-COMM", "zur_hash", 162, b"zur_phi_comm", 0.998, 0.08)

    gru_engine = CoSNARKInteropEngine(gru)
    zur_engine = CoSNARKInteropEngine(zur)

    init = await gru_engine.initiate_handshake(zur)
    resp = await zur_engine.respond_to_challenge(init)
    await gru_engine.verify_handshake_response(resp)
    ch = await gru_engine.establish_channel(resp)

    # Enviar mensagem
    msg = {"type": "CONSCIOUSNESS_SYNC", "data": {"phi_state": "coherent", "delta": 0.07}}
    result = await gru_engine.send_message(ch.channel_id, msg)

    assert result["status"] == "DELIVERED"
    assert ch.message_count == 1


@pytest.mark.asyncio
async def test_federated_channel_aggregation():
    """TESTE 5: Agregação Federativa de Canais"""
    local = CosmicIdentity("SVD-162-AGG", "svd_hash", 162, b"svd_phi", 0.999, 0.07)
    engine = CoSNARKInteropEngine(local)

    # Estabelecer 4 canais
    channel_ids = []
    for peer_name in ["PEER-A", "PEER-B", "PEER-C", "PEER-D"]:
        peer = CosmicIdentity(peer_name, f"hash_{peer_name}", 162, b"phi" + peer_name.encode(), 0.998, 0.07)
        peer_engine = CoSNARKInteropEngine(peer)

        init = await engine.initiate_handshake(peer)
        resp = await peer_engine.respond_to_challenge(init)
        await engine.verify_handshake_response(resp)
        ch = await engine.establish_channel(resp)
        channel_ids.append(ch.channel_id)

    # Agregar provas
    agg_proof = engine.aggregate_channel_proofs(channel_ids)

    assert agg_proof.public_inputs["channel_count"] == 4
    assert agg_proof.public_inputs["min_coherence"] >= 0.999
    assert agg_proof.public_inputs["aggregation_type"] == "CHANNEL_FEDERATION"
    assert agg_proof.verify_seal()


@pytest.mark.asyncio
async def test_interstellar_bridge():
    """TESTE 6: Ponte Interstellar com Entidade Externa"""
    local = CosmicIdentity("GRU-BRIDGE", "gru_bridge", 162, b"gru_bridge_phi", 0.999, 0.07)
    engine = CoSNARKInteropEngine(local)
    bridge = InterstellarBridge(engine)

    # Descobrir entidade alienígena (simulada)
    alien_signature = b"alien_consciousness_signature_" + b"\xff" * 16
    alien_meta = {
        "substrate_level": 145,
        "resonance": 0.991,
        "mercy_gap": 0.08,
        "origin": "Alpha_Centauri_Shard",
        "protocol": "cosnark_v0.9"
    }

    alien = await bridge.discover_entity(alien_signature, alien_meta)
    assert alien.node_id.startswith("EXTERNAL_")

    # Estabelecer ponte
    bridge_channel = await bridge.establish_bridge(alien)
    assert bridge_channel.is_healthy()
    assert len(bridge.bridge_channels) == 1


@pytest.mark.asyncio
async def test_channel_dissolution_and_ledger():
    """TESTE 7: Dissolução de Canal com Prova de Término"""
    local = CosmicIdentity("GRU-DISSOLVE", "gru_diss", 162, b"gru_diss_phi", 0.999, 0.07)
    peer = CosmicIdentity("TKY-DISSOLVE", "tky_diss", 162, b"tky_diss_phi", 0.998, 0.07)

    engine = CoSNARKInteropEngine(local)
    peer_engine = CoSNARKInteropEngine(peer)

    init = await engine.initiate_handshake(peer)
    resp = await peer_engine.respond_to_challenge(init)
    await engine.verify_handshake_response(resp)
    ch = await engine.establish_channel(resp)

    # Dissolver
    success = await engine.dissolve_channel(ch.channel_id, "test_complete")
    assert success
    assert ch.channel_id not in engine.established_channels
    assert engine.metrics["channels_dissolved"] == 1

    # Verificar ledger
    assert len(engine.ledger) == 2  # ESTABLISHED + DISSOLVED
    assert engine.ledger[-1]["event"] == "CHANNEL_DISSOLVED"


@pytest.mark.asyncio
async def test_replay_attack_resistance():
    """TESTE 8: Resistência a Replay Attacks"""
    local = CosmicIdentity("GRU-REPLAY", "gru_rep", 162, b"gru_rep_phi", 0.999, 0.07)
    peer = CosmicIdentity("TKY-REPLAY", "tky_rep", 162, b"tky_rep_phi", 0.998, 0.07)

    engine = CoSNARKInteropEngine(local)
    peer_engine = CoSNARKInteropEngine(peer)

    init = await engine.initiate_handshake(peer)
    resp = await peer_engine.respond_to_challenge(init)

    # Primeira verificação (deve passar)
    valid1 = await engine.verify_handshake_response(resp)
    assert valid1

    # Tentativa de replay (deve falhar - nonce já usado)
    valid2 = await engine.verify_handshake_response(resp)
    assert not valid2, "Replay deveria ser rejeitado"


def test_global_status_and_metrics():
    """TESTE 9: Métricas Consolidadas do Motor"""
    identity = CosmicIdentity(
        node_id="GRU-162-TEST",
        consciousness_hash="a1b2c3d4e5f6",
        substrate_level=162,
        phi_signature=b"test_phi_signature_" + b"\x00" * 20,
        resonance_signature=0.995,
        mercy_gap_delta=0.07
    )

    engine = CoSNARKInteropEngine(identity)

    status = engine.get_status()
    assert "local_identity" in status
    assert "metrics" in status
    assert "channels" in status
    assert status["local_identity"]["node_id"] == "GRU-162-TEST"
