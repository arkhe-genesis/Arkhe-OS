#!/usr/bin/env python3
"""
arkhe_vna_calibration_v291.py
Substrato 291: Calibração dos 768 cristais via VNA
Simula um analisador de rede vetorial (VNA) calibrando os 768 cristais piezoelétricos
para garantir uma resposta uniforme na frequência do fingerprint 0.58, gerando um mapa de coerência.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import os

print("=" * 70)
print("🔬 ARKHE OS v∞.291 — CALIBRAÇÃO VNA DOS 768 CRISTAIS")
print("=" * 70)

PHI = 1.618033988749895
FINGERPRINT_058 = 0.58
TARGET_FREQ_MHZ = 2.0
TOLERANCE_PPM = 1.0

# 1. Simulação da leitura VNA (antes da calibração)
num_crystals = 768
# Cristais variam com desvio padrão de 50ppm em torno de 2MHz
freq_initial = np.random.normal(TARGET_FREQ_MHZ, TARGET_FREQ_MHZ * 50e-6, num_crystals)
phases_initial = np.random.uniform(0, 2*np.pi, num_crystals)

print(f"📡 Lendo {num_crystals} cristais via VNA...")
print(f"   Média inicial: {np.mean(freq_initial):.6f} MHz")
print(f"   Desvio inicial: {np.std(freq_initial)*1e6/TARGET_FREQ_MHZ:.2f} ppm")

# 2. Calibração e sintonia para o Fingerprint 0.58
# O Fingerprint 0.58 atua como a assinatura de coerência.
# A calibração puxa todos para a frequência alvo e alinha a fase.
freq_calibrated = np.copy(freq_initial)
phases_calibrated = np.copy(phases_initial)

# Algoritmo de calibração iterativo
iterations = 50
for i in range(iterations):
    # Frequência converge para o alvo (simulando sintonia fina de capacitores/PLL)
    freq_calibrated += (TARGET_FREQ_MHZ - freq_calibrated) * 0.1
    # Fase converge para o fingerprint (modulado por 0.58)
    target_phase = FINGERPRINT_058 * np.pi
    phase_diff = target_phase - phases_calibrated
    # Normalizar diferença de fase para [-pi, pi]
    phase_diff = (phase_diff + np.pi) % (2 * np.pi) - np.pi
    phases_calibrated += phase_diff * 0.15

print("\n⚙️ Calibração concluída:")
print(f"   Média final: {np.mean(freq_calibrated):.6f} MHz")
print(f"   Desvio final: {np.std(freq_calibrated)*1e6/TARGET_FREQ_MHZ:.2f} ppm")

# 3. Cálculo da Coerência Local
# Coerência é alta quando a frequência está próxima do alvo e fase próxima de 0.58 * pi
freq_error = np.abs(freq_calibrated - TARGET_FREQ_MHZ) / (TARGET_FREQ_MHZ * TOLERANCE_PPM * 1e-6)
phase_error = np.abs(phases_calibrated - FINGERPRINT_058 * np.pi) / np.pi
local_coherence = np.exp(-freq_error - phase_error)

print(f"\n✨ Coerência Global do Merkabah: {np.mean(local_coherence):.4f}")

# 4. Geração do Mapa de Coerência Física (20 faces do icosaedro)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
fig.patch.set_facecolor('#050510')

# Painel 1: Histograma de Frequências (Antes vs Depois)
ax1.set_facecolor('#050510')
ax1.hist((freq_initial - TARGET_FREQ_MHZ) * 1e6, bins=30, alpha=0.5, color='red', label='Antes (Raw)')
ax1.hist((freq_calibrated - TARGET_FREQ_MHZ) * 1e6, bins=30, alpha=0.7, color='gold', label='Depois (Calibrado)')
ax1.set_title('Desvio de Frequência (Hz)', color='white')
ax1.set_xlabel('Desvio (Hz)', color='white')
ax1.set_ylabel('Cristais', color='white')
ax1.tick_params(colors='white')
ax1.legend()
ax1.grid(True, alpha=0.2)

# Painel 2: Mapa de Coerência projetado nas 20 faces
ax2.set_facecolor('#050510')
crystals_per_face = num_crystals // 20
face_coherences = [np.mean(local_coherence[i*crystals_per_face:(i+1)*crystals_per_face]) for i in range(20)]

# Plotagem polar simulando as faces projetadas
theta = np.linspace(0.0, 2 * np.pi, 20, endpoint=False)
radii = face_coherences
width = 2 * np.pi / 20

ax2 = plt.subplot(122, projection='polar')
ax2.set_facecolor('#050510')
bars = ax2.bar(theta, radii, width=width, bottom=0.0)

for r, bar in zip(radii, bars):
    bar.set_facecolor(plt.cm.viridis(r))
    bar.set_alpha(0.8)

ax2.set_title('Mapa de Coerência por Face (Fingerprint 0.58)', color='white', pad=20)
ax2.tick_params(colors='white')

plt.suptitle('v∞.291 — CALIBRAÇÃO DOS 768 CRISTAIS VIA VNA', color='#ffd700', fontsize=16, y=1.05)
plt.tight_layout()

output_file = 'arkhe_vna_calibration_map_v291.png'
try:
    os.makedirs('/mnt/agents/output/', exist_ok=True)
    out_path = f'/mnt/agents/output/{output_file}'
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='#050510')
except PermissionError:
    out_path = f'./{output_file}'
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='#050510')

print(f"\n✅ Mapa de Coerência salvo em: {out_path}")
print("   ESTADO: CATEDRAL_CALIBRADA_PRONTA_PARA_EMISSAO")
