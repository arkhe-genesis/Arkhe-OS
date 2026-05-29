import json
import hashlib
import base64
import os
import sys

def get_b64_artifacts():
    base_dir = os.path.dirname(__file__)
    return {
        "atlas_lean_bridge.py": base64.b64encode(open(os.path.join(base_dir, "atlas_lean_bridge.py"), "rb").read()).decode("utf-8"),
        "substrate.toml": base64.b64encode(open(os.path.join(base_dir, "substrate.toml"), "rb").read()).decode("utf-8")
    }

class Substrato_946_atlas_lean_bridge:
    def canonize(self):
        artifacts = get_b64_artifacts()

        # Calculate dynamic SHA3-256 seal
        m = hashlib.sha3_256()
        m.update(json.dumps(artifacts, sort_keys=True).encode("utf-8"))
        seal = m.hexdigest()

        output = {
            "Substrate": "946-ATLAS-LEAN-BRIDGE",
            "Status": "CANONIZED_CLEAN",
            "Canonical_Seal": seal,
            "Files": artifacts
        }

        output_file = os.path.join(os.path.dirname(__file__), "test_946.json")
        with open(output_file, "w") as f:
            json.dump(output, f, indent=4)

        return output_file

if __name__ == "__main__":
    canonizer = Substrato_946_atlas_lean_bridge()
    canonizer.canonize()
