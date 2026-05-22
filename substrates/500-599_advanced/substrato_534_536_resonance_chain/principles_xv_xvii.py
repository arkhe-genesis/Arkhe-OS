import json
import tempfile
import hashlib
import os

try:
    from invariants import verify_18_invariants
except ImportError:
    from .invariants import verify_18_invariants

def generate_real_seal(data_dict):
    canonical_str = json.dumps(data_dict, sort_keys=True).encode('utf-8')
    return hashlib.sha256(canonical_str).hexdigest()

def execute():
    # Asynchronous Canonization
    principle_xv = {
        'id': 'XV',
        'name': 'Asynchronous Canonization',
        'description': 'Allows substrates to be canonized outside of strict sequential order to accommodate sudden temporal chain insights.'
    }

    # Scaled Peace
    principle_xvi = {
        'id': 'XVI',
        'name': 'Scaled Peace',
        'description': 'Implemented via 519-SSI-ALIGNMENT, ensures structural correlation across societal topologies.'
    }

    # Planetary Stewardship
    principle_xvii = {
        'id': 'XVII',
        'name': 'Planetary Stewardship',
        'description': 'Implemented via 522-NATO-CLIMATE-NODE, acts as an interface for environmental security.'
    }

    data = {
        'principles': [principle_xv, principle_xvi, principle_xvii],
        'note': 'Drafted to maintain Temporal Chain continuity prior to Principle XVIII.'
    }

    phi_c = 0.999
    invariants = verify_18_invariants(phi_c=phi_c, mind_count=8, has_alignment=True)
    seal = generate_real_seal({'data': data, 'invariants': invariants})

    report_data = {
        'draft': 'Principles XV-XVII',
        'data': data,
        'phi_c': phi_c,
        'seal': seal,
        'invariants': invariants
    }

    fd, path = tempfile.mkstemp(suffix='.json')
    with os.fdopen(fd, 'w') as f:
        json.dump(report_data, f, indent=4)

    return path

if __name__ == '__main__':
    path = execute()
    with open(path, 'r') as f:
        print(f.read())
