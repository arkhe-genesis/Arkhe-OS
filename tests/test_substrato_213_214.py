import pytest
import asyncio
import hashlib
import time
from unittest.mock import AsyncMock, MagicMock
from deployment.inno_setup_tool import InnoSetupTool
from tools.production_critical_tools import ProductionCriticalToolExecutor, ProductionToolConfig, CriticalToolType
from security.hsm_pqc_production_integration import HSMProductionPQCSigner, HSMProductionConfig
from ml.delta_mem_tool_predictor import DeltaMemToolPredictor
from federation.federated_tool_catalog import FederatedToolCatalog, ToolDiscoveryQuery

@pytest.mark.asyncio
async def test_inno_setup_tool():
    # Mock dependencies
    hsm_signer = AsyncMock()
    hsm_signer.sign_data.return_value = {"success": True, "signature_hex": "1234abcd"}
    delta_mem = AsyncMock()
    temporal = AsyncMock()

    # Instance
    inno = InnoSetupTool(compiler_path="/fake/path", hsm_signer=hsm_signer, delta_mem=delta_mem, temporal=temporal)

    # Test compilation
    result = await inno.compile_installer("fake_script", "MyApp", "Output", sign_with_hsm=True)
    assert result["status"] == "success"
    assert result["signature_hex"] == "1234abcd"

    # Test idempotency (cache hit)
    result2 = await inno.compile_installer("fake_script", "MyApp", "Output", sign_with_hsm=True)
    assert result2["status"] == "cached"

@pytest.mark.asyncio
async def test_production_critical_tools():
    config = ProductionToolConfig(
        tool_id="test_db",
        tool_type=CriticalToolType.DATABASE_QUERY,
        endpoint="mock_db",
        credentials_vault_path="mock/path",
        timeout_seconds=5,
        retry_policy={"max_attempts": 3, "backoff_base": 2, "circuit_cooldown_seconds": 1},
        circuit_breaker_threshold=2,
        rate_limit_per_minute=10,
        requires_pqc_signature=True
    )

    hsm = AsyncMock()
    hsm.sign_data.return_value = {"success": True, "signature_hex": "deadbeef"}
    temporal = AsyncMock()
    guardian = AsyncMock()
    guardian.validate_operation.return_value = (True, "OK")
    guardian.validate_external_url.return_value = (True, "OK")

    executor = ProductionCriticalToolExecutor(config, hsm, temporal, guardian=guardian)

    # Test success DB query
    result = await executor.execute_database_query("SELECT 1", read_only=True)
    assert result["status"] == "success"
    assert "pqc_signature" in result["result"]
    assert result["result"]["pqc_signature"] == "deadbeef"

    # Test circuit breaker with DB query
    guardian.validate_operation.return_value = (True, "OK")
    # Force errors
    executor._circuit_open = False
    executor._failure_count = config.circuit_breaker_threshold
    executor._record_failure()
    assert executor._circuit_open is True

    result_cb = await executor.execute_database_query("SELECT 1")
    assert result_cb["status"] == "circuit_open"

@pytest.mark.asyncio
async def test_hsm_pqc_production():
    config = HSMProductionConfig(
        provider="mock",
        pkcs11_library="mock",
        slot_id=0,
        token_label="mock",
        key_label="test_key",
        pqc_algorithm="CRYSTALS-Dilithium3",
        pin_vault_path="mock",
        audit_all_operations=False
    )

    signer = HSMProductionPQCSigner(config)
    await signer._connect_to_hsm()

    result = await signer.sign_data(b"test_data")
    assert result["success"] is True
    assert "signature_hex" in result

    verify = await signer.verify_signature(b"test_data", result["signature_hex"])
    assert verify is True

@pytest.mark.asyncio
async def test_delta_mem_predictor():
    delta_wrapper = AsyncMock()
    predictor = DeltaMemToolPredictor(
        delta_mem_wrapper=delta_wrapper,
        available_tools=["db_query", "api_call", "hsm_sign"]
    )

    # Record some experiences
    await predictor.record_tool_call_experience(
        context="get user data", tool_id="db_query", parameters={},
        success=True, latency_ms=50, tokens_consumed=10, phi_c_before=0.8, phi_c_after=0.9
    )

    await predictor.record_tool_call_experience(
        context="fetch external weather", tool_id="api_call", parameters={},
        success=True, latency_ms=200, tokens_consumed=20, phi_c_before=0.8, phi_c_after=0.85
    )

    # Force online training
    await predictor._online_training_step(batch_size=1)

    # Predict
    pred = await predictor.predict_optimal_tool(context="query user database")
    assert pred.predicted_tool_id in predictor.available_tools
    assert pred.confidence > 0

@pytest.mark.asyncio
async def test_federated_catalog():
    hsm = AsyncMock()
    hsm.sign_data.return_value = {"success": True, "signature_hex": "fed_sig"}

    catalog = FederatedToolCatalog(
        node_id="node_1",
        org_id="org_A",
        local_tools={
            "tool_a": {"name": "A", "capabilities": ["data_read"], "avg_latency_ms": 50, "success_rate": 0.99},
            "tool_b": {"name": "B", "capabilities": ["data_write"], "avg_latency_ms": 100, "success_rate": 0.95}
        },
        hsm_signer=hsm
    )

    # Publish
    published = await catalog.publish_local_tools(dp_epsilon=2.0)
    assert len(published) == 2
    assert catalog._catalog["tool_a"].pqc_signature == "fed_sig"

    # Discover
    query = ToolDiscoveryQuery(required_capabilities=["data_read"])
    results = await catalog.discover_tools(query)
    assert len(results) >= 1
    assert "data_read" in results[0].capabilities
