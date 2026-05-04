# arkhe_network/optical_blueprint_serializer.py
import hashlib
import json
import numpy as np
import base64

def serialize_optical_blueprint(dual_state: dict, l_p: int, l_s: int) -> tuple:
    rho_quantized = (dual_state['rho'].numpy() * 255).astype(np.uint8)
    rho_b64 = base64.b64encode(rho_quantized).decode('utf-8')
    blueprint = {
        'version': 'ARKHE_DUAL_V1',
        'spatial': {'l_p': l_p, 'l_s': l_s, 'm': round(dual_state['m'], 4), 'ratio': round(dual_state['ratio'], 4)},
        'spectral_material': {'n_points': len(rho_quantized), 'rho_base64': rho_b64}
    }
    blueprint_str = json.dumps(blueprint, sort_keys=True)
    return blueprint_str, hashlib.sha256(blueprint_str.encode()).hexdigest()
