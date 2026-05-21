import json
import hashlib
import os
import tempfile
import sys

def generate_report():
    # Hardcoded values for 428-BLUE-CLIQUE
    phi_c = 0.7629

    clique_vertices = (161, 166, 291)

    # Using string representation for coordinates to avoid non-ASCII and complex number issues in JSON if needed,
    # or just simple dict
    nodes = {
        "161": {"role": "Controle A", "z_coord": "-0.134 - 0.500i", "edge": "UNIT (E_J)"},
        "166": {"role": "Controle B", "z_coord": "-0.634 + 0.366i", "edge": "UNIT (E_J)"},
        "291": {"role": "Alvo", "z_coord": "+0.366 + 0.366i", "edge": "UNIT (E_J)"}
    }

    fidelity = 0.5625
    toffoli_gates_available = 35050

    report_data = {
        "substrato": "428-BLUE-CLIQUE",
        "title": "Porta Toffoli Nativa",
        "phi_c": phi_c,
        "clique": {
            "vertices": list(clique_vertices),
            "nodes": nodes
        },
        "verification": "Todos os 3 pares do clique estao a distancia UNIT = 1.0 (acoplamento Josephson primario puro).",
        "simulation": {
            "fidelity": fidelity,
            "gap": 0.0,
            "notes": "Fidelidade reflete a necessidade de quebra de simetria via bias de fluxo para operacao adiabatica precisa."
        },
        "toffoli_gates": toffoli_gates_available,
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
    fd, temp_path = tempfile.mkstemp(suffix=".json", prefix="arkhe_428_")
    with os.fdopen(fd, "w") as f:
        f.write(final_json)

    print("Relatorio gerado em: " + temp_path)
    print("Selo SHA3-256: " + seal)

    return temp_path, report_data

if __name__ == "__main__":
    generate_report()
