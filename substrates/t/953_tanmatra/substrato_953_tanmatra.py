import json
import hashlib
import os
import base64

class Substrato953Tanmatra:
    def __init__(self):
        self.metadata = {
            "id": "953",
            "name": "TANMATRA",
            "type": "Embodied AI / Sensory Interface",
            "era": "7",
            "deity": "Icaro e Prithvi",
            "status": "CANONIZED_PROVISIONAL",
            "cross_links": ["951", "952", "954", "608", "563.1", "568", "569", "570", "890", "934", "554", "947", "948", "955"]
        }

        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Load and base64 encode payload
        payload_path = os.path.join(script_dir, "tanmatra.py")
        with open(payload_path, "r", encoding="utf-8") as f:
            self.payload_b64 = base64.b64encode(f.read().encode("utf-8")).decode("utf-8")

        toml_path = os.path.join(script_dir, "substrate.toml")
        with open(toml_path, "r", encoding="utf-8") as f:
            self.toml_b64 = base64.b64encode(f.read().encode("utf-8")).decode("utf-8")

    def get_canonical_seal(self):
        data_to_seal = {
            "metadata": self.metadata,
            "payload_b64": self.payload_b64,
            "toml_b64": self.toml_b64
        }
        canonical_str = json.dumps(data_to_seal, sort_keys=True, separators=(',', ':'))
        return hashlib.sha3_256(canonical_str.encode('utf-8')).hexdigest()

    def canonize(self):
        seal = self.get_canonical_seal()
        report = {
            "metadata": self.metadata,
            "payload_b64": self.payload_b64,
            "toml_b64": self.toml_b64,
            "Canonical_Seal": seal
        }

        script_dir = os.path.dirname(os.path.abspath(__file__))
        report_path = os.path.join(script_dir, "report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)

        return report_path
