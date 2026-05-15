import pytest
import asyncio
from security.pqc_rotation_manager import PQCKeyRotationManager
from federation.cross_org_scada_federation import CrossOrgSCADAFederation
from arkhe_ml.auto_ml.quantum_tinyml_optimizer import QuantumTinyMLOptimizer

@pytest.mark.asyncio
async def test_pqc_key_rotation():
    manager = PQCKeyRotationManager()
    result = await manager.rotate_keys()
    assert result["status"] == "success"
    assert result["downtime"] == 0

@pytest.mark.asyncio
async def test_cross_org_federation():
    federation = CrossOrgSCADAFederation()
    result = await federation.establish_federation("partner_002")
    assert result["status"] == "success"
    assert result["partner_id"] == "partner_002"

@pytest.mark.asyncio
async def test_quantum_tinyml_optimization():
    optimizer = QuantumTinyMLOptimizer()
    result = await optimizer.optimize_model("models/test.tflite")
    assert result["status"] == "success"
    assert result["compression_ratio"] == 0.6
    assert result["accuracy_boost"] == 0.02
