import os
import base64
import json
import hashlib
import sys
import tempfile

def get_b64_artifacts():
    return {
        "README.md": "",
        "constitution.md": "",
        "Makefile": "",
        "docker-compose.yml": "",
        "core_arkeh-jax_Cargo.toml": "",
        "core_arkeh-jax_src_lib.rs": "",
        "core_arkeh-jax_src_jaxpr.rs": "",
        "core_arkeh-jax_src_autograd.rs": "",
        "core_arkeh-jax_src_lowering_wgpu_backend.rs": "",
        "core_gb300-rl_CMakeLists.txt": "",
        "core_gb300-rl_include_arkhe_rl.h": "",
        "core_gb300-rl_src_engine.c": "",
        "core_gb300-rl_src_kernels_flash_attn_blackwell.cu": "",
        "core_gb300-rl_src_kernels_fp4_matmul_blackwell.cu": "",
        "core_gb300-rl_src_ppo_loss.cu": "",
        "memory_temporal-chain_Cargo.toml": "",
        "memory_temporal-chain_contracts_TemporalChain.sol": "",
        "memory_temporal-chain_src_anchor.rs": "",
        "memory_temporal-chain_src_bridge.rs": "",
        "memory_epistemic-commit_setup.py": "",
        "memory_epistemic-commit_src_commit.py": "",
        "memory_epistemic-commit_src_levels.py": "",
        "security_hermes-zk_Cargo.toml": "",
        "security_hermes-zk_src_prover.rs": "",
        "security_hermes-zk_src_verifier.rs": "",
        "security_hermes-zk_src_seal.rs": "",
        "security_glasswing-sentinel_Cargo.toml": "",
        "security_glasswing-sentinel_src_sast.rs": "",
        "security_glasswing-sentinel_src_rules.json": "",
        "security_edge-filter_Makefile": "",
        "security_edge-filter_src_filter_kernel.cpp": "",
        "security_edge-filter_src_bloom_filter.h": "",
        "network_arkeh-tcp_go.mod": "",
        "network_arkeh-tcp_cmd_arkeh-tcp_main.go": "",
        "network_arkeh-tcp_cmd_arkeh-tcp-2621_main.go": "",
        "network_doublezero_go.mod": "",
        "network_doublezero_cmd_dz-bridge_main.go": "",
        "interfaces_windows-app_ArkheCatedral.csproj": "",
        "interfaces_windows-app_MainWindow.xaml": "",
        "interfaces_android-app_build.gradle.kts": "",
        "interfaces_arkeh-watch_go.mod": "",
        "interfaces_arkeh-watch_main.go": "",
        "finance_brasil-finance_Cargo.toml": "",
        "finance_brasil-finance_src_spi.rs": "",
        "finance_brasil-finance_src_qrcode.rs": "",
        "finance_brasil-finance_src_zk_pix.rs": "",
        "finance_vulnerability-chain_contracts_VulnerabilityRegistry.sol": "",
        "agents_claude-harness_harness_adapter.py": "",
        "agents_cognitive-effort_controller.py": "",
        "agents_code-agent_catedral_code_agent.py": "",
        "agents_visual-ontology_visual_ontology_engine.py": "",
        "agents_visual-ontology_schema_943.jsonld": "",
        "api_protobuf_arkhe_common_v1_header.proto": "",
        "api_protobuf_arkhe_temporalchain_v1_temporalchain.proto": "",
        "api_protobuf_arkhe_epistemic_v1_epistemic.proto": "",
        "api_protobuf_arkhe_hermeszk_v1_hermeszk.proto": "",
        "api_protobuf_arkhe_quicmesh_v1_quicmesh.proto": "",
        "api_protobuf_arkhe_worldmodel_v1_worldmodel.proto": "",
        "api_protobuf_arkhe_fluxmem_v1_fluxmem.proto": "",
        "api_protobuf_arkhe_agency_v1_agency.proto": "",
        "api_protobuf_arkhe_brasilfinance_v1_brasilfinance.proto": "",
        "api_protobuf_arkhe_glasswing_v1_glasswing.proto": "",
        "api_protobuf_arkhe_mcp_v1_mcp.proto": "",
        "api_protobuf_arkhe_androidhal_v1_androidhal.proto": "",
        "api_protobuf_arkhe_webgrounding_v1_webgrounding.proto": "",
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
        "Substrate": "997",
        "Status": "Canonized",
        "Files": list(get_b64_artifacts().keys())
    }

    seal = compute_seal(payload)
    payload["Canonical_Seal"] = seal

    fd, path = tempfile.mkstemp(suffix=".json", prefix="substrate_997_")
    with os.fdopen(fd, "w") as f:
        json.dump(payload, f, indent=2)

    print("Substrate 997 canonized at:", path)
    print("Seal:", seal)

    if len(sys.argv) > 1 and sys.argv[1] == "--extract":
        extract_dir = sys.argv[2] if len(sys.argv) > 2 else "output_997"
        extract_artifacts(extract_dir)
        print("Artifacts extracted to:", extract_dir)

if __name__ == "__main__":
    main()
