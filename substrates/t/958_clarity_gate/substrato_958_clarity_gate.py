import json
import hashlib
import base64
import os

def get_b64_artifacts():
    base_dir = os.path.dirname(__file__)

    # Ensure clarity_gate.py exists
    payload_path = os.path.join(base_dir, "clarity_gate.py")
    if not os.path.exists(payload_path):
        with open(payload_path, "w") as f:
            f.write("# Fallback clarity_gate.py\n")

    # Ensure substrate.toml exists
    toml_path = os.path.join(base_dir, "substrate.toml")
    if not os.path.exists(toml_path):
        with open(toml_path, "w") as f:
            f.write("[substrate]\nid = 958\nname = \"Clarity Gate\"\n")

    return {
        "clarity_gate.py": base64.b64encode(open(payload_path, "rb").read()).decode("utf-8"),
        "substrate.toml": base64.b64encode(open(toml_path, "rb").read()).decode("utf-8")
    }

class Substrato_958_clarity_gate:
    def canonize(self):
        artifacts = get_b64_artifacts()

        # Calculate dynamic SHA3-256 seal
        m = hashlib.sha3_256()
        m.update(json.dumps(artifacts, sort_keys=True).encode("utf-8"))
        seal = m.hexdigest()

        output = {
            "Substrate": "958-CLARITY-GATE",
            "Status": "CANONIZED",
            "Canonical_Seal": seal,
            "Files": artifacts
        }

        output_file = os.path.join(os.path.dirname(__file__), "test_958.json")
        with open(output_file, "w") as f:
            json.dump(output, f, indent=4)

        return output_file

if __name__ == "__main__":
    canonizer = Substrato_958_clarity_gate()
    canonizer.canonize()
