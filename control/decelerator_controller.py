import numpy as np
from typing import List

class DeceleratorController:
    """Controla desaceleração EM com ativação seletiva de segmentos."""

    def __init__(self, total_segments: int = 500, max_active_segments: int = 8):
        self.N_total = total_segments
        self.N_max_active = max_active_segments
        self.segment_length = 1.0  # metro por segmento

    def compute_active_segments(self, payload_mass_kg: float, entry_velocity_kms: float) -> List[int]:
        """Calcula quais segmentos ativar para desaceleração ótima."""
        # Força total necessária: F = m·a, com a = 90 g = 882.9 m/s²
        a_target = 90.0 * 9.81  # m/s²
        F_total = payload_mass_kg * a_target  # Newtons

        # Força por segmento ativo: F_seg = B·I·L = 15 T · 8000 A · 0.5 m = 60 kN
        F_per_segment = 15.0 * 8000.0 * 0.5  # 60,000 N

        # Número de segmentos necessários
        N_needed = int(np.ceil(F_total / F_per_segment))
        N_needed = min(N_needed, self.N_max_active)  # Limitar a máximo configurado

        # Selecionar segmentos contíguos centrados na posição atual do payload
        # (simplificado: assumir payload no centro do track no início)
        center_segment = self.N_total // 2
        start_idx = max(0, center_segment - N_needed//2)
        active_segments = list(range(start_idx, start_idx + N_needed))

        return active_segments

    def generate_current_profile(self, active_segments: List[int], decel_time_s: float) -> np.ndarray:
        """Gera perfil de corrente para cada segmento ativo."""
        # Perfil trapezoidal: ramp-up, plateau, ramp-down
        t_ramp = 0.2 * decel_time_s  # 20% do tempo para rampa
        t_plateau = decel_time_s - 2*t_ramp

        profile = np.zeros((len(active_segments), int(decel_time_s * 1000)))  # 1 kHz sampling

        for i, seg in enumerate(active_segments):
            # Ramp-up linear
            for t in range(int(t_ramp * 1000)):
                profile[i, t] = 8000.0 * t / (t_ramp * 1000)
            # Plateau
            for t in range(int(t_ramp * 1000), int((t_ramp + t_plateau) * 1000)):
                profile[i, t] = 8000.0
            # Ramp-down
            for t in range(int((t_ramp + t_plateau) * 1000), int(decel_time_s * 1000)):
                profile[i, t] = 8000.0 * (1 - (t - (t_ramp + t_plateau)*1000) / (t_ramp * 1000))

        return profile
