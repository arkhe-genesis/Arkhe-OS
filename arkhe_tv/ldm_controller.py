#!/usr/bin/env python3
"""
Substrato 9033 — Arkhe TV: LDM Controller
Gerencia a multiplexação em camadas (Layered Division Multiplexing)
do ATSC 3.0, ajustando injeção de potência entre Core Layer e
Enhanced Layer com base na coerência Φ_C e métricas de recepção.
"""

import asyncio, hashlib, json, time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

class LDMMode(Enum):
    """Modos de operação LDM."""
    FIXED = "fixed"           # Injeção fixa (ex.: -10 dB)
    ADAPTIVE = "adaptive"     # Ajuste dinâmico baseado em Φ_C
    BALANCED = "balanced"     # Balanceia robustez vs capacidade
    ROBUST = "robust"         # Prioriza Core Layer (móvel/portátil)
    MAX_CAPACITY = "max_capacity"  # Prioriza Enhanced Layer (fixo 4K)

@dataclass
class LDMConfig:
    """Configuração de LDM entre duas PLPs."""
    core_plp_id: int
    enhanced_plp_id: int
    injection_level_db: float    # Potência da EL relativa à CL (negativo)
    mode: LDMMode = LDMMode.ADAPTIVE
    phi_c_target: float = 0.95
    adjustment_step_db: float = 0.5
    min_injection_db: float = -15.0
    max_injection_db: float = -3.0

@dataclass
class LDMMetrics:
    """Métricas de desempenho LDM."""
    core_layer_cnr_db: float
    enhanced_layer_cnr_db: float
    injection_level_db: float
    core_bitrate_mbps: float
    enhanced_bitrate_mbps: float
    phi_c_coherence: float
    timestamp: float = field(default_factory=time.time)

class LDMController:
    """
    Controlador de Layered Division Multiplexing (LDM) para ATSC 3.0.

    Ajusta dinamicamente o nível de injeção da Enhanced Layer sobre
    a Core Layer, balanceando:
    - Robustez da CL (para recepção móvel/portátil)
    - Capacidade da EL (para recepção fixa 4K HDR)

    A decisão é guiada por Φ_C: se a coerência cai, reduz a EL
    para proteger a CL; se sobe, aumenta a EL para maximizar qualidade.

    Comunica‑se com o headend Harmonic XOS via API REST.
    """

    def __init__(
        self,
        xos_adapter,  # HarmonicXOSAdapter instance
        temporal_chain=None,
        phi_bus=None,
        config: Optional[LDMConfig] = None,
    ):
        self.xos = xos_adapter
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self.config = config or LDMConfig(core_plp_id=1, enhanced_plp_id=2, injection_level_db=-10.0)
        self.history: List[LDMMetrics] = []
        self.current_injection_db = self.config.injection_level_db or -10.0

    async def get_current_metrics(self) -> LDMMetrics:
        """Obtém métricas atuais das PLPs via API do XOS."""
        plps = await self.xos.get_active_plps()

        core = next((p for p in plps if p.plp_id == self.config.core_plp_id), None)
        enhanced = next((p for p in plps if p.plp_id == self.config.enhanced_plp_id), None)

        if not core or not enhanced:
            raise RuntimeError("PLPs não encontradas no headend")

        # Φ_C agregado: média ponderada das duas camadas
        phi_c = 0.6 * core.phi_c + 0.4 * enhanced.phi_c

        metrics = LDMMetrics(
            core_layer_cnr_db=core.cnr_threshold_db + 5,  # simulado
            enhanced_layer_cnr_db=enhanced.cnr_threshold_db + 3,
            injection_level_db=self.current_injection_db,
            core_bitrate_mbps=core.bitrate_mbps,
            enhanced_bitrate_mbps=enhanced.bitrate_mbps,
            phi_c_coherence=phi_c,
        )

        self.history.append(metrics)
        if len(self.history) > 100:
            self.history.pop(0)

        return metrics

    async def optimize(self) -> float:
        """
        Executa uma iteração de otimização LDM.

        Returns:
            Novo nível de injeção em dB
        """
        if self.config.mode == LDMMode.FIXED:
            return self.current_injection_db

        metrics = await self.get_current_metrics()
        phi_c = metrics.phi_c_coherence

        # Calcular tendência de Φ_C
        if len(self.history) >= 5:
            recent_phi = [m.phi_c_coherence for m in self.history[-5:]]
            trend = recent_phi[-1] - recent_phi[0]
        else:
            trend = 0.0

        # Ajustar injeção baseado em Φ_C e tendência
        step = self.config.adjustment_step_db

        if phi_c < self.config.phi_c_target - 0.03:
            # Φ_C muito baixo → reduzir EL (aumentar robustez da CL)
            new_injection = max(
                self.config.min_injection_db,
                self.current_injection_db - step * 2
            )
        elif phi_c < self.config.phi_c_target:
            # Φ_C abaixo do alvo → leve redução
            new_injection = max(
                self.config.min_injection_db,
                self.current_injection_db - step
            )
        elif phi_c > self.config.phi_c_target + 0.02 and trend >= 0:
            # Φ_C acima do alvo e estável/subindo → aumentar EL (mais capacidade)
            new_injection = min(
                self.config.max_injection_db,
                self.current_injection_db + step
            )
        else:
            # Manter
            new_injection = self.current_injection_db

        # Arredondar para 0.5 dB
        new_injection = round(new_injection * 2) / 2

        # Aplicar mudança se necessário
        if abs(new_injection - self.current_injection_db) >= 0.5:
            await self._apply_injection(new_injection)
            self.current_injection_db = new_injection

            # Ancorar ajuste na TemporalChain
            if self.temporal:
                await self.temporal.anchor_event("ldm_adjusted", {
                    "core_plp": self.config.core_plp_id,
                    "enhanced_plp": self.config.enhanced_plp_id,
                    "previous_injection_db": self.current_injection_db,
                    "new_injection_db": new_injection,
                    "phi_c": phi_c,
                    "trend": trend,
                    "timestamp": time.time(),
                })

        return self.current_injection_db

    async def _apply_injection(self, injection_db: float):
        """Aplica novo nível de injeção via API do Harmonic XOS."""
        await self.xos.set_ldm_config(
            core_plp=self.config.core_plp_id,
            enhanced_plp=self.config.enhanced_plp_id,
            injection_db=injection_db,
        )
        print(f"⚡ LDM adjusted: injection={injection_db:.1f} dB")

    async def run_adaptive_loop(self, interval_s: float = 5.0):
        """Loop contínuo de otimização adaptativa."""
        print(f"🔄 LDM Adaptive loop started (interval={interval_s}s)")
        while True:
            try:
                new_inj = await self.optimize()
                print(f"   LDM Status: injection={new_inj:.1f} dB | Φ_C={self.history[-1].phi_c_coherence:.4f}")
            except Exception as e:
                print(f"⚠️ LDM optimization error: {e}")
            await asyncio.sleep(interval_s)
