import pytest
from substrato_6045_omni_interoperability_mesh import OmniInteroperabilityMesh, ComponentType

def test_mesh_initialization():
    mesh = OmniInteroperabilityMesh()
    assert len(mesh.adapters) > 0, "Adapters should be registered upon initialization"

def test_core_languages_registration():
    mesh = OmniInteroperabilityMesh()
    adapter = mesh.get_adapter("python")
    assert adapter is not None
    assert adapter.type == ComponentType.LANGUAGE
    assert adapter.arkhe_equivalent == "PYTHON_AST_QNC"

def test_frameworks_registration():
    mesh = OmniInteroperabilityMesh()
    adapter = mesh.get_adapter("FastAPI")
    assert adapter is not None
    assert adapter.type == ComponentType.BACKEND_FRAMEWORK
    assert "PHASE_COHERENT_API_GATEWAY" in adapter.arkhe_equivalent

def test_cloud_and_orchestration_registration():
    mesh = OmniInteroperabilityMesh()
    adapter = mesh.get_adapter("Kubernetes")
    assert adapter is not None
    assert adapter.type == ComponentType.CONTAINER_ORCHESTRATOR
    assert adapter.arkhe_equivalent == "DISTRIBUTED_CORE_NODES"

def test_blueprint_synthesis():
    mesh = OmniInteroperabilityMesh()
    blueprint = mesh.synthesize_integration_blueprint()
    assert blueprint["substrate"] == "6045"
    assert blueprint["total_adapters_registered"] == len(mesh.adapters)
    assert len(blueprint["adapters"]) > 0
    assert "binding_preview" in blueprint["adapters"][0]
