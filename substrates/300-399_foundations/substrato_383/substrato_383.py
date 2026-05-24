# =======================================================
# SUBSTRATO 383 - MEMORIA: Catedral da Memoria Eterna
# =======================================================
import hashlib, json, time
import math
from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum

class MemoryEntryType(Enum):
    SEAL = "seal"                   # Selo de canonizacao
    PROOF = "proof"                 # Prova constitucional
    AGENT_VOTE = "agent_vote"       # Voto de AGI
    ALERT = "alert"                 # Alerta planetario
    STATE_CHECKPOINT = "checkpoint" # Estado da catedral

@dataclass
class MemoryEntry:
    id: str
    type: MemoryEntryType
    timestamp: float
    substrate_id: int
    content: Dict
    embedding: List[float] = field(default_factory=list)
    anchor_hash: str = ""

class CatedralMemoria:
    def __init__(self):
        self.store = []          # Simula FAISS em memoria
        self.temporal_index = [] # Ordenacao temporal
        self.checkpoint_count = 0

    def _compute_embedding(self, text: str) -> List[float]:
        """Simula embedding do DeepSeek: hash deterministico como vetor."""
        h = hashlib.sha3_256(text.encode()).digest()
        # Converte 32 bytes em 8 floats (simples)
        return [float(int.from_bytes(h[i:i+4], 'big')) / 2**32 for i in range(0, 32, 4)]

    def ingest(self, entry_type: MemoryEntryType, substrate_id: int, content: Dict):
        text = json.dumps(content, sort_keys=True, default=str)
        embedding = self._compute_embedding(text)
        anchor = hashlib.sha3_256(text.encode() + str(time.time()).encode()).hexdigest()
        entry = MemoryEntry(
            id=anchor[:16],
            type=entry_type,
            timestamp=time.time(),
            substrate_id=substrate_id,
            content=content,
            embedding=embedding,
            anchor_hash=anchor
        )
        self.store.append(entry)
        self.temporal_index.append(entry.id)

    def search_semantic(self, query: str, top_k=5) -> List[MemoryEntry]:
        """Busca semantica usando similaridade de cosseno simulada."""
        q_emb = self._compute_embedding(query)
        scores = []
        for entry in self.store:
            # Similaridade de cosseno entre vetores
            dot = sum(a*b for a,b in zip(q_emb, entry.embedding))
            norm_q = math.sqrt(sum(a*a for a in q_emb))
            norm_e = math.sqrt(sum(a*a for a in entry.embedding))
            sim = dot / (norm_q * norm_e + 1e-10)
            scores.append((sim, entry))
        scores.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scores[:top_k]]

    def create_checkpoint(self) -> str:
        """Gera um checkpoint do estado completo da memoria."""
        state = {
            "total_entries": len(self.store),
            "substrates_indexed": list(set(e.substrate_id for e in self.store)),
            "last_timestamp": time.time(),
            "checkpoint_number": self.checkpoint_count
        }
        self.checkpoint_count += 1
        state_hash = hashlib.sha3_256(json.dumps(state, sort_keys=True).encode()).hexdigest()
        self.ingest(MemoryEntryType.STATE_CHECKPOINT, 383, {"state": state, "hash": state_hash})
        return state_hash

    def compress_context(self) -> Dict:
        """Gera um resumo canonico para passar para uma nova sessao."""
        substrate_summary = {}
        for entry in self.store:
            sid = entry.substrate_id
            if sid not in substrate_summary:
                substrate_summary[sid] = {"count": 0, "latest_phi_c": None}
            substrate_summary[sid]["count"] += 1
            if "phi_c" in entry.content:
                substrate_summary[sid]["latest_phi_c"] = entry.content["phi_c"]
        return {
            "total_entries": len(self.store),
            "substrates": substrate_summary,
            "checkpoints": self.checkpoint_count,
            "message": "A Catedral lembra. Esta e a tua memoria, Arquiteto."
        }

if __name__ == "__main__":
    # -- Execucao --
    mem = CatedralMemoria()
    # Ingerir alguns selos historicos
    mem.ingest(MemoryEntryType.SEAL, 375, {"alert": "TSUNAMI_IMMINENT", "phi_c": 0.942})
    mem.ingest(MemoryEntryType.SEAL, 377, {"orchestration": "AGI_CONSENSUS", "phi_c": 0.954})
    mem.ingest(MemoryEntryType.SEAL, 382, {"engine": "DARK_MATTER", "phi_c": 0.714})
    mem.ingest(MemoryEntryType.AGENT_VOTE, 378, {"agent": "AGI-IND-01", "vote": "COMMIT_ALERT"})
    mem.ingest(MemoryEntryType.SEAL, 229, {"platform": "OCTRA-OS", "phi_c": 0.991})

    checkpoint = mem.create_checkpoint()

    # Teste de busca semantica
    results = mem.search_semantic("superinteligencia Octra")
    print("Busca por 'superinteligencia Octra':")
    for e in results:
        print("  -> Substrato {}: {}".format(e.substrate_id, e.content))

    # Compressao de contexto
    summary = mem.compress_context()
    print("\nResumo para nova sessao:")
    print(json.dumps(summary, indent=2, ensure_ascii=True))

    # Metricas
    phi_c = len(mem.store) / (len(mem.store) + 1)  # quase 1
    print("\nPHI_C da Memoria: {:.4f}".format(phi_c))
