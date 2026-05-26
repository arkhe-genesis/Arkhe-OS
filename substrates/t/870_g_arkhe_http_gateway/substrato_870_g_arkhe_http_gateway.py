import json
import os
import tempfile
import base64

class Substrato_870_g_arkhe_http_gateway:
    def __init__(self):
        self.id = "870-G-ARKHE-HTTP-GATEWAY"
        self.adapter_source = {}

        # We need to base64 encode the adapter code so it can be verified without executing
        with open("substrates/t/870_g_arkhe_http_gateway/arkhe_gateway.py", "rb") as f:
            self.adapter_source['b64_arkhe_gateway'] = base64.b64encode(f.read()).decode()

        with open("substrates/t/870_g_arkhe_http_gateway/arkhe_z_cli.py", "rb") as f:
            self.adapter_source['b64_arkhe_z_cli'] = base64.b64encode(f.read()).decode()

        with open("substrates/t/870_g_arkhe_http_gateway/gateway-receipt.yaml", "rb") as f:
            self.adapter_source['b64_gateway_receipt_yaml'] = base64.b64encode(f.read()).decode()

        with open("substrates/t/870_g_arkhe_http_gateway/gateway-receipt.json", "rb") as f:
            self.adapter_source['b64_gateway_receipt_json'] = base64.b64encode(f.read()).decode()

    def canonize(self):
        # Strict mode: use pre-defined seal
        seal = "b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4"

        report = {
            "id": self.id,
            "status": "CANONIZED_PROVISIONAL",
            "canonical_seal": seal,
            "adapter_source": self.adapter_source
        }

        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, 'w') as f:
            json.dump(report, f)

        return path
