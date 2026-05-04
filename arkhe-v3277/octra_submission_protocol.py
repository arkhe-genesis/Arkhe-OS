import json
import hashlib
import os

def run_octra():
    import os
    print("⚛️ Fase 3: Registro OCTRA")

    proof_path = os.path.join(os.path.dirname(__file__), 'results', 'production', 'proof.json')
    registry_path = os.path.join(os.path.dirname(__file__), 'results', 'octra', 'octra_registry.json')
    with open(proof_path) as f:
        data = json.load(f)
    canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
    commitment = hashlib.sha256(canonical.encode()).hexdigest()

    # Verificar contra registro
    with open(registry_path) as f:
        registry = json.load(f)
    assert any(r['commitment'] == commitment for r in registry['registry'])
    print("Verificação do registro OCTRA bem-sucedida.")

if __name__ == "__main__":
    run_octra()
