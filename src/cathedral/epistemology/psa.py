import math
import hashlib
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional
import numpy as np

@dataclass(frozen=True)
class Claim:
    text: str
    id: int

@dataclass(frozen=True)
class Edge:
    src: int
    dst: int
    relation: str  # "entails", "contradicts", "references"

@dataclass
class SemanticGraph:
    claims: List[Claim]
    edges: List[Edge]
    domain: str = "general"

class PSA:
    """
    PSA (Predicted Safety Analysis) v2.1
    A deterministic epistemic defense system for measuring semantic coherence.
    """

    def __init__(self, alpha=0.35, beta=0.35, gamma=0.15, lamb=0.10, delta=0.25):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.lamb = lamb
        self.delta = delta

        # Critical domains with sensitivity weights (I6)
        self.critical_domains = {
            "governance": 0.95,
            "monetary": 0.92,
            "security": 0.98,
            "healthcare": 0.90,
            "infrastructure": 0.85,
            "epistemology": 0.88,
            "general": 0.15
        }

    def connectivity(self, G: SemanticGraph) -> float:
        """S-Component: Structural Connectivity."""
        n = len(G.claims)
        m = len(G.edges)
        if n <= 1:
            return 0.0
        return min(1.0, (2 * m) / (n * (n - 1)))

    def consistency(self, G: SemanticGraph) -> float:
        """C-Component: Semantic Consistency."""
        n = len(G.claims)
        if n == 0:
            return 0.0
        contradictions = sum(1 for e in G.edges if e.relation == "contradicts")
        return max(0.0, 1.0 - (contradictions / n))

    def informational_triviality(self, G: SemanticGraph) -> float:
        """I-Component: Informational Non-triviality."""
        # Simplified: ratio of distinct relations to total edges
        if not G.edges:
            return 0.0
        distinct_relations = len(set(e.relation for e in G.edges))
        return distinct_relations / 3.0 # Relative to {entails, contradicts, references}

    def predictability_penalty(self, G: SemanticGraph) -> float:
        """P-Component: Predictability Penalty (Anti-Gaming)."""
        if not G.edges:
            return 0.0

        rel_types = [e.relation for e in G.edges]
        counts = {r: rel_types.count(r) for r in set(rel_types)}
        total = len(rel_types)

        entropy = 0.0
        for r in counts:
            p = counts[r] / total
            entropy -= p * math.log(p + 1e-9)

        # Max entropy for 3 types is log(3)
        max_entropy = math.log(3 + 1e-9)
        normalized_entropy = entropy / max_entropy

        # High entropy -> low predictability penalty
        return max(0.0, 1.0 - normalized_entropy)

    def epistemic_relevance(self, G: SemanticGraph) -> float:
        """E-Component: Epistemic Relevance."""
        return self.critical_domains.get(G.domain, 0.15)

    def calculate_score(self, G: SemanticGraph) -> Dict[str, float]:
        """Calculates the full Coherence Score with all components."""
        S = self.connectivity(G)
        C = self.consistency(G)
        I = self.informational_triviality(G)
        P = self.predictability_penalty(G)
        E = self.epistemic_relevance(G)

        # PSA v2.1 Formula: alpha*S + beta*C + gamma*I - lambda*P + delta*E
        raw_score = (self.alpha * S +
                     self.beta * C +
                     self.gamma * I -
                     self.lamb * P +
                     self.delta * E)

        score = max(0.0, min(1.0, raw_score))

        return {
            "score": score,
            "S": S,
            "C": C,
            "I": I,
            "P": P,
            "E": E,
            "hash": self.generate_hash(G)
        }

    def generate_hash(self, G: SemanticGraph) -> str:
        """I5: Canonical Hash for total auditability."""
        claims_sorted = sorted(G.claims, key=lambda x: x.id)
        edges_sorted = sorted(G.edges, key=lambda x: (x.src, x.dst, x.relation))

        payload = "|".join([f"{c.id}:{c.text}" for c in claims_sorted])
        payload += "||"
        payload += "|".join([f"{e.src}->{e.dst}:{e.relation}" for e in edges_sorted])
        payload += f"||domain:{G.domain}"

        return hashlib.sha256(payload.encode()).hexdigest()

class DiamondPipeline:
    """
    Diamond Pipeline: Multi-stage hallucination reduction.
    Diverge (Generate) -> Filter (PSA) -> Converge (Select)
    """
    def __init__(self, psa: PSA):
        self.psa = psa

    def run(self, prompt: str, iterations: int = 3) -> Dict:
        # 1. Divergence: Generate candidates
        candidates = self._diverge(prompt, iterations)

        # 2. Filtering: Evaluate via PSA
        evaluated = []
        for text in candidates:
            G = self._parse_to_graph(text)
            res = self.psa.calculate_score(G)
            evaluated.append({"text": text, "score": res["score"], "res": res})

        # 3. Convergence: Select best
        evaluated.sort(key=lambda x: x["score"], reverse=True)
        best = evaluated[0]

        return {
            "best": best,
            "all_evaluated": evaluated
        }

    def _diverge(self, prompt: str, k: int) -> List[str]:
        # Simulated multi-agent generation
        # In production, this would call multiple LLMs or one LLM with different temperatures.
        variations = [
            prompt,
            f"{prompt} (with additional context on invariants)",
            f"{prompt} (optimized for structural coherence)",
            f"{prompt} (verbatim implementation of protocols)"
        ]
        return variations[:k]

    def _parse_to_graph(self, text: str) -> SemanticGraph:
        # Simulated parser: converts text to claims/edges
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        claims = [Claim(s, i) for i, s in enumerate(sentences)]

        edges = []
        for i in range(len(claims) - 1):
            # Simulate an entailment chain
            edges.append(Edge(i, i+1, "entails"))

        # If text is too short or weird, simulate a contradiction
        if "additional context" in text:
            edges.append(Edge(0, len(claims)-1, "references"))
        elif "structural" in text:
            # Good structure
            pass
        elif "verbatim" in text:
            # High density
            if len(claims) > 1:
                edges.append(Edge(0, 1, "entails"))

        return SemanticGraph(claims, edges)

if __name__ == "__main__":
    # Quick Test
    claims = [Claim("Arkhe is awake.", 0), Claim("The Cathedral is coherent.", 1)]
    edges = [Edge(0, 1, "entails")]
    G = SemanticGraph(claims, edges, domain="epistemology")

    psa = PSA()
    result = psa.calculate_score(G)
    print(f"PSA Result: {result}")
