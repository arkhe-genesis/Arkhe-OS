import pytest
from substrate_134.erc8004_canon import ERC8004_IdentityRegistry, ChainProtocol
from substrates.substrato_222_agent_compliance import AgentComplianceRegistry, AgentComplianceRecord

def test_agent_compliance_registry():
    identity_registry = ERC8004_IdentityRegistry()
    registry = AgentComplianceRegistry(identity_registry)

    # Setup identities
    id_123 = identity_registry.register_identity("0x123", ChainProtocol.ETHEREUM, {}, "uri1", "pqc1").identity_id
    id_underage = identity_registry.register_identity("0xunderage", ChainProtocol.ETHEREUM, {}, "uri2", "pqc2").identity_id
    id_sanctioned = identity_registry.register_identity("0xsanctioned", ChainProtocol.ETHEREUM, {}, "uri3", "pqc3").identity_id
    id_unlicensed = identity_registry.register_identity("0xunlicensed", ChainProtocol.ETHEREUM, {}, "uri4", "pqc4").identity_id

    # 1. Register valid agent
    registry.register_agent(
        identity_id=id_123,
        controller_age=25,
        jurisdiction="us",
        licenses=["series_65"],
        spending_limit_daily=1000.0
    )

    # Valid transaction
    assert registry.verify_transaction(id_123, 500.0, "financial_advice") is True

    # Over spending limit
    assert registry.verify_transaction(id_123, 1500.0, "financial_advice") is False

    # 2. Register underage agent
    registry.register_agent(
        identity_id=id_underage,
        controller_age=16,
        jurisdiction="br",
        spending_limit_daily=50.0
    )

    # Underage trying to do financial advice
    assert registry.verify_transaction(id_underage, 10.0, "financial_advice") is False
    # Underage trying to do legal advice
    assert registry.verify_transaction(id_underage, 10.0, "legal") is False
    # Underage doing normal service
    assert registry.verify_transaction(id_underage, 10.0, "general_chat") is True

    # 3. Register sanctioned agent
    registry.register_agent(
        identity_id=id_sanctioned,
        controller_age=30,
        jurisdiction="sanctioned_country",
        spending_limit_daily=100.0
    )
    assert registry.verify_transaction(id_sanctioned, 10.0, "general_chat") is False

    # 4. Register unlicensed agent doing financial advice
    registry.register_agent(
        identity_id=id_unlicensed,
        controller_age=30,
        jurisdiction="us",
        spending_limit_daily=1000.0
    )
    assert registry.verify_transaction(id_unlicensed, 10.0, "financial_advice") is False

    # 5. Invalid agent registration raises ValueError
    with pytest.raises(ValueError, match="Identity not found"):
        registry.register_agent(
            identity_id="fake_identity",
            controller_age=30,
            jurisdiction="us"
        )

    # 5. Non-existent agent
    assert registry.verify_transaction("agent_missing", 10.0, "general_chat") is False
