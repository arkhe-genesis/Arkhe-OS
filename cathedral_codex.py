# cathedral_codex.py — Mock do Códice Cristalino

import logging
from typing import Dict, Any, Optional

class CrystalCodex:
    """Mock do Códice Cristalino para testes de caos."""

    def __init__(self):
        self.artifacts: Dict[str, Dict[str, Any]] = {}
        self.corrupted = False

    async def store_artifact(self, artifact_id: str, content_hash: str, metadata: Dict[str, Any]):
        logging.info(f"[Codex] Armazenando artefato: {artifact_id}")
        self.artifacts[artifact_id] = {
            "hash": content_hash,
            "metadata": metadata
        }

    async def get_artifact(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        return self.artifacts.get(artifact_id)

    def simulate_corruption(self, enabled: bool):
        self.corrupted = enabled
        if enabled:
            logging.warning("[Codex] Corrupção de Merkle Tree simulada!")

    def verify_integrity(self) -> bool:
        return not self.corrupted
