import json
import hashlib
import base64
import os

def get_b64_artifacts():
    base_dir = os.path.dirname(__file__)
    node_dir = os.path.abspath(os.path.join(base_dir, "../../../node"))

    # Files to include
    payload_path = os.path.join(node_dir, "passport_gateway.py")
    api_gateway_path = os.path.join(node_dir, "api_gateway.py")
    server_path = os.path.join(node_dir, "server.py")

    # Ensure substrate.toml exists
    toml_path = os.path.join(base_dir, "substrate.toml")
    if not os.path.exists(toml_path):
        with open(toml_path, "w") as f:
            f.write("[substrate]\nid = 989\nname = \"Passport Gateway\"\n")

    return {
        "passport_gateway.py": base64.b64encode(open(payload_path, "rb").read()).decode("utf-8"),
        "api_gateway.py": base64.b64encode(open(api_gateway_path, "rb").read()).decode("utf-8"),
        "server.py": base64.b64encode(open(server_path, "rb").read()).decode("utf-8"),
        "substrate.toml": base64.b64encode(open(toml_path, "rb").read()).decode("utf-8")
    }

class Substrato_989_passport_gateway:
    def canonize(self):
        artifacts = get_b64_artifacts()

        # Calculate dynamic SHA3-256 seal
        m = hashlib.sha3_256()
        m.update(json.dumps(artifacts, sort_keys=True).encode("utf-8"))
        seal = m.hexdigest()

        output = {
            "Substrate": "989-PASSPORT-GATEWAY",
            "Status": "CANONIZED_PROVISIONAL",
            "Canonical_Seal": seal,
            "Files": artifacts
        }

        output_file = os.path.join(os.path.dirname(__file__), "report.json")
        with open(output_file, "w") as f:
            json.dump(output, f, indent=4)

        return output_file

if __name__ == "__main__":
    canonizer = Substrato_989_passport_gateway()
    print(canonizer.canonize())
