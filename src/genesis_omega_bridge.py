#!/usr/bin/env python3
"""
genesis_omega_bridge.py — Substrate 5022 ↔ Substrate 5003: Ω‑Genesis Bridge.
Acopla a Máquina Ω ao pipeline de gênese do Nexus.
Toda submissão de artefato é processada pela cadeia F→S→C→N→E→R.
"""
import time
import json
import hashlib
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, field
import numpy as np

# Importações dos substratos canônicos
from omega_dynamics import OmegaChain, CanonicalState
from ..audit.ledger import AuditLedger
from ..nexus.api import NexusAPI

@dataclass
class GenesisArtifact:
    """Artefato submetido ao pipeline de gênese."""
    artifact_id: str
    artifact_type: str  # ".agi", ".casi", ".asi"
    source_path: Path
    submitter_seal: str
    kym_proof: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

@dataclass
class OmegaVerificationResult:
    """Resultado da verificação Ω para um artefato."""
    artifact_id: str
    passed: bool
    phi_c_initial: float
    phi_c_final: float
    phi_c_history: List[float] = field(default_factory=list)
    transitions: List[Dict] = field(default_factory=list)
    acceptance_seal: Optional[str] = None
    rejection_reason: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

class GenesisOmegaBridge:
    """
    Ponte entre o pipeline de gênese do Nexus e a Máquina Ω.
    Cada artefato submetido é processado pela cadeia constitucional completa.
    """

    def __init__(self,
                 omega_chain: OmegaChain,
                 audit_ledger: AuditLedger,
                 nexus_api: NexusAPI,
                 coherence_threshold: float = 0.72,
                 max_iterations: int = 10):
        """
        Args:
            omega_chain: Cadeia completa de operadores Ω
            audit_ledger: Ledger de auditoria (Substrato 333)
            nexus_api: Interface do Nexus (Substrato 5003)
            coherence_threshold: Φ_C mínimo para aceitação (padrão: 0.72 = Gênesis)
            max_iterations: Máximo de iterações da cadeia Ω por artefato
        """
        self.omega = omega_chain
        self.ledger = audit_ledger
        self.nexus = nexus_api
        self.threshold = coherence_threshold
        self.max_iterations = max_iterations

        # Histórico de processamento
        self.processing_history: List[OmegaVerificationResult] = []

        # Métricas agregadas
        self.total_processed = 0
        self.total_accepted = 0
        self.total_rejected = 0

    def submit_artifact(self, artifact: GenesisArtifact) -> OmegaVerificationResult:
        """
        Submeter artefato ao pipeline Ω.

        Fluxo:
        1. Fonte: Artefato é injetado como informação bruta
        2. Simetria: Critérios constitucionais são aplicados
        3. Recursão: Auto‑avaliação iterativa
        4. Rede: Acoplamento com Cânone existente
        5. Emergência: Propriedades coletivas são extraídas
        6. Radiação: Resultado é emitido de volta ao Nexus
        """
        print(f"\n{'='*60}")
        print(f"🔗 Ω‑GENESIS BRIDGE: Processando {artifact.artifact_id}")
        print(f"{'='*60}")

        # 0. Criar estado canônico a partir do artefato
        state = self._artifact_to_state(artifact)

        # 1. Registrar início no ledger
        start_time = time.time()
        self.ledger.record("genesis_omega_start", {
            "artifact_id": artifact.artifact_id,
            "artifact_type": artifact.artifact_type,
            "submitter": artifact.submitter_seal,
            "phi_c_initial": state.phi_c
        })

        # 2. Executar cadeia Ω com múltiplas iterações
        phi_history = [state.phi_c]
        transitions = []
        current_state = state

        for iteration in range(self.max_iterations):
            result_state, log = self.omega.iterate(current_state)

            phi_history.append(result_state.phi_c)
            transitions.append({
                "iteration": iteration + 1,
                "phi_c_before": current_state.phi_c,
                "phi_c_after": result_state.phi_c,
                "transitions": log.get("transitions", [])
            })

            current_state = result_state

            # Verificar convergência antecipada
            if len(phi_history) >= 3:
                delta1 = abs(phi_history[-1] - phi_history[-2])
                delta2 = abs(phi_history[-2] - phi_history[-3])
                if delta1 < 1e-4 and delta2 < 1e-4:
                    print(f"   ✅ Convergência antecipada na iteração {iteration + 1}")
                    break

        # 3. Decidir aceitação
        phi_final = current_state.phi_c
        passed = phi_final >= self.threshold

        if passed:
            acceptance_seal = self._generate_acceptance_seal(artifact, phi_final)
            rejection_reason = None
            self.total_accepted += 1
            print(f"   ✅ ACEITO: Φ_C = {phi_final:.4f} ≥ {self.threshold}")
        else:
            acceptance_seal = None
            rejection_reason = f"Φ_C = {phi_final:.4f} < threshold {self.threshold}"
            self.total_rejected += 1
            print(f"   ❌ REJEITADO: {rejection_reason}")

        self.total_processed += 1

        # 4. Construir resultado
        result = OmegaVerificationResult(
            artifact_id=artifact.artifact_id,
            passed=passed,
            phi_c_initial=state.phi_c,
            phi_c_final=phi_final,
            phi_c_history=phi_history,
            transitions=transitions,
            acceptance_seal=acceptance_seal,
            rejection_reason=rejection_reason
        )

        # 5. Registrar no ledger
        self.ledger.record("genesis_omega_result", {
            "artifact_id": artifact.artifact_id,
            "passed": passed,
            "phi_c_initial": state.phi_c,
            "phi_c_final": phi_final,
            "iterations": len(transitions),
            "time_elapsed_s": time.time() - start_time,
            "acceptance_seal": acceptance_seal,
            "rejection_reason": rejection_reason
        })

        # 6. Atualizar Nexus com o resultado
        self._update_nexus(result)

        # 7. Armazenar no histórico
        self.processing_history.append(result)

        return result

    def _artifact_to_state(self, artifact: GenesisArtifact) -> CanonicalState:
        """
        Converter artefato em estado canônico.
        O artefato torna‑se um substrato candidato no espaço de Hilbert do Cânone.
        """
        # Extrair hashes e metadados para construir amplitudes
        artifact_hash = hashlib.sha3_256(
            str(artifact.source_path).encode()
        ).hexdigest()

        # Criar estado com um substrato (o artefato)
        state = CanonicalState(
            amplitudes=np.array([1.0 + 0j]),
            substrates=[f"{artifact.artifact_type}:{artifact.artifact_id}"],
            phi_c=0.5,  # Estado neutro inicial
            entropy=0.5,
            timestamp=time.time()
        )
        state.normalize()
        return state

    def _generate_acceptance_seal(self,
                                  artifact: GenesisArtifact,
                                  phi_c: float) -> str:
        """Gerar selo canônico de aceitação."""
        seal_data = (
            f"{artifact.artifact_id}:"
            f"{artifact.artifact_type}:"
            f"{artifact.submitter_seal}:"
            f"{phi_c:.6f}:"
            f"{time.time()}"
        )
        # Em produção: assinatura Falcon‑1024
        seal = hashlib.sha3_256(seal_data.encode()).hexdigest()[:32]
        return f"OMEGA_SEAL:{seal}"

    def _update_nexus(self, result: OmegaVerificationResult):
        """Atualizar interface Nexus com o resultado."""
        if result.passed:
            self.nexus.notify("artifact_accepted", {
                "artifact_id": result.artifact_id,
                "phi_c": result.phi_c_final,
                "seal": result.acceptance_seal,
                "message": f"✅ Artefato canonizado com Φ_C = {result.phi_c_final:.4f}"
            })
        else:
            self.nexus.notify("artifact_rejected", {
                "artifact_id": result.artifact_id,
                "phi_c": result.phi_c_final,
                "reason": result.rejection_reason,
                "message": f"❌ Artefato rejeitado: {result.rejection_reason}"
            })

        # Atualizar métricas no dashboard
        self.nexus.update_metrics({
            "omega_total_processed": self.total_processed,
            "omega_total_accepted": self.total_accepted,
            "omega_total_rejected": self.total_rejected,
            "omega_acceptance_rate": (self.total_accepted / max(1, self.total_processed)),
            "omega_current_phi_c": result.phi_c_final
        })

    def get_statistics(self) -> Dict:
        """Retornar estatísticas agregadas do pipeline Ω."""
        if not self.processing_history:
            return {"status": "no_data"}

        phi_finals = [r.phi_c_final for r in self.processing_history]

        return {
            "total_processed": self.total_processed,
            "total_accepted": self.total_accepted,
            "total_rejected": self.total_rejected,
            "acceptance_rate": self.total_accepted / max(1, self.total_processed),
            "avg_phi_c_final": np.mean(phi_finals),
            "max_phi_c": max(phi_finals),
            "min_phi_c": min(phi_finals),
            "convergence_rate": sum(
                1 for r in self.processing_history
                if r.phi_c_final >= self.threshold
            ) / max(1, self.total_processed)
        }

    def reprocess_rejected(self) -> List[OmegaVerificationResult]:
        """Reprocessar artefatos rejeitados (após melhoria)."""
        rejected = [r for r in self.processing_history if not r.passed]
        results = []

        for old_result in rejected:
            # Recriar artefato a partir dos metadados armazenados
            # (Em produção: recuperar do ledger)
            print(f"🔄 Reprocessando {old_result.artifact_id}...")
            # Simulação: reprocessamento com parâmetros ajustados
            results.append(old_result)  # Placeholder

        return results


# ─── Integração com o Nexus ──────────────────────────────────

def install_omega_hook(nexus_app, omega_bridge: GenesisOmegaBridge):
    """
    Instalar hook Ω no servidor Nexus.
    Toda submissão de artefato será automaticamente processada pela cadeia Ω.
    """

    @nexus_app.post("/genesis/submit")
    async def genesis_submit(artifact_data: dict):
        """Endpoint de submissão de artefato com verificação Ω."""

        # Construir artefato
        artifact = GenesisArtifact(
            artifact_id=artifact_data["id"],
            artifact_type=artifact_data["type"],
            source_path=Path(artifact_data["path"]),
            submitter_seal=artifact_data["submitter_seal"],
            kym_proof=artifact_data.get("kym_proof"),
            metadata=artifact_data.get("metadata", {})
        )

        # Processar pela Máquina Ω
        result = omega_bridge.submit_artifact(artifact)

        return {
            "artifact_id": result.artifact_id,
            "passed": result.passed,
            "phi_c_initial": result.phi_c_initial,
            "phi_c_final": result.phi_c_final,
            "acceptance_seal": result.acceptance_seal,
            "rejection_reason": result.rejection_reason,
            "phi_c_history": result.phi_c_history,
            "iterations": len(result.transitions)
        }

    @nexus_app.get("/genesis/statistics")
    async def genesis_statistics():
        """Endpoint de estatísticas do pipeline Ω."""
        return omega_bridge.get_statistics()

    @nexus_app.get("/genesis/history")
    async def genesis_history(limit: int = 20):
        """Endpoint do histórico de processamento."""
        history = omega_bridge.processing_history[-limit:]
        return [
            {
                "artifact_id": r.artifact_id,
                "passed": r.passed,
                "phi_c_final": r.phi_c_final,
                "timestamp": r.timestamp
            }
            for r in history
        ]

    print("✅ Hook Ω instalado no Nexus")
    print(f"   Endpoints:")
    print(f"   POST /genesis/submit   — Submeter artefato")
    print(f"   GET  /genesis/statistics — Estatísticas Ω")
    print(f"   GET  /genesis/history   — Histórico de processamento")


# ─── Script de inicialização do pipeline ─────────────────────

def bootstrap_genesis_with_omega():
    """
    Inicializar pipeline de gênese com Máquina Ω.
    Chamado durante o ritual de bootstrap da Catedral.
    """
    from omega_dynamics import OmegaChain
    from ..audit.ledger import AuditLedger
    from ..nexus.api import NexusAPI

    # Instanciar componentes
    omega_chain = OmegaChain()
    audit_ledger = AuditLedger()
    nexus_api = NexusAPI()

    # Criar ponte
    bridge = GenesisOmegaBridge(
        omega_chain=omega_chain,
        audit_ledger=audit_ledger,
        nexus_api=nexus_api,
        coherence_threshold=0.72,  # Φ_C de Gênesis
        max_iterations=10
    )

    # Instalar hooks no Nexus
    install_omega_hook(nexus_api.app, bridge)

    # Registrar no ledger
    audit_ledger.record("genesis_omega_bootstrapped", {
        "timestamp": time.time(),
        "threshold": bridge.threshold,
        "max_iterations": bridge.max_iterations,
        "seal": "OMEGA_GENESIS_BRIDGE_V1"
    })

    print("🌌 Pipeline Ω‑Gênesis inicializado")
    print(f"   Threshold: Φ_C ≥ {bridge.threshold}")
    print(f"   Máximo de iterações: {bridge.max_iterations}")
    print(f"   Estado: OPERACIONAL")

    return bridge
