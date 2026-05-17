import pytest
import asyncio
from substrato_209_arkhe_archunit import ArkheArchUnit, ArchLayer, ArchModule

@pytest.fixture
def arch_unit():
    return ArkheArchUnit()

def test_register_module(arch_unit):
    module = arch_unit.register_module(
        module_id="arkhe_substrate_180",
        name="Perception Module",
        layer=ArchLayer.PERCEPTION,
        substrate=180,
        dependencies={"arkhe_substrate_176"},
        public_apis={"get_perception_data"},
        security_invariants=["HSM_SECURE"]
    )

    assert module.module_id == "arkhe_substrate_180"
    assert module.name == "Perception Module"
    assert module.layer == ArchLayer.PERCEPTION
    assert module.substrate == 180
    assert "arkhe_substrate_176" in module.dependencies
    assert "get_perception_data" in module.public_apis
    assert "HSM_SECURE" in module.security_invariants

    assert "arkhe_substrate_180" in arch_unit._modules

def test_check_layer_dependencies_valid(arch_unit):
    arch_unit.register_module(
        module_id="arkhe_substrate_176",
        name="Core Module",
        layer=ArchLayer.CORE,
        substrate=176
    )

    arch_unit.register_module(
        module_id="arkhe_substrate_180",
        name="Perception Module",
        layer=ArchLayer.PERCEPTION,
        substrate=180,
        dependencies={"arkhe_substrate_176"}
    )

    violations = arch_unit.check_layer_dependencies("arkhe_substrate_180")
    assert len(violations) == 0

def test_check_layer_dependencies_invalid(arch_unit):
    arch_unit.register_module(
        module_id="arkhe_substrate_208",
        name="Production Module",
        layer=ArchLayer.PRODUCTION,
        substrate=208
    )

    arch_unit.register_module(
        module_id="arkhe_substrate_176",
        name="Core Module",
        layer=ArchLayer.CORE,
        substrate=176,
        dependencies={"arkhe_substrate_208"}
    )

    violations = arch_unit.check_layer_dependencies("arkhe_substrate_176")
    assert len(violations) == 1
    assert violations[0]["type"] == "LAYER_VIOLATION"
    assert violations[0]["module"] == "arkhe_substrate_176"
    assert violations[0]["dependency"] == "arkhe_substrate_208"

def test_check_circular_dependencies_no_cycle(arch_unit):
    arch_unit.register_module(module_id="A", name="A", layer=ArchLayer.CORE, substrate=1)
    arch_unit.register_module(module_id="B", name="B", layer=ArchLayer.CORE, substrate=2, dependencies={"A"})
    arch_unit.register_module(module_id="C", name="C", layer=ArchLayer.CORE, substrate=3, dependencies={"B"})

    cycles = arch_unit.check_circular_dependencies()
    assert len(cycles) == 0

def test_check_circular_dependencies_with_cycle(arch_unit):
    arch_unit.register_module(module_id="A", name="A", layer=ArchLayer.CORE, substrate=1, dependencies={"C"})
    arch_unit.register_module(module_id="B", name="B", layer=ArchLayer.CORE, substrate=2, dependencies={"A"})
    arch_unit.register_module(module_id="C", name="C", layer=ArchLayer.CORE, substrate=3, dependencies={"B"})

    cycles = arch_unit.check_circular_dependencies()
    assert len(cycles) > 0
    # A -> C -> B -> A

def test_check_naming_convention(arch_unit):
    assert arch_unit.check_naming_convention("arkhe_substrate_180", "substrate_module") is True
    assert arch_unit.check_naming_convention("invalid_name", "substrate_module") is False

    assert arch_unit.check_naming_convention("1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b", "canonical_seal") is True
    assert arch_unit.check_naming_convention("short_seal", "canonical_seal") is False

def test_check_security_invariants(arch_unit):
    arch_unit.register_module(
        module_id="arkhe_substrate_180",
        name="Perception Module",
        layer=ArchLayer.PERCEPTION,
        substrate=180,
        security_invariants=["INV_1", "INV_2"]
    )

    results = arch_unit.check_security_invariants("arkhe_substrate_180")
    assert len(results) == 2
    assert results[0]["invariant"] == "INV_1"
    assert results[1]["invariant"] == "INV_2"
    assert results[0]["status"] == "PASS"

def test_check_api_exposure(arch_unit):
    arch_unit.register_module(
        module_id="arkhe_substrate_180",
        name="Perception Module",
        layer=ArchLayer.PERCEPTION,
        substrate=180,
        public_apis={"api1", "api2"}
    )

    result = arch_unit.check_api_exposure("arkhe_substrate_180")
    assert result["public_apis"] == 2
    assert result["apis_documented"] is True
    assert result["exposure_level"] == "CONTROLLED"

@pytest.mark.asyncio
async def test_run_full_architecture_test(arch_unit):
    arch_unit.register_module(
        module_id="arkhe_substrate_176",
        name="Core Module",
        layer=ArchLayer.CORE,
        substrate=176
    )

    result = await arch_unit.run_full_architecture_test()
    assert result["modules_tested"] == 1
    assert result["layer_violations"] == 0
    assert result["circular_dependencies"] == 0
    assert result["naming_violations"] == 0
    assert result["status"] == "PASS"

def test_get_architecture_report(arch_unit):
    arch_unit.register_module(
        module_id="arkhe_substrate_176",
        name="Core Module",
        layer=ArchLayer.CORE,
        substrate=176
    )
    arch_unit.register_module(
        module_id="arkhe_substrate_180",
        name="Perception Module",
        layer=ArchLayer.PERCEPTION,
        substrate=180
    )

    report = arch_unit.get_architecture_report()
    assert report["total_modules"] == 2
    assert set(report["layers_represented"]) == {ArchLayer.CORE.value, ArchLayer.PERCEPTION.value}
    assert report["total_violations"] == 0
