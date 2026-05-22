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

def test_562_stim_qec_simulator():
    import importlib.util
    import os
    import json
    spec = importlib.util.spec_from_file_location(
        "substrato_562_stim_qec_simulator",
        "substrates/500-599_advanced/substrato_562_stim_qec_simulator/substrato_562_stim_qec_simulator.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    path = module.canonize()
    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data["phi_c"] == 0.999000
    assert data["status"] == "CANONIZED_CLEAN"
    assert data["seal"] == "3f9d1756b8d02fb88b18d455d8e9acaa8486e2ac368f9a4c682ac6e5fbbfc9f7"
    assert data["d3_logical_error"] <= 0.01

def test_562_f_strings():
    import re
    with open("substrates/500-599_advanced/substrato_562_stim_qec_simulator/substrato_562_stim_qec_simulator.py", 'r', encoding='utf-8') as f:
        content = f.read()
    for line in content.split('\n'):
        assert not bool(re.search(r'\bf["\']', line)), "f-strings are not allowed: " + line

def test_563_ftqc_unified():
    import importlib.util
    import os
    import json
    spec = importlib.util.spec_from_file_location(
        "substrato_563_ftqc_unified",
        "substrates/500-599_advanced/substrato_563_ftqc_unified/substrato_563_ftqc_unified.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    layer = module.FTQCUnifiedLayer()
    path = layer.canonize()
    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data["phi_c"] == 0.983889
    assert data["seal"] == "66896068625b33aa280e522878bda3989beab1be2dcf58c378c1e5c777047a93"

def test_563_f_strings():
    import re
    with open("substrates/500-599_advanced/substrato_563_ftqc_unified/substrato_563_ftqc_unified.py", 'r', encoding='utf-8') as f:
        content = f.read()
    for line in content.split('\n'):
        assert not bool(re.search(r'\bf["\']', line)), "f-strings are not allowed: " + line
