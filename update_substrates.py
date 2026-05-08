import json

with open('.claude/SUBSTRATES.json', 'r') as f:
    data = json.load(f)

new_substrates = [
    {
        "id": 329.1,
        "name": "Homomorphic Zero-Trust Runtime",
        "status": "active",
        "location": "arkhe_os/crypto/fhe/"
    },
    {
        "id": 330.2,
        "name": "Qiskit Quantum Entanglement Channel",
        "status": "active",
        "location": "arkhe_os/federation_protocol/quantum/"
    },
    {
        "id": 324.1,
        "name": "Advanced GLSL Shader for WORMHOLE.agi",
        "status": "active",
        "location": "agi/system32/wormhole/shaders/"
    }
]

# Avoid adding duplicates
existing_ids = {s['id'] for s in data['substrates']}
for sub in new_substrates:
    if sub['id'] not in existing_ids:
        data['substrates'].append(sub)

# Sort by id
data['substrates'].sort(key=lambda x: float(x['id']))

with open('.claude/SUBSTRATES.json', 'w') as f:
    json.dump(data, f, indent=2)
