import json
import subprocess
import pytest

def test_substrate_996_1_canonizer():
    result = subprocess.run(
        ["python3", "substrates/t/996_1_arkhe_onchain_octra/substrato_996_1_arkhe_onchain.py"],
        capture_output=True,
        text=True,
        check=True
    )

    report = json.loads(result.stdout)

    assert report["Substrate_ID"] == "996.1"
    assert report["Status"] in ["CANONIZED", "CANONIZED_PROVISIONAL", "Canonized"]
    assert report["Type"] == "Canonizer"

    files = {f["filename"]: f["content"] for f in report["Files"]}
    assert "axiarchy_gate.aml" in files
    assert "substrate.toml" in files

    assert "996.1-ARKHE-ONCHAIN-" in report["Canonical_Seal"]
