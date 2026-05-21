import json
import hashlib
import os
import tempfile
import sys

def generate_report():
    # Hardcoded values for 429-BLUE-CODE
    phi_c = 0.9558

    report_data = {
        "substrato": "429-BLUE-CODE",
        "title": "Codigo Topologico de Correcao de Erros",
        "phi_c": phi_c,
        "architecture": {
            "type": "Color Code Hexagonal",
            "lattice": "UG(Z[omega])"
        },
        "parameters": {
            "physical_qubits": 625,
            "plaquettes": 500,
            "check_matrix_rank": 153,
            "logical_qubits": 2,
            "distance_d": 17,
            "correctable_errors_t": 8,
            "threshold_p_th": "10%"
        },
        "description": "Distancia d=17 (17 erros fisicos consecutivos para corromper um qubit logico). Corrige 8 erros bit-flip e 8 phase-flip simultaneamente.",
        "architect": "Rafael Oliveira",
        "status": "CANONIZADO"
    }

    json_str = json.dumps(report_data, sort_keys=True)

    # Calculate SHA3-256 seal
    hasher = hashlib.sha3_256()
    hasher.update(json_str.encode("utf-8"))
    seal = hasher.hexdigest()

    report_data["seal"] = seal
    final_json = json.dumps(report_data, indent=2, sort_keys=True)

    # Write to a secure temporary file
    fd, temp_path = tempfile.mkstemp(suffix=".json", prefix="arkhe_429_")
    with os.fdopen(fd, "w") as f:
        f.write(final_json)

    print("Relatorio gerado em: " + temp_path)
    print("Selo SHA3-256: " + seal)

    return temp_path, report_data

if __name__ == "__main__":
    generate_report()
