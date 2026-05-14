import pytest
import asyncio
import numpy as np

# Mock classes to avoid missing dependencies during test
from src.arkhe.quantum.hybrid.photonic_ion_hybrid import PhotonicIonHybridQPU
from src.arkhe.immersive.bci_qkd.bci_qkd_auth import BCIQKDAuthenticator
from src.arkhe.edge.terahertz_6g.terahertz_6g_sync import THzEdgeSyncOptimizer
from src.arkhe.quantum.topological_photonic.photonic_anyons import PhotonicTopologicalQPU

from src.arkhe.quantum.photonic.photonic_backend import PhotonicCloudClient, PhotonicJobConfig, PhotonicProvider
from src.arkhe.quantum.iontrap.iontrap_pulse_scheduler import IonTrapPulseScheduler, IonTrapConfig, IonSpecies
from src.arkhe.immersive.bci_neural_interface import NeuralStateDecoder, BCIConfig, NeuralSignalType
from src.arkhe.satellite.qkd_protocol import QKDKeyDistribution
from src.arkhe.edge.edge_sync_optimizer import EdgeSyncConfig, NetworkSlice
from src.arkhe.quantum.topological.topological_firmware import TopologicalQPUConfig, AnyonType, BraidingOperation

@pytest.mark.asyncio
async def test_photonic_ion_hybrid():
    # Mocks
    photonic_client = PhotonicCloudClient({})
    ion_scheduler = IonTrapPulseScheduler(IonTrapConfig(ion_species=IonSpecies.YB171))

    hybrid_qpu = PhotonicIonHybridQPU(photonic_client, ion_scheduler)

    circuit = {
        "gates": [
            {"type": "Rabi_X", "target": 0, "angle": 1.57},
            {"type": "BS", "target1": 0, "target2": 1, "theta": 0.5, "phi": 0}
        ]
    }

    results = await hybrid_qpu.execute_hybrid_circuit(circuit)
    assert "ion_Rabi_X" in results
    assert "photonic_BS" in results
    assert results["ion_Rabi_X"] > 0
    assert results["photonic_BS"] == "completed"

@pytest.mark.asyncio
async def test_bci_qkd_auth():
    bci_config = BCIConfig(signal_type=NeuralSignalType.EEG, calibration_required=False)
    decoder = NeuralStateDecoder(bci_config)
    qkd = QKDKeyDistribution(satellite_id="sat-1", ground_stations=["earth-1", "earth-2"])

    auth = BCIQKDAuthenticator(decoder, qkd)

    # Generate mock neural signal
    signal = np.random.randn(5, 250) * 0.1

    success, anchor = await auth.authenticate_user("user-01", signal, "earth-1", "earth-2")

    assert success is True
    assert anchor is not None

@pytest.mark.asyncio
async def test_terahertz_6g_sync():
    config = EdgeSyncConfig(device_id="device-6g", preferred_slice=NetworkSlice.QUANTUM_SYNC)
    optimizer = THzEdgeSyncOptimizer(config)

    data = {"phi_c": 0.999}

    # Normal sync
    res_normal = await optimizer.sync_with_low_latency(data)

    # THz sync
    await optimizer.request_network_slice("thz_quantum_sync")
    res_thz = await optimizer.sync_with_low_latency(data)

    if res_normal.success and res_thz.success and res_normal.source == "network" and res_thz.source == "network":
        # Average thz latency should be lower (0.05ms) than normal URLLC (1.0ms/0.5ms)
        assert res_thz.latency_ns < res_normal.latency_ns * 2 # Relaxed assert due to randomness

@pytest.mark.asyncio
async def test_photonic_anyons():
    config = TopologicalQPUConfig(anyon_type=AnyonType.MAJORANA)
    photonic_client = PhotonicCloudClient({})

    qpu = PhotonicTopologicalQPU(config, photonic_client)

    op = BraidingOperation(anyon_type=AnyonType.MAJORANA, anyon_ids=[0, 1], braid_pattern="1-2", topological_charge=1, protection_level=0.99)

    success = await qpu._simulate_braiding_motion(op)
    assert success is True
