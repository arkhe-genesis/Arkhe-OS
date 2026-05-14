#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
threat_database_extended.py — Expansão do ThreatDatabase para MA‑S2
Adiciona padrões de ataque multi‑estágio, TTPs emergentes e correlação com threat intel.
"""

import json, hashlib, time
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

@dataclass
class MultiStageAttackPattern:
    """Padrão de ataque multi‑estágio para modelagem APM."""
    pattern_id: str
    name: str
    description: str
    stages: List['AttackStage']
    mitre_techniques: List[str]
    threat_actors: List[str]
    confidence: float  # 0.0–1.0
    last_updated: float
    emergent: bool = False  # TTP emergente (não catalogada previamente)

@dataclass
class AttackStage:
    """Estágio individual de um padrão multi‑estágio."""
    stage_number: int
    name: str
    technique: str  # MITRE ATT&CK technique ID
    objective: str
    indicators: List[str]  # IOCs ou comportamentos detectáveis
    success_probability: float  # Probabilidade de sucesso do estágio

@dataclass
class EmergingTTP:
    """TTP emergente detectada via análise de ameaças."""
    ttp_id: str
    name: str
    description: str
    first_observed: float
    sources: List[str]  # Fontes de inteligência
    mitre_mapping: Optional[str]  # Técnica MITRE mais próxima (se aplicável)
    confidence: float
    related_cves: List[str]

class ThreatDatabaseExtended:
    """
    ThreatDatabase expandido para MA‑S2 com:
    • Padrões de ataque multi‑estágio para APM
    • TTPs emergentes detectadas via ML/análise de threat intel
    • Correlação cruzada entre CVEs, técnicas MITRE e padrões de ataque
    """

    def __init__(self, cache_dir: str = "~/.arkhe/threat_cache"):
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Catálogos base (simulados para demo)
        self.multi_stage_patterns: Dict[str, MultiStageAttackPattern] = {}
        self.emerging_ttps: Dict[str, EmergingTTP] = {}
        self.cve_to_patterns: Dict[str, Set[str]] = {}  # CVE → pattern_ids

        self._load_catalogs()

    def _load_catalogs(self):
        """Carrega catálogos de padrões e TTPs."""
        # Em produção: baixar de APIs de threat intel (MISP, ATT&CK, etc.)
        # Para demo: carregar padrões simulados
        self._load_sample_multi_stage_patterns()
        self._load_sample_emerging_ttps()

    def _load_sample_multi_stage_patterns(self):
        """Carrega padrões multi‑estágio de demonstração."""
        patterns = [
            MultiStageAttackPattern(
                pattern_id="MSAP-001",
                name="Supply Chain Compromise → Lateral Movement → Data Exfiltration",
                description="Ataque via dependência comprometida seguido de movimento lateral e exfiltração.",
                stages=[
                    AttackStage(1, "Initial Access via Dependency", "T1195.002", "Comprometer pacote de terceiros", ["suspicious_package_install"], 0.85),
                    AttackStage(2, "Execution via Build Process", "T1105", "Executar código malicioso durante build", ["unusual_build_artifacts"], 0.75),
                    AttackStage(3, "Lateral Movement to Auth Service", "T1078", "Mover para serviço de autenticação", ["auth_service_anomalies"], 0.65),
                    AttackStage(4, "Data Exfiltration via Encrypted Channel", "T1041", "Exfiltrar dados via canal criptografado", ["large_outbound_encrypted"], 0.70),
                ],
                mitre_techniques=["T1195.002", "T1105", "T1078", "T1041"],
                threat_actors=["APT29", "Lazarus"],
                confidence=0.92,
                last_updated=time.time(),
            ),
            MultiStageAttackPattern(
                pattern_id="MSAP-002",
                name="AI Model Poisoning → Inference Manipulation → Decision Corruption",
                description="Envenenamento de modelo de IA para manipular inferências e corromper decisões.",
                stages=[
                    AttackStage(1, "Training Data Poisoning", "T1584.006", "Injetar dados maliciosos no treinamento", ["anomalous_training_samples"], 0.70),
                    AttackStage(2, "Model Backdoor Insertion", "T1556.006", "Inserir backdoor no modelo treinado", ["unexpected_model_behavior"], 0.60),
                    AttackStage(3, "Targeted Inference Trigger", "T1498", "Ativar backdoor via input específico", ["trigger_input_detected"], 0.80),
                    AttackStage(4, "Decision Manipulation", "T1499", "Manipular saída do modelo para objetivo malicioso", ["anomalous_predictions"], 0.75),
                ],
                mitre_techniques=["T1584.006", "T1556.006", "T1498", "T1499"],
                threat_actors=["Emergent AI Threat Actors"],
                confidence=0.78,
                last_updated=time.time(),
                emergent=True,
            ),
        ]
        for p in patterns:
            self.multi_stage_patterns[p.pattern_id] = p
            # Mapear CVEs relacionados (simulado)
            for cve in ["CVE-2026-12345", "CVE-2026-12348"] if p.pattern_id == "MSAP-001" else ["CVE-2026-99999"]:
                self.cve_to_patterns.setdefault(cve, set()).add(p.pattern_id)

    def _load_sample_emerging_ttps(self):
        """Carrega TTPs emergentes de demonstração."""
        ttps = [
            EmergingTTP(
                ttp_id="ETTP-001",
                name="Quantum‑Resistant Crypto Downgrade Attack",
                description="Forçar fallback para criptografia clássica em sistemas híbridos pós‑quânticos.",
                first_observed=time.time() - 86400*7,
                sources=["CISA Alert AA24-XXX", "Private Threat Intel Feed"],
                mitre_mapping="T1589.002",  # Credential dumping via crypto downgrade
                confidence=0.85,
                related_cves=["CVE-2026-77777"],
            ),
            EmergingTTP(
                ttp_id="ETTP-002",
                name="Epigenetic Data Manipulation via Φ_C Exploitation",
                description="Manipular dados epigenéticos explorando vulnerabilidades no cálculo de coerência Φ_C.",
                first_observed=time.time() - 86400*3,
                sources=["ARKHE Internal Research", "Academic Preprint"],
                mitre_mapping=None,  # Nova técnica sem mapeamento MITRE ainda
                confidence=0.62,
                related_cves=[],
            ),
        ]
        for t in ttps:
            self.emerging_ttps[t.ttp_id] = t

    def get_patterns_for_cve(self, cve: str) -> List[MultiStageAttackPattern]:
        """Retorna padrões multi‑estágio associados a um CVE."""
        pattern_ids = self.cve_to_patterns.get(cve, set())
        return [self.multi_stage_patterns[pid] for pid in pattern_ids if pid in self.multi_stage_patterns]

    def get_emerging_ttps_by_confidence(self, min_confidence: float = 0.7) -> List[EmergingTTP]:
        """Retorna TTPs emergentes acima de um limiar de confiança."""
        return [t for t in self.emerging_ttps.values() if t.confidence >= min_confidence]

    def correlate_attack_path_with_patterns(
        self,
        attack_path: List[str],  # Lista de técnicas MITRE ou serviços
    ) -> List[Tuple[MultiStageAttackPattern, float]]:
        """
        Correlaciona um caminho de ataque com padrões multi‑estágio conhecidos.
        Returns:
            Lista de (padrão, score de correspondência) ordenada por score.
        """
        results = []
        path_set = set(attack_path)

        for pattern in self.multi_stage_patterns.values():
            pattern_techniques = set(pattern.mitre_techniques)
            # Score baseado em sobreposição de técnicas e ordem dos estágios
            overlap = len(path_set & pattern_techniques)
            order_score = self._compute_order_score(attack_path, pattern.stages)
            score = (0.7 * overlap / max(len(pattern_techniques), 1)) + (0.3 * order_score)
            if score > 0.3:  # Limiar mínimo de relevância
                results.append((pattern, score))

        return sorted(results, key=lambda x: x[1], reverse=True)

    def _compute_order_score(self, path: List[str], stages: List[AttackStage]) -> float:
        """Computa score baseado na ordem dos estágios (simplificado)."""
        # Para demo: verificar se pelo menos 2 estágios consecutivos aparecem em ordem
        matches = 0
        for i in range(len(stages) - 1):
            if stages[i].technique in path and stages[i+1].technique in path:
                if path.index(stages[i].technique) < path.index(stages[i+1].technique):
                    matches += 1
        return matches / max(len(stages) - 1, 1)

    def export_for_apm_engine(self) -> Dict:
        """Exporta dados formatados para o motor de modelagem APM."""
        return {
            "multi_stage_patterns": [
                {
                    "id": p.pattern_id,
                    "name": p.name,
                    "stages": [{"technique": s.technique, "objective": s.objective} for s in p.stages],
                    "mitre_techniques": p.mitre_techniques,
                    "confidence": p.confidence,
                    "emergent": p.emergent,
                }
                for p in self.multi_stage_patterns.values()
            ],
            "emerging_ttps": [
                {
                    "id": t.ttp_id,
                    "name": t.name,
                    "mitre_mapping": t.mitre_mapping,
                    "confidence": t.confidence,
                    "related_cves": t.related_cves,
                }
                for t in self.emerging_ttps.values()
            ],
            "cve_pattern_map": {cve: list(pids) for cve, pids in self.cve_to_patterns.items()},
            "last_updated": time.time(),
        }