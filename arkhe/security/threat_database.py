"""
ThreatDatabase – Catálogo de ameaças com EPSS + KEV + MITRE ATT&CK
Substrato 9008: MA‑S2 Compliance Engine
"""
import hashlib
from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class Finding:
    cve: str
    cvss_score: float
    epss_score: float = 0.0
    kev_listed: bool = False
    description: str = ""
    mitre_tactics: List[str] = field(default_factory=list)

    def enrich_with_epss_kev(self):
        """CVS‑0.2: Enriquece com EPSS e KEV"""
        self.epss_score = ThreatDatabase.epss_lookup.get(self.cve, 0.0)
        self.kev_listed = self.cve in ThreatDatabase.cisa_kev_catalog

    def is_critical(self) -> bool:
        return self.compute_ma_s2_severity() >= 0.8

    def compute_ma_s2_severity(self) -> float:
        """
        MA‑S2 severity score:
        • CVSS (40%)
        • EPSS (35%)
        • KEV binary (25%)
        """
        cvss_norm = min(self.cvss_score / 10.0, 1.0)
        epss_norm = self.epss_score
        kev_boost = 1.0 if self.kev_listed else 0.0
        return 0.40 * cvss_norm + 0.35 * epss_norm + 0.25 * kev_boost

    def to_dict(self) -> Dict:
        return {
            "cve": self.cve,
            "cvss": self.cvss_score,
            "epss": self.epss_score,
            "kev": self.kev_listed,
            "severity": round(self.compute_ma_s2_severity(), 4),
            "critical": self.is_critical(),
            "mitre": self.mitre_tactics
        }

@dataclass
class AttackPath:
    id: str
    nodes: List[str]
    risk_score: float = 0.0
    mitre_techniques: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "path_id": self.id,
            "nodes": self.nodes,
            "risk_score": round(self.risk_score, 4),
            "mitre_techniques": self.mitre_techniques
        }

class ThreatDatabase:
    """Banco de dados de ameaças com EPSS e KEV integrados."""

    # Simulação de catálogos EPSS e KEV
    epss_lookup: Dict[str, float] = {
        "CVE-2026-12345": 0.95,
        "CVE-2026-12346": 0.72,
        "CVE-2026-12347": 0.15,
        "CVE-2026-12348": 0.88,
        "CVE-2026-00001": 0.99,
    }

    cisa_kev_catalog: set = {
        "CVE-2026-12345",
        "CVE-2026-12348",
        "CVE-2026-00001",
    }

    mitre_attack_patterns: Dict[str, List[str]] = {
        "CVE-2026-12345": ["T1190", "T1078", "T1059"],
        "CVE-2026-12346": ["T1190", "T1133"],
        "CVE-2026-12347": ["T1071"],
        "CVE-2026-12348": ["T1190", "T1078", "T1055", "T1059"],
    }

    def enrich_finding(self, finding: Finding) -> Finding:
        finding.enrich_with_epss_kev()
        finding.mitre_tactics = self.mitre_attack_patterns.get(finding.cve, [])
        return finding

    def get_threat_intel(self, cve: str) -> Dict:
        return {
            "cve": cve,
            "epss": self.epss_lookup.get(cve, 0.0),
            "kev": cve in self.cisa_kev_catalog,
            "mitre": self.mitre_attack_patterns.get(cve, [])
        }
