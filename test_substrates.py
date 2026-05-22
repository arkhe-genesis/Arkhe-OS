import pytest
import os
import sys

def test_validation():
    sys.path.append(os.path.abspath('substrates/300-399_foundations/substrato_301'))
    from validation.collective_sandbox import validate_collective_emergence
    import asyncio
    assert asyncio.run(validate_collective_emergence()) == True

def test_fips():
    sys.path.append(os.path.abspath('substrates/300-399_foundations/substrato_301'))
    from fips.collective_fips import certify_collective_modules
    assert certify_collective_modules() == True

def test_expansion():
    sys.path.append(os.path.abspath('substrates/300-399_foundations/substrato_301'))
    from expansion.multi_neuron_expansion import expand_neural_diversity
    import asyncio
    assert asyncio.run(expand_neural_diversity()) == True

if __name__ == '__main__':
    pytest.main(['-v', 'test_substrates.py'])

def test_substrato_562():
    import importlib.util
    import os
    import json
    import re

    # Load module dynamically
    file_path = os.path.abspath('substrates/500-599_advanced/substrato_562_stim_qec_simulator/substrato_562_stim_qec_simulator.py')
    spec = importlib.util.spec_from_file_location("substrato_562_stim_qec_simulator", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Assert f-strings are absent
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Simple regex to check for f-strings (excluding comments)
    lines = content.split('\n')
    for line in lines:
        if '#' in line:
            line = line[:line.find('#')]
        assert not re.search(r'\bf(["\'])', line), "f-string found in substrate_562"

    # Canonize
    canonizer = module.StimQecSimulatorCanonizer()
    path = canonizer.canonize()

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["substrate_id"] == "562-STIM-QEC-SIMULATOR"
    assert data["phi_c"] == 0.995556
    assert data["seal"] == "b1ad9ff79feed49d1bd2c7ace40477fdc8e8100a471099244a078c53cac9609a"
    assert "ETHICAL_ALIGNMENT" in data["invariants"]
    assert data["invariants"]["ETHICAL_ALIGNMENT"] == 1.0
