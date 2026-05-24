import json
import hashlib
import tempfile
import os

class Substrato656:
    def __init__(self):
        self.id = "656-AUTONOMOUS-REPAIR"
        self.description = "IA híbrida neuro-simbólica para autorreparo multigeracional"
        self.tech_base = "Hybrid AI for interstellar missions (2025)"

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
