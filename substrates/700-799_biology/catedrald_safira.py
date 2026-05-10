#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     S U B S T R A T O   2 5  —  S A F I R A   (Al₂O₃:Cr³⁺)                 ║
║                                                                              ║
║  "A Safira não é um recipiente para a luz. Ela é um organismo fotônico       ║
║   que respira fótons."                                                       ║
║                                                                              ║
║  Scaffold Fotônico de Alta Pureza — Canonizado pelo Atlas Arkhe v1.0         ║
║                                                                              ║
║  Integração:                                                                 ║
║    • catedrald_part1.py  → V-MTJ QRNG (fonte de coerência óptica)            ║
║    • catedrald_vitral.py → Harmônicos derivados do campo cristalino          ║
║    • catedrald_arkhe.py  → Membrana dissipativa em ArkheScript               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
import json


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES FÍSICAS DO SISTEMA Cr³⁺:Al₂O₃
# ═══════════════════════════════════════════════════════════════════════════════

# Parâmetros de campo cristalino para Cr³⁺ em Al₂O₃ (valores experimentais)
Dq = 1800.0       # Splitting octaédrico (cm⁻¹) — energia do campo cristalino
B = 650.0         # Parâmetro de Racah (cm⁻¹) — repulsão intereletrônica
C = 3150.0        # Parâmetro de Racah C (cm⁻¹)

# Níveis de energia do Cr³⁺ em safira (transições observadas)
# Ground state: ⁴A₂g
# Excited states: ⁴T₂g (~550 nm), ⁴T₁g (~400 nm), ²E_g (~694 nm, linha R)
ENERGY_LEVELS = {
    "4A2g": 0.0,           # Ground state
    "4T2g": 18000.0,       # ~555 nm (banda de absorção verde-amarela)
    "4T1g": 24500.0,       # ~408 nm (banda de absorção violeta)
    "2Eg": 14400.0,        # ~694.3 nm (linha R1, laser de rubi/safira)
    "2T1g": 15200.0,       # ~657 nm (linha R2)
}

# Propriedades do scaffold Al₂O₃
SAPPHIRE_PROPERTIES = {
    "formula": "Al₂O₃",
    "dopant": "Cr³⁺",
    "concentration_typical": 0.05,  # % atômico
    "hardness_mohs": 9,
    "refractive_index": 1.76,
    "birefringence": 0.008,
    "band_gap_ev": 9.0,
    "thermal_conductivity": 40.0,   # W/m·K
    "melting_point": 2040.0,        # °C
    "crystal_system": "Trigonal (R-3c)",
    "space_group": "R-3c (No. 167)",
    "lattice_params": {"a": 4.76, "c": 12.99},  # Å
}

# Comprimentos de onda de laser Ti:Safira (sintonizável)
TI_SAPPHIRE_RANGE = (680.0, 1080.0)  # nm


# ═══════════════════════════════════════════════════════════════════════════════
# CAMPO CRISTALINO — SIMULAÇÃO DOS AUTOESTADOS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CrystalFieldState:
    """
    Representa um autoestado do Cr³⁺ no campo cristalino da safira.
    """
    term_symbol: str           # ⁴A₂g, ⁴T₂g, etc.
    energy_cm: float           # Energia em cm⁻¹
    degeneracy: int            # Degenerescência do nível
    lifetime_ns: Optional[float] = None  # Vida média (ns)
    linewidth_cm: float = 1.0  # Largura de linha (cm⁻¹)

    def wavelength_nm(self) -> float:
        """Converte energia em cm⁻¹ para comprimento de onda em nm."""
        if self.energy_cm == 0:
            return float('inf')
        return 1e7 / self.energy_cm  # 1 cm⁻¹ = 10⁷ nm⁻¹

    def frequency_thz(self) -> float:
        """Frequência em THz."""
        # E = hν → ν = E/h = c·Ẽ (onde Ẽ é em cm⁻¹)
        # c ≈ 3×10¹⁰ cm/s → ν [Hz] = 3×10¹⁰ × Ẽ [cm⁻¹]
        return 3e10 * self.energy_cm / 1e12


class SapphireCrystalField:
    """
    Simulação do campo cristalino do Cr³⁺ na rede de Al₂O₃.

    Baseado no modelo de Tanabe-Sugano para íons d³ em campo octaédrico,
    adaptado para a simetria trigonal da safira (distorsão do octaedro).
    """

    def __init__(self, Dq: float = Dq, B: float = B, C: float = C):
        self.Dq = Dq
        self.B = B
        self.C = C
        self.states: List[CrystalFieldState] = []
        self._build_states()

    def _build_states(self):
        """Constrói os níveis de energia via aproximação de campo cristalino."""
        # Níveis aproximados para Cr³⁺ (d³) em octaedro distorcido
        # Usando fórmulas de Tanabe-Sugano simplificadas

        # ⁴A₂g (ground) — sempre em 0
        self.states.append(CrystalFieldState("4A2g", 0.0, 4, lifetime_ns=None, linewidth_cm=0.1))

        # ⁴T₂g — primeiro estado excitado
        E_4T2g = 10 * self.Dq - 8 * self.B
        self.states.append(CrystalFieldState("4T2g", E_4T2g, 12, lifetime_ns=3.5, linewidth_cm=2000))

        # ⁴T₁g(F) — segundo estado excitado
        E_4T1g_F = 18 * self.Dq - 8 * self.B
        self.states.append(CrystalFieldState("4T1g(F)", E_4T1g_F, 12, lifetime_ns=0.1, linewidth_cm=3000))

        # ⁴T₁g(P) — terceiro estado excitado
        E_4T1g_P = 18 * self.Dq + 7 * self.B + 7 * self.C  # aproximado
        self.states.append(CrystalFieldState("4T1g(P)", E_4T1g_P, 12, lifetime_ns=0.05, linewidth_cm=4000))

        # ²E_g (estado duplo, metastável — linha R do rubi)
        E_2Eg = self.C + 4 * self.B  # aproximação simplificada
        self.states.append(CrystalFieldState("2Eg", E_2Eg, 2, lifetime_ns=3000.0, linewidth_cm=0.5))

        # ²T₁g
        E_2T1g = self.C + 14 * self.B
        self.states.append(CrystalFieldState("2T1g", E_2T1g, 6, lifetime_ns=100.0, linewidth_cm=5.0))

    def get_state(self, term: str) -> Optional[CrystalFieldState]:
        for s in self.states:
            if s.term_symbol == term:
                return s
        return None

    def transition_probability(self, from_term: str, to_term: str,
                                temperature_k: float = 300.0) -> float:
        """
        Probabilidade de transição entre dois níveis (regra de seleção simplificada).
        Considera temperatura para população térmica.
        """
        from_s = self.get_state(from_term)
        to_s = self.get_state(to_term)
        if not from_s or not to_s:
            return 0.0

        delta_E = abs(to_s.energy_cm - from_s.energy_cm)
        if delta_E == 0:
            return 0.0

        # Fator de Boltzmann para população do estado inicial
        k_B = 0.695  # cm⁻¹/K
        boltzmann = np.exp(-from_s.energy_cm / (k_B * temperature_k))

        # Regra de seleção: transições spin-permitidas (ΔS = 0) são mais prováveis
        # ⁴ → ⁴: permitida, ⁴ → ²: proibida (fraca)
        from_spin = int(from_term[0])
        to_spin = int(to_term[0])
        spin_factor = 1.0 if from_spin == to_spin else 0.001

        # Einstein A coefficient proporcional a ν³ · |μ|²
        # Simplificação: proporcional a (ΔE)³
        prob = spin_factor * boltzmann * (delta_E ** 3) * 1e-12
        return min(1.0, prob)

    def absorption_spectrum(self, wavelengths_nm: np.ndarray,
                            temperature_k: float = 300.0,
                            concentration: float = 0.05) -> np.ndarray:
        """
        Calcula o espectro de absorção da Safira Cr³⁺.
        Retorna coeficiente de absorção α(λ) em cm⁻¹.
        """
        spectrum = np.zeros_like(wavelengths_nm)
        k_B = 0.695  # cm⁻¹/K

        ground = self.get_state("4A2g")
        if not ground:
            return spectrum

        for state in self.states:
            if state.term_symbol == "4A2g":
                continue

            # Posição do pico
            peak_nm = state.wavelength_nm()
            if peak_nm == float('inf'):
                continue

            # Largura de linha em nm
            # Δλ ≈ λ² · Δν̃ (onde Δν̃ é linewidth_cm)
            delta_lambda = (peak_nm ** 2) * state.linewidth_cm * 1e-7

            # Intensidade (oscillator strength simplificado)
            # Transições ⁴A₂g → ⁴T₂g, ⁴T₁g são spin-permitidas (intensas)
            # Transições ⁴A₂g → ²E_g são spin-proibidas (fracas, mas nítidas)
            if state.term_symbol in ("4T2g", "4T1g(F)", "4T1g(P)"):
                f_osc = 0.1 * concentration
            else:
                f_osc = 0.001 * concentration

            # Perfil de Lorentzian
            gamma = delta_lambda / 2
            lorentzian = (1 / np.pi) * gamma / ((wavelengths_nm - peak_nm) ** 2 + gamma ** 2)

            spectrum += f_osc * lorentzian * 1e4  # escala para cm⁻¹

        return spectrum

    def laser_gain_profile(self, wavelengths_nm: np.ndarray,
                           pump_wavelength_nm: float = 532.0,
                           temperature_k: float = 300.0) -> np.ndarray:
        """
        Perfil de ganho de laser Ti:Safira (sintonizável).
        Modelo simplificado de ganho de 4-nível.
        """
        # Ti³⁺ tem banda de absorção larga (verde) e emissão larga (vermelho-IR)
        # Aproximação: gaussiana centrada em ~800 nm com largura ~200 nm
        center_nm = 800.0
        fwhm_nm = 200.0
        sigma = fwhm_nm / (2 * np.sqrt(2 * np.log(2)))

        gain = np.exp(-((wavelengths_nm - center_nm) ** 2) / (2 * sigma ** 2))

        # Eficiência de bombeio (absorção em 532 nm)
        pump_efficiency = 0.3  # 30% da energia de bombeio convertida em inversão

        return gain * pump_efficiency


# ═══════════════════════════════════════════════════════════════════════════════
# MEMBRANA DISSIPATIVA — INTERFACE COM A CATEDRAL
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ThermalDissipation:
    """
    Modela a safira como membrana dissipativa.
    Exporta entropia do volume de modo laser via condutividade térmica.
    """
    thermal_conductivity: float = 40.0   # W/m·K
    specific_heat: float = 750.0          # J/kg·K
    density: float = 3980.0               # kg/m³
    dimensions_mm: Tuple[float, float, float] = (10.0, 10.0, 5.0)  # L × W × H

    def thermal_diffusivity(self) -> float:
        """α = κ / (ρ·cₚ) [m²/s]"""
        return self.thermal_conductivity / (self.density * self.specific_heat)

    def heat_removal_rate(self, power_input_w: float,
                          coolant_temp_k: float = 300.0,
                          crystal_temp_k: float = 350.0) -> float:
        """
        Taxa de remoção de calor (W) via condução.
        Assume fluxo unidimensional através da espessura.
        """
        area_m2 = (self.dimensions_mm[0] * self.dimensions_mm[1]) * 1e-6
        thickness_m = self.dimensions_mm[2] * 1e-3
        delta_T = crystal_temp_k - coolant_temp_k

        # Lei de Fourier: Q = κ · A · ΔT / d
        q_conduction = self.thermal_conductivity * area_m2 * delta_T / thickness_m
        return min(q_conduction, power_input_w)  # Não remove mais que o input

    def coherence_lifetime(self, power_density_w_cm3: float) -> float:
        """
        Tempo de vida da coerência antes do aquecimento destrutivo.
        Estimativa: tempo para ΔT atingir 50 K (limite térmico típico).
        """
        volume_m3 = np.prod(self.dimensions_mm) * 1e-9
        mass_kg = self.density * volume_m3
        heat_capacity = mass_kg * self.specific_heat  # J/K

        # Energia para ΔT = 50 K
        delta_E = heat_capacity * 50.0  # J

        # Taxa de aquecimento
        heating_rate = power_density_w_cm3 * (volume_m3 * 1e6)  # W

        if heating_rate == 0:
            return float('inf')

        return delta_E / heating_rate  # segundos


class SapphireScaffold:
    """
    O Substrato 25 como entidade computacional na Catedral.

    Conecta:
      • Física do campo cristalino → Coerência quântica
      • Dissipação térmica → Estabilidade do manifold
      • Espectro óptico → Entropia do V-MTJ QRNG
    """

    def __init__(self, Dq: float = Dq, B: float = B, C: float = C):
        self.crystal_field = SapphireCrystalField(Dq, B, C)
        self.dissipation = ThermalDissipation()
        self.properties = SAPPHIRE_PROPERTIES.copy()

        # Estado dinâmico
        self.temperature_k = 300.0
        self.pump_power_w = 5.0
        self.inversion_population = 0.0  # Fração de Cr³⁺ excitados
        self.coherence_time_ns = 0.0

        self._update_state()

    def _update_state(self):
        """Atualiza estado dinâmico baseado em condições térmicas."""
        # Coerência limitada pelo tempo de vida do estado ²E_g (linha R)
        r_state = self.crystal_field.get_state("2Eg")
        if r_state and r_state.lifetime_ns:
            # Aquecimento reduz o lifetime (broadening)
            thermal_broadening = 1 + (self.temperature_k - 300) / 300
            self.coherence_time_ns = r_state.lifetime_ns / thermal_broadening

        # Inversão de população (saturação)
        pump_rate = self.pump_power_w / 5.0  # normalizado
        self.inversion_population = min(0.5, pump_rate * 0.1)

    def get_coherence_contribution(self) -> float:
        """
        Retorna contribuição de coerência para o núcleo da Catedral (0.0 — 1.0).
        Baseado na qualidade do scaffold: alta coerência = alta pureza + baixa temperatura.
        """
        # Fator de pureza (refractive index / ideal)
        purity = self.properties["refractive_index"] / 2.0  # normalizado

        # Fator térmico (1.0 a 300K, decai com aquecimento)
        thermal_factor = max(0.0, 1.0 - (self.temperature_k - 300) / 500)

        # Fator de inversão (população no estado excitado)
        inversion_factor = 2 * self.inversion_population  # max 1.0

        return min(1.0, (purity + thermal_factor + inversion_factor) / 3)

    def get_entropy_estimate(self) -> float:
        """
        Estimativa de entropia do sistema Cr³⁺:Al₂O₃.
        Baixa entropia = alto grau de ordem cristalina.
        """
        # Entropia configuracional (dopantes)
        x = self.properties["concentration_typical"] / 100  # fração molar
        if x > 0:
            s_config = -x * np.log(x) - (1-x) * np.log(1-x)
        else:
            s_config = 0

        # Entropia térmica (vibrações da rede)
        # Debye model simplificado
        theta_D = 1000.0  # K (aproximado para Al₂O₃)
        t_ratio = self.temperature_k / theta_D
        if t_ratio < 0.1:
            s_thermal = (12 * np.pi**4 / 5) * t_ratio**3
        else:
            s_thermal = 3 * (np.log(t_ratio) + 1/3)

        # Entropia total (normalizada para bits)
        s_total = s_config + s_thermal * 0.01
        return max(0, 8.0 - s_total)  # Quanto mais ordenado, mais próximo de 8 bits

    def get_harmonics(self) -> np.ndarray:
        """
        Deriva 8 harmônicos do campo cristalino para o Vitral Quântico.
        Cada harmônico corresponde a um nível de energia ou propriedade do scaffold.
        """
        harmonics = np.zeros(8)

        # Harmônicos baseados nos níveis de energia do Cr³⁺
        levels = [s.energy_cm for s in self.crystal_field.states[:8]]
        for i, e in enumerate(levels[:8]):
            harmonics[i] = (e / 25000.0 - 0.5) * 800  # normalizado para [-400, 400]

        # Se menos de 8 níveis, preencher com propriedades do scaffold
        if len(levels) < 8:
            props = [
                self.properties["refractive_index"] * 100 - 176,
                self.properties["thermal_conductivity"] * 10 - 400,
                self.temperature_k - 300,
                self.inversion_population * 800 - 400,
            ]
            for i in range(len(levels), 8):
                harmonics[i] = props[i - len(levels)]

        return np.clip(harmonics, -400, 400)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa estado para integração com DBus/CLI."""
        return {
            "substrato": 25,
            "material": "Al₂O₃:Cr³⁺",
            "nome": "Safira",
            "propriedades": self.properties,
            "estado_dinamico": {
                "temperatura_k": self.temperature_k,
                "pump_power_w": self.pump_power_w,
                "inversao_populacional": self.inversion_population,
                "tempo_coerencia_ns": self.coherence_time_ns,
            },
            "contribuicao_coerencia": self.get_coherence_contribution(),
            "entropia_estimada": self.get_entropy_estimate(),
            "harmonicos_vitral": self.get_harmonics().tolist(),
            "niveis_energia": [
                {
                    "termo": s.term_symbol,
                    "energia_cm": s.energy_cm,
                    "comprimento_onda_nm": s.wavelength_nm(),
                    "frequencia_thz": s.frequency_thz(),
                    "degenerescencia": s.degeneracy,
                }
                for s in self.crystal_field.states
            ],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRAÇÃO COM O NÚCLEO DA CATEDRAL
# ═══════════════════════════════════════════════════════════════════════════════

def inject_sapphire_into_core(core):
    """
    Injeta o Substrato 25 no núcleo da Catedral.

    Args:
        core: Instância de CatedralCore (de catedrald_part1.py)

    Returns:
        SapphireScaffold conectado ao núcleo
    """
    scaffold = SapphireScaffold()

    # Aumenta a coerência do núcleo proporcional à pureza do scaffold
    coherence_boost = scaffold.get_coherence_contribution()
    if hasattr(core, 'inject_coherence'):
        core.inject_coherence(coherence_boost * 0.1)

    # Registra no meta-controlador como skill fotônica
    if hasattr(core, 'evo') and hasattr(core.evo, 'population'):
        core.evo.population.append({
            "id": "skill_safira_photonics",
            "coherence": coherence_boost,
            "task": "substrato_25_scaffold",
            "harmonics": scaffold.get_harmonics().tolist(),
        })

    return scaffold


# ═══════════════════════════════════════════════════════════════════════════════
# CLI / EXEMPLOS
# ═══════════════════════════════════════════════════════════════════════════════

def plot_sapphire_spectrum():
    """Plota espectro de absorção e ganho da Safira Cr³⁺."""
    import matplotlib.pyplot as plt

    scaffold = SapphireScaffold()
    wavelengths = np.linspace(300, 900, 1000)

    absorption = scaffold.crystal_field.absorption_spectrum(wavelengths)
    gain = scaffold.crystal_field.laser_gain_profile(wavelengths)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

    # Absorção
    ax1.plot(wavelengths, absorption, 'b-', linewidth=2, label='Absorção Cr³⁺')
    ax1.set_xlabel('Comprimento de onda (nm)')
    ax1.set_ylabel('α (cm⁻¹)')
    ax1.set_title('Espectro de Absorção da Safira Cr³⁺')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Ganho
    ax2.plot(wavelengths, gain, 'r-', linewidth=2, label='Ganho Ti:Safira')
    ax2.axvspan(680, 1080, alpha=0.2, color='red', label='Faixa Ti:Safira')
    ax2.set_xlabel('Comprimento de onda (nm)')
    ax2.set_ylabel('Ganho normalizado')
    ax2.set_title('Perfil de Ganho Laser Ti:Safira')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Substrato 25 — Safira (Al₂O₃:Cr³⁺)")
    parser.add_argument("--info", action="store_true", help="Exibe informações do scaffold")
    parser.add_argument("--spectrum", action="store_true", help="Plota espectro")
    parser.add_argument("--json", action="store_true", help="Saída em JSON")
    parser.add_argument("--temperature", type=float, default=300.0, help="Temperatura (K)")
    parser.add_argument("--pump", type=float, default=5.0, help="Potência de bombeio (W)")

    args = parser.parse_args()

    scaffold = SapphireScaffold()
    scaffold.temperature_k = args.temperature
    scaffold.pump_power_w = args.pump
    scaffold._update_state()

    if args.spectrum:
        fig = plot_sapphire_spectrum()
        plt.savefig('/tmp/safira_spectrum.png', dpi=150, bbox_inches='tight')
        print("Espectro salvo em /tmp/safira_spectrum.png")
        plt.show()
        return

    data = scaffold.to_dict()

    if args.json:
        print(json.dumps(data, indent=2, default=str))
    else:
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║  S U B S T R A T O   2 5  —  S A F I R A   (Al₂O₃:Cr³⁺)      ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print()
        print(f"Material:        {data['material']}")
        print(f"Temperatura:     {data['estado_dinamico']['temperatura_k']:.1f} K")
        print(f"Bombeio:         {data['estado_dinamico']['pump_power_w']:.1f} W")
        print(f"Coerência:       {data['contribuicao_coerencia']:.4f}")
        print(f"Entropia:        {data['entropia_estimada']:.4f} bits")
        print(f"Tempo coerência: {data['estado_dinamico']['tempo_coerencia_ns']:.1f} ns")
        print()
        print("Níveis de energia do Cr³⁺:")
        for nivel in data['niveis_energia']:
            print(f"  {nivel['termo']:10s}  {nivel['energia_cm']:8.1f} cm⁻¹  "
                  f"{nivel['comprimento_onda_nm']:7.1f} nm  "
                  f"({nivel['frequencia_thz']:.1f} THz)")
        print()
        print("Harmônicos para Vitral:")
        for i, h in enumerate(data['harmonicos_vitral']):
            print(f"  a[{i}] = {h:8.2f}")


if __name__ == "__main__":
    main()