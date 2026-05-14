#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ma_s2_integration.py — Integração do TemporalChain com conformidade MA‑S2.
Cada controle MA‑S2 gera eventos auditáveis na cadeia temporal.
"""

from typing import Dict, Optional
from .core import TemporalChain, EventType
import time

class MA_S2_TimechainIntegration:
    """Integração que mapeia controles MA‑S2 para eventos na Timechain."""

    # Mapeamento de controles MA‑S2 → tipos de evento
    CONTROL_EVENT_MAP = {
        # CVS
        "CVS-0.1": EventType.CVS_SCAN,
        "CVS-0.2": EventType.CVS_SCAN,
        "CVS-0.3": EventType.CVS_SCAN,
        "CVS-0.4": EventType.CVS_SCAN,
        "CVS-0.5": EventType.CVS_SCAN,
        # APM
        "APM-1.1": EventType.APM_PATH,
        "APM-1.2": EventType.APM_PATH,
        "APM-1.3": EventType.APM_PATH,
        "APM-1.4": EventType.APM_PATH,
        # INV
        "INV-2.1": EventType.INV_SBOM,
        "INV-2.2": EventType.INV_SBOM,
        "INV-2.3": EventType.INV_SBOM,
        "INV-2.4": EventType.INV_SBOM,
        "INV-2.5": EventType.INV_SBOM,
        # ARO
        "ARO-3.1": EventType.ARO_DEPLOY,
        "ARO-3.2": EventType.ARO_DEPLOY,
        "ARO-3.3": EventType.ARO_DEPLOY,
        "ARO-3.4": EventType.ARO_DEPLOY,
        "ARO-3.5": EventType.ARO_DEPLOY,
        "ARO-3.6": EventType.ARO_DEPLOY,
    }

    def __init__(self, timechain: TemporalChain):
        self.timechain = timechain

    async def log_control_execution(
        self,
        control_id: str,
        execution_result: Dict,
        metadata: Optional[Dict] = None,
        causal_deps: Optional[list] = None,
    ) -> str:
        """
        Registra execução de controle MA‑S2 na cadeia temporal.

        Returns:
            Seal do evento ancorado
        """
        event_type = self.CONTROL_EVENT_MAP.get(control_id, EventType.CUSTOM)

        payload = {
            "control_id": control_id,
            "result": execution_result,
            "compliance_status": execution_result.get("status", "unknown"),
        }

        anchor = await self.timechain.anchor_event(
            event_type=event_type,
            payload=payload,
            metadata={
                "ma_s2_control": control_id,
                "domain": control_id.split("-")[0],
                **(metadata or {}),
            },
            causal_deps=causal_deps,
        )

        return anchor.event.seal

    async def generate_compliance_proof(
        self,
        control_ids: list,
        time_range: Optional[tuple] = None,
    ) -> Dict:
        """
        Gera prova de conformidade para auditoria externa.

        Returns:
            Dict com eventos relevantes, selos e prova Merkle
        """
        events = []
        seals = []

        for control_id in control_ids:
            event_type = self.CONTROL_EVENT_MAP.get(control_id)
            if not event_type:
                continue

            query_params = {"event_type": event_type.value}
            if time_range:
                query_params["start_time"] = time_range[0]
                query_params["end_time"] = time_range[1]

            control_events = await self.timechain.query_events(**query_params, limit=1000)
            events.extend(control_events)
            seals.extend([e.seal for e in control_events])

        # Gerar prova Merkle para os selos
        merkle_proof = None
        if seals and self.timechain.merkle_root:
            # Em produção: gerar prova Merkle real
            merkle_proof = {
                "root": self.timechain.merkle_root,
                "event_seals": seals[:10],  # Limitar para demo
            }

        return {
            "control_ids": control_ids,
            "event_count": len(events),
            "event_seals": [e[:16] + "..." for e in seals],
            "merkle_proof": merkle_proof,
            "chain_seal": self.timechain.current_seal,
            "generated_at": time.time(),
        }
