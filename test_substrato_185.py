import pytest
import json
import os
import subprocess

def test_substrato_185_output():
    # Ensure script is run to generate output
    if os.path.exists("substrato_185_polyglot_harmony.json"):
        os.remove("substrato_185_polyglot_harmony.json")

    subprocess.run(["python3", "substrato_185_polyglot_harmony.py"], check=True)

    assert os.path.exists("substrato_185_polyglot_harmony.json")
    with open("substrato_185_polyglot_harmony.json", "r") as f:
        data = json.load(f)

    assert data["seal"] == "e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0"

    events = data["events"]
    assert len(events) == 6

    languages = [e["language"].lower() for e in events]
    assert "python" in languages
    assert "go" in languages
    assert "rust" in languages
    assert "node.js" in languages
    assert "typescript" in languages
    assert "java" in languages

    for event in events:
        assert event["phi_c"] == 1.0

if __name__ == "__main__":
    pytest.main(["-v", "test_substrato_185.py"])
