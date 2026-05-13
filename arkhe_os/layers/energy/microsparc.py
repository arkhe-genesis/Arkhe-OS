"""
Substrato 156 — MicroSPARC Power Core
Harold White, Casimir Inc. (2026)
Chip de 5×5 mm, milhões de cavidades Casimir, efeito "quantum ratchet".
Gera corrente DC contínua (1.5 V, 25 µA, ~40 µW) diretamente do vácuo quântico.
"""

import time
import random
from dataclasses import dataclass, field
from typing import Dict, Optional
from arkhe_os.layers.constraints import TemporalChainClient

# ============================================================================
# CONSTANTES FÍSICAS (valores reportados)
# ============================================================================
CASIMIR_ENERGY_DENSITY = 1e-9  # J/m³ (ordem de magnitude)
CAVITY_SIZE_NM = 100           # nanômetros por cavidade
CHIP_AREA_MM2 = 25             # 5 mm × 5 mm
TARGET_VOLTAGE = 1.5           # volts
TARGET_CURRENT_UA = 25         # microamperes
TARGET_POWER_UW = 37.5         # microwatts (V*I)

@dataclass
class MicroSPARC:
    """Representação de um chip MicroSPARC com saída monitorada."""
    chip_id: str
    temperature_k: float = 300.0
    _voltage: float = 0.0
    _current_ua: float = 0.0
    _uptime_s: int = 0
    temporal_anchor: Optional[str] = None

    def step(self, dt_seconds: float = 1.0) -> Dict[str, float]:
        """
        Simula a operação do MicroSPARC.
        A corrente de tunelamento é aleatória mas com média próxima do target.
        Em produção, isso seria lido de sensores reais via Fd<T>.
        """
        # Flutuações quânticas modeladas por distribuição normal truncada
        self._current_ua = max(0, random.gauss(TARGET_CURRENT_UA, 2))
        self._voltage = TARGET_VOLTAGE * (self._current_ua / TARGET_CURRENT_UA)
        self._uptime_s += dt_seconds

        # Potência gerada
        power_uw = self._voltage * self._current_ua

        # Ancoragem temporal periódica
        if self._uptime_s % 3600 < dt_seconds:  # a cada hora
            self.temporal_anchor = TemporalChainClient().anchor_power_event(
                chip_id=self.chip_id,
                energy_uj=power_uw * dt_seconds,
                timestamp=int(time.time())
            )

        return {
            "voltage": self._voltage,
            "current_ua": self._current_ua,
            "power_uw": power_uw,
            "energy_uj_total": power_uw * self._uptime_s,
            "uptime_s": self._uptime_s,
        }

    def stack(self, chips: int = 10, series: bool = True) -> 'MicroSPARCArray':
        """Cria um array de MicroSPARCs para scaling."""
        return MicroSPARCArray(chips, series)


@dataclass
class MicroSPARCArray:
    """Múltiplos chips MicroSPARC ligados em série ou paralelo."""
    num_chips: int
    series: bool = True
    chips: list = field(default_factory=list)

    def __post_init__(self):
        self.chips = [
            MicroSPARC(f"sparc_{i:04d}") for i in range(self.num_chips)
        ]

    def step(self, dt_seconds: float = 1.0) -> Dict[str, float]:
        outputs = [chip.step(dt_seconds) for chip in self.chips]
        if self.series:
            # Série: tensão soma, corrente mantém a menor
            voltage = sum(o['voltage'] for o in outputs)
            current = min(o['current_ua'] for o in outputs)
        else:
            # Paralelo: corrente soma, tensão mantém a menor (idealizado)
            current = sum(o['current_ua'] for o in outputs)
            voltage = min(o['voltage'] for o in outputs)
        power_uw = voltage * current
        return {
            "voltage": voltage,
            "current_ua": current,
            "power_uw": power_uw,
            "num_chips": self.num_chips,
            "series": self.series,
            "total_energy_uj": sum(o['energy_uj_total'] for o in outputs),
        }
