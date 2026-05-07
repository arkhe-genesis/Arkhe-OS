# arkhe_os/starter/shared/lfir_parser.py
"""
Parser LFIR (Language-agnostic Intermediate Representation) para múltiplas linguagens bancárias.
Extrai grafos de dependência, métricas de coerência Φ_C e predicados regulatórios.
"""
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import hashlib
import json
from pathlib import Path
import os
from datetime import datetime

class Language(Enum):
    JAVA = "java"
    PYTHON = "python"
    CSHARP = "csharp"
    COBOL = "cobol"
    UNKNOWN = "unknown"

@dataclass
class LFIRNode:
    """Nó no grafo LFIR representando um elemento de código."""
    node_id: str
    name: str
    node_type: str  # "class", "function", "predicate", "endpoint", etc.
    language: Language
    file_path: str
    line_start: int
    line_end: int
    complexity: float = 1.0
    regulatory_tags: List[str] = field(default_factory=list)  # ["BCB", "GDPR", "fairness", etc.]
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    def compute_coherence_contribution(self) -> float:
        """Calcula contribuição deste nó para a coerência global Φ_C."""
        # Fatores: complexidade, tags regulatórias, dependências
        base = 1.0 / (1.0 + self.complexity * 0.1)
        tag_bonus = len(self.regulatory_tags) * 0.05
        dep_penalty = len(self.dependencies) * 0.02
        return max(0.0, min(1.0, base + tag_bonus - dep_penalty))

@dataclass
class LFIRGraph:
    """Grafo LFIR completo para um projeto ou módulo."""
    project_id: str
    language: Language
    nodes: Dict[str, LFIRNode] = field(default_factory=dict)
    edges: List[Dict] = field(default_factory=list)  # {source, target, type, weight}
    regulatory_predicates: List[Dict] = field(default_factory=list)
    global_coherence: float = 0.0

    def add_node(self, node: LFIRNode):
        self.nodes[node.node_id] = node

    def add_edge(self, source: str, target: str, edge_type: str, weight: float = 1.0):
        self.edges.append({
            "source": source,
            "target": target,
            "type": edge_type,
            "weight": weight
        })

    def compute_global_coherence(self) -> float:
        """Calcula coerência global Φ_C para o grafo."""
        if not self.nodes:
            return 0.0
        # Média ponderada das contribuições dos nós
        total = sum(node.compute_coherence_contribution() for node in self.nodes.values())
        self.global_coherence = total / len(self.nodes)
        return self.global_coherence

    def to_dict(self) -> Dict:
        """Serializa grafo para exportação JSON."""
        return {
            "project_id": self.project_id,
            "language": self.language.value,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "global_coherence": round(self.global_coherence, 4),
            "regulatory_predicates": self.regulatory_predicates,
            "nodes": {
                nid: {
                    "name": n.name,
                    "type": n.node_type,
                    "complexity": n.complexity,
                    "regulatory_tags": n.regulatory_tags,
                    "coherence_contribution": round(n.compute_coherence_contribution(), 4)
                }
                for nid, n in self.nodes.items()
            }
        }

class PolymathLFIRParser:
    """Parser poliglota para extração de LFIR de múltiplas linguagens."""

    def __init__(self):
        self.parsers = {
            Language.JAVA: JavaLFIRParser(),
            Language.PYTHON: PythonLFIRParser(),
            Language.CSHARP: CSharpLFIRParser(),
            Language.COBOL: CobolLFIRParser(),
        }

    def detect_language(self, file_path: str) -> Language:
        """Detecta linguagem baseada em extensão e conteúdo."""
        ext = Path(file_path).suffix.lower()
        if ext == ".java":
            return Language.JAVA
        elif ext == ".py":
            return Language.PYTHON
        elif ext == ".cs":
            return Language.CSHARP
        elif ext in [".cob", ".cbl", ".cpy"]:
            return Language.COBOL
        return Language.UNKNOWN

    def parse_file(self, file_path: str, language: Optional[Language] = None) -> LFIRGraph:
        """Parseia um arquivo individual para LFIR."""
        if language is None:
            language = self.detect_language(file_path)
        if language == Language.UNKNOWN:
            raise ValueError(f"Cannot parse unknown language: {file_path}")
        parser = self.parsers.get(language)
        if parser is None:
            raise ValueError(f"No parser registered for language: {language}")
        return parser.parse_file(file_path)

    def parse_directory(self, dir_path: str, exclude: Optional[List[str]] = None) -> LFIRGraph:
        """Parseia recursivamente um diretório para LFIR agregado."""
        if exclude is None:
            exclude = ["node_modules", ".git", "__pycache__", "bin", "obj", "target"]

        aggregated = LFIRGraph(
            project_id=Path(dir_path).name,
            language=Language.UNKNOWN  # Will be refined during parsing
        )

        for root, dirs, files in os.walk(dir_path):
            # Filter excluded directories
            dirs[:] = [d for d in dirs if d not in exclude]

            for file in files:
                file_path = os.path.join(root, file)
                lang = self.detect_language(file_path)
                if lang != Language.UNKNOWN:
                    try:
                        graph = self.parse_file(file_path, lang)
                        # Merge into aggregated graph
                        for node_id, node in graph.nodes.items():
                            aggregated.add_node(node)
                        for edge in graph.edges:
                            aggregated.add_edge(**edge)
                        aggregated.regulatory_predicates.extend(graph.regulatory_predicates)
                    except Exception as e:
                        # Log error but continue parsing other files
                        print(f"⚠️ Error parsing {file_path}: {e}")

        # Compute global coherence after aggregation
        aggregated.compute_global_coherence()
        return aggregated

    def export_lfir_json(self, graph: LFIRGraph, output_path: str):
        """Exporta grafo LFIR para JSON com selo canônico."""
        export_data = graph.to_dict()
        # Add canonical seal based on content hash
        content_hash = hashlib.sha256(
            json.dumps(export_data, sort_keys=True).encode()
        ).hexdigest()
        export_data["canonical_seal"] = content_hash[:16]
        export_data["export_timestamp"] = datetime.now().isoformat()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        return export_data

# Language-specific parsers (simplified examples)
class JavaLFIRParser:
    def parse_file(self, file_path: str) -> LFIRGraph:
        # Implementation: parse Java AST, extract classes, methods, annotations
        # Extract @ComplianceVerified, @RegulatoryPredicate, etc.
        return LFIRGraph(project_id="java_project", language=Language.JAVA)

class PythonLFIRParser:
    def parse_file(self, file_path: str) -> LFIRGraph:
        # Implementation: parse Python AST, extract functions, decorators, type hints
        # Extract @regulatory_compliant, @federated_training, etc.
        return LFIRGraph(project_id="python_project", language=Language.PYTHON)

class CSharpLFIRParser:
    def parse_file(self, file_path: str) -> LFIRGraph:
        # Implementation: parse C# syntax tree, extract classes, methods, attributes
        # Extract [ComplianceVerified], [RegulatoryPredicate], etc.
        return LFIRGraph(project_id="csharp_project", language=Language.CSHARP)

class CobolLFIRParser:
    def parse_file(self, file_path: str) -> LFIRGraph:
        # Implementation: parse COBOL source, extract paragraphs, sections, data divisions
        # Map DECIMAL fields to regulatory predicates, extract business rules
        return LFIRGraph(project_id="cobol_project", language=Language.COBOL)
