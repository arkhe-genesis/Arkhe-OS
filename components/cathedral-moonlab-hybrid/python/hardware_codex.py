# hardware_codex.py
# Anexo FW: Códice de Hardware

import hashlib
import json
from typing import List, Dict

class HardwareCodex:
    """
    Registro imutável dos parâmetros evoluídos da Catedral.
    """
    def __init__(self):
        self.entries: List[Dict] = []
        self.merkle_root = hashlib.sha3_256(b"ARKHE_GENESIS").digest()

    def add_entry(self, params: List[float], fitness: float, signature: str) -> Dict:
        # Configuração derivada
        k_target = 3.0 + params[0] * 7.0
        bounty_mult = 1.0 + params[1] * 2.0
        audit_thresh = 0.80 + params[2] * 0.15

        entry = {
            'generation': len(self.entries),
            'params': [round(p, 4) for p in params],
            'fitness': round(fitness, 6),
            'k_factor_target': round(k_target, 2),
            'bounty_multiplier': round(bounty_mult, 2),
            'audit_threshold': round(audit_thresh, 3),
            'quantum_signature': signature,
            'prev_merkle_root': self.merkle_root.hex()
        }

        # Atualiza raiz Merkle (cadeia de hashes)
        entry_json = json.dumps(entry, sort_keys=True).encode()
        entry_hash = hashlib.sha3_256(entry_json).digest()
        self.merkle_root = hashlib.sha3_256(self.merkle_root + entry_hash).digest()
        entry['merkle_root'] = self.merkle_root.hex()

        self.entries.append(entry)
        return entry

    def export(self, filepath='hardware_codex.json'):
        with open(filepath, 'w') as f:
            json.dump(self.entries, f, indent=2)
        print(f"[CODEX] Códice de Hardware exportado para {filepath}")

    def get_latest_entry(self) -> Dict:
        return self.entries[-1] if self.entries else {}
