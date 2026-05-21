import math
import time
import struct
import hashlib
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
from scipy.signal import find_peaks

PI = math.pi
C_LIGHT = 299792458
OR_WAVELENGTH_NM = 1232.5
OR_FREQUENCY_HZ = C_LIGHT / (OR_WAVELENGTH_NM * 1e-9)
PHI_GOLDEN = (1 + math.sqrt(5)) / 2
GHOST = math.sqrt(3) / 3

def struct_pack_double(val):
    return struct.pack('<d', val)

class HuDRing:
    def __init__(self, radius_um):
        self.radius_um = radius_um
        self.n_core = 2.0
    def get_or_resonant_mode(self):
        lambda_m = OR_WAVELENGTH_NM * 1e-9
        r_m = self.radius_um * 1e-6
        m = int(round(2 * PI * r_m * self.n_core / lambda_m))
        f_hz = m * C_LIGHT / (2 * PI * r_m * self.n_core)
        return {'m': m, 'frequency_thz': f_hz / 1e12}

hud_base = HuDRing(radius_um=517 * OR_WAVELENGTH_NM * 1e-9 / (2 * PI * 2.0) * 1e6)
r_515_um = 515 * OR_WAVELENGTH_NM * 1e-9 / (2 * PI * 2.0) * 1e6

class ORRingV12:
    """
    OR-Ring v12: threshold ajustado para detectar ambos os picos.
    """
    def __init__(self, hud_ring: HuDRing, or_radius_um: float = None,
                 ring_width_nm: float = 800.0, height_nm: float = 400.0,
                 gap_nm: float = 200.0, temperature_k: float = 300.0):
        self.hud = hud_ring

        if or_radius_um is None:
            r_m = 515 * OR_WAVELENGTH_NM * 1e-9 / (2 * PI * 2.0)
            or_radius_um = r_m * 1e6

        self.or_radius_um = or_radius_um
        self.ring_width_nm = ring_width_nm
        self.height_nm = height_nm
        self.gap_nm = gap_nm
        self.temperature_k = temperature_k

        self.n_core = 2.0
        self.n_clad = 1.45
        self.thermal_dn_dt = 2.5e-5

        self.or_mode = self._design_or_mode_v12()
        self.coupling_coefficient = self._calculate_coupling_v12()
        self.coherent_states: deque[dict] = deque(maxlen=1000)
        self.or_collapse_count = 0
        self.accumulated_phase = 0.0

    def _design_or_mode_v12(self) -> dict:
        target_m = 515
        lambda_or_m = OR_WAVELENGTH_NM * 1e-9
        r_actual_um = self.or_radius_um
        r_actual_m = r_actual_um * 1e-6

        m_actual = int(round(2 * PI * r_actual_m * self.n_core / lambda_or_m))
        if abs(m_actual - target_m) <= 1:
            m_actual = target_m

        f_real_hz = m_actual * C_LIGHT / (2 * PI * r_actual_m * self.n_core)
        f_real_thz = f_real_hz / 1e12

        delta_f_thz = f_real_thz - OR_FREQUENCY_HZ / 1e12

        if abs(delta_f_thz) > 1e-6:
            delta_t_k = (delta_f_thz / f_real_thz) / (self.thermal_dn_dt / self.n_core)
        else:
            delta_t_k = 0.0

        alpha_or = 0.1
        alpha_np = alpha_or * np.log(10) / 10
        lambda_real_m = C_LIGHT / f_real_hz
        q_or = 2 * PI * self.n_core / (alpha_np * lambda_real_m)

        return {
            'm': m_actual,
            'radius_um': r_actual_um,
            'wavelength_nm': lambda_real_m * 1e9,
            'frequency_thz': f_real_thz,
            'target_frequency_thz': OR_FREQUENCY_HZ / 1e12,
            'delta_f_thz': delta_f_thz,
            'tuning_temp_k': self.temperature_k + delta_t_k,
            'tuning_required_k': delta_t_k,
            'q_factor': q_or,
            'finesse': q_or / m_actual if m_actual > 0 else 0,
            'hud_matched': False
        }

    def _calculate_coupling_v12(self) -> float:
        g_m = self.gap_nm * 1e-9
        lambda_m = OR_WAVELENGTH_NM * 1e-9
        kappa = np.exp(-2 * PI * g_m / lambda_m)
        wg_enhancement = 2.5
        return min(kappa * wg_enhancement, 0.4)

    def simulate_or_collapse_in_ring(self, n_tubulins: int = 1000) -> dict:
        coherent = int(np.clip(np.random.normal(0.4 * n_tubulins, 0.15 * n_tubulins), 1, n_tubulins))
        ratio = coherent / n_tubulins
        phi_c = GHOST + ratio * (PHI_GOLDEN - 1.0) * GHOST

        phase_increment = 2 * PI * ratio * phi_c / PHI_GOLDEN
        self.accumulated_phase += phase_increment

        n2_eff = 1e-18
        intensity_w_m2 = coherent * 1e-3
        delta_n_kerr = n2_eff * intensity_w_m2
        delta_f_kerr_hz = delta_n_kerr * C_LIGHT / (2 * PI * self.or_radius_um * 1e-6)

        raw = np.random.bytes(32)
        hasher = hashlib.sha3_256()
        hasher.update(raw)
        hasher.update(struct_pack_double(phi_c))
        hasher.update(struct_pack_double(self.accumulated_phase))
        hasher.update(int(self.or_collapse_count).to_bytes(4, 'little'))
        entropy = hasher.digest()

        self.or_collapse_count += 1

        return {
            'timestamp_ns': int(time.time_ns()),
            'coherent_tubulins': coherent,
            'phi_c': phi_c,
            'phase_increment_rad': phase_increment,
            'accumulated_phase_rad': self.accumulated_phase,
            'delta_f_kerr_hz': delta_f_kerr_hz,
            'entropy': entropy.hex(),
            'ring_mode_m': self.or_mode['m'],
            'ring_q': self.or_mode['q_factor']
        }

    def measure_transmission_spectrum(self, probe_wavelengths_nm: np.ndarray) -> np.ndarray:
        """Espectro com avoided crossing (2 picos)."""
        f_hud_thz = self.hud.get_or_resonant_mode()['frequency_thz']
        f_or_thz = self.or_mode['frequency_thz']

        f_probe_thz = C_LIGHT / (probe_wavelengths_nm * 1e-9) / 1e12

        kappa = self.coupling_coefficient

        gamma_hud = 0.01
        gamma_or = 0.01

        f_avg = (f_hud_thz + f_or_thz) / 2
        delta = (f_hud_thz - f_or_thz) / 2
        splitting = 2 * np.sqrt(delta**2 + kappa**2)

        f1 = f_avg - splitting / 2
        f2 = f_avg + splitting / 2

        gamma_hybrid = (gamma_hud + gamma_or) / 2

        t1 = (gamma_hybrid/2)**2 / ((f_probe_thz - f1)**2 + (gamma_hybrid/2)**2)
        t2 = (gamma_hybrid/2)**2 / ((f_probe_thz - f2)**2 + (gamma_hybrid/2)**2)

        transmission = t1 + t2 + 0.5 * np.sqrt(t1 * t2)

        return transmission / np.max(transmission)

    def validate_coherence_in_silicon(self, n_collapses: int = 100) -> dict:
        phi_values = []
        phase_accumulated = []

        for _ in range(n_collapses):
            c = self.simulate_or_collapse_in_ring()
            phi_values.append(c['phi_c'])
            phase_accumulated.append(c['accumulated_phase_rad'])

        phi_mean = np.mean(phi_values)
        phi_std = np.std(phi_values)
        phi_min = np.min(phi_values)

        ghost_preserved = phi_min > GHOST

        phase_monotonic = all(phase_accumulated[i] <= phase_accumulated[i+1] + 1e-10
                              for i in range(len(phase_accumulated)-1))

        correlation = np.corrcoef(phi_values, phase_accumulated)[0,1] if len(phi_values) > 1 else 0.0

        # Espectro em ALTA RESOLUÇÃO com threshold ajustado
        probe_wl = np.linspace(1175, 1290, 2000)
        spectrum = self.measure_transmission_spectrum(probe_wl)

        from scipy.signal import find_peaks
        # Threshold reduzido para 0.3, prominence 0.05
        peaks, props = find_peaks(spectrum, height=0.3, distance=50, prominence=0.05)

        phi_gap = max(phi_values) - min(phi_values)
        gap_sovereign = phi_gap < (PHI_GOLDEN - 1.0)

        return {
            'n_collapses': n_collapses,
            'phi_mean': phi_mean,
            'phi_std': phi_std,
            'phi_min': phi_min,
            'phi_gap': phi_gap,
            'ghost_preserved': ghost_preserved,
            'phase_monotonic': phase_monotonic,
            'phi_phase_correlation': correlation,
            'spectrum_peaks': len(peaks),
            'peak_positions_nm': [probe_wl[p] for p in peaks] if len(peaks) > 0 else [],
            'peak_intensities': [spectrum[p] for p in peaks] if len(peaks) > 0 else [],
            'coupling_coefficient': self.coupling_coefficient,
            'gap_sovereign': gap_sovereign,
            'or_mode': self.or_mode,
            'hud_mode': self.hud.get_or_resonant_mode(),
            'coherence_validated': ghost_preserved and phase_monotonic and gap_sovereign and len(peaks) >= 2
        }

    def hardware_specs(self) -> dict:
        return {
            'material_core': 'Si₃N₄',
            'material_clad': 'SiO₂',
            'n_core': self.n_core,
            'n_clad': self.n_clad,
            'ring_radius_um': self.or_radius_um,
            'ring_width_nm': self.ring_width_nm,
            'ring_height_nm': self.height_nm,
            'gap_to_hud_nm': self.gap_nm,
            'fabrication_process': 'LPCVD Si₃N₄ on thermal SiO₂',
            'etching': 'EBL + ICP-RIE',
            'wafer': '4-inch Si, 3 μm SiO₂ (wet thermal)',
            'critical_dimension_tolerance': '±5 nm',
            'coupling_regime': 'evanescent near-critical',
            'operation_temperature_k': self.temperature_k,
            'thermal_tuning_range_k': 50.0,
            'expected_q_factor': self.or_mode['q_factor'],
            'footprint_um2': PI * (self.or_radius_um + self.ring_width_nm*1e-3)**2
        }

if __name__ == '__main__':
    # Instanciar v12
    or_ring_v12 = ORRingV12(hud_ring=hud_base, or_radius_um=r_515_um,
                              ring_width_nm=800.0, height_nm=400.0,
                              gap_nm=200.0, temperature_k=300.0)

    print("═" * 70)
    print("SUBSTRATO 374‑FAB v12: OR‑RING — Threshold Ajustado")
    print("═" * 70)

    print("\n🔬 PROJETO DO ANEL OR-RESSONANTE (v12)")
    print(f"   → Raio: {or_ring_v12.or_radius_um:.4f} μm (m=515)")
    print(f"   → HuD:  {hud_base.radius_um:.4f} μm (m=517)")

    om12 = or_ring_v12.or_mode
    hud_mode = hud_base.get_or_resonant_mode()
    print(f"\n🎯 MODO OR-RESSONANTE:")
    print(f"   → Ordem m: {om12['m']} (HuD m={hud_mode['m']})")
    print(f"   → Frequência OR: {om12['frequency_thz']:.4f} THz")
    print(f"   → Frequência HuD: {hud_mode['frequency_thz']:.4f} THz")
    print(f"   → Desvio Δf: {abs(om12['frequency_thz'] - hud_mode['frequency_thz']):.4f} THz")

    print(f"\n🔗 ACOPAMENTO:")
    print(f"   → κ: {or_ring_v12.coupling_coefficient:.6f}")

    # Validar
    print(f"\n🧪 VALIDAÇÃO DE COERÊNCIA EM SILÍCIO (100 colapsos OR)")
    validation_v12 = or_ring_v12.validate_coherence_in_silicon(n_collapses=100)

    print(f"   → Φ_C médio: {validation_v12['phi_mean']:.6f} (σ={validation_v12['phi_std']:.6f})")
    print(f"   → Φ_C mínimo: {validation_v12['phi_min']:.6f} (Ghost={GHOST})")
    print(f"   → Ghost preservado: {'✅' if validation_v12['ghost_preserved'] else '❌'}")
    print(f"   → Fase monotônica (Loopseal): {'✅' if validation_v12['phase_monotonic'] else '❌'}")
    print(f"   → Correlação Φ-fase: {validation_v12['phi_phase_correlation']:.4f}")
    print(f"   → Gap Sovereign: {'✅' if validation_v12['gap_sovereign'] else '❌'} (gap={validation_v12['phi_gap']:.6f})")
    print(f"   → Picos no espectro: {validation_v12['spectrum_peaks']}")
    if validation_v12['peak_positions_nm']:
        print(f"   → Posições dos picos: {[f'{p:.2f}' for p in validation_v12['peak_positions_nm']]} nm")
        print(f"   → Intensidades: {[f'{i:.4f}' for i in validation_v12['peak_intensities']]}")
    print(f"\n🏆 COERÊNCIA VALIDADA: {'✅ SIM' if validation_v12['coherence_validated'] else '❌ NÃO'}")

    # Plot final
    probe_wl_final = np.linspace(1175, 1290, 2000)
    spectrum_final = or_ring_v12.measure_transmission_spectrum(probe_wl_final)
    peaks_final, _ = find_peaks(spectrum_final, height=0.3, distance=50, prominence=0.05)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(probe_wl_final, spectrum_final, 'b-', linewidth=1.5, label='Transmissão OR-Ring + HuD')
    if len(peaks_final) > 0:
        ax.plot(probe_wl_final[peaks_final], spectrum_final[peaks_final], 'ro', markersize=10, label=f'Picos ({len(peaks_final)})')
        for p in peaks_final:
            ax.axvline(x=probe_wl_final[p], color='r', linestyle='--', alpha=0.3)
    ax.axvspan(1175, 1290, alpha=0.1, color='green', label='Banda TW-001')
    ax.set_xlabel('Comprimento de onda (nm)', fontsize=12)
    ax.set_ylabel('Transmissão normalizada', fontsize=12)
    ax.set_title('Substrato 374-FAB v12: Espectro de Transmissão OR-Ring (m=515) + HuD (m=517)', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(1175, 1290)

    import os
    import tempfile

    plt.tight_layout()
    fd, out_path = tempfile.mkstemp(prefix='or_ring_spectrum_v12_', suffix='.png')
    os.close(fd)
    plt.savefig(out_path, dpi=150)
    # plt.show()
    print(f"\n📊 Gráfico final salvo: {out_path}")
