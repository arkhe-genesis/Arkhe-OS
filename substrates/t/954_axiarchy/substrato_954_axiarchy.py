import json
import hashlib
import base64
import os
import sys

def get_b64_artifacts():
    base_dir = os.path.dirname(__file__)
    return {
        "axiarchy.py": base64.b64encode(open(os.path.join(base_dir, "axiarchy.py"), "rb").read()).decode("utf-8"),
        "axiarchy_954.lean": base64.b64encode(open(os.path.join(base_dir, "axiarchy_954.lean"), "rb").read()).decode("utf-8"),
        "substrate.toml": base64.b64encode(open(os.path.join(base_dir, "substrate.toml"), "rb").read()).decode("utf-8")
    }

class Substrato_954_axiarchy:
    def canonize(self):
        artifacts = get_b64_artifacts()

        # Calculate dynamic SHA3-256 seal
        m = hashlib.sha3_256()
        m.update(json.dumps(artifacts, sort_keys=True).encode("utf-8"))
        seal = m.hexdigest()

        output = {
            "Substrate": "954-AXIARCHY",
            "Status": "CANONIZED_PROVISIONAL",
            "Canonical_Seal": seal,
            "Files": artifacts
        }

        output_file = os.path.join(os.path.dirname(__file__), "test_954.json")
        with open(output_file, "w") as f:
            json.dump(output, f, indent=4)

        return output_file

if __name__ == "__main__":
    canonizer = Substrato_954_axiarchy()
    canonizer.canonize()
