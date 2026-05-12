#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arkhein/hypergraph.py — Hypergrafo Semântico com Coerência φ-Ótima
Substrato Arkhein 0.1.0: RAG Estrutural para ConRAG v4.0
"""

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import numpy as np

# Constante áurea para coerência φ-ótima
PHI = (1 + math.sqrt(5)) / 2  # ~1.618
PHI_INV = 1 / PHI  # ~0.618 — limiar mínimo de coerência

class EdgeType(Enum):
    """Tipos de relação semântica no hypergrafo."""
    IS_A = "is_a"                    # Hierarquia: Dog IS_A Animal
    PART_OF = "part_of"              # Composição: Wheel PART_OF Car
    CAUSES = "causes"                # Causalidade: Virus CAUSES Disease
    CORRELATES = "correlates"        # Correlação estatística
    CONTRADICTS = "contradicts"      # Contradição lógica
    SUPPORTS = "supports"            # Evidência de suporte
    DERIVED_FROM = "derived_from"    # Derivação lógica
    TEMPORAL_BEFORE = "temporal_before"  # Ordem temporal

@dataclass
class SemanticNode:
    """Nó conceitual no hypergrafo Arkhein."""
    id: str                          # Hash canônico do conceito
    label: str                       # Nome legível
    domain: str                      # Domínio: "medicina", "direito", etc.
    definitions: List[str]           # Definições canônicas
    sources: List[Dict]              # Fontes com hashes e timestamps
    aliases: List[str] = field(default_factory=list)  # Sinônimos
    embeddings: Optional[np.ndarray] = None  # Embedding semântico
    metadata: Dict = field(default_factory=dict)

    def canonical_hash(self) -> str:
        """Hash SHA3-256 canônico do nó."""
        data = json.dumps({
            'label': self.label,
            'domain': self.domain,
            'definitions': sorted(self.definitions),
            'sources': sorted(s.get('hash', '') for s in self.sources)
        }, sort_keys=True)
        return hashlib.sha3_256(data.encode()).hexdigest()

@dataclass
class SemanticEdge:
    """Aresta semântica entre nós."""
    source: str                      # ID do nó fonte
    target: str                      # ID do nó alvo
    edge_type: EdgeType
    strength: float                  # Força da relação [0, 1]
    evidence: List[Dict]             # Evidências que suportam a relação
    temporal_validity: Optional[Tuple[float, float]] = None  # (start, end) em timestamp

    def coherence_score(self) -> float:
        """Calcula coerência da aresta baseada em evidência e força."""
        if not self.evidence:
            return 0.0
        # Coerência = força × qualidade_média_evidência
        evidence_quality = np.mean([e.get('quality', 0.5) for e in self.evidence])
        return self.strength * evidence_quality

class ArkheinHypergraph:
    """
    Hypergrafo semântico para recuperação estrutural de fatos.
    Características:
    - Coerência φ-ótima: apenas arestas com score ≥ φ⁻¹ (~0.618) são mantidas
    - Busca estrutural: ranking considera profundidade, força, cobertura
    - Invariantes I1-I5 aplicadas em todas as operações
    """

    def __init__(self, coherence_threshold: float = PHI_INV, embedding_dim: int = 768):
        self.nodes: Dict[str, SemanticNode] = {}
        self.edges: Dict[Tuple[str, str, EdgeType], SemanticEdge] = {}
        self.coherence_threshold = coherence_threshold

        # Inicializa o índice FAISS (Flat L2) para busca semântica
        try:
            import faiss
            self._index_embeddings = faiss.IndexFlatL2(embedding_dim)
            self._id_map: Dict[int, str] = {}
            self._next_faiss_id = 0
            self.embedding_dim = embedding_dim
        except ImportError:
            self._index_embeddings = None
            self.embedding_dim = None

    def add_node(self, node: SemanticNode) -> bool:
        """Adiciona nó ao hypergrafo."""
        # Invariante I1: Não-violação física (verificação básica)
        if not self._check_physical_laws(node):
            return False
        # Invariante I2: Falsificabilidade
        if not self._check_falsifiability(node):
            return False

        node_id = node.canonical_hash()
        self.nodes[node_id] = node

        # Adicionar ao índice FAISS se o embedding existir
        if node.embeddings is not None and self._index_embeddings is not None:
            # Garantir formato float32 para o faiss
            vec = np.array([node.embeddings], dtype=np.float32)
            if vec.shape[1] == self.embedding_dim:
                self._index_embeddings.add(vec)
                self._id_map[self._next_faiss_id] = node_id
                self._next_faiss_id += 1

        return True

    def add_edge(self, edge: SemanticEdge) -> bool:
        """Adiciona aresta apenas se coerência ≥ φ⁻¹."""
        coherence = edge.coherence_score()
        if coherence < self.coherence_threshold:
            return False  # Rejeitada por incoerência
        # Invariante I4: Verificação em tempo polinomial
        if not self._check_polynomial_complexity(edge):
            return False
        key = (edge.source, edge.target, edge.edge_type)
        self.edges[key] = edge
        return True

    def retrieve(self, query: str, domain: str,
                 max_results: int = 20) -> List[Dict]:
        """
        Recupera fatos estruturalmente relevantes para uma query.
        Pipeline:
        1. Decomposição semântica da query em conceitos
        2. Busca de nós relacionados no hypergrafo
        3. Ranking por relevância estrutural (não apenas similaridade)
        4. Filtragem por invariantes I1-I5
        """
        # 1. Decomposição semântica
        concepts = self._decompose_query(query, domain)

        # 2. Busca de candidatos
        candidates = []
        for concept in concepts:
            # Busca exata por alias
            exact_matches = self._find_by_alias(concept, domain)
            candidates.extend(exact_matches)
            # Busca semântica por embedding (se disponível)
            if self._index_embeddings is not None:
                semantic_matches = self._semantic_search(concept, top_k=10)
                candidates.extend(semantic_matches)

        # 3. Expansão estrutural: vizinhos coerentes
        expanded = []
        for node_id in set(c['id'] for c in candidates):
            neighbors = self._coherent_neighbors(node_id, max_depth=2)
            expanded.extend(neighbors)

        # 4. Ranking estrutural
        ranked = self._structural_ranking(expanded, query, domain)

        # 5. Aplicar invariantes finais
        verified = [f for f in ranked if self._apply_invariants(f, domain)]

        return verified[:max_results]

    def _decompose_query(self, query: str, domain: str) -> List[str]:
        """Decompõe query em conceitos canônicos."""
        # Em produção: usar NLP + domínio específico
        # Simplificação: tokenização + lematização básica
        import re
        tokens = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_-]*\b', query.lower())
        # Filtrar stopwords do domínio
        stopwords = self._get_domain_stopwords(domain)
        return [t for t in tokens if t not in stopwords and len(t) > 2]

    def _find_by_alias(self, concept: str, domain: str) -> List[Dict]:
        """Busca exata por conceito ou alias."""
        results = []
        for node in self.nodes.values():
            if node.domain != domain:
                continue
            if concept == node.label.lower() or concept in [a.lower() for a in node.aliases]:
                results.append({
                    'id': node.id,
                    'label': node.label,
                    'definitions': node.definitions,
                    'sources': node.sources,
                    'relevance': 1.0
                })
        return results

    def _coherent_neighbors(self, node_id: str, max_depth: int) -> List[Dict]:
        """Retorna vizinhos com coerência ≥ φ⁻¹ até profundidade max_depth."""
        neighbors = []
        visited = {node_id}
        queue = [(node_id, 0)]

        while queue:
            current_id, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            # Buscar arestas incidentes
            for (src, tgt, etype), edge in self.edges.items():
                if src == current_id and tgt not in visited:
                    if edge.coherence_score() >= self.coherence_threshold:
                        neighbor = self.nodes.get(tgt)
                        if neighbor:
                            neighbors.append({
                                'id': tgt,
                                'label': neighbor.label,
                                'relation': etype.value,
                                'strength': edge.strength,
                                'coherence': edge.coherence_score(),
                                'evidence': edge.evidence
                            })
                            visited.add(tgt)
                            queue.append((tgt, depth + 1))
                elif tgt == current_id and src not in visited:
                    if edge.coherence_score() >= self.coherence_threshold:
                        neighbor = self.nodes.get(src)
                        if neighbor:
                            neighbors.append({
                                'id': src,
                                'label': neighbor.label,
                                'relation': f"inverse_{etype.value}",
                                'strength': edge.strength,
                                'coherence': edge.coherence_score(),
                                'evidence': edge.evidence
                            })
                            visited.add(src)
                            queue.append((src, depth + 1))
        return neighbors

    def _structural_ranking(self, candidates: List[Dict],
                           query: str, domain: str) -> List[Dict]:
        """Ranking por relevância estrutural (não apenas similaridade)."""
        scored = []
        for candidate in candidates:
            # Fatores de ranking:
            # 1. Cobertura de conceitos da query
            coverage = self._concept_coverage(candidate, query)
            # 2. Força das relações estruturais
            structural_strength = candidate.get('strength', 0.5)
            # 3. Coerência da aresta
            coherence = candidate.get('coherence', 0.618)
            # 4. Qualidade das fontes
            source_quality = np.mean([s.get('quality', 0.5)
                                     for s in candidate.get('evidence', [])] or [0.5])
            # 5. Recência temporal (se aplicável)
            recency = self._temporal_recency(candidate)

            # Score combinado (ponderado)
            score = (
                0.30 * coverage +
                0.25 * structural_strength +
                0.20 * coherence +
                0.15 * source_quality +
                0.10 * recency
            )
            scored.append({**candidate, 'score': score})

        # Ordenar por score decrescente
        return sorted(scored, key=lambda x: x['score'], reverse=True)

    def _apply_invariants(self, fact: Dict, domain: str) -> bool:
        """Aplica invariantes I1-I5 para filtragem final."""
        # I1: Não-violação física
        if not self._check_physical_laws_fact(fact):
            return False
        # I2: Falsificabilidade
        if not self._check_falsifiability_fact(fact):
            return False
        # I3: Independência de substrato (sempre true para fatos)
        # I4: Complexidade polinomial (já verificada na construção)
        # I5: Autonomia local (sempre true para fatos recuperados)
        return True

    # Métodos auxiliares de verificação de invariantes
    def _check_physical_laws(self, node: SemanticNode) -> bool:
        """I1: Verifica se definições violam leis físicas conhecidas."""
        # Simplificação: lista negra de afirmações fisicamente impossíveis
        impossible = [
            "perpetual motion", "faster than light", "negative mass",
            "violate conservation of energy", "create energy from nothing"
        ]
        text = " ".join(node.definitions).lower()
        return not any(phrase in text for phrase in impossible)

    def _check_falsifiability(self, node: SemanticNode) -> bool:
        """I2: Verifica se conceito é falsificável em princípio."""
        # Simplificação: conceitos não-testáveis são rejeitados
        non_falsifiable = ["metaphysical", "supernatural", "unknowable"]
        text = " ".join(node.definitions).lower()
        return not any(term in text for term in non_falsifiable)

    def _check_polynomial_complexity(self, edge: SemanticEdge) -> bool:
        """I4: Verifica se verificação da aresta é em tempo polinomial."""
        # Simplificação: arestas com evidência excessivamente complexa são rejeitadas
        return len(str(edge.evidence)) < 10000  # Limite arbitrário

    def _check_physical_laws_fact(self, fact: Dict) -> bool:
        """I1 aplicado a fato recuperado."""
        text = " ".join(fact.get('definitions', [])).lower()
        impossible = ["perpetual motion", "faster than light"]
        return not any(phrase in text for phrase in impossible)

    def _check_falsifiability_fact(self, fact: Dict) -> bool:
        """I2 aplicado a fato recuperado."""
        text = " ".join(fact.get('definitions', [])).lower()
        non_falsifiable = ["metaphysical", "supernatural"]
        return not any(term in text for term in non_falsifiable)

    def _concept_coverage(self, fact: Dict, query: str) -> float:
        """Calcula fração de conceitos da query cobertos pelo fato."""
        query_concepts = set(self._decompose_query(query, fact.get('domain', '')))
        fact_concepts = set(fact.get('label', '').lower().split())
        if not query_concepts:
            return 0.0
        return len(query_concepts & fact_concepts) / len(query_concepts)

    def _temporal_recency(self, fact: Dict) -> float:
        """Calcula recência temporal do fato (0-1)."""
        # Simplificação: fatos com timestamp recente têm score maior
        sources = fact.get('sources', [])
        if not sources:
            return 0.5
        timestamps = [s.get('timestamp', 0) for s in sources if 'timestamp' in s]
        if not timestamps:
            return 0.5
        latest = max(timestamps)
        now = time.time()
        # Decaimento exponencial: 1 ano = fator 0.9
        age_years = (now - latest) / (365.25 * 24 * 3600)
        return max(0.0, min(1.0, 0.9 ** age_years))

    def _get_domain_stopwords(self, domain: str) -> Set[str]:
        """Stopwords específicas por domínio."""
        common = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "being"}
        domain_specific = {
            "medicina": {"patient", "subject", "case", "study", "group"},
            "direito": {"case", "court", "party", "defendant", "plaintiff"},
            "ciencia": {"experiment", "result", "data", "method", "analysis"},
        }
        return common | domain_specific.get(domain, set())

    def _semantic_search(self, concept: str, top_k: int) -> List[Dict]:
        """Busca semântica por embedding no FAISS."""
        if self._index_embeddings is None or self._index_embeddings.ntotal == 0:
            return []

        # Em produção: usar um modelo de embedding real (como sentence-transformers)
        # para converter o texto 'concept' em um vetor.
        # Aqui, simulamos um embedding (vetor aleatório normalizado)
        try:
            import faiss
            mock_embedding = np.random.randn(1, self.embedding_dim).astype(np.float32)
            faiss.normalize_L2(mock_embedding)

            distances, indices = self._index_embeddings.search(mock_embedding, top_k)

            results = []
            for i, idx in enumerate(indices[0]):
                if idx != -1 and idx in self._id_map:
                    node_id = self._id_map[idx]
                    node = self.nodes.get(node_id)
                    if node:
                        results.append({
                            'id': node.id,
                            'label': node.label,
                            'definitions': node.definitions,
                            'sources': node.sources,
                            'relevance': float(1.0 / (1.0 + distances[0][i])) # Conversão de distância L2 para relevância
                        })
            return results
        except Exception:
            return []
