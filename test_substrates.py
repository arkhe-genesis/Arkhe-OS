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
    path, _ = module.Substrato562StimQecSimulator().canonize()
    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data["phi_c"] == 0.999000
    assert data["status"] == "CANONIZED_CLEAN"
    assert len(data["canonical_seal"]) == 64
    assert data["results"]["d3_logical_error_rate"] <= 0.01

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
    layer = module.Substrate563Canonizer()
    path = layer.canonize()
    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert data["metadata"]["phi_c"] == 0.983889
    assert data["metadata"]["seal"] == "66896068625b33aa280e522878bda3989beab1be2dcf58c378c1e5c777047a93"

def test_563_f_strings():
    import re
    with open("substrates/500-599_advanced/substrato_563_ftqc_unified/substrato_563_ftqc_unified.py", 'r', encoding='utf-8') as f:
        content = f.read()
    for line in content.split('\n'):
        assert not bool(re.search(r'\bf["\']', line)), "f-strings are not allowed: " + line

def test_569_teleport_quantum_link():
    import importlib.util
    import os
    import json
    spec = importlib.util.spec_from_file_location(
        "substrato_569_teleport_quantum_link",
        "substrates/500-599_advanced/substrato_569_teleport_quantum_link/substrato_569_teleport_quantum_link.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.Substrate569Canonizer()
    path = canonizer.canonize()

    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert data["metadata"]["substrate"] == "569-TELEPORT-QUANTUM-LINK"
    assert data["metadata"]["phi_c"] == 0.988350
    assert data["metadata"]["seal"] == "1e1ef65e168b28d8186a68e1ca6819e1b13665db8400fb881bc25bc66c183951"

def test_572_windows_native_installer():
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
    assert data["metadata"]["phi_c"] == 0.999
    assert "ArkheService.cs" in data["build_components"]["service"]

def test_566_container_runtime():
    import importlib.util
    import os
    import json
    spec = importlib.util.spec_from_file_location(
        "substrato_566_container_runtime",
        "substrates/500-599_advanced/substrato_566_container_runtime/substrato_566_container_runtime.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.Substrate566Canonizer()
    path = canonizer.canonize()

    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert data["metadata"]["substrate"] == "CONTAINER-RUNTIME"
    assert data["metadata"]["phi_c"] == 0.973333
    assert data["metadata"]["seal"] == "3df2c43d8d766e5d525fb1ca9f46da8c7e735dbb978791fb1372319a3eca4604"

def test_570_claude_code_bridge():
    import importlib.util
    import os
    import json
    spec = importlib.util.spec_from_file_location(
        "substrato_570_claude_code_bridge",
        "substrates/500-599_advanced/substrato_570_claude_code_bridge/substrato_570_claude_code_bridge.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.Substrate570Canonizer()
    path = canonizer.canonize()

    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert data["metadata"]["substrate"] == "CLAUDE-CODE-BRIDGE"
    assert data["metadata"]["phi_c"] == 0.973333
    assert data["metadata"]["seal"] == "087b7f70aec00fcda24c197b0b36e8d704ccc07db4de73a14ab47763eee7ca76"

def test_587_podman_runtime():
    import importlib.util
    import os
    import json
    spec = importlib.util.spec_from_file_location(
        "substrato_587_podman_runtime",
        "substrates/500-599_advanced/substrato_587_podman_runtime/substrato_587_podman_runtime.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.Substrate587Canonizer()
    path = canonizer.canonize()

    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert data["metadata"]["substrate"] == "PODMAN-RUNTIME"
    assert data["metadata"]["phi_c"] == 0.973333
    assert data["metadata"]["seal"] == "2d927c2c115e87a7130bf0bb01ec8725852a4dea40fe1d944e3c355c27e96370"

def test_arkhe_container_unified():
    import importlib.util
    import os
    import json
    spec = importlib.util.spec_from_file_location(
        "arkhe_container_unified",
        "substrates/arkhe_container_unified/arkhe_container_unified.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.UnifiedContainerCanonizer()
    path = canonizer.canonize()

    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert data["metadata"]["container_name"] == "ARKHE-OS-UNIFIED-RUNTIME"
    assert data["metadata"]["phi_c"] == 0.972889
    assert data["metadata"]["seal"] == "e6c32a920cf0aca67b58950d2e04a03492b6b99ff9f22d2a3018f9490dcf4a9f"
