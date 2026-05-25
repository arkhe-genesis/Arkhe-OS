import json
import base64
import os
import tempfile
import hashlib

def canonize():
    """
    Canonizes the Substrate 826.2 (GNN Isomorphism Finder).
    Generates a canonical JSON report with a SHA3-256 seal.
    Strictly avoids f-strings.
    """
    with open(os.path.join(os.path.dirname(__file__), "gnn_isomorphism_finder.py"), "rb") as f:
        script_content = f.read()

    b64_script = base64.b64encode(script_content).decode("utf-8")

    payload = {
        "id": "826-GNN-ISOMORPHISM-FINDER",
        "type": "QUANTUM",
        "name": "GNN Isomorphism Finder",
        "architect": "ORCID 0009-0005-2697-4668",
        "files": {
            "gnn_isomorphism_finder.py": b64_script
        }
    }

    # Generate SHA3-256 seal
    payload_str = json.dumps(payload, sort_keys=True)
    seal = hashlib.sha3_256(payload_str.encode("utf-8")).hexdigest()

    payload["canonical_seal"] = seal

    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(payload, f, indent=4)

    return path, seal, payload

if __name__ == "__main__":
    path, seal, payload = canonize()
    print("Canonized Substrate 826-GNN-ISOMORPHISM-FINDER")
    print("Seal: " + seal)
    print("Report written to: " + path)
