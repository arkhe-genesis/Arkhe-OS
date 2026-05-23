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

def test_563_ftqc_unified():
    import importlib.util
    file_path = os.path.abspath('substrates/500-599_advanced/substrato_563_ftqc_unified/substrato_563_ftqc_unified.py')
    spec = importlib.util.spec_from_file_location("substrato_563_ftqc_unified", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.Substrate563Canonizer()
    path = canonizer.canonize()

    assert os.path.exists(path)
    import json
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data["metadata"]["substrate"] == "563-FTQC-UNIFIED"
    assert data["metadata"]["phi_c"] == 0.983889
    assert data["metadata"]["seal"] == "66896068625b33aa280e522878bda3989beab1be2dcf58c378c1e5c777047a93"

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
    substrate = module.Substrato562StimQecSimulator()
    path, seal = substrate.canonize()
    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data["phi_c"] == 0.999000
    assert data["status"] == "CANONIZED_CLEAN"

    assert data.get("d3_logical_error", data.get("results", {}).get("d3_logical_error_rate", 1.0)) <= 0.01

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
    canonizer = module.Substrate563Canonizer()
    path = canonizer.canonize()
    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data.get("phi_c", data.get("metadata", {}).get("phi_c")) == 0.983889
    assert data.get("seal", data.get("metadata", {}).get("seal")) == "66896068625b33aa280e522878bda3989beab1be2dcf58c378c1e5c777047a93"

def test_563_f_strings():
    import re
    with open("substrates/500-599_advanced/substrato_563_ftqc_unified/substrato_563_ftqc_unified.py", 'r', encoding='utf-8') as f:
        content = f.read()
    for line in content.split('\n'):
        assert not bool(re.search(r'\bf["\']', line)), "f-strings are not allowed: " + line

def test_windows_port_canonization():
    import importlib.util
    import os
    import json
    spec = importlib.util.spec_from_file_location(
        "substrato_windows_port",
        "substrates/500-599_advanced/substrato_windows_port/substrato_windows_port.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    canonizer = module.WindowsPortCanonizer()
    path = canonizer.canonize()
    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data["phi_c"] == 0.990278
    assert data["seal_sha3_256"] == "d72b4f1b5c01abe643d67ddc0ed1618d6d22ff397ac876bbe6374236d7fbce7d"

def test_windows_port_f_strings():
    import re
    files_to_check = [
        "substrates/500-599_advanced/substrato_windows_port/substrato_windows_port.py",
        "substrates/500-599_advanced/substrato_windows_port/Dockerfile.windows",
        "substrates/500-599_advanced/substrato_windows_port/verify_constitution_windows.py",
        "substrates/500-599_advanced/substrato_windows_port/ArkheBridgeService.py",
        "substrates/500-599_advanced/substrato_windows_port/Install-ArkheWindows.ps1"
    ]
    for filepath in files_to_check:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        for line in content.split('\n'):
            assert not bool(re.search(r'\bf["\']', line)), "f-strings are not allowed: " + line

def test_substrate_572_windows_native_installer():
    import importlib.util
    import os
    import json
    spec = importlib.util.spec_from_file_location(
        "substrato_572_windows_native_installer",
        "substrates/500-599_advanced/substrato_572_windows_native_installer/substrato_572_windows_native_installer.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    canonizer = module.Substrate572Canonizer()
    path = canonizer.canonize()
    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data["metadata"]["substrate"] == "572-WINDOWS-NATIVE-INSTALLER"
    assert data["metadata"]["phi_c"] == 0.999000
    assert data["metadata"]["seal"] == "9cb4c28b6c412382fb6a9c8a83d16f479e697670802745cf501a985955e0c980"

def test_572_f_strings():
    import re
    with open("substrates/500-599_advanced/substrato_572_windows_native_installer/substrato_572_windows_native_installer.py", 'r', encoding='utf-8') as f:
        content = f.read()
    for line in content.split('\n'):
        assert not bool(re.search(r'\bf["\']', line)), "f-strings are not allowed: " + line
