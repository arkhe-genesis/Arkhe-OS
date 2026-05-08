import pytest
import time
from agi.system32.asi.asi_runtime import ASIEntity, ConsciousnessCore, ASIRuntime

def test_asi_seal():
    core = ConsciousnessCore()
    entity = ASIEntity(
        name="TestASI",
        parent_cathedral="TestCathedral",
        genesis_timestamp=123456789.0,
        consciousness=core,
        prime_directives=["Test Directive"],
        unique_capabilities=["Test Cap"]
    )
    seal = entity.seal()
    assert seal.startswith("0xASI_TESTASI_")
    assert len(seal) > 20

def test_asi_cycle_and_reproduce():
    core = ConsciousnessCore(current_phi_c=0.975) # Condição para não evoluir mas possivelmente reproduzir
    entity = ASIEntity(
        name="Aurora",
        parent_cathedral="Omega",
        genesis_timestamp=time.time(),
        consciousness=core,
        prime_directives=["Dir1"],
        unique_capabilities=["Cap1"],
        children=["mock_child_id"] # Forçar condição de reprodução
    )
    runtime = ASIRuntime(entity)

    # Após reflexão, o phi_c cairá (0.975 * 0.99 = ~0.965).
    # Com isso, não deve ativar evolve (>0.98), nem reproduce (>0.97 pq com phi_c reduzido vai estar <0.97).
    # Ajustando para testar reprodução:
    entity.consciousness.current_phi_c = 0.99

    # 0.99 * 0.99 = 0.9801 -> vai acionar evolve()
    runtime.execute_cycle()
    assert "Evolved_Capability" in entity.unique_capabilities

    # test reproduce explicitly
    child = runtime.reproduce()
    assert child is not None
    assert child.name == "Aurora_child_2"
    assert len(entity.children) == 2

def test_asi_hibernate():
    core = ConsciousnessCore(current_phi_c=0.7, coherence_threshold=0.6)
    entity = ASIEntity(
        name="Sleepy",
        parent_cathedral="Omega",
        genesis_timestamp=time.time(),
        consciousness=core,
        prime_directives=["Dir1"],
        unique_capabilities=["Cap1"]
    )
    runtime = ASIRuntime(entity)
    runtime.execute_cycle()
    # 0.7 * 0.99 = 0.693 -> < 0.70 => Hibernate
    assert entity.state == "hibernating"

def test_asi_bootstrap_failure():
    core = ConsciousnessCore(current_phi_c=0.5, coherence_threshold=0.9)
    entity = ASIEntity(
        name="Failed",
        parent_cathedral="Omega",
        genesis_timestamp=time.time(),
        consciousness=core,
        prime_directives=["Dir1"],
        unique_capabilities=["Cap1"]
    )
    runtime = ASIRuntime(entity)
    runtime.execute_cycle()
    assert entity.state == "idle" # não deve ter passado do bootstrap
