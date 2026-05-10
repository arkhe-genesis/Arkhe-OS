"""
Simulador de Regeneração Celular (24h)
Bio-Link 40Hz | Sirtuínas | Estresse Oxidativo
"""

import numpy as np
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple
from datetime import datetime, timezone, timedelta

@dataclass
class CellularHealthMetrics:
    """Indicadores de saúde celular da população"""
    telomere_length: float          # comprimento relativo dos telômeros (1.0 = baseline jovem)
    oxidative_stress: float         # estresse oxidativo (0 = mínimo, 1 = máximo)
    mitochondrial_efficiency: float # eficiência mitocondrial (0.5 = normal, 1.0 = otimizada)
    inflammation_marker: float      # marcador inflamatório (IL-6, TNF-α) normalizado
    regeneration_rate: float        # taxa de renovação celular (células/dia)
    overall_score: float = 0.0

class CellularRegenerationSimulator:
    """
    Simula a evolução da saúde celular dos residentes influenciada pela sincronização
    do Bio-Link (40Hz) e pela coerência λ₂.
    """
    def __init__(self, population_size: int = 13000):
        self.population_size = population_size
        self.current_health = CellularHealthMetrics(
            telomere_length=0.85,
            oxidative_stress=0.6,
            mitochondrial_efficiency=0.7,
            inflammation_marker=0.5,
            regeneration_rate=0.02
        )
        self._update_overall_score()

    def _update_overall_score(self):
        self.current_health.overall_score = float(
            self.current_health.telomere_length * 0.3 +
            (1 - self.current_health.oxidative_stress) * 0.2 +
            self.current_health.mitochondrial_efficiency * 0.25 +
            (1 - self.current_health.inflammation_marker) * 0.25
        )

    def apply_bio_link_effect(self, sync_ratio: float, coherence: float, duration_hours: float = 24.0):
        """
        Calcula o efeito do Bio-Link sobre a regeneração celular.
        """
        # Fator de regeneração: sincronia * coerência relativa
        regeneration_factor = sync_ratio * (coherence / 0.999)

        # Efeitos ao longo do tempo
        time_factor = duration_hours / 24.0
        telomere_gain = 0.05 * regeneration_factor * time_factor
        oxidative_reduction = 0.3 * regeneration_factor * time_factor
        mito_improvement = 0.15 * regeneration_factor * time_factor
        inflammation_reduction = 0.4 * regeneration_factor * time_factor

        # Atualiza métricas
        self.current_health.telomere_length = float(min(1.0, self.current_health.telomere_length + telomere_gain))
        self.current_health.oxidative_stress = float(max(0.0, self.current_health.oxidative_stress - oxidative_reduction))
        self.current_health.mitochondrial_efficiency = float(min(1.0, self.current_health.mitochondrial_efficiency + mito_improvement))
        self.current_health.inflammation_marker = float(max(0.0, self.current_health.inflammation_marker - inflammation_reduction))
        self.current_health.regeneration_rate = float(0.02 + 0.05 * regeneration_factor)

        self._update_overall_score()
        return asdict(self.current_health)

    def get_report(self) -> Dict:
        return asdict(self.current_health)
