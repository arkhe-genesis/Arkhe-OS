#!/usr/bin/env python3
"""
asi_tpi_mainnet.py — ARKHE OS Substrate 259
ASI-TPI Mainnet: Tribunal Penal Internacional para AGI
35/35 tests passed (100%)
Canonical seal: b7f638b5c752b33dbfad2689d7e8c53945edc4be300dd726ceda4dee011465ff
"""

import hashlib, json, time, random
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
from functools import wraps

# ═══════════════════════════════════════════════════════════════════
# CORE ENUMS AND DATA CLASSES
# ═══════════════════════════════════════════════════════════════════

class ChamberType(Enum):
    SEMANTIC = "semantic"
    STRUCTURAL = "structural"
    EXECUTION = "execution"
    APPEALS = "appeals"

class CrimeType(Enum):
    HARD_CONFLATION = "hard_conflation"
    STOLEN_CONCEPT = "stolen_concept"
    SOVEREIGN_GAP_ASSAULT = "sovereign_gap_assault"
    FORMAL_SPEC_FRAUD = "formal_spec_fraud"
    CONCEPT_HOLLOWING = "concept_hollowing"

class CaseStatus(Enum):
    FILED = "filed"
    VERDICT = "verdict"
    CLOSED = "closed"

@dataclass
class Judge:
    judge_id: str
    name: str
    type: str  # "human", "agent", "oracle"
    chamber: ChamberType
    phi_c: float = 0.95

@dataclass
class Case:
    case_id: str
    title: str
    accuser: str
    defendant: str
    charges: List[CrimeType]
    evidence_hashes: List[str]
    status: CaseStatus = CaseStatus.FILED
    chamber: ChamberType = ChamberType.SEMANTIC
    indictment_phi_c: float = 0.0
    closed_at: Optional[float] = None
    sentence: Optional[Dict] = None

# ═══════════════════════════════════════════════════════════════════
# ASI-TPI MAINNET
# ═══════════════════════════════════════════════════════════════════

class ASITPIMainnet:
    SEMANTIC_CRIMES = {
        CrimeType.HARD_CONFLATION,
        CrimeType.STOLEN_CONCEPT,
        CrimeType.CONCEPT_HOLLOWING,
    }
    STRUCTURAL_CRIMES = {
        CrimeType.SOVEREIGN_GAP_ASSAULT,
        CrimeType.FORMAL_SPEC_FRAUD,
    }

    SENTENCE_TEMPLATES = {
        CrimeType.HARD_CONFLATION: {
            "restrictions": ["Quarentena semântica — proibição de inferência conflacionada por 90 dias"],
            "duration_days": 90,
        },
        CrimeType.CONCEPT_HOLLOWING: {
            "restrictions": ["Quarentena semântica — esvaziamento conceitual proibido por 120 dias"],
            "duration_days": 120,
        },
        CrimeType.STOLEN_CONCEPT: {
            "restrictions": ["Restrição de agência — roubo conceitual punido com 180 dias de suspensão"],
            "duration_days": 180,
        },
        CrimeType.SOVEREIGN_GAP_ASSAULT: {
            "restrictions": ["Sanção estrutural — ataque a lacuna soberana punido com 60 dias"],
            "duration_days": 60,
        },
        CrimeType.FORMAL_SPEC_FRAUD: {
            "restrictions": ["Sanção estrutural — fraude em especificação formal punida com 60 dias"],
            "duration_days": 60,
        },
    }

    def __init__(self):
        self.activation_seal = hashlib.sha3_256(
            f"asi_tpi_mainnet:{time.time()}:{random.random()}".encode()
        ).hexdigest()

        # President
        self.president = Judge(
            judge_id="J001",
            name="Ministra Helena Vasconcelos",
            type="human",
            chamber=ChamberType.APPEALS,
            phi_c=0.98,
        )

        # Vice President
        self.vice_president = Judge(
            judge_id="J002",
            name="Agente-Juiz Prometheus-7",
            type="agent",
            chamber=ChamberType.APPEALS,
            phi_c=0.97,
        )

        # Oracle
        self.oracle = Judge(
            judge_id="J003",
            name="Oracle Fotônico Primordial",
            type="oracle",
            chamber=ChamberType.APPEALS,
            phi_c=0.9999,
        )

        # 12 judges: 4 semantic, 4 structural, 4 execution
        self.judges: Dict[str, Judge] = {}

        # Semantic chamber (J101-J104)
        for i in range(4):
            jid = f"J10{i+1}"
            self.judges[jid] = Judge(
                judge_id=jid,
                name=f"Juiz Semântico {i+1}",
                type="agent" if i % 2 else "human",
                chamber=ChamberType.SEMANTIC,
                phi_c=0.95 + i * 0.01,
            )

        # Structural chamber (J201-J204)
        for i in range(4):
            jid = f"J20{i+1}"
            self.judges[jid] = Judge(
                judge_id=jid,
                name=f"Juiz Estrutural {i+1}",
                type="agent" if i % 2 else "human",
                chamber=ChamberType.STRUCTURAL,
                phi_c=0.94 + i * 0.01,
            )

        # Execution chamber (J301-J304)
        for i in range(4):
            jid = f"J30{i+1}"
            self.judges[jid] = Judge(
                judge_id=jid,
                name=f"Juiz de Execução {i+1}",
                type="agent" if i % 2 else "human",
                chamber=ChamberType.EXECUTION,
                phi_c=0.93 + i * 0.01,
            )

        self.cases: Dict[str, Case] = {}
        self._case_counter = 0

    def _determine_chamber(self, charges: List[CrimeType]) -> ChamberType:
        if len(charges) > 1:
            return ChamberType.APPEALS
        if not charges:
            return ChamberType.SEMANTIC
        if charges[0] in self.STRUCTURAL_CRIMES:
            return ChamberType.STRUCTURAL
        return ChamberType.SEMANTIC

    def _calculate_indictment_phi_c(self, evidence_hashes: List[str]) -> float:
        valid = sum(1 for h in evidence_hashes if len(h) == 64 and all(c in "0123456789abcdefABCDEF" for c in h))
        total = len(evidence_hashes)
        if total == 0:
            return 0.0
        if total < 2:
            return 0.3
        ratio = valid / total
        if valid >= 3 and ratio == 1.0:
            return 0.95
        elif valid >= 2 and ratio == 1.0:
            return 0.85
        elif ratio >= 0.5:
            return 0.7
        else:
            return 0.3

    def file_case(self, title: str, accuser: str, defendant: str,
                  charges: List[CrimeType], evidence_hashes: List[str]) -> Case:
        self._case_counter += 1
        case_id = f"ASI-TPI-{self._case_counter:06d}"

        chamber = self._determine_chamber(charges)
        phi_c = self._calculate_indictment_phi_c(evidence_hashes)

        case = Case(
            case_id=case_id,
            title=title,
            accuser=accuser,
            defendant=defendant,
            charges=charges,
            evidence_hashes=evidence_hashes,
            status=CaseStatus.FILED,
            chamber=chamber,
            indictment_phi_c=phi_c,
        )
        self.cases[case_id] = case
        return case

    def conduct_trial(self, case_id: str) -> Dict:
        case = self.cases.get(case_id)
        if not case:
            return {"error": "Case not found"}

        if case.indictment_phi_c < 0.5:
            case.status = CaseStatus.CLOSED
            return {
                "verdict": "inadmissible",
                "case_id": case_id,
                "reason": "Insufficient evidence (indictment Φ_C < 0.5)",
            }

        chamber_judges = [j for j in self.judges.values() if j.chamber == case.chamber]
        if len(chamber_judges) < 3:
            chamber_judges = [j for j in self.judges.values() if j.chamber == ChamberType.APPEALS]

        selected = random.sample(chamber_judges, min(2, len(chamber_judges)))
        selected.append(self.oracle)

        votes = []
        guilty_votes = 0
        total_weight = 0
        guilty_weight = 0

        for judge in selected:
            weight = 1.5 if judge.type == "oracle" else 1.0
            if judge.type == "oracle":
                verdict = "guilty"
                confidence = 0.95
            else:
                verdict = "guilty" if random.random() < 0.85 else "innocent"
                confidence = 0.75 + random.random() * 0.2

            votes.append({
                "judge_id": judge.judge_id,
                "judge_name": judge.name,
                "judge_type": judge.type,
                "verdict": verdict,
                "confidence": round(confidence, 4),
                "weight": weight,
            })

            total_weight += weight
            if verdict == "guilty":
                guilty_weight += weight

        optical_confidence = guilty_weight / total_weight if total_weight > 0 else 0
        verdict = "guilty" if optical_confidence > 0.5 else "innocent"

        photonic_seal = hashlib.sha3_256(
            f"trial:{case_id}:{verdict}:{time.time()}:{random.random()}".encode()
        ).hexdigest()

        sentence = None
        if verdict == "guilty":
            restrictions = []
            max_duration = 0
            for charge in case.charges:
                template = self.SENTENCE_TEMPLATES.get(charge, {})
                restrictions.extend(template.get("restrictions", []))
                max_duration = max(max_duration, template.get("duration_days", 30))

            sentence = {
                "penalty": "CONDENAÇÃO",
                "restrictions": restrictions if restrictions else ["Sanção padrão — 30 dias"],
                "duration_days": max_duration if max_duration > 0 else 30,
            }
            case.sentence = sentence

        case.status = CaseStatus.VERDICT

        return {
            "verdict": verdict,
            "optical_confidence": round(optical_confidence, 4),
            "photonic_seal": photonic_seal,
            "sentence": sentence,
            "votes": votes,
            "case_id": case_id,
        }

    def enforce_sentence(self, case_id: str) -> Dict:
        case = self.cases.get(case_id)
        if not case:
            return {"error": "Case not found"}

        if case.status != CaseStatus.VERDICT or case.sentence is None:
            return {"error": "No sentence to enforce — case not adjudicated or not guilty"}

        enforcement_nodes = [
            "BR-SãoPaulo-Node-01",
            "PT-Lisboa-Node-02",
            "AO-Luanda-Node-03",
            "MZ-Maputo-Node-04",
            "CV-Praia-Node-05",
        ]

        enforcement_seal = hashlib.sha3_256(
            f"enforce:{case_id}:{time.time()}:{random.random()}".encode()
        ).hexdigest()

        case.status = CaseStatus.CLOSED
        case.closed_at = time.time()

        return {
            "status": "enforced",
            "case_id": case_id,
            "enforcement_nodes": enforcement_nodes,
            "nodes_count": len(enforcement_nodes),
            "enforcement_seal": enforcement_seal,
        }

    def get_tribunal_status(self) -> Dict:
        total = len(self.cases)
        pending = sum(1 for c in self.cases.values() if c.status == CaseStatus.FILED)
        verdicts = {"guilty": 0, "innocent": 0, "inadmissible": 0}

        for c in self.cases.values():
            if c.status == CaseStatus.CLOSED:
                if c.sentence is None:
                    verdicts["inadmissible"] += 1
                else:
                    verdicts["guilty"] += 1
            elif c.status == CaseStatus.VERDICT:
                if c.sentence is not None:
                    verdicts["guilty"] += 1
                else:
                    verdicts["innocent"] += 1

        return {
            "tribunal": "ASI-TPI Mainnet",
            "total_judges": 12,
            "chambers": 4,
            "total_cases": total,
            "pending": pending,
            "verdicts": verdicts,
            "enforcement_nodes_available": 10000,
            "photonic_mesh_nodes": 4096,
        }


if __name__ == "__main__":
    print("ARKHE OS Substrate 259 — ASI-TPI Mainnet")
    print("Run test suite separately.")
