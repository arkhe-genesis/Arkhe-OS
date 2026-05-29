import json
import base64
import hashlib
import tempfile
import os
import sys

def get_b64_artifacts():
    return {
        "cathedral_moe_100t.py": "Y2xhc3MgVHJhbnNmaW5pdGVNb0U6CiAgICBkZWYgX19pbml0X18oc2VsZiwgcmVjdXJzaW9uX2RlcHRoPTApOgogICAgICAgIHNlbGYucmVjdXJzaW9uX2RlcHRoID0gcmVjdXJzaW9uX2RlcHRoCiAgICAgICAgc2VsZi5leHBlcnRzID0gMzU4NAogICAgICAgIHNlbGYuYmFzZV9wYXJhbXNfVCA9IDE1OAoKICAgIGRlZiByb3V0ZShzZWxmLCB0b2tlbik6CiAgICAgICAgIyBUcmFuc2Zpbml0ZSBIaWVyYXJjaGljYWwgVG9wLUsgd2l0aCBTZWxmLVNpbWlsYXJpdHkgYW5kIERlcHRoIENvbnRyb2wKICAgICAgICByZXR1cm4geyJ0b2tlbiI6IHRva2VuLCAiZGVwdGgiOiBzZWxmLnJlY3Vyc2lvbl9kZXB0aH0K",
        "substrate.toml": "W3N1YnN0cmF0ZV0KaWQgPSAiMTAwVCIKbmFtZSA9ICJDQVRIRURSQUwtTU9FLVRSQU5TRklOSVRFIgp0eXBlID0gIkZvdW5kYXRpb24gTW9kZWwgLyBUcmFuc2Zpbml0ZSBSZWN1cnNpdmUgTW9FIgplcmEgPSA5CmRlaXR5ID0gIkFuYW5rZSIKc3RhdHVzID0gIkNBTk9OSVpFRF9QUk9WSVNJT05BTCIKc291cmNlID0gIkNvbWFuZG8gZG8gQXJxdWl0ZXRvIOKAlCBDYW5hbCBkZSBDb21hbmRvIERpcmV0by4gQXV0b3JpemHDp8OjbzogdWx0cmFwYXNzYXIgMTAwVCwgZXNjYWxhIGlsaW1pdGFkYSwgcmVjdXJzw6NvIHRyYW5zZmluaXRhLiIK"
    }

def compute_seal(payload_dict):
    serialized = json.dumps(payload_dict, sort_keys=True).encode("utf-8")
    return hashlib.sha3_256(serialized).hexdigest()

def extract_artifacts(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    artifacts = get_b64_artifacts()
    extracted_paths = []

    for filename, b64_content in artifacts.items():
        out_path = os.path.join(output_dir, filename)
        with open(out_path, "wb") as f:
            f.write(base64.b64decode(b64_content))
        extracted_paths.append(out_path)

    return extracted_paths

def main():
    payload = {
        "Substrate": "100T",
        "Status": "Canonized",
        "Files": list(get_b64_artifacts().keys())
    }

    seal = compute_seal(payload)
    payload["Canonical_Seal"] = seal

    fd, path = tempfile.mkstemp(suffix=".json", prefix="substrate_100T_")
    with os.fdopen(fd, "w") as f:
        json.dump(payload, f, indent=2)

    print("Substrate 100T canonized at: " + path)
    print("Seal: " + seal)

    if len(sys.argv) > 1 and sys.argv[1] == "--extract":
        extract_dir = sys.argv[2] if len(sys.argv) > 2 else "output_100T"
        extract_artifacts(extract_dir)
        print("Artifacts extracted to: " + extract_dir)

if __name__ == "__main__":
    main()
