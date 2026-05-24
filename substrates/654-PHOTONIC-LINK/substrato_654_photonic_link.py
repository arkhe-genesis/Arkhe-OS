import json
import hashlib
import tempfile
import os

class Substrato654:
    def __init__(self):
        self.id = "654-PHOTONIC-LINK"
        self.description = "Transceptor óptico interestelar (downlink de dados)"
        self.tech_base = "NASA DSOC, soliton microcomb escalado"

    def canonize(self):
        # We must strictly avoid f-strings!
        data = {
            "id": self.id,
            "description": self.description,
            "tech_base": self.tech_base,
            "status": "CANONIZED_CLEAN"
        }

        # Serialize to JSON with sorted keys for deterministic hash
        json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        seal = hashlib.sha3_256(json_str.encode('utf-8')).hexdigest()
        data["canonical_seal"] = seal

        # Write to a temporary file
        fd, path = tempfile.mkstemp(suffix=".json", text=True)
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=4)

        return path
