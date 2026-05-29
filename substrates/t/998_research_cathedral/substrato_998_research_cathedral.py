import os
import base64
import json
import hashlib
import sys
import tempfile

def get_b64_artifacts():
    return {
        "README.md": "",
        "papers_fluxmem_arxiv_2605.28773.pd\x66": "",
        "world-model-v3_experiments_trainer.py": "",
        "world-model-v3_models_attention.py": "",
        "fluxmem-evolution_src_bmm_gate.py": "",
        "fluxmem-evolution_src_consolidation.py": "",
        "fluxmem-evolution_benchmarks_locomo_test.py": "",
        "bec-engine_src_gpe_solver.py": "",
        "bec-engine_src_split_step.c": "",
        "bec-engine_notebooks_rabi_oscillations.ipynb": "",
        "atom-chip-interface_src_bloch_reader.py": "",
        "adaptive-thinking_experiments_effort_vs_complexity.py": "",
        "adaptive-thinking_models_cost_predictor.py": "",
        "agent-eval-benchmarks_benchmarks_swe_bench.py": "",
        "agent-eval-benchmarks_benchmarks_gaia_test.py": "",
        "agent-eval-benchmarks_results_tracking.json": "",
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
        "Substrate": "998",
        "Status": "Canonized",
        "Files": list(get_b64_artifacts().keys())
    }

    seal = compute_seal(payload)
    payload["Canonical_Seal"] = seal

    fd, path = tempfile.mkstemp(suffix=".json", prefix="substrate_998_")
    with os.fdopen(fd, "w") as f:
        json.dump(payload, f, indent=2)

    print("Substrate 998 canonized at:", path)
    print("Seal:", seal)

    if len(sys.argv) > 1 and sys.argv[1] == "--extract":
        extract_dir = sys.argv[2] if len(sys.argv) > 2 else "output_998"
        extract_artifacts(extract_dir)
        print("Artifacts extracted to:", extract_dir)

if __name__ == "__main__":
    main()
