import pytest
from arkhe_quantum_production.epr_sync import EPRClockSyncEngine
from arkhe_quantum_production.ldpc import PhotonAssistedLDPC
from arkhe_quantum_production.dithering import QuantumJitterDithering
from arkhe_quantum_production.qos_router import PhiCQosRouter
from arkhe_quantum_production.hardware_controller import QuantumDotHardwareController
from arkhe_quantum_production.bell_validator import QuantumCorrelationValidator
from arkhe_quantum_production.hybrid_signer import HybridPQCQuantumSigner

from arkhe_tinyml.core import TinyModel, LocalPhiCEngine, TinyAgent
from arkhe_tinyml.federated import FederatedTinyTrainer
from arkhe_tinyml.guardrails import TinyGuardrails
from arkhe_tinyml.tflite_bridge import TFLiteMicroBridge

# --- TinyML Edge Tests (9) ---
def test_tinymodel_inference():
    model = TinyModel()
    res = model.infer([0.1, 0.2])
    assert res["latency_ms"] < 5.0

def test_local_phi_c_memory():
    engine = LocalPhiCEngine()
    res = engine.get_phi_c()
    assert res["memory_bytes"] < 4000

def test_tinyagent_cycle():
    agent = TinyAgent()
    res = agent.step()
    assert "sense" in res["cycle"]

def test_guardrails_check():
    guard = TinyGuardrails()
    res = guard.check("motor_off")
    assert res["rom_based"] is True

def test_federated_trainer():
    trainer = FederatedTinyTrainer()
    res = trainer.aggregate([0.1, -0.1])
    assert res["epsilon"] == 2.0

def test_tflite_bridge_allocation():
    bridge = TFLiteMicroBridge()
    res = bridge.allocate()
    assert res["arena_size_kb"] == 8

def test_tinymodel_latency_target():
    model = TinyModel()
    res = model.infer([0])
    assert res["latency_ms"] < 0.1 # 0.09 target

def test_phi_c_engine_footprint():
    engine = LocalPhiCEngine()
    res = engine.get_phi_c()
    assert res["memory_bytes"] < 100 # << 100 bytes

def test_guardrails_allowed():
    guard = TinyGuardrails()
    assert guard.check("safe_action")["allowed"] is True

# --- Quantum Sync Tests (2) ---
def test_epr_sync_precision():
    engine = EPRClockSyncEngine()
    res = engine.sync()
    assert res["precision"] == "picosecond"

def test_hardware_controller_emission():
    controller = QuantumDotHardwareController()
    res = controller.emit()
    assert res["rate_mhz"] == 40
    assert res["wavelength_nm"] == 1550

# --- Quantum Async Tests (8) ---
def test_ldpc_correction():
    ldpc = PhotonAssistedLDPC()
    assert ldpc.correct("data") == "data"

def test_dithering_application():
    dithering = QuantumJitterDithering()
    assert dithering.apply("signal") == "signal"

def test_qos_router():
    router = PhiCQosRouter()
    res = router.route("packet")
    assert res["routed"] is True

def test_bell_validator():
    validator = QuantumCorrelationValidator()
    res = validator.validate_chsh()
    assert res["S"] > 2.0

def test_hybrid_signer():
    signer = HybridPQCQuantumSigner()
    res = signer.sign("data")
    assert res["fallback"] == "available"

def test_bell_validator_exact():
    validator = QuantumCorrelationValidator()
    res = validator.validate_chsh()
    assert res["S"] == 2.70

def test_hybrid_signer_signature():
    signer = HybridPQCQuantumSigner()
    res = signer.sign("data")
    assert "pqc" in res["signature"]

def test_qos_router_phi_c():
    router = PhiCQosRouter()
    res = router.route("packet")
    assert res["phi_c"] == 0.99

# --- Pipeline Integrado 191+192 Test (1) ---
def test_integrated_pipeline():
    model = TinyModel()
    signer = HybridPQCQuantumSigner()
    inf = model.infer([0])
    sig = signer.sign(str(inf))
    assert inf["latency_ms"] < 5.0
    assert sig["fallback"] == "available"
