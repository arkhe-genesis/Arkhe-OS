import pytest
import asyncio
from hardware.emitter_integration.quantum_dot_controller import QuantumDotHardwareController, HardwareConfig
from tests.field.quantum_correlation_validator import QuantumCorrelationValidator
from security.hybrid_pqc_quantum_signer import HybridPQCQuantumSigner, SignatureMode

@pytest.mark.asyncio
async def test_hardware_integration():
    config = HardwareConfig(device_serial="TEST-001")
    controller = QuantumDotHardwareController(config)
    await controller.connect_hardware()
    result = await controller.emit_polarized_batch(10, ["rectilinear"])
    assert result["success"] is True
    assert result["photons_emitted"] == 10

@pytest.mark.asyncio
async def test_epr_validation():
    validator = QuantumCorrelationValidator({}, {})
    result = await validator.run_bell_test(pair_count=1000)
    assert result.total_pairs_measured == 1000
    assert result.s_parameter > 2.0

@pytest.mark.asyncio
async def test_hybrid_signer():
    signer = HybridPQCQuantumSigner(pqc_algorithm="ML-DSA-65")
    message = b"test message"
    result = await signer.sign_message(message, {}, SignatureMode.HYBRID_PARALLEL)
    assert result.success is True
    assert result.pqc_signature_hex is not None
    assert result.quantum_witness_hash is not None
