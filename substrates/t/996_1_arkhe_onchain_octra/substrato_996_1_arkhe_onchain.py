import base64
import json
import hashlib
import sys

def compute_seal(payloads):
    h = hashlib.sha3_256()
    for k in sorted(payloads.keys()):
        h.update(k.encode('utf-8'))
        h.update(payloads[k].encode('utf-8'))
    return "996.1-ARKHE-ONCHAIN-" + h.hexdigest()[:16].upper()

def main():
    try:
        with open("substrates/t/996_1_arkhe_onchain_octra/axiarchy_gate.aml", "rb") as f:
            aml_content = f.read()
    except Exception:
        aml_content = b""

    try:
        with open("substrates/t/996_1_arkhe_onchain_octra/substrate.toml", "rb") as f:
            toml_content = f.read()
    except Exception:
        toml_content = b""

    aml_b64 = base64.b64encode(aml_content).decode("utf-8")
    toml_b64 = base64.b64encode(toml_content).decode("utf-8")

    payloads = {
        "axiarchy_gate.aml": aml_b64,
        "substrate.toml": toml_b64
    }

    seal = compute_seal(payloads)

    report = {
        "Substrate_ID": "996.1",
        "Name": "ARKHE-ONCHAIN (Octra Bridge)",
        "Type": "Canonizer",
        "Status": "Canonized",
        "Architect_ORCID": "0009-0005-2697-4668",
        "Odometer": "∞.Ω.∇+++.996.1",
        "Files": [{"filename": k, "content": v} for k, v in payloads.items()],
        "Canonical_Seal": seal
    }

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
