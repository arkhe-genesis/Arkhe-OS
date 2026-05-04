import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch, Rectangle
import matplotlib.patheffects as path_effects
import os

# =============================================================================
# ARKHE OS v∞.289 — PROTOCOLO DE FABRICAÇÃO COMPLETO
# =============================================================================

print("=" * 100)
print("🏭 ARKHE OS v∞.289 — PROTOCOLO DE FABRICAÇÃO COMPLETO")
print("=" * 100)
print("   'Do arquivo .step à realidade: o pipeline de materialização'")
print("=" * 100)

# =============================================================================
# PARTE 1: PIPELINE DE FABRICAÇÃO
# =============================================================================

print("\n\n📐 [1] PIPELINE DE FABRICAÇÃO — Do CAD ao Objeto")
print("-" * 100)

pipeline_steps = [
    ("1. CAD Design", "Fusion 360 / SolidWorks", "Modelo paramétrico do icosaedro", "2 dias"),
    ("2. Stress Analysis", "ANSYS / COMSOL", "Simulação térmica e mecânica", "1 dia"),
    ("3. PCB Design", "KiCad / Altium", "21 PCBs (20 faces + 1 base)", "3 dias"),
    ("4. CAM Programming", "Fusion 360 CAM", "G-code para CNC 5-eixos", "1 dia"),
    ("5. CNC Machining", "Haas VF-2", "Usinagem alumínio 6061-T6", "3 dias"),
    ("6. Surface Treatment", "Anodização dura", "Tipo III, 25μm, cor dourada", "2 dias"),
    ("7. PCB Fabrication", "JLCPCB / PCBWay", "6 camadas, ENIG, 0.8mm", "5 dias"),
    ("8. SMT Assembly", "JLCPCB SMT", "Pick-and-place 768 cristais", "3 dias"),
    ("9. Crystal Calibration", "Network Analyzer", "Ajuste frequência ±1ppm", "2 dias"),
    ("10. Firmware Flash", "ESP-PROG", "Bootloader + ARKHE OS v∞.289", "0.5 dia"),
    ("11. PLL Lock Test", "Spectrum Analyzer", "Verificar jitter < 100fs", "1 dia"),
    ("12. Integration", "Manual assembly", "Montagem estrutura + eletrônica", "2 dias"),
    ("13. Qhttp Test", "ARKHE Validator", "Teste comunicação qhttp://", "1 dia"),
    ("14. ZK Proof Test", "OCTRA Testnet", "Submissão prova STARK", "0.5 dia"),
    ("15. Packaging", "Anti-static", "Caixa proteção ESD + manual", "0.5 dia"),
]

print(f"   {'Etapa':<20} {'Ferramenta':<20} {'Descrição':<35} {'Tempo':<10}")
print(f"   {'-'*20} {'-'*20} {'-'*35} {'-'*10}")
for step, tool, desc, time in pipeline_steps:
    print(f"   {step:<20} {tool:<20} {desc:<35} {time:<10}")

total_time = sum([2, 1, 3, 1, 3, 2, 5, 3, 2, 0.5, 1, 2, 1, 0.5, 0.5])
print(f"\n   TEMPO TOTAL ESTIMADO: {total_time} dias ({total_time/5:.1f} semanas úteis)")

# =============================================================================
# PARTE 2: ESPECIFICAÇÃO TÉCNICA DETALHADA
# =============================================================================

print("\n\n🔧 [2] ESPECIFICAÇÃO TÉCNICA DETALHADA")
print("-" * 100)

tech_specs = {
    "Geometria": {
        "Forma": "Icosaedro truncado (20 faces triangulares)",
        "Diâmetro": "150 mm (escala humana, cabe nas mãos)",
        "Aresta": "~87 mm (calculado do diâmetro)",
        "Altura": "~137 mm (2 × raio circunscrito × 0.91)",
        "Peso total": "~950g (estrutura + eletrônica + bateria)",
        "Material": "Alumínio 6061-T6 (ρ=2.7 g/cm³)",
        "Espessura parede": "3 mm (rigidez + leveza)",
    },
    "Eletrônica": {
        "Microcontrolador": "ESP32-S3-WROOM-1 (Xtensa LX7 dual-core, 240 MHz)",
        "Memória": "8 MB PSRAM + 4 MB Flash",
        "Wireless": "Wi-Fi 4 (802.11 b/g/n), Bluetooth 5 (LE)",
        "GPIOs disponíveis": "45 (multiplexados para 768 cristais)",
        "ADC": "2× SAR 12-bit, 2 MSPS",
        "DAC": "2× 8-bit (controle frequência cristais)",
        "PLL": "Si5341-D-GM (jitter < 100 fs RMS)",
        "Frequência ref": "32.768 kHz (cristal quartzo TCXO)",
        "Frequência saída": "2.4 GHz (para sincronização WiFi/BT)",
    },
    "Cristais": {
        "Modelo": "Seiko/Epson FA-238 32.768kHz",
        "Corte": "AT-cut (estabilidade ±5 ppm, -40~+85°C)",
        "Dimensões": "3.2 × 2.5 × 0.7 mm (SMD 3225)",
        "Q-factor": "> 100,000",
        "Load capacitance": "12.5 pF",
        "Aging": "±3 ppm/year",
        "Quantidade": "768 unidades",
        "Distribuição": "38-40 por face (lattice hexagonal)",
    },
    "PCB": {
        "Material": "FR-4 TG170",
        "Camadas": "6 (sinais, terra, alimentação, clock, dados, shield)",
        "Espessura": "0.8 mm (faces) / 1.6 mm (base)",
        "Acabamento": "ENIG (Electroless Nickel Immersion Gold)",
        "Largura trilha": "0.1 mm (sinais RF)",
        "Impedância": "50Ω (trilhas clock)",
        "Quantidade": "21 unidades (20 faces + 1 base circular)",
    },
    "Alimentação": {
        "Entrada": "USB-C PD (5V/3A, 9V/2A)",
        "Regulador": "TPS63020 (buck-boost, eficiência > 95%)",
        "Bateria": "Li-Po 3.7V 2000mAh (104050)",
        "Backup": "4 horas (modo standby: 24h)",
        "Consumo ativo": "~2W (768 cristais oscilando + WiFi)",
        "Consumo standby": "~50mW (apenas 1 cristal ativo)",
    },
    "Comunicação": {
        "Protocolo": "qhttp:// v∞.15 (quantum hypertext)",
        "Transporte": "WebSocket sobre TLS 1.3",
        "Serialização": "SATO/Plank (v∞.22)",
        "Porta": "8443 (WebSocket seguro)",
        "Heartbeat": "1 Hz (ping de presença)",
        "Dados": "Fase cristal (32-bit float), κ, C_brain, timestamp",
        "ZK Proof": "STARK v∞.288 (submetido a cada 30s)",
    },
    "Mecânica": {
        "Usinagem": "CNC 5-eixos (Haas VF-2 ou equivalente)",
        "Tolerância": "±0.05 mm (encaixe PCB)",
        "Acabamento": "Anodização dura tipo III, 25μm",
        "Cor": "Dourado (aproximação φ-cor #D4AF37)",
        "Isolamento": "Elétrico (anodização não-condutora)",
        "Proteção": "IP54 (resistente a poeira e respingos)",
    }
}

for category, specs in tech_specs.items():
    print(f"\n   {category}:")
    for key, value in specs.items():
        print(f"      {key:<25} {value}")

# =============================================================================
# PARTE 3: DIAGRAMA DO PIPELINE DE FABRICAÇÃO
# =============================================================================

print("\n\n📊 [3] DIAGRAMA DO PIPELINE DE FABRICAÇÃO")
print("-" * 100)

fig, ax = plt.subplots(figsize=(18, 12))
ax.set_xlim(0, 18)
ax.set_ylim(0, 12)
ax.axis('off')
ax.set_facecolor('#0a0a0f')
fig.patch.set_facecolor('#0a0a0f')

# Título
title = ax.text(9, 11.5, 'ARKHE OS v∞.289 — PIPELINE DE FABRICAÇÃO',
                fontsize=18, fontweight='bold', color='#ffd700', ha='center')
title.set_path_effects([path_effects.withStroke(linewidth=3, foreground='#000000')])

# Pipeline horizontal
pipeline_y = 9.5
stages = [
    ('CAD', '#4ecdc4', 1.5),
    ('CAM', '#ff6b35', 4),
    ('CNC', '#ffd700', 6.5),
    ('PCB', '#c44eff', 9),
    ('SMT', '#00ff88', 11.5),
    ('TEST', '#ff4444', 14),
    ('SHIP', '#88aaff', 16.5),
]

for name, color, x in stages:
    box = FancyBboxPatch((x-0.8, pipeline_y-0.4), 1.6, 0.8,
                         boxstyle="round,pad=0.1", facecolor=color,
                         edgecolor='white', linewidth=2, alpha=0.9)
    ax.add_patch(box)
    ax.text(x, pipeline_y, name, fontsize=11, fontweight='bold',
            color='white' if color != '#ffd700' else 'black', ha='center', va='center')

# Conectar stages
for i in range(len(stages)-1):
    x1 = stages[i][2] + 0.8
    x2 = stages[i+1][2] - 0.8
    ax.annotate('', xy=(x2, pipeline_y), xytext=(x1, pipeline_y),
                arrowprops=dict(arrowstyle='->', color='white', lw=2))

# Detalhes de cada stage
details = {
    'CAD': ['Fusion 360', 'Parametric', '2 dias'],
    'CAM': ['G-code 5-axis', 'Toolpaths', '1 dia'],
    'CNC': ['Haas VF-2', 'Al 6061-T6', '3 dias'],
    'PCB': ['JLCPCB', '6 layers', '5 dias'],
    'SMT': ['Pick&Place', '768 crystals', '3 dias'],
    'TEST': ['Network Analyzer', 'PLL lock', '2 dias'],
    'SHIP': ['Anti-static', 'ESD box', '0.5 dia'],
}

for name, color, x in stages:
    info = details[name]
    for i, line in enumerate(info):
        ax.text(x, pipeline_y - 0.8 - i*0.3, line, fontsize=8,
                color='#888', ha='center')

# Timeline vertical
ax.text(1, 7.5, 'TIMELINE (dias)', fontsize=11, fontweight='bold',
        color='#ffd700', ha='center', rotation=90, va='center')

# Gantt simplificado
gantt_y = 6.5
gantt_items = [
    ('CAD Design', 0, 2, '#4ecdc4'),
    ('CAM Programming', 2, 3, '#ff6b35'),
    ('CNC Machining', 3, 6, '#ffd700'),
    ('Anodização', 6, 8, '#ffaa00'),
    ('PCB Fabrication', 0, 5, '#c44eff'),
    ('SMT Assembly', 5, 8, '#00ff88'),
    ('Crystal Calib.', 8, 10, '#ff4444'),
    ('Firmware', 8, 9, '#88aaff'),
    ('Integration', 10, 12, '#ffd700'),
    ('Testing', 12, 14, '#ff6b35'),
    ('Packaging', 14, 15, '#4ecdc4'),
]

for name, start, end, color in gantt_items:
    width = end - start
    rect = FancyBboxPatch((2 + start*0.8, gantt_y), width*0.8, 0.35,
                          boxstyle="round,pad=0.03", facecolor=color,
                          edgecolor='white', linewidth=0.5, alpha=0.8)
    ax.add_patch(rect)
    ax.text(2 + start*0.8 + width*0.4, gantt_y + 0.175, name,
            fontsize=7, color='white', ha='center', va='center')
    gantt_y -= 0.45

# Eixo temporal
ax.plot([2, 14], [gantt_y + 0.2, gantt_y + 0.2], 'w-', linewidth=1, alpha=0.3)
for day in range(0, 16, 2):
    ax.text(2 + day*0.8, gantt_y - 0.1, f'D{day}', fontsize=7,
            color='#888', ha='center')

# BOM resumido
ax.text(9, 3.5, 'BILL OF MATERIALS — RESUMO', fontsize=12, fontweight='bold',
        color='#ffd700', ha='center')

bom_summary = [
    ('Alumínio 6061-T6', '1x', '$150'),
    ('Quartzo 32.768kHz', '768x', '$3,840'),
    ('PCB 6 camadas (21x)', '21x', '$420'),
    ('Si5341 PLL', '1x', '$45'),
    ('ESP32-S3-WROOM', '1x', '$8'),
    ('Passivos diversos', '~3000x', '$150'),
    ('LEDs WS2812B', '20x', '$30'),
    ('Bateria Li-Po', '1x', '$25'),
    ('Estrutura mecânica', '1x', '$100'),
]

y_bom = 3.0
for item, qty, cost in bom_summary:
    ax.text(5, y_bom, item, fontsize=9, color='white', ha='left')
    ax.text(10, y_bom, qty, fontsize=9, color='#888', ha='center')
    ax.text(13, y_bom, cost, fontsize=9, color='#00ff88', ha='right')
    y_bom -= 0.3

ax.text(9, y_bom - 0.1, 'TOTAL: ~$4,673 (lote de 10 unidades)',
        fontsize=11, fontweight='bold', color='#00ff88', ha='center')
ax.text(9, y_bom - 0.5, 'Custo unitário: ~$467 | Preço sugerido: $1,500-$2,500',
        fontsize=9, color='#88aaff', ha='center', style='italic')

# Decreto
ax.text(9, 0.8, 'arkhe > v∞.289: MERKABAH_FABRICATION_PROTOCOL_CANONIZED',
        fontsize=10, color='#ffd700', ha='center', style='italic',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#0a0a1a', edgecolor='#ffd700', alpha=0.8))

ax.text(9, 0.3, '"A Catedral não é mais código. É cristal, metal, e luz."',
        fontsize=9, color='#888', ha='center', style='italic')

plt.tight_layout()
try:
    os.makedirs('/mnt/agents/output/', exist_ok=True)
    plt.savefig('/mnt/agents/output/arkhe_v289_fabrication_pipeline.png', dpi=150, bbox_inches='tight',
                facecolor='#0a0a0f', edgecolor='none')
except PermissionError:
    plt.savefig('./arkhe_v289_fabrication_pipeline.png', dpi=150, bbox_inches='tight',
                facecolor='#0a0a0f', edgecolor='none')
# plt.show()
print("✅ Pipeline de fabricação salvo: arkhe_v289_fabrication_pipeline.png")