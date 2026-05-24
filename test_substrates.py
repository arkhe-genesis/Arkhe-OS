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


def test_619_octra():
    import importlib.util
    import os
    import json
    spec = importlib.util.spec_from_file_location(
        "substrato_619_octra",
        "substrates/619-OCTRA/substrato_619_octra.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    path = module.canonize_619()
    assert os.path.exists(path)

    json_path = os.path.join(path, "FICHA_CANONICA_619.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["id"] == "619-OCTRA"
    assert "seal_sha3_256" in data
    assert len(data["seal_sha3_256"]) == 64

    plugin_path = os.path.join(path, "arkhe_os", "plugins", "octra", "arkhe_octra.py")
    assert os.path.exists(plugin_path)

def test_619_f_strings():
    import os
    file_path = "substrates/619-OCTRA/substrato_619_octra.py"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.split('\n')
    for i, line in enumerate(lines):
        if " f'" in line or ' f"' in line or line.startswith("f'") or line.startswith('f"'):
            assert False, "f-string found in line {}: {}".format(i+1, line.strip())


def test_621_erdos_unit_distance():
    import importlib.util
    import json
    import os

    file_path = os.path.abspath('substrates/621-ERDOS-UNIT-DISTANCE/substrato_621_erdos.py')
    spec = importlib.util.spec_from_file_location("substrato_621_erdos", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.Substrato621ErdosUnitDistance()
    path = canonizer.generate_json()

    assert os.path.exists(path)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["id"] == "621-ERDOS-UNIT-DISTANCE"

def test_621_f_strings():
    import os
    import re
    file_path = os.path.abspath('substrates/621-ERDOS-UNIT-DISTANCE/substrato_621_erdos.py')
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert not bool(re.search(r'\bf["\']', content)), "f-strings are strictly forbidden in python files"


def test_627_tse_fcc_parser():
    import sys, os
    sys.path.append(os.path.abspath('substrates/627-TSE-FCC-PARSER'))
    import substrato_627_tse_fcc_parser
    canonizer = substrato_627_tse_fcc_parser.Substrato627TseFccParser()
    report_path = canonizer.canonize()
    assert os.path.exists(report_path)

def test_627_f_strings():
    import sys, os
    sys.path.append(os.path.abspath('substrates/627-TSE-FCC-PARSER'))
    import substrato_627_tse_fcc_parser
    with open(substrato_627_tse_fcc_parser.__file__, "r", encoding="utf-8") as f:
        content = f.read()
    import re
    assert not re.search(r'\bf(["\'])', content), "Found f-string in substrato_627_tse_fcc_parser.py"

def test_628_fec_parser():
    import sys, os
    sys.path.append(os.path.abspath('substrates/628-FEC-PARSER'))
    import substrato_628_fec_parser
    canonizer = substrato_628_fec_parser.Substrato628FecParser()
    report_path = canonizer.canonize()
    assert os.path.exists(report_path)

def test_628_f_strings():
    import sys, os
    sys.path.append(os.path.abspath('substrates/628-FEC-PARSER'))
    import substrato_628_fec_parser
    with open(substrato_628_fec_parser.__file__, "r", encoding="utf-8") as f:
        content = f.read()
    import re
    assert not re.search(r'\bf(["\'])', content), "Found f-string in substrato_628_fec_parser.py"

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
        import json
        data = json.load(f)
    assert data.get("metadata", data).get("phi_c", data.get("phi_c")) == 0.999000
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
        import json
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
        import json
        data = json.load(f)

    assert data["metadata"]["substrate"] == "569-TELEPORT-QUANTUM-LINK"
    assert data["metadata"]["phi_c"] == 0.988350
    assert data["metadata"]["seal"] == "1e1ef65e168b28d8186a68e1ca6819e1b13665db8400fb881bc25bc66c183951"

def test_585_groth16_zksecurity():
    import importlib.util
    import os
    spec = importlib.util.spec_from_file_location(
        "substrato_585_groth16_zksecurity",
        "substrates/500-599_advanced/substrato_585_groth16_zksecurity/substrato_585_groth16_zksecurity.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.Substrate585Canonizer()
    res = canonizer.canonize()

    assert os.path.exists(res["temp_dir"])
    assert os.path.exists(res["manifest_path"])
    assert len(res["seal"]) == 64


def test_arkhe_unified():
    import importlib.util
    import os
    import json
    spec = importlib.util.spec_from_file_location(
        "substrato_arkhe_unified",
        "substrates/500-599_advanced/substrato_arkhe_unified/substrato_arkhe_unified.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.SubstrateArkheUnifiedCanonizer()
    path = canonizer.canonize()

    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        import json
        data = json.load(f)

    assert data["metadata"]["substrate"] == "ARKHE-UNIFIED"
    assert data["metadata"]["phi_c"] == 0.972889
    assert data["metadata"]["seal"] == "e6c32a920cf0aca67b58950d2e04a03492b6b99ff9f22d2a3018f9490dcf4a9f"
    assert data["metadata"]["dcs"] == 0.978555
    assert data["metadata"]["architect"] == "ORCID:0009-0005-2697-4668"

def test_arkhe_unified_f_strings():
    import re
    with open("substrates/500-599_advanced/substrato_arkhe_unified/substrato_arkhe_unified.py", 'r', encoding='utf-8') as f:
        content = f.read()
    for line in content.split('\n'):
        assert not bool(re.search(r'(?<![A-Za-z0-9_])f["\']', line)), "f-strings are not allowed: " + line

def test_595_iris_alpha():
    import importlib.util
    import os
    import json
    spec = importlib.util.spec_from_file_location(
        "substrato_595_iris_alpha",
        "substrates/500-599_advanced/substrato_595_iris_alpha/substrato_595_iris_alpha.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.Substrate595IrisAlpha()
    path = canonizer.canonize()

    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        import json
        data = json.load(f)

    assert data["metadata"]["id"] == "595-IRIS-ALPHA"
    assert data["metadata"]["phi_c"] == 0.95
    assert data["metadata"]["canonical_seal"] == "e7000398d9804be9a3ebe1f16b900d99e81abc6c22423687a85adfab42683073"

def test_595_f_strings():
    import re
    with open("substrates/500-599_advanced/substrato_595_iris_alpha/substrato_595_iris_alpha.py", 'r', encoding='utf-8') as f:
        content = f.read()
    for line in content.split('\n'):
        assert not bool(re.search(r'(?<![A-Za-z0-9_])f["\']', line)), "f-strings are not allowed: " + line

def test_597_biollm():
    import importlib.util
    import os
    import json
    spec = importlib.util.spec_from_file_location(
        "substrato_597_biollm",
        "substrates/500-599_advanced/substrato_597_biollm/substrato_597_biollm.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.Substrate597BioLLM()
    path = canonizer.canonize()

    assert os.path.exists(path)
    with open(path, 'r', encoding='utf-8') as f:
        import json
        data = json.load(f)

    assert data["metadata"]["id"] == "597-BIOLLM"
    assert data["metadata"]["phi_c"] == 0.891667
    assert len(data["metadata"]["seal"]) == 64

def test_597_f_strings():
    import re
    with open("substrates/500-599_advanced/substrato_597_biollm/substrato_597_biollm.py", 'r', encoding='utf-8') as f:
        content = f.read()
    for line in content.split('\n'):
        assert not bool(re.search(r'(?<![A-Za-z0-9_])f["\']', line)), "f-strings are not allowed: " + line


def test_603_hashtree_cc():
    import importlib.util
    import json
    import os

    file_path = os.path.abspath('substrates/603-HASHTREE-CC/substrato_603_hashtree_cc.py')
    spec = importlib.util.spec_from_file_location("substrato_603_hashtree_cc", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.Substrato603HashtreeCC()
    path = canonizer.generate_json()

    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["id"] == "603-HASHTREE-CC"
    assert "canonical_seal" in data
    assert len(data["canonical_seal"]) == 64

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "f'" not in content and 'f"' not in content, "f-strings are strictly forbidden"

def test_615_photonic_6g():
    import importlib.util
    import json
    import os

    file_path = os.path.abspath('substrates/600-699_advanced/substrato_615_photonic_6g/substrato_615_photonic_6g.py')
    spec = importlib.util.spec_from_file_location("substrato_615_photonic_6g", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.Substrate615Canonizer()
    report_path = canonizer.canonize()

    assert os.path.exists(report_path)

    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["id"] == "615-PHOTONIC-6G"
    assert "seal" in data
    assert len(data["seal"]) == 64
    assert len(data["artifacts"]) == 5
    assert data["status"] == "CANONIZED"

    # Check that f-strings are strictly forbidden in the source
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "f'" not in content and 'f"' not in content, "f-strings are strictly forbidden"

def test_604_cybersecurity_ai():
    import importlib.util
    import json
    import os

    file_path = os.path.abspath('substrates/604-CYBERSECURITY-AI/substrato_604_cybersecurity_ai.py')
    spec = importlib.util.spec_from_file_location("substrato_604_cybersecurity_ai", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.Substrato604CybersecurityAI()
    path = canonizer.generate_json()

    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["id"] == "604-CYBERSECURITY-AI"
    assert "canonical_seal" in data
    assert len(data["canonical_seal"]) == 64

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "f'" not in content and 'f"' not in content, "f-strings are strictly forbidden"

def test_612_llm_foundations():
    import importlib.util
    import json
    import os

    file_path = os.path.abspath('substrates/612-LLM-FOUNDATIONS/substrato_612_llm_foundations.py')
    spec = importlib.util.spec_from_file_location("substrato_612_llm_foundations", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.Substrato612LlmFoundations()
    path = canonizer.generate_json()

    assert os.path.exists(path)

    json_path = os.path.join(path, "FICHA_CANONICA_612.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["id"] == "612-LLM-FOUNDATIONS"
    assert "seal_sha256" in data
    assert len(data["seal_sha256"]) == 64

def test_612_f_strings():
    import os
    file_path = os.path.abspath('substrates/612-LLM-FOUNDATIONS/substrato_612_llm_foundations.py')
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "f'" not in content and 'f"' not in content, "f-strings are strictly forbidden"

def test_620_monastic_sandboxing():
    import importlib.util
    import json
    import os

    file_path = os.path.abspath('substrates/620-MONASTIC-SANDBOXING/substrato_620_monastic_sandboxing.py')
    spec = importlib.util.spec_from_file_location("substrato_620_monastic_sandboxing", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.Substrato620MonasticSandboxing()
    path = canonizer.generate_json()

    assert os.path.exists(path)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["id"] == "620-MONASTIC-SANDBOXING"
    assert "canonical_seal" in data
    assert len(data["canonical_seal"]) == 64

def test_620_f_strings():
    import os
    import re
    file_path = os.path.abspath('substrates/620-MONASTIC-SANDBOXING/substrato_620_monastic_sandboxing.py')
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert not bool(re.search(r'\bf["\']', content)), "f-strings are strictly forbidden in python files"

    plugin_path = os.path.abspath('arkhe-os-cli/arkhe_os/plugins/arkhe_monastic.py')
    with open(plugin_path, "r", encoding="utf-8") as f:
        plugin_content = f.read()
    assert "f'" not in plugin_content and 'f"' not in plugin_content, "f-strings are strictly forbidden in plugin files"

def test_623_iobnt_survey():
    import importlib.util
    import os
    import json
    spec = importlib.util.spec_from_file_location(
        "substrato_623_iobnt_survey",
        "substrates/623-IOBNT-SURVEY/substrato_623_iobnt_survey.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.Substrato623IOBNTSurvey()
    path = canonizer.generate_json()
    assert os.path.exists(path)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["id"] == "623-IOBNT-SURVEY"
    assert "canonical_seal" in data

def test_623_f_strings():
    import os
    import re
    file_path = "substrates/623-IOBNT-SURVEY/substrato_623_iobnt_survey.py"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert not re.search(r'\bf(["\'])', content), "f-strings are strictly forbidden in python files"

    plugin_path = "arkhe-os-cli/arkhe_os/plugins/arkhe_iobnt.py"
    with open(plugin_path, "r", encoding="utf-8") as f:
        plugin_content = f.read()

    assert not re.search(r'\bf(["\'])', plugin_content), "f-strings are strictly forbidden in python files"

def test_substrato_xalgorix():
    import importlib.util
    import json
    import os
    import re

    file_path = os.path.abspath('substrates/400-499_advanced/substrato_xalgord_xalgorix/substrato_xalgord_xalgorix.py')
    spec = importlib.util.spec_from_file_location("substrato_xalgord_xalgorix", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    canonizer = module.SubstratoXalgorix()
    path = canonizer.canonize()

    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["Title"] == "Xalgorix - The Most Powerful Open-Source AI Pentesting Agent"
    assert "Description" in data
    assert "Features" in data
    assert "Architecture" in data

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert not re.search(r'\bf(["\'])', content), "f-strings are strictly forbidden in python files"

if __name__ == '__main__':
    pytest.main(['-v', 'test_substrates.py'])
