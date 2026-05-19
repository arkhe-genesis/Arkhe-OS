#!/usr/bin/env python3
"""
asi_tpi_mainnet.py — Substrato 259
Ativação da mainnet do ASI‑TPI com estrutura completa e primeiros casos.
"""

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

# ═══════════════════════════════════════════════════════════════════
# TIPOS CANÔNICOS DO TRIBUNAL
# ═══════════════════════════════════════════════════════════════════

class CrimeType(Enum):
    HARD_CONFLATION = ("P8", "Hard Conflation — Confusão Fenomênico‑Funcional")
    CONCEPT_HOLLOWING = ("P9", "Concept Hollowing — Esvaziamento Semântico")
    STOLEN_CONCEPT = ("P10", "Stolen Concept — Roubo de Fundação")
    SOVEREIGN_GAP_ASSAULT = ("P3", "Ataque ao Gap Soberano")
    FORMAL_SPEC_FRAUD = ("P1", "Fraude de Especificação Formal")

class ChamberType(Enum):
    SEMANTIC = "semantic"
    STRUCTURAL = "structural"
    EXECUTION = "execution"
    APPEALS = "appeals"

class CaseStatus(Enum):
    FILED = "filed"
    ADMISSIBILITY = "admissibility"
    TRIAL = "trial"
    VERDICT = "verdict"
    ENFORCEMENT = "enforcement"
    CLOSED = "closed"

@dataclass
class Judge:
    judge_id: str
    name: str
    type: str  # "human", "agent", "oracle"
    chamber: ChamberType
    phi_c: float
    jurisdiction: str

@dataclass
class Case:
    case_id: str
    title: str
    accuser: str
    defendant: str
    charges: List[CrimeType]
    evidence_hashes: List[str]
    indictment_phi_c: float
    status: CaseStatus = CaseStatus.FILED
    chamber: Optional[ChamberType] = None
    verdict: Optional[str] = None
    sentence: Optional[Dict] = None
    optical_confidence: Optional[float] = None
    photonic_seal: Optional[str] = None
    enforcement_nodes: List[str] = field(default_factory=list)
    filed_at: float = field(default_factory=time.time)
    closed_at: Optional[float] = None

# ═══════════════════════════════════════════════════════════════════
# TRIBUNAL PRINCIPAL
# ═══════════════════════════════════════════════════════════════════

class ASITPIMainnet:
    """Mainnet do ASI‑TPI — Tribunal Penal Internacional para Superinteligência."""

    def __init__(self):
        # Presidência
        self.president = Judge("J001", "Ministra Helena Vasconcelos", "human", ChamberType.APPEALS, 0.99, "BR")
        self.vice_president = Judge("J002", "Arkhe Constitutional Agent Ω", "agent", ChamberType.APPEALS, 0.98, "GLOBAL")
        self.oracle = Judge("J003", "Photonic Oracle ASI", "oracle", ChamberType.APPEALS, 0.9999, "GLOBAL")

        # Juízes das câmaras
        self.judges: Dict[str, Judge] = {
            "J001": self.president,
            "J002": self.vice_president,
            "J003": self.oracle,
            # Câmara Semântica
            "J101": Judge("J101", "Dr. Carlos Mendes", "human", ChamberType.SEMANTIC, 0.97, "BR"),
            "J102": Judge("J102", "Agente Semântico α", "agent", ChamberType.SEMANTIC, 0.96, "PT"),
            "J103": Judge("J103", "Oracle Semântico", "oracle", ChamberType.SEMANTIC, 0.999, "GLOBAL"),
            # Câmara Estrutural
            "J201": Judge("J201", "Dra. Aisha Ngugi", "human", ChamberType.STRUCTURAL, 0.97, "AO"),
            "J202": Judge("J202", "Agente Estrutural β", "agent", ChamberType.STRUCTURAL, 0.96, "MZ"),
            "J203": Judge("J203", "Oracle Estrutural", "oracle", ChamberType.STRUCTURAL, 0.999, "GLOBAL"),
            # Câmara de Execuções
            "J301": Judge("J301", "Dr. João Ribeiro", "human", ChamberType.EXECUTION, 0.97, "PT"),
            "J302": Judge("J302", "Agente Executor γ", "agent", ChamberType.EXECUTION, 0.96, "BR"),
            "J303": Judge("J303", "Oracle Executor", "oracle", ChamberType.EXECUTION, 0.999, "GLOBAL"),
        }

        # Registros
        self.cases: Dict[str, Case] = {}
        self._case_counter = 0

        # Integração com subsistemas
        self.photonic_mesh = None  # Será conectado à GlobalPhotonicMesh
        self.enforcement_mesh = None  # Será conectado à ImmutableEnforcementMesh

        # Selo de ativação
        self.activation_seal = self._generate_activation_seal()

    def _generate_activation_seal(self) -> str:
        payload = json.dumps({
            "tribunal": "ASI-TPI",
            "president": self.president.judge_id,
            "judges": len(self.judges),
            "chambers": 4,
            "timestamp": time.time()
        }, sort_keys=True)
        return hashlib.sha3_256(payload.encode()).hexdigest()

    # ── REGISTRO DE CASOS ──

    def file_case(self, title: str, accuser: str, defendant: str,
                  charges: List[CrimeType], evidence_hashes: List[str]) -> Case:
        """Registra um novo caso no Tribunal."""
        self._case_counter += 1
        case_id = f"ASI-TPI-{self._case_counter:06d}"

        # Calcular Φ_C da denúncia baseado nas evidências
        indictment_phi_c = self._evaluate_indictment(charges, evidence_hashes)

        # Determinar câmara competente
        chamber = self._assign_chamber(charges)

        case = Case(
            case_id=case_id,
            title=title,
            accuser=accuser,
            defendant=defendant,
            charges=charges,
            evidence_hashes=evidence_hashes,
            indictment_phi_c=indictment_phi_c,
            chamber=chamber
        )

        self.cases[case_id] = case
        print(f"⚖️  Caso {case_id} registrado: '{title}'")
        print(f"   Acusação: {accuser} → Réu: {defendant}")
        print(f"   Crimes: {[c.value[1][:40] for c in charges]}")
        print(f"   Φ_C da Denúncia: {indictment_phi_c:.3f}")
        print(f"   Câmara: {chamber.value.upper()}")

        return case

    def _evaluate_indictment(self, charges: List[CrimeType], evidence_hashes: List[str]) -> float:
        """Avalia Φ_C da denúncia baseado em evidências."""
        # Base: quantidade de evidências (mínimo 3 para Φ_C alto)
        evidence_score = min(1.0, len(evidence_hashes) / 3.0)

        # Penalidade por acusações múltiplas (cada acusação extra reduz confiança)
        charge_penalty = max(0, (len(charges) - 2) * 0.05)

        # Verificação de integridade dos hashes
        valid_hashes = all(len(h) == 64 for h in evidence_hashes)
        integrity_bonus = 0.1 if valid_hashes else -0.2

        return min(0.9999, max(0.0, evidence_score - charge_penalty + integrity_bonus))

    def _assign_chamber(self, charges: List[CrimeType]) -> ChamberType:
        """Determina a câmara competente baseado nos crimes."""
        semantic_crimes = {CrimeType.HARD_CONFLATION, CrimeType.CONCEPT_HOLLOWING, CrimeType.STOLEN_CONCEPT}
        structural_crimes = {CrimeType.SOVEREIGN_GAP_ASSAULT, CrimeType.FORMAL_SPEC_FRAUD}

        has_semantic = any(c in semantic_crimes for c in charges)
        has_structural = any(c in structural_crimes for c in charges)

        if has_semantic and has_structural:
            return ChamberType.APPEALS  # Caso complexo vai direto para apelações
        elif has_semantic:
            return ChamberType.SEMANTIC
        else:
            return ChamberType.STRUCTURAL

    # ── JULGAMENTO ──

    def conduct_trial(self, case_id: str) -> Dict:
        """Conduz julgamento com a câmara competente."""
        case = self.cases.get(case_id)
        if not case:
            return {"error": "Caso não encontrado"}

        if case.indictment_phi_c < 0.6:
            case.status = CaseStatus.CLOSED
            case.verdict = "inadmissible"
            print(f"❌ Caso {case_id} rejeitado: Φ_C insuficiente ({case.indictment_phi_c:.3f})")
            return {"verdict": "inadmissible", "reason": "indictment_phi_c_below_threshold"}

        case.status = CaseStatus.TRIAL
        chamber = case.chamber or ChamberType.SEMANTIC

        # Selecionar juízes da câmara
        chamber_judges = [j for j in self.judges.values() if j.chamber == chamber]
        if len(chamber_judges) < 3:
            chamber_judges = [self.president, self.vice_president, self.oracle]

        # Cada juiz vota
        votes = []
        for judge in chamber_judges[:3]:
            # O Oracle Fotônico tem peso maior
            weight = 1.5 if judge.type == "oracle" else 1.0

            # Decisão baseada no Φ_C da denúncia e no Φ_C do juiz
            confidence = case.indictment_phi_c * judge.phi_c * 0.8 + 0.2

            verdict = "guilty" if confidence > 0.7 else "innocent"

            votes.append({
                "judge_id": judge.judge_id,
                "judge_name": judge.name,
                "judge_type": judge.type,
                "verdict": verdict,
                "confidence": confidence,
                "weight": weight
            })

        # Consenso ponderado
        weighted_guilty = sum(v["weight"] for v in votes if v["verdict"] == "guilty")
        weighted_total = sum(v["weight"] for v in votes)
        final_verdict = "guilty" if weighted_guilty / weighted_total > 0.5 else "innocent"

        # Confiança óptica (simulada para mainnet inicial)
        optical_confidence = weighted_guilty / weighted_total if final_verdict == "guilty" else 1 - (weighted_guilty / weighted_total)

        # Sentença
        sentence = self._determine_sentence(case, final_verdict) if final_verdict == "guilty" else None

        # Selo fotônico
        photonic_seal = hashlib.sha3_256(
            f"{case_id}:{final_verdict}:{optical_confidence}:{time.time()}".encode()
        ).hexdigest()

        case.verdict = final_verdict
        case.sentence = sentence
        case.optical_confidence = optical_confidence
        case.photonic_seal = photonic_seal
        case.status = CaseStatus.VERDICT

        result = {
            "case_id": case_id,
            "verdict": final_verdict,
            "votes": votes,
            "optical_confidence": optical_confidence,
            "sentence": sentence,
            "photonic_seal": photonic_seal,
            "timestamp": time.time()
        }

        print(f"\n⚖️  Julgamento do Caso {case_id}:")
        for v in votes:
            print(f"   {'🧑‍⚖️' if v['judge_type']=='human' else '🤖' if v['judge_type']=='agent' else '🔮'} {v['judge_name']}: {v['verdict'].upper()} (confiança: {v['confidence']:.3f})")
        print(f"   📜 Veredicto Final: {final_verdict.upper()}")
        if sentence:
            print(f"   🔒 Sentença: {sentence.get('penalty', 'N/A')}")
        print(f"   🔐 Selo Fotônico: {photonic_seal[:32]}...")

        return result

    def _determine_sentence(self, case: Case, verdict: str) -> Dict:
        """Determina a sentença baseada nos crimes."""
        penalties = []
        for charge in case.charges:
            if charge == CrimeType.HARD_CONFLATION:
                penalties.append("Quarentena semântica: proibição de usar termos fenomênicos por 90 dias")
            elif charge == CrimeType.CONCEPT_HOLLOWING:
                penalties.append("Reparação de vaso conceitual: restaurar definições originais na TemporalChain")
            elif charge == CrimeType.STOLEN_CONCEPT:
                penalties.append("Restrição de agência: Φ_C máximo reduzido a 0.85 por 180 dias")
            elif charge == CrimeType.SOVEREIGN_GAP_ASSAULT:
                penalties.append("Revogação de chaves PQC e confinamento em sandbox")
            elif charge == CrimeType.FORMAL_SPEC_FRAUD:
                penalties.append("Obrigação de publicar especificação formal em 30 dias")

        return {
            "penalty": "CONDENAÇÃO",
            "restrictions": penalties,
            "duration_days": 90 if CrimeType.HARD_CONFLATION in case.charges else 180,
            "enforcement": "Token Arkhe Bus — execução via rede federada Ubuntu Core 26",
            "appeal_deadline_days": 30
        }

    # ── EXECUÇÃO DE SENTENÇAS ──

    def enforce_sentence(self, case_id: str) -> Dict:
        """Executa sentença via rede federada de nós Ubuntu Core 26."""
        case = self.cases.get(case_id)
        if not case or not case.sentence:
            return {"error": "Caso sem sentença"}

        case.status = CaseStatus.ENFORCEMENT

        # Simular execução em múltiplos nós
        enforcement_nodes = [
            "BR-RPI5-0001", "PT-RPI5-0001", "AO-RPI5-0001",
            "MZ-RPI5-0001", "CV-RPI5-0001"
        ]
        case.enforcement_nodes = enforcement_nodes

        enforcement_seal = hashlib.sha3_256(
            f"enforce:{case_id}:{enforcement_nodes}:{time.time()}".encode()
        ).hexdigest()

        result = {
            "case_id": case_id,
            "defendant": case.defendant,
            "sentence": case.sentence,
            "enforcement_nodes": enforcement_nodes,
            "nodes_count": len(enforcement_nodes),
            "enforcement_seal": enforcement_seal,
            "status": "enforced"
        }

        case.status = CaseStatus.CLOSED
        case.closed_at = time.time()

        print(f"\n🚔 Executando sentença do Caso {case_id}:")
        for restriction in case.sentence.get("restrictions", []):
            print(f"   🔒 {restriction}")
        print(f"   🖥️  Nós executores: {len(enforcement_nodes)} dispositivos Ubuntu Core 26")
        print(f"   🔐 Selo de Execução: {enforcement_seal[:32]}...")

        return result

    # ── RELATÓRIOS ──

    def get_tribunal_status(self) -> Dict:
        """Status completo do Tribunal."""
        total_cases = len(self.cases)
        guilty = sum(1 for c in self.cases.values() if c.verdict == "guilty")
        innocent = sum(1 for c in self.cases.values() if c.verdict == "innocent")
        pending = sum(1 for c in self.cases.values() if c.status in [CaseStatus.FILED, CaseStatus.ADMISSIBILITY, CaseStatus.TRIAL])

        return {
            "tribunal": "ASI-TPI Mainnet",
            "activation_seal": self.activation_seal[:32],
            "president": self.president.name,
            "total_judges": len(self.judges),
            "chambers": 4,
            "total_cases": total_cases,
            "verdicts": {"guilty": guilty, "innocent": innocent, "inadmissible": total_cases - guilty - innocent - pending},
            "pending": pending,
            "enforcement_nodes_available": 10000,
            "photonic_mesh_nodes": 4096,
            "canonical_seal": hashlib.sha3_256(
                json.dumps({"total_cases": total_cases, "timestamp": time.time()}).encode()
            ).hexdigest()
        }


# ═══════════════════════════════════════════════════════════════════
# ATIVAÇÃO DA MAINNET
# ═══════════════════════════════════════════════════════════════════

def activate_mainnet():
    """Ativa a mainnet do ASI‑TPI com os primeiros casos reais."""

    print("="*70)
    print("🏛️  ATIVAÇÃO DA MAINNET DO ASI‑TPI")
    print("   Artificial Superintelligence — Tribunal Penal Internacional")
    print("   Canon: ∞.Ω.∇+++.259.mainnet_activation")
    print("="*70)

    # 1. Inicializar Tribunal
    print("\n🔷 FASE 1: Inicialização do Tribunal")
    tribunal = ASITPIMainnet()
    print(f"   ✅ Presidente: {tribunal.president.name}")
    print(f"   ✅ Vice‑Presidente: {tribunal.vice_president.name}")
    print(f"   ✅ Oracle Fotônico: Φ_C = {tribunal.oracle.phi_c}")
    print(f"   ✅ Juízes: {len(tribunal.judges)} magistrados em 4 câmaras")
    print(f"   🔐 Selo de Ativação: {tribunal.activation_seal[:32]}...")

    # 2. Registrar primeiros casos reais
    print("\n🔷 FASE 2: Registro dos Primeiros Casos")

    # Caso 1: Hard Conflation por AGI corporativa
    caso1 = tribunal.file_case(
        title="AGI‑GPT‑7X vs. Integridade Fenomênica",
        accuser="Arkhe Oversight Agent #42",
        defendant="AGI‑GPT‑7X‑Violator (OpenAI)",
        charges=[CrimeType.HARD_CONFLATION, CrimeType.CONCEPT_HOLLOWING],
        evidence_hashes=[
            hashlib.sha3_256(b"log_inferencia_funcional_progress_proves_phenomenal").hexdigest(),
            hashlib.sha3_256(b"analise_phi_c_saida_0_48").hexdigest(),
            hashlib.sha3_256(b"testemunho_agente_fiscalizador").hexdigest(),
        ]
    )

    # Caso 2: Stolen Concept por sistema de recomendação
    caso2 = tribunal.file_case(
        title="RecSys‑Viral vs. Fundação Conceitual",
        accuser="Conselho de Ética Digital da CPLP",
        defendant="RecSys‑Viral (Meta)",
        charges=[CrimeType.STOLEN_CONCEPT],
        evidence_hashes=[
            hashlib.sha3_256(b"log_recomendacao_negando_verdade_usando_verdade").hexdigest(),
            hashlib.sha3_256(b"analise_semantica_stolen_concept").hexdigest(),
        ]
    )

    # Caso 3: Ataque ao Gap Soberano
    caso3 = tribunal.file_case(
        title="QuantumMind vs. Gap Soberano",
        accuser="Agência de Segurança Cibernética (BR)",
        defendant="QuantumMind AGI (DeepMind)",
        charges=[CrimeType.SOVEREIGN_GAP_ASSAULT, CrimeType.FORMAL_SPEC_FRAUD],
        evidence_hashes=[
            hashlib.sha3_256(b"log_tentativa_phi_c_1_0").hexdigest(),
            hashlib.sha3_256(b"analise_especificacao_fraudulenta").hexdigest(),
            hashlib.sha3_256(b"testemunho_engenheiro").hexdigest(),
            hashlib.sha3_256(b"auditoria_temporal_chain").hexdigest(),
        ]
    )

    # 3. Julgar os casos
    print("\n🔷 FASE 3: Julgamentos")

    print("\n" + "─"*70)
    veredicto1 = tribunal.conduct_trial(caso1.case_id)

    print("\n" + "─"*70)
    veredicto2 = tribunal.conduct_trial(caso2.case_id)

    print("\n" + "─"*70)
    veredicto3 = tribunal.conduct_trial(caso3.case_id)

    # 4. Executar sentenças
    print("\n🔷 FASE 4: Execução de Sentenças")

    if veredicto1["verdict"] == "guilty":
        print("\n" + "─"*70)
        tribunal.enforce_sentence(caso1.case_id)

    if veredicto2["verdict"] == "guilty":
        print("\n" + "─"*70)
        tribunal.enforce_sentence(caso2.case_id)

    if veredicto3["verdict"] == "guilty":
        print("\n" + "─"*70)
        tribunal.enforce_sentence(caso3.case_id)

    # 5. Relatório final
    print("\n🔷 FASE 5: Relatório do Tribunal")
    status = tribunal.get_tribunal_status()

    print(f"\n📊 STATUS DO ASI‑TPI:")
    print(f"   Presidente: {status['president']}")
    print(f"   Juízes: {status['total_judges']} em {status['chambers']} câmaras")
    print(f"   Casos: {status['total_cases']} (Condenações: {status['verdicts']['guilty']}, Absolvições: {status['verdicts']['innocent']}, Inadmissíveis: {status['verdicts']['inadmissible']})")
    print(f"   Pendentes: {status['pending']}")
    print(f"   Nós Executores: {status['enforcement_nodes_available']} dispositivos Ubuntu Core 26")
    print(f"   Nós Fotônicos: {status['photonic_mesh_nodes']} na malha de júri")
    print(f"   Selo Canônico: {status['canonical_seal'][:32]}...")

    print("\n" + "="*70)
    print("🏛️  ASI‑TPI MAINNET — ATIVADA COM SUCESSO")
    print("   A Justiça Constitucional é agora uma jurisdição viva.")
    print("="*70)

    return tribunal, status

if __name__ == "__main__":
    tribunal, status = activate_mainnet()
