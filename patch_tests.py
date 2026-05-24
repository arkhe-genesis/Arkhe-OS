import sys

def patch_tests():
    with open("test_substrates.py", "r") as f:
        content = f.read()

    test_code = """
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

    lines = content.split('\\n')
    for i, line in enumerate(lines):
        if " f'" in line or ' f"' in line or line.startswith("f'") or line.startswith('f"'):
            assert False, "f-string found in line {}: {}".format(i+1, line.strip())
"""

    if "def test_619_octra():" not in content:
        # Find where to insert
        split_token = "if __name__ == '__main__':"
        if split_token in content:
            parts = content.split(split_token)
            new_content = parts[0] + test_code + "\n" + split_token + parts[1]
            with open("test_substrates.py", "w") as f:
                f.write(new_content)
            print("Tests added.")
        else:
            with open("test_substrates.py", "a") as f:
                f.write("\n" + test_code)
            print("Tests appended.")
    else:
        print("Tests already exist.")

if __name__ == "__main__":
    patch_tests()
