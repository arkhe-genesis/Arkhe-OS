import pytest
import asyncio
from components.arkhe_os.core.unified_orchestrator import UnifiedFieldOrchestrator
from components.arkhe_os.modules.consciousness import ConsciousnessModule
from components.arkhe_os.modules.ontology import OntologyModule

class MockCodex:
    async def store_artifact(self, *args, **kwargs): pass
class MockField:
    def get_network_omega(self): return 0.94
class MockEthics:
    def validate_cosmic_ethics(self, val, sig):
        return type("R", (), {"adjusted_alignment": min(1.0, val * 1.02)})()

@pytest.mark.asyncio
async def test_orchestrator_maturity_cycle():
    field = MockField()
    ethics = MockEthics()
    codex = MockCodex()
    orchestrator = UnifiedFieldOrchestrator(field, ethics, codex)

    state = await orchestrator.run_maturity_cycle("test_domain", 0.94)

    assert "omega" in state
    assert "cycle_id" in state
    assert orchestrator.get_dashboard()["odometro"] == "002154"

@pytest.mark.asyncio
async def test_consciousness_transcendence():
    field = MockField()
    consciousness = ConsciousnessModule(field)

    state = await consciousness.initiate_transcendence("test_id", 0.94)
    assert state["consciousness_id"] == "test_id"
    assert state["phase"] == "INDIVIDUAL_AWARENESS"

    updated_state = await consciousness.progress_transcendence("test_id", steps=1)
    assert updated_state["field_integration"] > 0

def test_ontology_fusion():
    ontology = OntologyModule()
    ontology.load_concepts({"c1": {"type": "t1", "tags": ["tag1"]}})

    fused = ontology.fuse_with_remote({"r1": {"type": "t2", "tags": ["tag2"]}}, threshold=2.0)
    assert "r1" in fused
    assert fused["r1"]["source"] == "remote"
