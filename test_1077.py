import subprocess
import json

def test_substrate_1077():
    result = subprocess.run(
        ["python3", "substrato_1077_goose_cathedral_bridge.py"],
        capture_output=True,
        text=True,
        check=True
    )
    report = json.loads(result.stdout)
    assert report["SubstrateID"] == "1077"
    assert report["Name"] == "GOOSE-CATHEDRAL BRIDGE"
    assert "goose_cathedral_bridge.py" in report["Files"]
    assert "substrate.toml" in report["Files"]
