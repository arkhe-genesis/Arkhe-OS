import pytest
from substrate_134.erc8004_canon import (
    ERC8004_IdentityRegistry, ERC8004_TokenArkheBridge, ChainProtocol
)

def test_erc8004_registry():
    registry = ERC8004_IdentityRegistry()
    identity = registry.register_identity(
        "0x123", ChainProtocol.ETHEREUM, {ChainProtocol.POLYGON: "0x456"},
        "ipfs://test", "pqc:pubkey"
    )

    assert identity.primary_address == "0x123"
    assert identity.chain_protocol == ChainProtocol.ETHEREUM

    proof = registry.add_verification_proof(
        identity.identity_id, ChainProtocol.POLYGON, 100, [], [], 0.9
    )

    assert not registry.verify_identity_cross_chain(identity.identity_id)

    registry.add_verification_proof(
        identity.identity_id, ChainProtocol.ARBITRUM, 200, [], [], 0.95
    )

    assert registry.verify_identity_cross_chain(identity.identity_id)

def test_erc8004_token_bridge():
    registry = ERC8004_IdentityRegistry()
    identity = registry.register_identity(
        "0x123", ChainProtocol.ETHEREUM, {}, "ipfs://test", "pqc:pubkey"
    )

    bridge = ERC8004_TokenArkheBridge(registry)
    token = {"payload": "test"}
    enriched = bridge.embed_identity_in_token(token, identity.identity_id)

    assert "erc8004_passport" in enriched

    extracted = bridge.extract_identity_from_token(enriched)
    assert extracted.identity_id == identity.identity_id
