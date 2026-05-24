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
    with open(path, 'r', encoding='utf-8') as f:
        import json
        data = json.load(f)
    assert data["metadata"]["substrate"] == "563-FTQC-UNIFIED"
    assert data["metadata"]["phi_c"] == 0.983889
    assert data["metadata"]["seal"] == "66896068625b33aa280e522878bda3989beab1be2dcf58c378c1e5c777047a93"


def test_611_codegraph():
    import importlib.util
    import os
    import json
    spec = importlib.util.spec_from_file_location(
        "substrato_611_codegraph",
        "substrates/611-CODEGRAPH/substrato_611_codegraph.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    path = module.canonize_611()
    assert os.path.exists(path)

    with open(path, "r") as f:
        data = json.load(f)

    assert data["substrate"] == "611-CODEGRAPH"
    assert "CodeGraph" in data["description"]
    assert "seal_computed" in data

def test_611_f_strings():
    import os
    file_path = "substrates/611-CODEGRAPH/substrato_611_codegraph.py"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Simple check for f-strings
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if " f'" in line or ' f"' in line or line.startswith("f'") or line.startswith('f"'):
            assert False, "f-string found in line {}: {}".format(i+1, line.strip())


def test_614_shieldnet():
    import importlib.util
    import os
    import json
    spec = importlib.util.spec_from_file_location(
        "substrato_614_shieldnet",
        "substrates/614-SHIELDNET/substrato_614_shieldnet.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    report_path = module.canonize_614()
    assert report_path is not None
    assert os.path.exists(report_path)
    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["substrate"] == "614-SHIELDNET"

    with open("substrates/614-SHIELDNET/substrato_614_shieldnet.py", "r", encoding="utf-8") as f:
        content = f.read()
    assert "f'" not in content and 'f"' not in content, "f-strings are strictly forbidden"

if __name__ == '__main__':
    pytest.main()
