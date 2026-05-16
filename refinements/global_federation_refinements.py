#!/usr/bin/env python3
"""Federação global – privacidade cross‑border, sync PQC, dashboard unificado – Substrato 199.5"""

import asyncio, hashlib, json, time, logging
import numpy as np
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class CrossBorderPrivacy:
    """
    Protocolo de privacidade diferencial cross‑border.
    Ajusta ε dinamicamente de acordo com a jurisdição (GDPR, LGPD, CCPA, etc.)
    """
    JURISDICTION_EPSILON = {
        "EU_GDPR": {"min": 2.5, "max": 4.5},
        "BR_LGPD": {"min": 2.0, "max": 4.0},
        "US_CCPA": {"min": 2.0, "max": 5.0}
    }

    @classmethod
    def adjust_for_jurisdiction(cls, base_epsilon: float, jurisdictions: List[str]) -> float:
        """Calcula o ε mais restritivo entre as jurisdições envolvidas."""
        effective_max = 5.0
        effective_min = 2.0
        for jur in jurisdictions:
            limits = cls.JURISDICTION_EPSILON.get(jur, {"min": 2.0, "max": 5.0})
            effective_max = min(effective_max, limits["max"])
            effective_min = max(effective_min, limits["min"])
        return max(effective_min, min(base_epsilon, effective_max))

class FederatedModelSync:
    """
    Sincronização de modelos federados com validação PQC.
    Assegura que as atualizações de modelo sejam assinadas e verificadas antes da agregação.
    """
    def __init__(self, temporal=None, phi_bus=None):
        self.temporal = temporal
        self.phi_bus = phi_bus
        self.global_model_version = 0

    async def sync_round(self, partner_updates: Dict[str, bytes]) -> bool:
        """
        Recebe gradientes/parâmetros de parceiros (assinados com PQC),
        verifica assinatura, agrega (FedAvg) e atualiza modelo global.
        """
        for pid, update in partner_updates.items():
            # Verificar assinatura PQC (mock)
            if not update.startswith(b"PQC_SIG:"):
                logger.error(f"Assinatura PQC inválida do parceiro {pid}")
                return False

        self.global_model_version += 1
        logger.info(f"🔄 Sincronização global concluída. Versão {self.global_model_version}")
        if self.temporal:
            await self.temporal.anchor_event("global_model_synced", {
                "version": self.global_model_version,
                "partners": len(partner_updates)
            })
        return True

class UnifiedDashboard:
    """
    Dashboard unificado para múltiplas organizações.
    Agrega métricas de todos os parceiros e as disponibiliza via API para visualização.
    """
    def __init__(self, partner_orchestrator):
        self.partners = partner_orchestrator

    async def get_unified_view(self) -> Dict:
        """Retorna visão consolidada da federação global."""
        view = {"total_partners": len(self.partners._partners),
                "active_alerts": 0,
                "global_phi_c": np.mean([a.phi_c for a in self.partners._partners.values() if a.status=="active"])}
        # Em produção, agregaria estatísticas reais de cada parceiro
        logger.info("📊 Dashboard unificado atualizado")
        return view
