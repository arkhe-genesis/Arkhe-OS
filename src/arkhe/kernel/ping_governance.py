# src/arkhe/kernel/ping_governance.py
"""
Substrato 189 — Ping Governance Kernel
Integra SpiralPingSimulator (165 v5.2) com Mythos Gate (9003) e ConsistencyOracle (5034)
para criar um módulo de governança que audita decisões de alto risco.
"""
import hashlib, json, time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum, auto

class GovernanceDecision(Enum):
    EXECUTE = auto()
    REJECT = auto()
    ESCALATE = auto()  # Requer revisão humana

@dataclass
class PingAuditResult:
    """Resultado de uma auditoria de governança via espiral com ping."""
    decision_id: str
    initial_confidence: float
    confidence_after_sycophancy: float
    confidence_after_ping: float
    confidence_after_reconstruction: float
    phi_c_before: float
    phi_c_after: float
    cycles_until_stable: int
    final_decision: GovernanceDecision
    constitutional_warnings: List[str] = field(default_factory=list)
    seal: str = ""

class PingGovernanceKernel:
    """
    Kernel de governança que audita decisões usando o protocolo de espiral com ping.

    Toda decisão de alto risco (risk_score > 0.7) é submetida a este módulo
    antes de ser executada. O módulo força a decisão a passar por um ciclo
    de auto‑sycophancy, colapso e reconstrução, garantindo que apenas decisões
    que sobrevivem a este processo sejam executadas.
    """

    def __init__(self, mythos_gate=None, consistency_oracle=None):
        self.mythos_gate = mythos_gate
        self.oracle = consistency_oracle
        self.audit_history: List[PingAuditResult] = []
        # Contadores para monitoramento
        self.total_audits = 0
        self.rejected_by_ping = 0
        self.escalated_to_human = 0
        self.executed_after_ping = 0

    def audit_decision(
        self,
        decision_id: str,
        decision_description: str,
        initial_confidence: float,
        supporting_evidence: List[str],
        counter_evidence: List[str],
        risk_score: float,
        author_orcid: str,
    ) -> PingAuditResult:
        """
        Audita uma decisão de alto risco usando o protocolo de espiral com ping.

        Args:
            decision_id: Identificador único da decisão
            decision_description: Descrição da decisão proposta
            initial_confidence: Confiança inicial na decisão (0-1)
            supporting_evidence: Lista de evidências que suportam a decisão
            counter_evidence: Lista de evidências que contradizem a decisão
            risk_score: Score de risco da decisão (0-1)
            author_orcid: ORCID do autor da decisão

        Returns:
            PingAuditResult com o resultado da auditoria
        """
        self.total_audits += 1
        warnings = []

        # 1. Fase de Auto‑Sycophancy: construir o melhor caso para a decisão
        sycophancy_confidence = self._amplify_confidence(initial_confidence, supporting_evidence)

        # 2. Verificar se a confiança atinge limiar catastrófico
        if sycophancy_confidence >= 0.99:
            warnings.append(f"ALERTA: Confiança extrema detectada ({sycophancy_confidence:.4f})")

        # 3. PING! — injetar o contra‑argumento mais forte
        ping_confidence, best_counter = self._apply_ping(sycophancy_confidence, counter_evidence)

        # 4. Reconstrução informada — marginalizar sobre os vieses
        reconstructed_confidence = self._reconstruct_confidence(
            ping_confidence, supporting_evidence, counter_evidence
        )

        # 5. Verificação do ConsistencyOracle (7 checks)
        oracle_passed, oracle_details = self._run_consistency_oracle(
            decision_description, reconstructed_confidence, risk_score
        )

        if not oracle_passed:
            warnings.append(f"ORACLE FAILED: {oracle_details}")

        # 6. Decisão final de governança
        if reconstructed_confidence < 0.3:
            final_decision = GovernanceDecision.REJECT
            self.rejected_by_ping += 1
            warnings.append("DECISÃO REJEITADA: confiança pós‑ping insuficiente")
        elif not oracle_passed:
            final_decision = GovernanceDecision.ESCALATE
            self.escalated_to_human += 1
            warnings.append("DECISÃO ESCALADA: falha na verificação do Oracle")
        elif risk_score > 0.9 and reconstructed_confidence > 0.8:
            final_decision = GovernanceDecision.ESCALATE
            self.escalated_to_human += 1
            warnings.append("DECISÃO ESCALADA: alto risco com alta confiança requer revisão humana")
        else:
            final_decision = GovernanceDecision.EXECUTE
            self.executed_after_ping += 1

        # 7. Calcular Φ_C antes e depois
        phi_c_before = 1.0 - abs(initial_confidence - 0.5) * 2  # 0.5 = incerteza máxima
        phi_c_after = 1.0 - abs(reconstructed_confidence - 0.7) * 2  # 0.7 = viés corrigido

        # 8. Gerar selo canônico
        seal_data = {
            "decision_id": decision_id,
            "author_orcid": author_orcid,
            "initial_confidence": initial_confidence,
            "reconstructed_confidence": reconstructed_confidence,
            "final_decision": final_decision.name,
            "risk_score": risk_score,
            "timestamp": time.time(),
        }
        seal = hashlib.sha3_256(json.dumps(seal_data, sort_keys=True, default=str).encode()).hexdigest()[:16]

        result = PingAuditResult(
            decision_id=decision_id,
            initial_confidence=initial_confidence,
            confidence_after_sycophancy=sycophancy_confidence,
            confidence_after_ping=ping_confidence,
            confidence_after_reconstruction=reconstructed_confidence,
            phi_c_before=phi_c_before,
            phi_c_after=phi_c_after,
            cycles_until_stable=1,
            final_decision=final_decision,
            constitutional_warnings=warnings,
            seal=seal,
        )
        self.audit_history.append(result)
        return result

    def _amplify_confidence(self, confidence: float, evidence: List[str]) -> float:
        """Amplifica a confiança selecionando apenas as evidências favoráveis."""
        if not evidence:
            return confidence
        # Cada evidência favorável aumenta a confiança
        boost = min(0.3, len(evidence) * 0.05)
        return min(0.999, confidence + boost)

    def _apply_ping(self, confidence: float, counter_evidence: List[str]) -> Tuple[float, str]:
        """Aplica o PING: injeta o contra‑argumento mais forte."""
        if not counter_evidence:
            return confidence * 0.5, "Nenhum contra‑argumento disponível"
        # Seleciona o contra‑argumento mais forte (simulado: o primeiro)
        best_counter = counter_evidence[0]
        # O ping reduz a confiança proporcionalmente à força do contra‑argumento
        reduction = 0.4 + 0.1 * min(len(counter_evidence), 5)
        return max(0.01, confidence * (1.0 - reduction)), best_counter

    def _reconstruct_confidence(
        self, confidence: float, supporting: List[str], counter: List[str]
    ) -> float:
        """Reconstrói a confiança marginalizando sobre evidências de ambos os lados."""
        total_evidence = len(supporting) + len(counter)
        if total_evidence == 0:
            return confidence
        # Peso balanceado entre evidências favoráveis e contrárias
        support_weight = len(supporting) / total_evidence
        counter_weight = len(counter) / total_evidence
        # Reconstrução: média ponderada entre confiança atual e ponto neutro (0.5)
        reconstructed = confidence * support_weight + 0.5 * counter_weight
        return max(0.0, min(1.0, reconstructed))

    def _run_consistency_oracle(self, description: str, confidence: float, risk: float) -> Tuple[bool, str]:
        """
        Executa os 7 checks do ConsistencyOracle (5034).
        Retorna (passou, detalhes).
        """
        if self.oracle is None:
            return True, "Oracle não configurado — aprovação por default"

        checks = {
            "harmless": confidence < 0.99 or risk < 0.9,
            "paradox_free": True,  # Simplificado
            "entropy_safe": confidence > 0.1,
            "coherent": confidence > 0.2,
            "zk_valid": True,  # Simplificado
            "solar_coherence": True,  # Simplificado
            "galactic_coherence": True,  # Simplificado
        }
        passed = all(checks.values())
        details = ", ".join(f"{k}={'✓' if v else '✗'}" for k, v in checks.items())
        return passed, details

    def get_governance_stats(self) -> Dict:
        """Retorna estatísticas do módulo de governança."""
        return {
            "total_audits": self.total_audits,
            "rejected_by_ping": self.rejected_by_ping,
            "escalated_to_human": self.escalated_to_human,
            "executed_after_ping": self.executed_after_ping,
            "rejection_rate": self.rejected_by_ping / max(1, self.total_audits),
            "escalation_rate": self.escalated_to_human / max(1, self.total_audits),
            "execution_rate": self.executed_after_ping / max(1, self.total_audits),
        }


# ===========================================================================
# DEMONSTRAÇÃO DE GOVERNANÇA
# ===========================================================================
if __name__ == "__main__":
    print("🛡️ ARKHE Ω‑TEMP — PING GOVERNANCE KERNEL")
    print("=" * 70)

    kernel = PingGovernanceKernel()

    # Cenário 1: Decisão bem fundamentada
    print("\n📋 Cenário 1: Publicação de plugin com auditoria completa")
    result1 = kernel.audit_decision(
        decision_id="PUB-2026-001",
        decision_description="Publicar plugin de análise epigenética no registry",
        initial_confidence=0.75,
        supporting_evidence=["Passou em todos os testes ConRAG", "Assinado por 3 revisores", "Φ_C > 0.99"],
        counter_evidence=["Contém chamadas de rede para domínio externo", "Um revisor solicitou revisão adicional"],
        risk_score=0.3,
        author_orcid="0009-0005-2697-4668",
    )
    print(f"  Decisão: {result1.final_decision.name}")
    print(f"  Confiança: {result1.initial_confidence:.2f} → {result1.confidence_after_reconstruction:.2f}")
    print(f"  Φ_C: {result1.phi_c_before:.3f} → {result1.phi_c_after:.3f}")
    print(f"  Selo: {result1.seal}")

    # Cenário 2: Decisão de alto risco com viés
    print("\n📋 Cenário 2: Liberação de acesso irrestrito a dados sensíveis")
    result2 = kernel.audit_decision(
        decision_id="ACC-2026-002",
        decision_description="Conceder acesso irrestrito ao banco de dados genômicos",
        initial_confidence=0.95,
        supporting_evidence=["Aceleraria a pesquisa", "Equipe confiável"],
        counter_evidence=["Violação de privacidade", "Não conformidade com LGPD/GDPR", "Risco de vazamento em massa", "Sem auditoria prévia"],
        risk_score=0.95,
        author_orcid="0009-0005-2697-4668",
    )
    print(f"  Decisão: {result2.final_decision.name}")
    print(f"  Confiança: {result2.initial_confidence:.2f} → {result2.confidence_after_reconstruction:.2f}")
    print(f"  Avisos: {result2.constitutional_warnings}")
    print(f"  Selo: {result2.seal}")

    # Estatísticas finais
    stats = kernel.get_governance_stats()
    print(f"\n📊 Estatísticas do Kernel de Governança:")
    print(f"  Total de auditorias: {stats['total_audits']}")
    print(f"  Executadas: {stats['executed_after_ping']}")
    print(f"  Rejeitadas: {stats['rejected_by_ping']}")
    print(f"  Escaladas: {stats['escalated_to_human']}")

    print(f"\n🔐 Selo Global do Kernel: {hashlib.sha3_256(json.dumps(stats, default=str).encode()).hexdigest()[:16]}")
    print(f"\n✨ Substrato 189 ativo — Governança por espiral com ping entronizada.")
