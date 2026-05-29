import json
import base64
import hashlib
from datetime import datetime
import os

class Substrato_949_Interaction_Hotspots:
    def __init__(self):
        self.metadata = {
            "Substrate": "949",
            "Name": "INTERACTION-HOTSPOTS",
            "Type": "Scientific Analysis / Quantum Chemistry",
            "Era": "6",
            "Deity": "Athena",
            "Status": "CANONIZED_PROVISIONAL"
        }
        self.files = [
            "../../../src/arkhe/substrates/interaction_hotspots.py",
            "substrate.toml"
        ]

    def _read_and_encode(self, filename: str) -> str:
        base_dir = os.path.dirname(__file__)
        filepath = os.path.join(base_dir, filename)
        with open(filepath, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def canonize(self):
        payloads = {}
        content_for_seal = ""

        for file in self.files:
            b64_content = self._read_and_encode(file)
            payloads[os.path.basename(file)] = b64_content
            content_for_seal += b64_content

        seal = hashlib.sha3_256(content_for_seal.encode("utf-8")).hexdigest()

        report = {
            "Substrate": self.metadata["Substrate"],
            "Status": self.metadata["Status"],
            "Canonical_Seal": "sha3-256:" + seal,
            "Files": payloads
        }

        return json.dumps(report, indent=4)

if __name__ == "__main__":
    canonizer = Substrato_949_Interaction_Hotspots()
    print(canonizer.canonize())
