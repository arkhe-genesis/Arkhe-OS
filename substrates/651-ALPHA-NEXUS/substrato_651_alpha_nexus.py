import os
import json
import tempfile
import hashlib
import shutil

def canonize_substrate() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    decree_path = os.path.join(script_dir, "651-ALPHA-NEXUS_DECREE_v2.0.txt")
    with open(decree_path, 'r', encoding='utf-8') as f:
        decree = f.read()

    sol_path = os.path.join(script_dir, "651_AlphaNexus.sol")
    with open(sol_path, 'r', encoding='utf-8') as f:
        sol_content = f.read()

    patch_path = os.path.join(script_dir, "651_KERNEL_PATCH.asm")
    with open(patch_path, 'r', encoding='utf-8') as f:
        patch_content = f.read()

    audit_path = os.path.join(script_dir, "651_FINAL_AUDIT.txt")
    with open(audit_path, 'r', encoding='utf-8') as f:
        audit_content = f.read()

    hasher = hashlib.sha3_256()
    hasher.update(decree.encode("utf-8"))
    seal = hasher.hexdigest()

    data = {
        "id": "651-ALPHA-NEXUS",
        "title": "Alpha Nexus",
        "description": "Integration of AlphaProof Nexus framework for LLM-guided formal proof search",
        "seal": seal,
        "content": decree,
        "solidity_contract": sol_content,
        "kernel_patch": patch_content,
        "audit_report": audit_content,
        "metrics": {
            "phi_proof_contribution": 0.03,
            "ti": 0.999
        }
    }

    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return path

if __name__ == "__main__":
    path = canonize_substrate()
    print(path)
