import re

def test_617_f_strings():
    file_path = "substrates/617-QUANTUM-TELEPORT/substrato_617_quantum_teleport.py"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    assert not re.search(r'\bf(["\'])', content), "f-strings found!"

def test_719_f_strings():
    import ast
    with open('substrates/s/719_glosa_240_metacognition/substrato_719_glosa_240_metacognition.py', 'r') as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        assert not isinstance(node, ast.JoinedStr)

def test_825_f_strings():
    import ast
    with open('substrates/t/825_parametric_memory_engine/substrato_825_parametric_memory_engine.py', 'r') as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        assert not isinstance(node, ast.JoinedStr)

def test_841_f_strings():
    import ast
    with open('substrates/t/841_web3_ontology_bridge/substrato_841_web3_ontology_bridge.py', 'r') as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        assert not isinstance(node, ast.JoinedStr)

def test_870_f_strings():
    import ast
    with open('substrates/t/870_blockchain_z_glm/substrato_870_blockchain_z_glm.py', 'r') as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        assert not isinstance(node, ast.JoinedStr)

def test_870_g_f_strings():
    import glob
    for filepath in glob.glob("substrates/t/870_g_arkhe_http_gateway/*.py"):
        with open(filepath, 'r') as f:
            content = f.read()
            assert "f\"" not in content, f"f-strings are strictly prohibited in the codebase. Found in {filepath}"

def test_pvac_f_strings_898_899_900():
    import os
    files_to_check = [
        "substrates/t/898_kolmogorov_weight/substrato_898.py",
        "substrates/t/899_lightclock_harmony/substrato_899.py",
        "substrates/t/900_peptide_saas/substrato_900.py",
    ]
    for file in files_to_check:
        with open(file, 'r') as f:
            content = f.read()
            assert 'f"' not in content, f"Found f-string in {file}"
            assert "f'" not in content, f"Found f-string in {file}"

def test_pvac_f_strings_905_909():
    import os
    files_to_check = [
        "substrates/t/905_crops_local_ai_stack/substrato_905_crops_local_ai_stack.py",
        "substrates/t/906_lucebox_inference_engine/substrato_906_lucebox_inference_engine.py",
        "substrates/t/907_voxterm_audio_privacy/substrato_907_voxterm_audio_privacy.py",
        "substrates/t/908_leanstral_fv_bridge/substrato_908_leanstral_fv_bridge.py",
        "substrates/t/909_zk_remote_llm/substrato_909_zk_remote_llm.py",
    ]
    for file in files_to_check:
        with open(file, 'r') as f:
            content = f.read()
            assert 'f"' not in content, f"Found f-string in {file}"
def test_substrate_918_f_strings():
    with open("substrates/t/918_qemu_orchestration/substrate_918_qemu_orchestration.py", "r") as f:
        content = f.read()
    assert 'f"' not in content and "f'" not in content, "F-strings are strictly forbidden in Python canonizers."
def test_substrate_919_f_strings():
    with open("substrates/t/919_omni_substrate/substrato_919_omni_substrate.py", "r") as f:
        content = f.read()
    assert 'f"' not in content and "f'" not in content, "F-strings are strictly forbidden in Python canonizers."
def test_substrate_926_f_strings():
    with open("substrates/t/926_chrome_devtools_mcp_bridge/substrato_926_chrome_devtools_mcp_bridge.py", "r") as f:
        content = f.read()
    assert 'f"' not in content and "f'" not in content, "F-strings are strictly forbidden in Python canonizers."
def test_substrate_929_f_strings():
    import os
    file_path = "substrates/t/929_arkhe_android_os_bridge/substrato_929_arkhe_android_os_bridge.py"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            content = f.read()
        assert 'f"' not in content and "f'" not in content, "F-strings are strictly forbidden in Python canonizers."

def test_substrate_931_f_strings():
    import os
    file_path = "substrates/t/931_interfold_coordination_bridge/substrato_931_interfold_coordination_bridge.py"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            content = f.read()
        assert 'f"' not in content and "f'" not in content, "F-strings are strictly forbidden in Python canonizers."

def test_933_f_strings():
    import ast
    with open('substrates/t/933_brazilian_financial_infrastructure_bridge/substrato_933_brazilian_financial_infrastructure_bridge.py', 'r') as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        assert not isinstance(node, ast.JoinedStr)
    with open('substrates/t/933_brazilian_financial_infrastructure_bridge/substrate_933_bfi_bridge.py', 'r') as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        assert not isinstance(node, ast.JoinedStr)

def test_substrate_923_2_f_strings():
    import os
    file_path = "substrates/t/923_2_vulnerability_temporalchain/substrato_923_2_vulnerability_temporalchain.py"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            content = f.read()
        assert 'f"' not in content and "f'" not in content, "F-strings are strictly forbidden in Python canonizers."

def test_substrate_100T_f_strings():
    import os
    file_path = "substrates/t/100T_moe_centum/substrato_100t_moe_centum.py"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            content = f.read()
        assert 'f"' not in content and "f'" not in content, "F-strings are strictly forbidden in Python canonizers."

def test_substrate_944_f_strings():
    import os
    file_path = "substrates/t/944_glasswing_sentinel/substrato_944_glasswing_sentinel.py"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            content = f.read()
        assert 'f"' not in content and "f'" not in content, "F-strings are strictly forbidden in Python canonizers."

def test_272_f_strings():
    with open("substrates/t/272_oracle_aws_bridge/substrato_272_oracle_aws_bridge.py", "r") as f:
        content = f.read()

    assert "f\"" not in content, "f-strings are strictly prohibited"
    assert "f'" not in content, "f-strings are strictly prohibited"

def test_substrate_563_1_f_strings():
    import ast
    with open('substrates/t/563_1_cortexmae_bridge/substrato_563_1_cortexmae_bridge.py', 'r') as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        assert not isinstance(node, ast.JoinedStr), "f-strings found in 563.1!"
