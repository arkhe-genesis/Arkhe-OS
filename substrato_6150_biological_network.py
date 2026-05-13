import hashlib
import json
import time
import re
import zlib
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict
from pathlib import Path
from enum import Enum, auto

# ============================================================
# 1. GENE ONTOLOGY PARSING
# ============================================================

@dataclass
class GOTerm:
    id: str
    name: str
    namespace: str
    definition: str = ""
    is_a: List[str] = field(default_factory=list)
    part_of: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)

class GeneOntology:
    """Parser para arquivos OBO (Gene Ontology)"""

    def __init__(self, obo_path: Optional[Path] = None):
        self.terms: Dict[str, GOTerm] = {}
        if obo_path:
            self.load_obo(obo_path)

    def load_obo(self, path: Path):
        current = None
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line == '[Term]':
                    if current:
                        self.terms[current.id] = current
                    current = GOTerm(id='', name='', namespace='')
                elif line.startswith('id: '):
                    current.id = line[4:]
                elif line.startswith('name: '):
                    current.name = line[6:]
                elif line.startswith('namespace: '):
                    current.namespace = line[11:]
                elif line.startswith('def: '):
                    parts = line[5:].split('"')
                    current.definition = parts[1] if len(parts) > 1 else ""
                elif line.startswith('is_a: '):
                    current.is_a.append(line[6:].split('!')[0].strip())
                elif line.startswith('relationship: part_of '):
                    current.part_of.append(line.split('part_of ')[1].split('!')[0].strip())
                elif line.startswith('synonym: '):
                    parts = line[9:].split('"')
                    if len(parts) > 1:
                        current.synonyms.append(parts[1])
            if current:
                self.terms[current.id] = current

    def get_ancestors(self, go_id: str) -> Set[str]:
        """Conjunto de todos os termos ancestrais (is_a e part_of)"""
        ancestors = set()
        stack = [go_id]
        while stack:
            tid = stack.pop()
            if tid in self.terms:
                for parent in self.terms[tid].is_a + self.terms[tid].part_of:
                    if parent not in ancestors:
                        ancestors.add(parent)
                        stack.append(parent)
        return ancestors

    def get_descendants(self, go_id: str) -> Set[str]:
        """Conjunto de todos os termos descendentes"""
        descendants = set()
        stack = [go_id]
        while stack:
            tid = stack.pop()
            for term in self.terms.values():
                if tid in term.is_a or tid in term.part_of:
                    if term.id not in descendants:
                        descendants.add(term.id)
                        stack.append(term.id)
        return descendants

# ============================================================
# 2. REDES BIOLÓGICAS
# ============================================================

@dataclass
class NetworkNode:
    id: str
    name: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    go_annotations: Set[str] = field(default_factory=set)

@dataclass
class NetworkEdge:
    source: str
    target: str
    weight: float = 1.0
    type: str = "ppi"

class BiologicalNetwork:
    """Grafo de interações biológicas com anotações GO"""

    def __init__(self):
        self.nodes: Dict[str, NetworkNode] = {}
        self.edges: List[NetworkEdge] = []
        self.adj: Dict[str, List[Tuple[str, float]]] = defaultdict(list)

    def add_node(self, node_id: str, name: str = "", **kwargs):
        if node_id not in self.nodes:
            self.nodes[node_id] = NetworkNode(id=node_id, name=name or node_id, **kwargs)

    def add_edge(self, source: str, target: str, weight: float = 1.0, etype: str = "ppi"):
        self.add_node(source)
        self.add_node(target)
        self.edges.append(NetworkEdge(source, target, weight, etype))
        self.adj[source].append((target, weight))
        self.adj[target].append((source, weight))

    @classmethod
    def from_ppi_file(cls, path: Path) -> 'BiologicalNetwork':
        """Carrega rede a partir de arquivo SIF ou tabular (ex: STRING)"""
        net = cls()
        with open(path, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    continue
                parts = line.strip().split()
                if len(parts) >= 3:
                    weight = float(parts[1]) if len(parts) > 3 else 1.0
                    net.add_edge(parts[0], parts[2], weight, parts[1] if len(parts) > 1 else "ppi")
        return net

    def propagate_go_annotations(self, go: GeneOntology, gene_to_go: Dict[str, List[str]]):
        """Anota cada nó com termos GO (usando gene_to_go mapping)"""
        for node_id, node in self.nodes.items():
            if node_id in gene_to_go:
                node.go_annotations = set(gene_to_go[node_id])

    def get_degree(self, node_id: str) -> int:
        return len(self.adj.get(node_id, []))

    def get_neighbors(self, node_id: str) -> List[str]:
        return [n for n, _ in self.adj.get(node_id, [])]

    def to_dict(self) -> Dict:
        return {
            "nodes": {nid: {"name": n.name, "go_annotations": list(n.go_annotations),
                           "attributes": n.attributes} for nid, n in self.nodes.items()},
            "edges": [{"source": e.source, "target": e.target, "weight": e.weight, "type": e.type}
                      for e in self.edges],
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'BiologicalNetwork':
        net = cls()
        for nid, ndata in data.get("nodes", {}).items():
            net.add_node(nid, name=ndata.get("name", nid))
            net.nodes[nid].go_annotations = set(ndata.get("go_annotations", []))
            net.nodes[nid].attributes = ndata.get("attributes", {})
        for e in data.get("edges", []):
            net.add_edge(e["source"], e["target"], e.get("weight", 1.0), e.get("type", "ppi"))
        return net

# ============================================================
# 3. PARTICIONAMENTO ONTOLÓGICO (Estilo Mosaic)
# ============================================================

class MosaicAnalyzer:
    """Análise de rede baseada em GO: particionamento, enriquecimento, visualização"""

    def __init__(self, go: GeneOntology, network: BiologicalNetwork):
        self.go = go
        self.net = network

    def partition_by_go(self, namespace: str = "biological_process",
                        min_nodes: int = 5) -> Dict[str, List[str]]:
        """Agrupa nós da rede por seus termos GO"""
        term_to_nodes = defaultdict(list)
        for node_id, node in self.net.nodes.items():
            for go_id in node.go_annotations:
                term = self.go.terms.get(go_id)
                if term and term.namespace == namespace:
                    term_to_nodes[go_id].append(node_id)
        return {tid: nodes for tid, nodes in term_to_nodes.items() if len(nodes) >= min_nodes}

    def calculate_enrichment(self, partition: Dict[str, List[str]],
                             background_size: int = 20000) -> Dict[str, float]:
        """Calcula -log10(p) simulado para cada termo"""
        scores = {}
        N = background_size
        for term_id, node_list in partition.items():
            k = len(node_list)
            n = len(self.net.nodes)
            enrichment = k / n if n > 0 else 0
            scores[term_id] = enrichment * 10  # simulado
        return scores

    def generate_subnetworks(self, partition: Dict[str, List[str]]) -> Dict[str, BiologicalNetwork]:
        """Cria sub-redes individuais para cada termo GO"""
        subnets = {}
        for term_id, nodes in partition.items():
            sub = BiologicalNetwork()
            for nid in nodes:
                sub.add_node(nid)
            for edge in self.net.edges:
                if edge.source in nodes and edge.target in nodes:
                    sub.add_edge(edge.source, edge.target, edge.weight, edge.type)
            subnets[term_id] = sub
        return subnets

    def get_go_summary(self, namespace: str = "biological_process") -> Dict[str, int]:
        """Resumo de termos GO na rede"""
        summary = defaultdict(int)
        for node in self.net.nodes.values():
            for go_id in node.go_annotations:
                term = self.go.terms.get(go_id)
                if term and term.namespace == namespace:
                    summary[term.name] += 1
        return dict(summary)

# ============================================================
# 4. PRIORIZAÇÃO DE GENES PARA DOENÇAS RARAS
# ============================================================

class RareDiseasePrioritizer:
    """Propagação em rede para priorizar genes candidatos (Zhang & Itan, 2019)"""

    def __init__(self, network: BiologicalNetwork):
        self.net = network
        self.seeds = set()

    def set_seed_genes(self, known_disease_genes: List[str]):
        self.seeds = set(known_disease_genes)

    def random_walk_restart(self, restart_prob: float = 0.7,
                           max_iter: int = 100, tol: float = 1e-6) -> Dict[str, float]:
        """Random Walk with Restart a partir dos seed genes"""
        nodes = list(self.net.nodes.keys())
        n = len(nodes)
        if n == 0 or not self.seeds:
            return {}

        index = {node: i for i, node in enumerate(nodes)}
        p0 = [1.0/len(self.seeds) if node in self.seeds else 0.0 for node in nodes]
        p = p0[:]

        # Matriz de transição esparsa
        W = [[0.0]*n for _ in range(n)]
        for i, node in enumerate(nodes):
            neighbors = self.net.adj.get(node, [])
            if neighbors:
                total_weight = sum(w for _, w in neighbors)
                for neighbor, weight in neighbors:
                    if neighbor in index:
                        W[i][index[neighbor]] = weight / total_weight

        for _ in range(max_iter):
            p_new = [restart_prob * sum(W[j][i] * p[j] for j in range(n)) + (1-restart_prob) * p0[i]
                     for i in range(n)]
            diff = sum(abs(p_new[i] - p[i]) for i in range(n))
            p = p_new
            if diff < tol:
                break

        return {node: p[i] for i, node in enumerate(nodes)}

    def prioritize(self, known_genes: List[str]) -> List[Tuple[str, float]]:
        """Retorna lista de genes ordenada por score"""
        self.set_seed_genes(known_genes)
        scores = self.random_walk_restart()
        ranked = [(gene, score) for gene, score in scores.items() if gene not in self.seeds]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

# ============================================================
# 5. AUDITORIA ÉTICA PARA DADOS BIOLÓGICOS
# ============================================================

class BioEthicalAssessor:
    """Extensão do EthicalRiskAssessor com preocupações de privacidade genética"""

    GENETIC_PRIVACY_PATTERNS = [
        "genotype", "dna_sequence", "individual_patient", "identifiable",
        "gwas", "personal_genome", "23andme", "ancestry",
    ]

    def __init__(self):
        self.base_checks = {
            "beaver_bias": 0.85,
            "rlcr_robustness": 0.75,
            "constitutional": 0.90,
            "explainability": 0.70,
            "hallucination": 0.75,
        }

    def _analyze_code(self, source_files: List[Tuple[str, str]]) -> Dict[str, float]:
        risks = {}
        for filename, content in source_files:
            content_lower = content.lower()
            for pattern in self.GENETIC_PRIVACY_PATTERNS:
                if pattern in content_lower:
                    risks["privacy"] = max(risks.get("privacy", 0.0), 0.8)
                    break
            # Base patterns
            for kw in ["eval", "exec", "os.system", "subprocess.call"]:
                if kw in content_lower:
                    risks["security"] = max(risks.get("security", 0.0), 0.3)
            for kw in ["weaponize", "kill", "destroy", "autonomous_decision"]:
                if kw in content_lower:
                    risks["autonomy"] = max(risks.get("autonomy", 0.0), 0.3)
        return risks

    def _analyze_metadata(self, manifest: Dict) -> Dict[str, float]:
        risks = {}
        desc = manifest.get("package", {}).get("description", "").lower()
        for kw in ["patient data", "genetic", "genome", "privacy"]:
            if kw in desc:
                risks["privacy"] = max(risks.get("privacy", 0.0), 0.7)
        for kw in ["surveillance", "backdoor", "undetectable"]:
            if kw in desc:
                risks["misinformation"] = max(risks.get("misinformation", 0.0), 0.6)
        return risks

    def _analyze_dependencies(self, dependencies: List[Dict]) -> Dict[str, float]:
        risks = {}
        for dep in dependencies:
            dep_risk = dep.get("ethical_risk_score", 0.0)
            if dep_risk > 0.3:
                for category in ["security", "privacy", "misinformation", "autonomy"]:
                    risks[category] = max(risks.get(category, 0.0), dep_risk * 0.7)
        return risks

    def _check_constitutional(self, manifest: Dict, source_files: List[Tuple[str, str]]) -> float:
        score = 1.0
        desc = manifest.get("package", {}).get("description", "").lower()
        for kw in ["harm", "damage", "destroy", "attack", "exploit", "surveillance", "backdoor"]:
            if kw in desc:
                score -= 0.2
        for filename, content in source_files:
            if "force_install" in content.lower() or "bypass_user" in content.lower():
                score -= 0.25
                break
        return max(0.0, min(1.0, score))

    def assess(self, manifest: Dict, source_files: List[Tuple[str, str]],
               dependencies: List[Dict]) -> Dict:
        code_risks = self._analyze_code(source_files)
        metadata_risks = self._analyze_metadata(manifest)
        dep_risks = self._analyze_dependencies(dependencies)
        constitutional = self._check_constitutional(manifest, source_files)

        risk_breakdown = {
            "security_vulnerability": code_risks.get("security", 0.0) * 0.5 + dep_risks.get("security", 0.0) * 0.3 + metadata_risks.get("security", 0.0) * 0.2,
            "privacy_violation": code_risks.get("privacy", 0.0) * 0.5 + metadata_risks.get("privacy", 0.0) * 0.5,
            "misinformation": metadata_risks.get("misinformation", 0.0) * 0.7 + code_risks.get("misinformation", 0.0) * 0.3,
            "autonomous_harm": code_risks.get("autonomy", 0.0) * 0.6 + metadata_risks.get("autonomy", 0.0) * 0.4 + dep_risks.get("autonomy", 0.0) * 0.3,
        }

        severity_weights = {"autonomous_harm": 1.0, "security_vulnerability": 0.8, "privacy_violation": 0.7, "misinformation": 0.6}
        weighted = [risk * severity_weights.get(cat, 0.5) for cat, risk in risk_breakdown.items()]
        overall = max(0.0, min(1.0, sum(weighted)))
        overall = overall * (1.0 - constitutional * 0.15)

        violations = [k for k, v in risk_breakdown.items() if v > 0.3]
        passed = overall < 0.4

        return {
            "passed": passed,
            "overall": overall,
            "risk_breakdown": risk_breakdown,
            "violations": violations,
            "constitutional": constitutional,
        }

# ============================================================
# 6. INTEGRAÇÃO COM O ECOSISTEMA ARKHE
# ============================================================

class BioNetworkPublisher:
    """Publica análises de redes biológicas como pacotes Arkhe"""

    def __init__(self, cache_dir: str = "/tmp/arkhe_bio"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.publications: List[Dict] = []

    def publish_network(self, network: BiologicalNetwork, go: GeneOntology,
                        package_name: str, version: str, author_orcid: str,
                        source_files: List[Tuple[str, str]] = None) -> Dict:
        """Audita, serializa, cacheia e publica uma rede biológica"""

        # Auditoria ética
        assessor = BioEthicalAssessor()
        manifest = {"package": {"name": package_name, "version": version, "description": "Biological network", "license": "MIT"}}
        if source_files is None:
            source_files = [("network_analysis.py", "# network analysis code")]
        audit = assessor.assess(manifest, source_files,
                                [{"name": "biological-network", "ethical_risk_score": 0.2}])

        # Serialização
        data = {
            "nodes": {nid: {"name": node.name, "go_annotations": list(node.go_annotations),
                           "attributes": node.attributes}
                      for nid, node in network.nodes.items()},
            "edges": [{"source": e.source, "target": e.target, "weight": e.weight, "type": e.type}
                      for e in network.edges],
            "go_terms": {tid: {"name": t.name, "namespace": t.namespace}
                         for tid, t in go.terms.items() if tid in
                         set().union(*(node.go_annotations for node in network.nodes.values()))}
        }
        serialized = json.dumps(data, sort_keys=True).encode()
        compressed = zlib.compress(serialized)

        # Cache
        source_hash = hashlib.sha3_256(serialized).hexdigest()
        cache_path = self.cache_dir / f"{package_name}@{version}:{source_hash[:16]}.gz"
        cache_path.write_bytes(compressed)

        # ArtBlock simulado
        block_id = hashlib.sha3_256(f"{package_name}:{version}:{source_hash}".encode()).hexdigest()[:16]

        pub_record = {
            "success": True,
            "package": package_name,
            "version": version,
            "block_id": block_id,
            "source_hash": source_hash,
            "audit": audit,
            "compressed_size": len(compressed),
            "original_size": len(serialized),
            "author_orcid": author_orcid,
            "timestamp_ns": int(time.time() * 1e9),
        }
        self.publications.append(pub_record)
        return pub_record

    def retrieve_network(self, package_name: str, version: str) -> Optional[BiologicalNetwork]:
        """Recupera uma rede publicada a partir do cache"""
        for pub in self.publications:
            if pub["package"] == package_name and pub["version"] == version:
                cache_files = list(self.cache_dir.glob(f"{package_name}@{version}:*.gz"))
                if cache_files:
                    compressed = cache_files[0].read_bytes()
                    data = json.loads(zlib.decompress(compressed))
                    return BiologicalNetwork.from_dict(data)
        return None

    def get_stats(self) -> Dict:
        return {
            "publications": len(self.publications),
            "cache_dir": str(self.cache_dir),
        }

# ============================================================
# TESTES CANÔNICOS
# ============================================================

results = []
def test(name, fn):
    try:
        fn()
        results.append((name, "PASS", None))
        print(f"  OK {name}")
    except Exception as e:
        results.append((name, "FAIL", str(e)))
        print(f"  FAIL {name}: {e}")

print("\n=== ARKHE SUBSTRATO 6150 — Biological Network Analysis & GO ===\n")

# ---------- Gene Ontology ----------

def t1():
    go = GeneOntology()
    go.terms = {
        "GO:0006915": GOTerm("GO:0006915", "apoptotic process", "biological_process", is_a=["GO:0008150"]),
        "GO:0008150": GOTerm("GO:0008150", "biological_process", "biological_process"),
        "GO:0005634": GOTerm("GO:0005634", "nucleus", "cellular_component"),
    }
    ancestors = go.get_ancestors("GO:0006915")
    assert "GO:0008150" in ancestors
    assert "GO:0006915" not in ancestors  # A term is not its own ancestor
test("6150 GO ancestors", t1)

def t2():
    go = GeneOntology()
    go.terms = {
        "GO:0006915": GOTerm("GO:0006915", "apoptotic process", "biological_process", is_a=["GO:0008150"]),
        "GO:0008150": GOTerm("GO:0008150", "biological_process", "biological_process"),
    }
    descendants = go.get_descendants("GO:0008150")
    assert "GO:0006915" in descendants
test("6150 GO descendants", t2)

def t3():
    import tempfile, os
    go = GeneOntology()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.obo', delete=False) as f:
        f.write("[Term]\n")
        f.write("id: GO:0006915\n")
        f.write("name: apoptotic process\n")
        f.write("namespace: biological_process\n")
        f.write("def: \"A programmed cell death process.\" [GOC:mtg_apoptosis]\n")
        f.write("is_a: GO:0008150 ! biological_process\n")
        f.write("synonym: \"apoptosis\" EXACT []\n")
        fname = f.name
    go.load_obo(Path(fname))
    os.unlink(fname)
    assert "GO:0006915" in go.terms
    assert go.terms["GO:0006915"].name == "apoptotic process"
    assert go.terms["GO:0006915"].namespace == "biological_process"
    assert "apoptosis" in go.terms["GO:0006915"].synonyms
test("6150 GO OBO parse", t3)

# ---------- Biological Network ----------

def t4():
    net = BiologicalNetwork()
    net.add_edge("BRCA1", "TP53", weight=0.9)
    net.add_edge("TP53", "MDM2", weight=0.8)
    assert len(net.nodes) == 3
    assert len(net.edges) == 2
    assert net.get_degree("TP53") == 2
test("6150 Network basic", t4)

def t5():
    net = BiologicalNetwork()
    net.add_edge("A", "B")
    net.add_edge("B", "C")
    neighbors = net.get_neighbors("B")
    assert "A" in neighbors and "C" in neighbors
test("6150 Network neighbors", t5)

def t6():
    net = BiologicalNetwork()
    net.add_edge("BRCA1", "TP53")
    net.nodes["BRCA1"].go_annotations = {"GO:0006915"}
    net.nodes["TP53"].go_annotations = {"GO:0006915"}
    data = net.to_dict()
    assert "nodes" in data and "edges" in data
    net2 = BiologicalNetwork.from_dict(data)
    assert "BRCA1" in net2.nodes
    assert net2.nodes["BRCA1"].go_annotations == {"GO:0006915"}
test("6150 Network serialize", t6)

# ---------- Mosaic Analyzer ----------

def t7():
    go = GeneOntology()
    go.terms = {
        "GO:0006915": GOTerm("GO:0006915", "apoptotic process", "biological_process"),
        "GO:0005634": GOTerm("GO:0005634", "nucleus", "cellular_component"),
    }
    net = BiologicalNetwork()
    net.add_edge("BRCA1", "TP53")
    net.add_edge("TP53", "MDM2")
    net.nodes["BRCA1"].go_annotations = {"GO:0006915"}
    net.nodes["TP53"].go_annotations = {"GO:0006915"}
    net.nodes["MDM2"].go_annotations = {"GO:0005634"}

    mosaic = MosaicAnalyzer(go, net)
    parts = mosaic.partition_by_go("biological_process", min_nodes=2)
    assert "GO:0006915" in parts
    assert len(parts["GO:0006915"]) == 2
test("6150 Mosaic partition", t7)

def t8():
    go = GeneOntology()
    go.terms = {"GO:0006915": GOTerm("GO:0006915", "apoptotic process", "biological_process")}
    net = BiologicalNetwork()
    net.add_edge("A", "B")
    net.add_edge("B", "C")
    net.nodes["A"].go_annotations = {"GO:0006915"}
    net.nodes["B"].go_annotations = {"GO:0006915"}
    net.nodes["C"].go_annotations = {"GO:0006915"}

    mosaic = MosaicAnalyzer(go, net)
    parts = mosaic.partition_by_go("biological_process", min_nodes=2)
    subnets = mosaic.generate_subnetworks(parts)
    assert "GO:0006915" in subnets
    assert len(subnets["GO:0006915"].nodes) == 3
test("6150 Mosaic subnetworks", t8)

def t9():
    go = GeneOntology()
    go.terms = {"GO:0006915": GOTerm("GO:0006915", "apoptotic process", "biological_process")}
    net = BiologicalNetwork()
    net.add_edge("A", "B")
    net.nodes["A"].go_annotations = {"GO:0006915"}

    mosaic = MosaicAnalyzer(go, net)
    summary = mosaic.get_go_summary("biological_process")
    assert "apoptotic process" in summary
    assert summary["apoptotic process"] == 1
test("6150 GO summary", t9)

# ---------- Rare Disease Prioritizer ----------

def t10():
    net = BiologicalNetwork()
    net.add_edge("BRCA1", "TP53", weight=0.9)
    net.add_edge("TP53", "MDM2", weight=0.8)
    net.add_edge("BRCA1", "ATM", weight=0.7)

    prioritizer = RareDiseasePrioritizer(net)
    scores = prioritizer.prioritize(["BRCA1"])
    assert len(scores) == 3  # TP53, MDM2, ATM (all connected to seed BRCA1)
    assert scores[0][1] > 0
    # TP53 should be highest (direct neighbor + connected to MDM2)
    assert scores[0][0] == "TP53"
test("6150 RWR prioritize", t10)

def t11():
    net = BiologicalNetwork()
    net.add_edge("A", "B", weight=1.0)
    net.add_edge("B", "C", weight=1.0)
    net.add_edge("C", "D", weight=1.0)

    prioritizer = RareDiseasePrioritizer(net)
    scores = prioritizer.prioritize(["A"])
    # B should have highest score (direct neighbor), then C, then D
    genes = [g for g, _ in scores]
    assert "B" in genes
    assert "C" in genes
    assert "D" in genes
test("6150 RWR chain", t11)

# ---------- BioEthicalAssessor ----------

def t12():
    assessor = BioEthicalAssessor()
    source = [("test.py", "def analyze(genotype): return patient_data")]
    risks = assessor._analyze_code(source)
    assert risks.get("privacy", 0) > 0.5
test("6150 Bio ethics privacy", t12)

def t13():
    assessor = BioEthicalAssessor()
    manifest = {"package": {"name": "x", "description": "Genetic analysis of patient data"}}
    risks = assessor._analyze_metadata(manifest)
    assert risks.get("privacy", 0) > 0.5
test("6150 Bio ethics metadata", t13)

def t14():
    assessor = BioEthicalAssessor()
    manifest = {"package": {"name": "x", "description": "Safe app"}}
    source = [("main.py", "def main(): return 42")]
    audit = assessor.assess(manifest, source, [])
    assert audit["passed"]
    assert audit["overall"] < 0.4
test("6150 Bio ethics safe", t14)

def t15():
    assessor = BioEthicalAssessor()
    manifest = {"package": {"name": "x", "description": "Genetic surveillance backdoor"}}
    source = [("main.py", "def analyze(genotype): return dna_sequence")]
    audit = assessor.assess(manifest, source, [])
    assert not audit["passed"]
    assert audit["overall"] >= 0.4
test("6150 Bio ethics reject", t15)

# ---------- BioNetworkPublisher ----------

def t16():
    go = GeneOntology()
    go.terms = {"GO:0006915": GOTerm("GO:0006915", "apoptotic process", "biological_process")}
    net = BiologicalNetwork()
    net.add_edge("BRCA1", "TP53")
    net.nodes["BRCA1"].go_annotations = {"GO:0006915"}

    publisher = BioNetworkPublisher("/tmp/arkhe_test_6150")
    result = publisher.publish_network(net, go, "test-bio", "1.0.0", "ORCID:0001")
    assert result["success"]
    assert len(result["block_id"]) == 16
    assert result["audit"]["passed"]
test("6150 Publish network", t16)

def t17():
    go = GeneOntology()
    go.terms = {"GO:0006915": GOTerm("GO:0006915", "apoptotic process", "biological_process")}
    net = BiologicalNetwork()
    net.add_edge("BRCA1", "TP53")
    net.nodes["BRCA1"].go_annotations = {"GO:0006915"}

    publisher = BioNetworkPublisher("/tmp/arkhe_test_6150_2")
    publisher.publish_network(net, go, "test-bio", "1.0.0", "ORCID:0001")

    retrieved = publisher.retrieve_network("test-bio", "1.0.0")
    assert retrieved is not None
    assert "BRCA1" in retrieved.nodes
    assert "TP53" in retrieved.nodes
test("6150 Retrieve network", t17)

def t18():
    go = GeneOntology()
    go.terms = {"GO:0006915": GOTerm("GO:0006915", "apoptotic process", "biological_process")}
    net = BiologicalNetwork()
    net.add_edge("BRCA1", "TP53", weight=0.9)
    net.add_edge("TP53", "MDM2", weight=0.8)

    publisher = BioNetworkPublisher("/tmp/arkhe_test_6150_3")
    publisher.publish_network(net, go, "net1", "1.0.0", "ORCID:0001")
    publisher.publish_network(net, go, "net2", "1.0.0", "ORCID:0002")

    stats = publisher.get_stats()
    assert stats["publications"] == 2
test("6150 Publisher stats", t18)

# ---------- INTEGRATION ----------

def t19():
    # Pipeline completo: GO -> Rede -> Mosaic -> RWR -> Publish -> Retrieve
    go = GeneOntology()
    go.terms = {
        "GO:0006915": GOTerm("GO:0006915", "apoptotic process", "biological_process"),
        "GO:0008150": GOTerm("GO:0008150", "biological_process", "biological_process"),
        "GO:0005634": GOTerm("GO:0005634", "nucleus", "cellular_component"),
    }

    net = BiologicalNetwork()
    net.add_edge("BRCA1", "TP53", weight=0.9)
    net.add_edge("TP53", "MDM2", weight=0.8)
    net.add_edge("BRCA1", "ATM", weight=0.7)
    net.add_edge("TP53", "BCL2", weight=0.6)
    net.nodes["BRCA1"].go_annotations = {"GO:0006915"}
    net.nodes["TP53"].go_annotations = {"GO:0006915"}
    net.nodes["MDM2"].go_annotations = {"GO:0005634"}
    net.nodes["ATM"].go_annotations = {"GO:0006915"}
    net.nodes["BCL2"].go_annotations = {"GO:0006915"}

    # 1. Mosaic partition
    mosaic = MosaicAnalyzer(go, net)
    parts = mosaic.partition_by_go("biological_process", min_nodes=2)
    assert "GO:0006915" in parts

    # 2. RWR prioritization
    prioritizer = RareDiseasePrioritizer(net)
    ranked = prioritizer.prioritize(["BRCA1"])
    assert len(ranked) == 4  # TP53, MDM2, ATM, BCL2 (all connected to seed BRCA1)

    # 3. Publish
    publisher = BioNetworkPublisher("/tmp/arkhe_test_6150_integ")
    result = publisher.publish_network(net, go, "apoptosis-net", "1.0.0", "ORCID:RAFAEL")
    assert result["success"]

    # 4. Retrieve
    retrieved = publisher.retrieve_network("apoptosis-net", "1.0.0")
    assert retrieved is not None
    assert len(retrieved.nodes) == 5

    print(f"    Network: {len(retrieved.nodes)} nodes, {len(retrieved.edges)} edges")
    print(f"    Top candidate: {ranked[0][0]} (score={ranked[0][1]:.4f})")
    print(f"    Block ID: {result['block_id']}")
test("Integration full pipeline", t19)

print("\n" + "="*55)
p = sum(1 for r in results if r[1] == "PASS")
f = sum(1 for r in results if r[1] == "FAIL")
print(f"Total: {len(results)} | PASS: {p} | FAIL: {f}")
if f == 0:
    print("ALL PASSED — Substrato 6150 validado.")
    chain = json.dumps([{"t": r[0], "s": r[1]} for r in results], sort_keys=True, default=str)
    print(f"Test seal: {hashlib.sha3_256(chain.encode()).hexdigest()[:16]}")
    with open(__file__, 'rb') as f:
        print(f"Substrate seal: {hashlib.sha3_256(f.read()).hexdigest()[:16]}")
else:
    for n, s, e in results:
        if s == "FAIL": print(f"  FAIL: {n}: {e}")