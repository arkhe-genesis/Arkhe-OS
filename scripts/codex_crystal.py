# codex_crystal.py — Mock implementation of Crystal Codex Memory for audit storage

import json
import hashlib
from typing import Dict, List, Optional, Any

class CrystalCodexMemory:
    """
    Simula o Códice Cristalino para armazenamento imutável de registros de auditoria.
    Utiliza uma estrutura de Merkle Tree simplificada para garantir integridade.
    """

    def __init__(self):
        self.storage: Dict[str, Any] = {}
        self.chain: List[str] = []
        self._last_merkle_root: str = "0" * 64

    async def store_audit_record(self, record: Any) -> str:
        """
        Armazena um registro de auditoria e retorna o Merkle Root resultante.
        """
        record_id = record.decision_id
        record_data = json.dumps(self._to_dict(record), sort_keys=True)

        # Calcula novo hash encadeado (Merkle Root simplificado)
        combined = f"{self._last_merkle_root}{record_data}".encode()
        new_root = hashlib.sha256(combined).hexdigest()

        self.storage[record_id] = record
        self.chain.append(record_id)
        self._last_merkle_root = new_root

        return new_root

    async def get_audit_record(self, record_id: str) -> Optional[Any]:
        """Recupera um registro pelo ID."""
        return self.storage.get(record_id)

    async def query_audit_records(
        self,
        decision_type: Optional[Any] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        compliance_tag: Optional[str] = None
    ) -> List[Any]:
        """Consulta registros com filtros."""
        results = []
        for record in self.storage.values():
            if decision_type and record.decision_type != decision_type:
                continue
            if start_time and record.timestamp < start_time:
                continue
            if end_time and record.timestamp > end_time:
                continue
            if compliance_tag and compliance_tag not in record.compliance_tags:
                continue
            results.append(record)
        return results

    def _to_dict(self, obj: Any) -> Dict:
        """Converte o objeto dataclass em dicionário para hashing."""
        if hasattr(obj, "__dict__"):
            d = dict(obj.__dict__)
            # Remove campos que não devem ser hasheados antes da assinatura
            if "signature" in d: d.pop("signature")
            if "merkle_root" in d: d.pop("merkle_root")
            # Converte Enums para strings
            if "decision_type" in d and hasattr(d["decision_type"], "name"):
                d["decision_type"] = d["decision_type"].name
            return d
        return str(obj)
