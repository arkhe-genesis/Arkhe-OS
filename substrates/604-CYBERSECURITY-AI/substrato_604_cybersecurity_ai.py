import json
import os
import tempfile
import hashlib

class Substrato604CybersecurityAI:
    """
    Canonizes Substrate 604-CYBERSECURITY-AI as requested.
    """
    def __init__(self):
        self.data = {
            "id": "604-CYBERSECURITY-AI",
            "name": "Cybersecurity AI (CAI) — Agent-Based Security Testing Framework",
            "repository": "https://github.com/aliasrobotics/cai",
            "authors": "Alias Robotics (Víctor Mayoral-Vilches, PhD)",
            "funding": "European EIC accelerator RIS (GA 101161136)",
            "paper": "arXiv:2504.06017",
            "license": "MIT",
            "stack": "Python 3.10+, ReAct, 300+ LLM backends, uv",
            "type": "Substrato de segurança ofensiva/defensiva (auditoria externa)",
            "status": "CANONIZED_PROVISIONAL",
            "incorporation_date": "25 de Maio de 2026",
            "known_vulnerability": "CVE-2025-67511 (command injection em ≤0.5.9)",
            "canonical_seal": "pending"
        }

    def generate_json(self):
        canonical_str = json.dumps(self.data, sort_keys=True)
        seal = hashlib.sha3_256(canonical_str.encode("utf-8")).hexdigest()
        self.data["canonical_seal"] = seal

        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

        return path

if __name__ == "__main__":
    canonizer = Substrato604CybersecurityAI()
    path = canonizer.generate_json()
    print("Canonized 604-CYBERSECURITY-AI to: " + path)
