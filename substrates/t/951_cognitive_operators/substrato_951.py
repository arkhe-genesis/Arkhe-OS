import json
import hashlib
import os
import base64

class Substrato951:
    def __init__(self):
        self.metadata = {
            "id": "951-953",
            "name": "Cognitive Operators",
            "type": "Cognitive Algorithms",
            "era": "7",
            "status": "CANONIZED_PROVISIONAL",
            "cross_links": ["1018"]
        }

        script_dir = os.path.dirname(os.path.abspath(__file__))

        payload_path = os.path.join(script_dir, "cognitive_operators.py")
        with open(payload_path, "r", encoding="utf-8") as f:
            self.payload_b64 = base64.b64encode(f.read().encode("utf-8")).decode("utf-8")

        toml_path = os.path.join(script_dir, "substrate.toml")
        with open(toml_path, "r", encoding="utf-8") as f:
            self.toml_b64 = base64.b64encode(f.read().encode("utf-8")).decode("utf-8")

    def get_canonical_seal(self):
        data_to_seal = {
            "id": self.metadata["id"],
            "name": self.metadata["name"],
            "payload_hash": hashlib.sha3_256(self.payload_b64.encode("utf-8")).hexdigest(),
            "toml_hash": hashlib.sha3_256(self.toml_b64.encode("utf-8")).hexdigest()
        }
        seal_string = json.dumps(data_to_seal, sort_keys=True)
        return hashlib.sha3_256(seal_string.encode("utf-8")).hexdigest()

    def generate_report(self):
        return {
            "Substrate_ID": self.metadata["id"],
            "Name": self.metadata["name"],
            "Type": self.metadata["type"],
            "Era": self.metadata["era"],
            "Status": self.metadata["status"],
            "Cross_Links": self.metadata["cross_links"],
            "Canonical_Seal": self.get_canonical_seal(),
            "Files": {
                "cognitive_operators.py": self.payload_b64,
                "substrate.toml": self.toml_b64
            }
        }

if __name__ == "__main__":
    substrate = Substrato951()
    print(json.dumps(substrate.generate_report(), indent=2))
