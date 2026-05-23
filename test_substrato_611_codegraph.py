import os
import json
import subprocess

def test_substrato_611():
    result = subprocess.run(["python3", "substrates/611-CODEGRAPH/substrato_611_codegraph.py"], capture_output=True, text=True)
    assert result.returncode == 0

    output_line = result.stdout.strip()
    assert output_line.startswith("Canonized Substrate 611-CODEGRAPH to: ")

    path = output_line.split(": ")[1]
    assert os.path.exists(path)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["id"] == "611-CODEGRAPH"
    assert data["status"] == "CANONIZED_PROVISIONAL"
    assert "seal" in data
    assert len(data["seal"]) == 64

if __name__ == "__main__":
    test_substrato_611()
    print("Test passed!")
