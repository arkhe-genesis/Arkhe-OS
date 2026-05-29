import os
import base64
import json
import hashlib
import sys
import tempfile

def get_b64_artifacts():
    return {
        "README.md": "",
        "mythos-engine_deities_hermes_trismegistus.md": "",
        "mythos-engine_deities_prometheus.md": "",
        "mythos-engine_deities_tefis.md": "",
        "mythos-engine_myths_creation_of_the_cathedral.md": "",
        "mythos-engine_myths_the_great_work.md": "",
        "sophon-bridge_sophon_physics.md": "",
        "sophon-bridge_entanglement_metaphor.md": "",
        "council-of-deities_council_charter.md": "",
        "council-of-deities_sessions_session_001.md": "",
        "design-fiction_leak_001.md": "",
        "design-fiction_leak_002_complete.md": "",
        "stainedglass-theme_colors.json": "",
        "stainedglass-theme_palettes_sacred_gold.png": "",
        "stainedglass-theme_palettes_divine_blue.png": "",
        "constitution_magnifica_humanitas.md": "",
        "constitution_arkhe_constitution.md": "",
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
        "Substrate": "999",
        "Status": "Canonized",
        "Files": list(get_b64_artifacts().keys())
    }

    seal = compute_seal(payload)
    payload["Canonical_Seal"] = seal

    fd, path = tempfile.mkstemp(suffix=".json", prefix="substrate_999_")
    with os.fdopen(fd, "w") as f:
        json.dump(payload, f, indent=2)

    print("Substrate 999 canonized at:", path)
    print("Seal:", seal)

    if len(sys.argv) > 1 and sys.argv[1] == "--extract":
        extract_dir = sys.argv[2] if len(sys.argv) > 2 else "output_999"
        extract_artifacts(extract_dir)
        print("Artifacts extracted to:", extract_dir)

if __name__ == "__main__":
    main()
