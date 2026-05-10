#!/usr/bin/env python3
"""
coherence_monitor.py — Monitor de coerência para dependências Python.
Analisa grafo de dependências e alerta sobre riscos de Φ_C.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import time

@dataclass
class DependencyAnalysis:
    """Resultado da análise de coerência de dependências."""
    total_packages: int
    avg_coherence: float
    risk_level: str  # low, medium, high
    low_coherence_packages: List[Dict]
    circular_dependencies: List[List[str]]
    suggestions: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}

class DependencyCoherenceMonitor:
    """Monitora e analisa coerência de dependências Python."""

    # Thresholds canônicos
    COHERENCE_THRESHOLDS = {
        "critical": 0.5,
        "warning": 0.7,
        "acceptable": 0.85
    }

    # Pesos para cálculo de risco
    RISK_WEIGHTS = {
        "low_coherence": 0.4,
        "circular_deps": 0.3,
        "unmaintained": 0.2,
        "security_issues": 0.1
    }

    def __init__(self, registry_client=None):
        from .registry import SovereignRegistryClient
        self.registry = registry_client or SovereignRegistryClient()
        self._coherence_cache: Dict[str, float] = {}

    def analyze_requirements(self, requirements_path: Path) -> DependencyAnalysis:
        """Analisar arquivo requirements.txt."""
        packages = self._parse_requirements(requirements_path)
        return self.analyze_packages(packages)

    def analyze_packages(self, packages: Dict[str, Optional[str]]) -> DependencyAnalysis:
        """Analisar lista de pacotes e versões."""
        coherence_scores = []
        low_coh = []
        dep_graph: Dict[str, List[str]] = {}

        for name, version in packages.items():
            # Obter manifesto do registry
            manifest = self.registry.get_package_manifest(name, version)
            if not manifest:
                continue

            coh = manifest.coherence_score or self._estimate_coherence(manifest)
            coherence_scores.append(coh)
            self._coherence_cache[f"{name}=={manifest.version}"] = coh

            if coh < self.COHERENCE_THRESHOLDS["warning"]:
                low_coh.append({
                    "name": name,
                    "version": manifest.version,
                    "coherence": coh,
                    "phi_rep": manifest.phi_rep
                })

            # Construir grafo de dependências
            dep_graph[name] = list(getattr(manifest, 'dependencies', {}).keys())

        # Detectar dependências circulares
        circular = self._find_circular_dependencies(dep_graph)

        # Calcular métricas agregadas
        avg_coh = sum(coherence_scores) / len(coherence_scores) if coherence_scores else 0.0
        risk = self._calculate_risk(avg_coh, len(low_coh), len(circular), packages)

        # Gerar sugestões
        suggestions = self._generate_suggestions(low_coh, packages)

        return DependencyAnalysis(
            total_packages=len(packages),
            avg_coherence=avg_coh,
            risk_level=risk,
            low_coherence_packages=low_coh,
            circular_dependencies=circular,
            suggestions=suggestions
        )

    def _parse_requirements(self, path: Path) -> Dict[str, Optional[str]]:
        """Parse requirements.txt para dict {name: version_spec}."""
        packages = {}
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # Parse simples: nome==versão ou nome>=versão
                if '==' in line:
                    name, ver = line.split('==', 1)
                    packages[name.strip()] = ver.strip()
                elif '>=' in line:
                    name, ver = line.split('>=', 1)
                    packages[name.strip()] = ver.strip()
                else:
                    packages[line] = None
        return packages

    def _estimate_coherence(self, manifest) -> float:
        """Estimar coerência se não fornecida."""
        # Heurística baseada em Φ-REP e idade
        base = manifest.phi_rep * 0.7
        age_factor = max(0, 1 - (time.time() - manifest.published_at) / (365 * 86400))
        return min(1.0, base + age_factor * 0.3)

    def _find_circular_dependencies(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """Detectar ciclos no grafo de dependências."""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # Ciclo encontrado
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    def _calculate_risk(self, avg_coh: float, low_count: int,
                       circular_count: int, packages: Dict) -> str:
        """Calcular nível de risco baseado em múltiplos fatores."""
        score = 0.0

        # Fator 1: Coerência média baixa
        if avg_coh < self.COHERENCE_THRESHOLDS["critical"]:
            score += self.RISK_WEIGHTS["low_coherence"] * 2
        elif avg_coh < self.COHERENCE_THRESHOLDS["warning"]:
            score += self.RISK_WEIGHTS["low_coherence"]

        # Fator 2: Muitos pacotes com baixa coerência
        low_ratio = low_count / max(1, len(packages))
        score += self.RISK_WEIGHTS["low_coherence"] * low_ratio

        # Fator 3: Dependências circulares
        score += self.RISK_WEIGHTS["circular_deps"] * min(1.0, circular_count * 0.5)

        # Classificar
        if score >= 0.7:
            return "high"
        elif score >= 0.4:
            return "medium"
        return "low"

    def _generate_suggestions(self, low_coh: List[Dict],
                             packages: Dict) -> List[Dict]:
        """Gerar sugestões de alternativas mais coerentes."""
        suggestions = []
        for pkg in low_coh:
            # Buscar alternativas no registry com maior Φ_C
            alternatives = self.registry.search(
                pkg["name"],
                min_phi_rep=pkg["phi_rep"] + 0.1
            )
            for alt in alternatives[:3]:  # Top 3
                if alt.coherence_score and alt.coherence_score > pkg["coherence"]:
                    suggestions.append({
                        "current": f"{pkg['name']}=={pkg['version']}",
                        "alternative": f"{alt.name}=={alt.version}",
                        "coherence_gain": alt.coherence_score - pkg["coherence"],
                        "reason": f"Higher coherence ({alt.coherence_score:.3f} vs {pkg['coherence']:.3f})"
                    })
        return suggestions