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

def test_substrate_261_f_strings():
    """Verify that Substrate 261 does not contain f-strings."""
    script_path = "substrates/t/261_arkhe_brasil_finance/substrato_261_arkhe_brasil_finance.py"
    with open(script_path, "r") as f:
        content = f.read()
        assert 'f"' not in content and "f'" not in content, "F-strings are strictly forbidden in Python canonizers."

def test_substrate_945_f_strings():
    import os
    file_path = "substrates/t/945_openmdw_fcr_bridge/substrato_945_openmdw_fcr_bridge.py"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            content = f.read()
        assert 'f"' not in content and "f'" not in content, "F-strings are strictly forbidden in Python canonizers."

def test_substrate_958_f_strings():
    import os
    file_path = "substrates/t/958_clarity_gate/substrato_958_clarity_gate.py"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            content = f.read()
        assert 'f"' not in content and "f'" not in content, "F-strings are strictly forbidden in Python canonizers."

def test_no_f_strings_972_1():
    import re
    with open("substrates/t/972_1_nostr_tor_ipfs_bridge/substrato_972_1_nostr_tor_ipfs_bridge.py", "r") as f:
        content = f.read()
    assert re.search(r"f['\"]", content) is None

def test_no_f_strings_973():
    import re
    with open("substrates/t/973_nostr_relay/substrato_973_nostr_relay.py", "r") as f:
        content = f.read()
    assert re.search(r"f['\"]", content) is None

def test_no_f_strings_974():
    import re
    with open("substrates/t/974_tor_mesh/substrato_974_tor_mesh.py", "r") as f:
        content = f.read()
    assert re.search(r"f['\"]", content) is None

def test_no_f_strings_975():
    import re
    with open("substrates/t/975_ipfs_core/substrato_975_ipfs_core.py", "r") as f:
        content = f.read()
    assert re.search(r"f['\"]", content) is None

def test_no_f_strings_970():
    import re
    with open("substrates/t/970_enterprise_mind/substrato_970_enterprise_mind.py", "r") as f:
        content = f.read()
    assert re.search(r"f['\"]", content) is None

def test_no_f_strings_971():
    import re
    with open("substrates/t/971_self_reflexive_cathedral/substrato_971_self_reflexive.py", "r") as f:
        content = f.read()
    assert re.search(r"f['\"]", content) is None

def test_no_f_strings_972():
    import re
    with open("substrates/t/972_internet_cathedral/substrato_972_internet_cathedral.py", "r") as f:
        content = f.read()
    assert re.search(r"f['\"]", content) is None

def test_no_f_strings_972_1():
    import re
    with open("substrates/t/972_1_nostr_tor_ipfs_bridge/substrato_972_1_nostr_tor_ipfs_bridge.py", "r") as f:
        content = f.read()
    assert re.search(r"f['\"]", content) is None

def test_no_f_strings_973():
    import re
    with open("substrates/t/973_nostr_relay/substrato_973_nostr_relay.py", "r") as f:
        content = f.read()
    assert re.search(r"f['\"]", content) is None

def test_no_f_strings_974():
    import re
    with open("substrates/t/974_tor_mesh/substrato_974_tor_mesh.py", "r") as f:
        content = f.read()
    assert re.search(r"f['\"]", content) is None

def test_no_f_strings_975():
    import re
    with open("substrates/t/975_ipfs_core/substrato_975_ipfs_core.py", "r") as f:
        content = f.read()
    assert re.search(r"f['\"]", content) is None

def test_no_f_strings_970():
    import re
    with open("substrates/t/970_enterprise_mind/substrato_970_enterprise_mind.py", "r") as f:
        content = f.read()
    assert re.search(r"f['\"]", content) is None

def test_no_f_strings_971():
    import re
    with open("substrates/t/971_self_reflexive_cathedral/substrato_971_self_reflexive.py", "r") as f:
        content = f.read()
    assert re.search(r"f['\"]", content) is None

def test_no_f_strings_972():
    import re
    with open("substrates/t/972_internet_cathedral/substrato_972_internet_cathedral.py", "r") as f:
        content = f.read()
    assert re.search(r"f['\"]", content) is None

def test_substrate_989_f_strings():
    import os
    file_path = "substrates/t/989_passport_gateway/substrato_989_passport_gateway.py"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            content = f.read()
        assert 'f"' not in content and "f'" not in content, "F-strings are strictly forbidden in Python canonizers."
