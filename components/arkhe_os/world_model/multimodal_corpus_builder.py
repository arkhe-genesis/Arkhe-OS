import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np

@dataclass
class MultimodalSample:
    """Amostra alinhada para treinamento do World Model."""
    sample_id: str
    # Múltiplas representações do mesmo conceito
    code_text: Optional[str] = None          # Código fonte
    spec_text: Optional[str] = None          # OpenAPI/GraphQL/Protobuf
    doc_text: Optional[str] = None           # Documentação
    lfir_graph: Optional[Dict] = None        # Grafo LFIR serializado
    coherence_label: Optional[float] = None  # Φ_C real se disponível
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        # Hash canônico para deduplicação
        self.sample_id = self.sample_id or self._compute_hash()

    def _compute_hash(self) -> str:
        """Hash baseado em conteúdo para identificação única."""
        content = f"{self.code_text}{self.spec_text}{self.doc_text}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

class MultimodalCorpusBuilder:
    """Constrói corpus alinhado para pré-treinamento do World Model."""

    def __init__(self, output_dir: str, min_alignment_score: float = 0.7):
        self.output_dir = Path(output_dir)
        self.min_alignment_score = min_alignment_score
        self.samples: List[MultimodalSample] = []

    def add_from_code_repo(self, repo_path: str, lfir_cache: Optional[str] = None):
        """Extrai amostras de repositório de código com LFIRs cacheados."""
        # Implementação simplificada
        pass

    def add_from_api_specs(self, specs_dir: str, code_mapping: Dict[str, str]):
        """Alinha specs de API com implementações de código correspondentes."""
        # Matching heurístico por nome de endpoint + hashing
        pass

    def add_from_blockchain_data(self, blockchain: str, blocks_range: Tuple[int, int]):
        """Incorpora dados de blockchain (Bitcoin, Lightning) como exemplos de consenso."""
        # Parsing de blocos → LFIR → amostras multimodais
        pass

    def align_modalities(self) -> List[MultimodalSample]:
        """Alinha representações multimodais via embedding similarity."""
        aligned = []
        for sample in self.samples:
            if self._compute_alignment_score(sample) >= self.min_alignment_score:
                aligned.append(sample)
        return aligned

    def _compute_alignment_score(self, sample: MultimodalSample) -> float:
        """Score de alinhamento entre modalidades (simplificado)."""
        scores = []
        if sample.code_text and sample.spec_text:
            scores.append(self._text_similarity(sample.code_text, sample.spec_text))
        if sample.lfir_graph and sample.code_text:
            scores.append(self._graph_code_consistency(sample.lfir_graph, sample.code_text))
        return np.mean(scores) if scores else 0.0

    def _text_similarity(self, text_a: str, text_b: str) -> float:
        """Similaridade de texto via TF-IDF + cosseno (placeholder)."""
        # Em produção: usar embeddings do próprio World Model em treinamento
        return 0.8  # Placeholder

    def _graph_code_consistency(self, graph: Dict, code: str) -> float:
        """Verifica consistência entre grafo LFIR e código fonte."""
        # Verificar se nós do grafo correspondem a elementos do código
        return 0.9  # Placeholder

    def save(self, filename: str = "multimodal_corpus.jsonl"):
        """Salva corpus em formato JSONL para treinamento."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(self.output_dir / filename, 'w') as f:
            for sample in self.samples:
                f.write(json.dumps(sample.__dict__) + '\n')
