import pytest
from substrate_202.reference_impl.verifier_loop_poc import VerifierLoopOrchestrator
from substrate_134.erc8004_canon import ERC8004_IdentityRegistry, ChainProtocol, ERC8004_TokenArkheBridge
from substrate_202.dashboards.phi_composite_dashboard import PhiCCompositeDashboard, LayerType

@pytest.mark.asyncio
async def test_full_verifier_loop_with_erc8004_and_phi_dashboard():
    # 1. Setup ERC-8004
    registry = ERC8004_IdentityRegistry()
    identity = registry.register_identity(
        "0xMain", ChainProtocol.ETHEREUM, {ChainProtocol.ARKHE_TEMPORAL: "arkhe:123"},
        "ipfs://test", "pqc:pubkey"
    )
    bridge = ERC8004_TokenArkheBridge(registry)

    # 2. Setup Phi Dashboard
    dashboard = PhiCCompositeDashboard()

    # 3. Execute Loop
    orchestrator = VerifierLoopOrchestrator()
    result = await orchestrator.execute_full_loop("A", "B", 100.0)
    assert orchestrator.verify_loop_integrity(result)

    # 4. Integrate ERC-8004 into Token Arkhe layer output
    token_payload = {"intention_seal": result["layers"]["layer_3_token_arkhe"]["seal"]}
    enriched_token = bridge.embed_identity_in_token(token_payload, identity.identity_id)
    assert "erc8004_passport" in enriched_token

    # 5. Update Phi Dashboard with simulated metrics from the loop
    dashboard.simulate_layer_update(LayerType.MAINFRAME_ACID, 0.999, 0.99, 10.0, 0.001)
    dashboard.simulate_layer_update(LayerType.BEAVER_LOGIC, 0.995, 0.99, 50.0, 0.005)
    dashboard.simulate_layer_update(LayerType.TOKEN_ARKHE_INTENTION, 0.96, 0.95, 200.0, 0.02)
    dashboard.simulate_layer_update(LayerType.TEMPORALCHAIN_META, 0.9999, 0.999, 1000.0, 0.0001)

    report = await dashboard._generate_and_publish_report()
    assert report.composite_phi_c > 0.95
    assert report.alert_level in ["normal", "warning"]
