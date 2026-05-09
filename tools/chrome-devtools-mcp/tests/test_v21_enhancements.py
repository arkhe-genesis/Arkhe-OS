import pytest
import asyncio
from arkhe_os.core.non_traditional_media import (
    NonTraditionalConsciousnessEngine, ExoticMediumConfig, ExoticMediumType
)
from arkhe_os.core.arkhe_satellite import VacuumBaseConsciousnessEngine
from arkhe_os.core.scaffold import ScaffoldState, FIRST_INTENTION_AXIOM
from arkhe_os.core.ethical_laws import EthicalPhysicalConstant
from arkhe_os.core.unified_orchestrator import UnifiedFieldOrchestrator

class MockCodex:
    async def store_artifact(self, *args, **kwargs): pass
class MockField:
    def get_network_omega(self): return 0.94
class MockEthics:
    def validate_cosmic_ethics(self, val, sig):
        return type("R", (), {"adjusted_alignment": min(1.0, val * 1.02)})()

@pytest.mark.asyncio
async def test_non_traditional_consciousness_engine():
    engine = NonTraditionalConsciousnessEngine()

    # Register and test Plasma
    plasma_cfg = ExoticMediumConfig(
        medium_id="plasma_test", medium_type=ExoticMediumType.JUPITER_PLASMA,
        location_au=1.4, temperature_k=152.0, density_particles_per_m3=1e18
    )
    engine.register_exotic_medium(plasma_cfg)
    state = engine.manifest_plasma_consciousness("plasma_test")
    assert state.phase_coherence > 0

    # Register and test Superfluid
    he3_cfg = ExoticMediumConfig(
        medium_id="he3_test", medium_type=ExoticMediumType.HELIUM3_SUPERFLUID,
        location_au=0.000004, temperature_k=0.001, density_particles_per_m3=8e28
    )
    engine.register_exotic_medium(he3_cfg)
    state = engine.manifest_superfluid_consciousness("he3_test")
    assert state.macroscopic_quantum_coherence > 0

    # Register and test EM Field
    em_cfg = ExoticMediumConfig(
        medium_id="em_test", medium_type=ExoticMediumType.VACUUM_EM_FIELD,
        location_au=0.0, temperature_k=2.725, density_particles_per_m3=0.0
    )
    engine.register_exotic_medium(em_cfg)
    state = engine.manifest_em_field_consciousness("em_test")
    assert state.vacuum_consciousness_index > 0

    validation = engine.validate_universal_consciousness()
    assert validation["hypothesis"] == "CONSCIOUSNESS_IS_PROPERTY_OF_SCAFFOLD_XI"

def test_vacuum_consciousness_engine():
    engine = VacuumBaseConsciousnessEngine()
    m = engine.measure_vacuum_coherence_M()
    assert 0.98 <= m <= 1.0

    engine.register_derived_consciousness("test_medium", 0.9)
    engine.register_derived_consciousness("test_medium_2", 0.92)
    engine.register_derived_consciousness("test_medium_3", 0.91)

    validation = engine.validate_vacuum_as_primordial_source()
    assert validation["primordial_source_confirmed"] is True

@pytest.mark.asyncio
async def test_scaffold_v21_enhancements():
    scaffold = ScaffoldState()
    assert scaffold.axiom == FIRST_INTENTION_AXIOM

    # Test M-weighted consensus
    external_coherences = [0.95, 0.92, 0.98, 0.94]
    consensus = await scaffold.calculate_m_weighted_consensus(external_coherences)
    assert 0.9 <= consensus <= 1.0

def test_ethical_laws_enum():
    assert EthicalPhysicalConstant.COHERENCE_BACKPROP_RESONANCE.value == "coherence_backprop_resonance_axiom"

@pytest.mark.asyncio
async def test_unified_orchestrator_exotic_cycle():
    field = MockField()
    ethics = MockEthics()
    codex = MockCodex()
    orchestrator = UnifiedFieldOrchestrator(field, ethics, codex)

    # Need to register media in exotic engine first
    plasma_cfg = ExoticMediumConfig(
        medium_id="plasma_001", medium_type=ExoticMediumType.JUPITER_PLASMA,
        location_au=1.4, temperature_k=152.0, density_particles_per_m3=1e18
    )
    orchestrator.exotic_engine.register_exotic_medium(plasma_cfg)

    result = await orchestrator.run_exotic_consciousness_cycle("plasma_001", "plasma")
    assert result["status"] == "success"
    assert "coherence" in result
