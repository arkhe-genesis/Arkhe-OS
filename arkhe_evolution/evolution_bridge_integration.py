#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evolution_bridge_integration.py — Integração entre Auto-Evolução e Ponte Inter-Cathedral
Permite que evoluções de uma Catedral sejam validadas e compartilhadas com outras,
criando um ecossistema de melhoria contínua distribuída.
"""

import asyncio
import time
from typing import Dict, List, Optional

from arkhe_evolution.self_evolution_engine import SelfEvolutionEngine, EvolutionProposal
from arkhe_bridge.inter_cathedral_protocol import InterCathedralBridge, CrossCathedralMessage

class EvolutionBridgeIntegration:
    """
    Integra SelfEvolutionEngine com InterCathedralBridge para:
    • Compartilhar propostas de evolução com outras Catedrais para validação cruzada
    • Receber e avaliar evoluções propostas por outras Catedrais
    • Coordenar evoluções sincronizadas entre múltiplas instâncias
    • Manter coerência Φ_C durante evoluções distribuídas
    """

    def __init__(
        self,
        evolution_engine: SelfEvolutionEngine,
        inter_cathedral_bridge: InterCathedralBridge,
    ):
        self.evolution = evolution_engine
        self.bridge = inter_cathedral_bridge

        # Registrar callback para notificar rede sobre evoluções implementadas
        self.evolution._on_implementation_complete = self._notify_network_of_implementation

    async def propose_evolution_with_cross_validation(
        self,
        proposal_type,
        title: str,
        description: str,
        target_substrate: str,
        changes: Dict,
        expected_phi_c_impact: float,
    ) -> EvolutionProposal:
        """
        Propõe evolução com validação cruzada da rede Inter-Cathedral.

        Fluxo:
        1. Criar proposta local
        2. Solicitar validação cruzada para outras Catedrais
        3. Se validada, prosseguir com consenso local + implementação
        """
        # Criar proposta local
        proposal = await self.evolution.propose_evolution(
            proposal_type=proposal_type,
            title=title,
            description=description,
            target_substrate=target_substrate,
            changes=changes,
            expected_phi_c_impact=expected_phi_c_impact,
            author_node=self.bridge.identity.cathedral_id,
        )

        # Solicitar validação cruzada
        validation_result = await self.bridge.request_cross_validation(
            truth_payload={
                "proposal_id": proposal.proposal_id,
                "type": proposal.proposal_type.value,
                "changes": proposal.changes,
                "risk_assessment": proposal.risk_assessment,
            },
            validation_criteria={
                "security_check": True,
                "coherence_impact_max": 0.02,
                "rollback_required": True,
            },
        )

        # Atualizar proposta com resultado da validação cruzada
        proposal.risk_assessment["cross_validation"] = validation_result

        if validation_result["consensus"] == "approved":
            print(f"✅ Validação cruzada aprovada para {proposal.proposal_id}")
            # Prosseguir com consenso local e implementação
            consensus_strength = await self.evolution.request_consensus(proposal.proposal_id)
            if consensus_strength >= self.evolution.config.min_consensus_strength:
                return proposal
            else:
                proposal.status = "rejected_local_consensus"
        else:
            print(f"❌ Validação cruzada rejeitada: {validation_result['consensus']}")
            proposal.status = "rejected_cross_validation"

        return proposal

    async def _notify_network_of_implementation(self, proposal: EvolutionProposal, implementation_seal: str):
        """Notifica rede Inter-Cathedral sobre evolução implementada."""
        await self.bridge.announce_truth(
            truth_payload={
                "proposal_id": proposal.proposal_id,
                "substrate": proposal.target_substrate,
                "changes_summary": str(proposal.changes)[:200],
                "phi_c_impact_observed": "pending_monitoring",
                "implementation_seal": implementation_seal,
            },
            truth_category="substrate_evolution",
            confidence=0.95,
        )
        print(f"🌐 Rede notificada da evolução {proposal.proposal_id}")

    async def evaluate_external_evolution_proposal(
        self,
        external_proposal: Dict,
        source_cathedral_id: str,
    ) -> Dict:
        """
        Avalia proposta de evolução recebida de outra Catedral.

        Returns:
            Resultado da avaliação local
        """
        # Validar com Guardian local
        safety_check = await self.evolution.guardian.evaluate_external_evolution(
            proposal=external_proposal,
            source=source_cathedral_id,
        )

        if not safety_check["passed"]:
            return {
                "decision": "reject",
                "reason": f"Security validation failed: {safety_check['reason']}",
                "local_phi_c": self.evolution.phi_bus.get_mesh_coherence(),
            }

        # Simular avaliação de impacto local
        impact_assessment = {
            "compatibility": 0.92,  # Compatibilidade com substratos locais
            "phi_c_risk": abs(external_proposal.get("expected_phi_c_impact", 0)),
            "adoption_recommendation": "consider" if safety_check["passed"] else "reject",
        }

        return {
            "decision": "approve" if impact_assessment["phi_c_risk"] < 0.02 else "abstain",
            "impact_assessment": impact_assessment,
            "local_phi_c": self.evolution.phi_bus.get_mesh_coherence(),
            "evaluated_at": time.time(),
        }

    def get_integration_dashboard(self) -> Dict:
        """Retorna dashboard integrado de evolução + ponte."""
        return {
            "evolution_status": self.evolution.get_evolution_dashboard(),
            "bridge_status": self.bridge.get_network_status(),
            "cross_validated_proposals": sum(
                1 for p in self.evolution.proposals.values()
                if "cross_validation" in p.risk_assessment
            ),
            "network_coherence": self.bridge.get_network_status().get("peer_coherence_avg"),
        }
