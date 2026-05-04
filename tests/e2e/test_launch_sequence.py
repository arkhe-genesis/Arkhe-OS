import pytest
import asyncio
import time
from compiler.llm_compiler import LLMCompiler
from optimizer.ucb1_bandit import CoherenceTensor7D
from safety.coherence_monitor import CoherenceMonitor

# Mocks para o teste
class MockConsensus:
    def register_vertex(self, vertex):
        pass

class MockCoherenceStake7D:
    def __init__(self, name, array):
        pass

class MockRailSim:
    async def execute_launch(self, kernel, power_sim):
        await asyncio.sleep(0.1)

    async def get_launch_telemetry(self):
        return [{"mercy_gap": 0.05, "acceleration_g": 250.0}]

class MockPowerSim:
    async def get_recovered_energy(self):
        return 100

def create_launch_vc(data):
    return {"payload_hash": "abc"}

@pytest.mark.asyncio
async def test_full_launch_sequence():
    """Testa sequência completa de lançamento com monitoramento 7D."""

    llm_compiler = LLMCompiler()
    consensus = MockConsensus()
    rail_sim = MockRailSim()
    power_sim = MockPowerSim()

    # 1. Compilar cerimônia de lançamento
    kernel = llm_compiler.compile_ceremony(
        ceremony_name="launch_mass_driver",
        params={"payload_mass": 500.0, "target_velocity": 2380.0, "payload_id": "p1"},
        hardware_target="zynq_ultrascale_fpga"
    )
    assert kernel.contract_proof is not None

    # 2. Simular pré-lançamento com coerência 7D nominal
    good_coherence = CoherenceTensor7D(
        phase=0.072, latency_us=495.0, power_mw=145.0,
        mercy_gap=0.071, security=0.96, privacy=0.93, interpretability=0.89
    )
    consensus.register_vertex(MockCoherenceStake7D("lmd", [good_coherence]*10))

    # 3. Executar lançamento simulado
    start = time.time()
    await rail_sim.execute_launch(kernel, power_sim)
    duration = time.time() - start

    assert duration < 5.0, f"Lançamento levou {duration:.2f}s, esperado <5s"

    # 4. Verificar pós-lançamento
    recovered = await power_sim.get_recovered_energy()
    assert recovered > 0, "Nenhuma energia recuperada"

    telemetry = await rail_sim.get_launch_telemetry()
    for sample in telemetry:
        assert 0.04 <= sample["mercy_gap"] <= 0.10, "Mercy gap violada"
        assert sample["acceleration_g"] <= 300.0, "Limite de aceleração excedido"

    # 5. Verificar entrada no ledger ético
    launch_vc = create_launch_vc({})
    assert "payload_hash" in launch_vc

@pytest.mark.asyncio
async def test_emergency_abort_on_mercy_gap_violation():
    """Testa que violação de mercy gap dispara abort de emergência."""

    abort_triggered = False
    def mock_emergency_abort():
        nonlocal abort_triggered
        abort_triggered = True

    monitor = CoherenceMonitor(MockConsensus(), mock_emergency_abort)

    # Simular degradação de mercy gap durante lançamento
    async def mock_fetch_degraded():
        return CoherenceTensor7D(
            phase=0.07, latency_us=500.0, power_mw=150.0,
            mercy_gap=0.035,  # Abaixo do piso de 0.04!
            security=0.95, privacy=0.92, interpretability=0.88
        )

    monitor._fetch_current_coherence = mock_fetch_degraded
    await monitor.start()

    await asyncio.sleep(0.1)  # Permitir um ciclo de monitoramento

    monitor.stop()

    assert abort_triggered, "Abort de emergência não disparado para violação de mercy gap"

    alerts = monitor.get_recent_alerts()
    mercy_alerts = [a for a in alerts if a.dimension == "mercy_gap"]
    assert len(mercy_alerts) > 0
    assert mercy_alerts[0].severity == "emergency"
