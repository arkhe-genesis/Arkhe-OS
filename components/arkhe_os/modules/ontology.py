"""
Ontology Module: Concept Fusion & Mapping
"""
import uuid
from typing import Dict, List, Any

class OntologyModule:
    def __init__(self):
        self.local_concepts: Dict[str, Dict[str, Any]] = {}
        self.fused_concepts: Dict[str, Dict[str, Any]] = {}
        self.mappings: List[Dict] = []

    def load_concepts(self, concepts: Dict[str, Dict[str, Any]]):
        self.local_concepts.update(concepts)

    def fuse_with_remote(self, remote_concepts: Dict[str, Dict[str, Any]], threshold: float = 0.7) -> Dict[str, Dict[str, Any]]:
        fused = dict(self.local_concepts)
        for remote_id, remote in remote_concepts.items():
            sim = self._compute_similarity(remote)
            if sim >= threshold:
                fused_id = f"fused_{remote_id}_{uuid.uuid4().hex[:4]}"
                fused[fused_id] = {
                    **remote, "source": "remote", "fusion_similarity": sim
                }
            else:
                fused[remote_id] = {**remote, "source": "remote"}
        self.fused_concepts = fused
        return fused

    def _compute_similarity(self, concept: Dict) -> float:
        return min(1.0, (len(concept.get("tags", [])) * 0.3) + (0.7 if concept.get("type") else 0.0))
