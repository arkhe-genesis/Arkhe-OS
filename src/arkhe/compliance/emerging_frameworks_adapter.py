#!/usr/bin/env python3
"""
emerging_frameworks_adapter.py — Adaptador para Frameworks Emergentes.
Suporta AI Act (EU), Quantum Security Standards (NIST, ETSI) e outros.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class EmergingFramework(Enum):
    EU_AI_ACT = "eu_ai_act"
    QUANTUM_SECURE = "nist_quantum"
    CYBER_RESILIENCE = "eu_cyber_resilience"
    US_EXEC_ORDER = "us_ai_executive_order"

@dataclass
class EmergingRequirement:
    framework: EmergingFramework
    article_id: str
    title: str
    obligation: str
    risk_category: str  # unacceptable, high, limited, minimal
    effective_date: str

class EmergingFrameworksAdapter:
    """
    Mapeia controles MA‑S2 para requisitos de frameworks emergentes.
    """
    REQUIREMENTS = {
        EmergingFramework.EU_AI_ACT: [
            EmergingRequirement(EmergingFramework.EU_AI_ACT, "Art. 9", "Risk Management System",
                                "Establish and document risk management for AI systems.",
                                "high", "2026-08-01"),
            EmergingRequirement(EmergingFramework.EU_AI_ACT, "Art. 15", "Accuracy, Robustness, Cybersecurity",
                                "AI systems must achieve appropriate accuracy and robustness.",
                                "high", "2026-08-01"),
        ],
        EmergingFramework.QUANTUM_SECURE: [
            EmergingRequirement(EmergingFramework.QUANTUM_SECURE, "NIST.SP.800-213", "Quantum-Safe Cryptography",
                                "Transition to post‑quantum cryptography algorithms.",
                                "critical", "2026-12-31"),
        ],
    }

    def __init__(self, ma_s2_engine):
        self.engine = ma_s2_engine

    def map_ma_s2_to_emerging(self, framework: EmergingFramework) -> List[Dict]:
        """Mapeia controles MA‑S2 para obrigações de frameworks emergentes."""
        mappings = {
            "CVS-0.1": {"eu_ai_act": "Art.15", "quantum": None},
            "CVS-0.4": {"eu_ai_act": "Art.9", "quantum": None},
            "INV-2.1": {"eu_ai_act": None, "quantum": "NIST.SP.800-213"},
        }
        result = []
        for req in self.REQUIREMENTS.get(framework, []):
            for control, map_data in mappings.items():
                target = map_data.get("eu_ai_act" if framework == EmergingFramework.EU_AI_ACT else "quantum")
                if target and req.article_id == target:
                    result.append({"control": control, "requirement": req.title, "obligation": req.obligation})
        return result

    def assess_compliance(self, framework: EmergingFramework) -> Dict:
        mapped = self.map_ma_s2_to_emerging(framework)
        return {
            "framework": framework.value,
            "requirements_mapped": len(mapped),
            "recommended_actions": [m["obligation"] for m in mapped],
        }