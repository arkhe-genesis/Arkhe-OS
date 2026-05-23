import pytest

def test_substrato_611():
    import subprocess
    import json

    result = subprocess.run(["python3", "substrates/611-CODEGRAPH/substrato_611_codegraph.py"], capture_output=True, text=True)
    assert result.returncode == 0

    output_line = result.stdout.strip()
    path = output_line.split(": ")[1]

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["id"] == "611-CODEGRAPH"
