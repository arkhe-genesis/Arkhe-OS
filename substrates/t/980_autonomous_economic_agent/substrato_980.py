import json
import base64
import hashlib
import sys
import os

class Substrato_980_AutonomousEconomicAgent:
    def canonize(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        payload_file = "substrate_980.py"
        toml_file = "substrate.toml"

        try:
            with open(os.path.join(script_dir, payload_file), "r") as f:
                payload_content = f.read()
            with open(os.path.join(script_dir, toml_file), "r") as f:
                toml_content = f.read()
        except FileNotFoundError:
            payload_content = 'print("MOCK")\n'
            toml_content = 'mock'

        b64_payload = base64.b64encode(payload_content.encode('utf-8')).decode('utf-8')
        b64_toml = base64.b64encode(toml_content.encode('utf-8')).decode('utf-8')

        seal_input = payload_content
        canon_seal = 'sha3-256:' + hashlib.sha3_256(seal_input.encode('utf-8')).hexdigest()

        report = {
            'Substrate': '980',
            'Status': 'Canonized',
            'Canonical_Seal': canon_seal,
            'Files': {
                payload_file: b64_payload,
                toml_file: b64_toml
            }
        }

        print(json.dumps(report, indent=4))
        return report

if __name__ == "__main__":
    canonizer = Substrato_980_AutonomousEconomicAgent()
    canonizer.canonize()
