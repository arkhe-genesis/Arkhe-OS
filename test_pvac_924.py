def test_pvac_924_compound_motion():
    import subprocess
    import json
    result = subprocess.run(["python3", "substrates/t/924_compound_motion_dynamics/substrate_924_compound_motion_dynamics.py"], capture_output=True, text=True)
    assert result.returncode == 0

    path = result.stdout.strip()
    if "Report generated at: " in path:
        path = path.split("Report generated at: ")[1].strip()
        with open(path, "r") as f:
            data = json.load(f)

    assert data["Substrate"] == "924-COMPOUND-MOTION-DYNAMICS"
    assert data["Canonical_Seal"] == "e3667af7b8b16f32b5d28098c8ef8a1812a644ffa5fa900d3c3b6ba5987c7706"
