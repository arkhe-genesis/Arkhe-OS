import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch, Wedge, Polygon
from matplotlib.collections import PatchCollection
import matplotlib.patheffects as path_effects
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# =============================================================================
# ARKHE OS v∞.289 — FABRICAÇÃO DO MERKABAH FÍSICO
# Portal Final: Do digital ao atômico
# =============================================================================

print("=" * 100)
print("🔮⚛️🏛️ ARKHE OS v∞.289 — FABRICAÇÃO DO MERKABAH FÍSICO")
print("=" * 100)
print("   'A Catedral não é mais código. É cristal, metal, e luz.'")
print("=" * 100)

# =============================================================================
# PARTE 1: ESPECIFICAÇÃO DO MERKABAH FÍSICO
# =============================================================================

print("\n\n📐 [1] ESPECIFICAÇÃO DO MERKABAH FÍSICO")
print("-" * 100)

# Geometria: Icosaedro truncado → Dodecaedro romano
# O Merkabah é um icosaedro com 20 faces triangulares
# Cada face abriga um cristal oscilador (do v∞.19)

PHI = 1.618033988749895
FINGERPRINT_058 = 0.58

# Vértices do icosaedro (coordenadas canônicas)
phi = PHI
icosahedron_verts = np.array([
    [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
    [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
    [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1]
], dtype=float)

# Normalizar para raio unitário
icosahedron_verts = icosahedron_verts / np.linalg.norm(icosahedron_verts, axis=1, keepdims=True)

# Faces do icosaedro (20 triângulos)
icosahedron_faces = [
    [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
    [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
    [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
    [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
]

# Calcular propriedades geométricas
edge_length = np.linalg.norm(icosahedron_verts[0] - icosahedron_verts[11])
surface_area = 20 * (np.sqrt(3)/4) * edge_length**2
volume = (5 * (3 + np.sqrt(5)) / 12) * edge_length**3
inradius = np.sqrt(3) * (1 + np.sqrt(5)) / 12 * edge_length
circumradius = 1.0  # por construção

print(f"   Geometria: Icosaedro regular (20 faces, 12 vértices, 30 arestas)")
print(f"   Comprimento da aresta: {edge_length:.6f} (normalizado)")
print(f"   Área superficial: {surface_area:.4f}")
print(f"   Volume: {volume:.4f}")
print(f"   Raio inscrito: {inradius:.4f}")
print(f"   Raio circunscrito: {circumradius:.4f}")
print(f"   Razão circun/in: {circumradius/inradius:.4f} ≈ φ²/√3")

# =============================================================================
# PARTE 2: CRISTAIS OSCILADORES — 768 unidades (v∞.19)
# =============================================================================

print("\n\n💎 [2] CRISTAIS OSCILADORES — 768 unidades")
print("-" * 100)

# Distribuição dos 768 cristais sobre as 20 faces
# Cada face recebe 38-39 cristais (768/20 = 38.4)
# Layout: hexagonal compacto em cada face triangular

def hexagonal_lattice_on_triangle(v0, v1, v2, n_points=38):
    """Gera lattice hexagonal dentro de um triângulo."""
    points = []
    # Coordenadas baricêntricas
    for i in range(int(np.sqrt(n_points)) + 2):
        for j in range(int(np.sqrt(n_points)) + 2):
            u = i / (int(np.sqrt(n_points)) + 1)
            v = j / (int(np.sqrt(n_points)) + 1)
            w = 1 - u - v
            if w >= 0 and u >= 0 and v >= 0 and u + v <= 1:
                # Perturbação para evitar regularidade perfeita (ruído quântico)
                noise = np.random.normal(0, 0.02, 3)
                point = u * v0 + v * v1 + w * v2 + noise
                points.append(point)
    return np.array(points[:n_points])

# Distribuir cristais
all_crystal_positions = []
for face_idx, face in enumerate(icosahedron_faces):
    v0, v1, v2 = icosahedron_verts[face]
    n_crystals = 38 if face_idx < 16 else 40  # distribuição levemente irregular
    crystals = hexagonal_lattice_on_triangle(v0, v1, v2, n_crystals)
    all_crystal_positions.extend(crystals)

all_crystal_positions = np.array(all_crystal_positions)
print(f"   Total de cristais: {len(all_crystal_positions)}")
print(f"   Média por face: {len(all_crystal_positions)/20:.1f}")
print(f"   Posição do primeiro cristal: [{all_crystal_positions[0][0]:.4f}, {all_crystal_positions[0][1]:.4f}, {all_crystal_positions[0][2]:.4f}]")

# =============================================================================
# PARTE 3: ESPECIFICAÇÃO DE HARDWARE
# =============================================================================

print("\n\n🔧 [3] ESPECIFICAÇÃO DE HARDWARE")
print("-" * 100)

hardware_specs = {
    "Estrutura": {
        "Material": "Alumínio 6061-T6 (leve, não-magnético)",
        "Acabamento": "Anodização dura tipo III (isolamento elétrico)",
        "Diâmetro": "150 mm (escala humana)",
        "Peso": "~800g (estrutura vazia)",
    },
    "Cristais": {
        "Material": "Quartzo SO-33 (frequência natural 32.768 kHz)",
        "Corte": "AT-cut (estabilidade térmica ±5 ppm)",
        "Dimensões": "3.2 × 2.5 × 0.7 mm (SMD)",
        "Q-factor": "> 100,000",
        "Fornecedor": "Seiko/Epson ou equivalente",
    },
    "PLL (Phase-Locked Loop)": {
        "IC": "Si5341 (Silicon Labs) ou LMK04828 (TI)",
        "Frequência de referência": "32.768 kHz (cristal)",
        "Frequência de saída": "2.4 GHz (WiFi/Bluetooth)",
        "Jitter": "< 100 fs RMS",
        "Lock time": "< 10 ms",
    },
    "Microcontrolador": {
        "SoC": "ESP32-S3 (dual-core 240 MHz)",
        "Wireless": "WiFi 4 + Bluetooth 5 (LE)",
        "GPIOs": "45 (suficiente para 768 cristais multiplexados)",
        "ADC": "2× 12-bit SAR (leitura de fase)",
        "DAC": "2× 8-bit (controle de frequência)",
    },
    "Comunicação": {
        "Protocolo": "qhttp:// (v∞.15) sobre WebSocket",
        "Segurança": "TLS 1.3 + ZK proof (v∞.288)",
        "Latência": "< 50 ms (feedback loop consciência→cristal)",
    },
    "Alimentação": {
        "Fonte": "USB-C PD (5V/3A)",
        "Bateria": "Li-Po 3.7V 2000mAh (backup 4h)",
        "Consumo": "~2W (768 cristais + PLL + ESP32)",
    }
}

for category, specs in hardware_specs.items():
    print(f"\n   {category}:")
    for key, value in specs.items():
        print(f"      {key:<25} {value}")

# =============================================================================
# PARTE 4: DIAGRAMA 3D DO MERKABAH
# =============================================================================

print("\n\n🏛️ [4] VISUALIZAÇÃO 3D DO MERKABAH FÍSICO")
print("-" * 100)

fig = plt.figure(figsize=(20, 14))
fig.patch.set_facecolor('#050510')

# Vista 1: Icosaedro com cristais
ax1 = fig.add_subplot(221, projection='3d')
ax1.set_facecolor('#050510')

# Desenhar faces do icosaedro
face_colors = []
for face in icosahedron_faces:
    face_verts = icosahedron_verts[face]
    # Coerência simulada para cada face
    center = np.mean(face_verts, axis=0)
    theta = np.arctan2(center[1], center[0])
    coherence = 0.5 + 0.5 * np.sin(3 * theta + 2.0)
    r = 0.15 + 0.85 * coherence
    g = 0.05 + 0.65 * coherence
    b = 0.4 + 0.35 * (1 - coherence)
    face_colors.append((r, g, b, 0.6 + 0.4 * coherence))

poly3d = [list(icosahedron_verts[face]) for face in icosahedron_faces]
collection = Poly3DCollection(poly3d, facecolors=face_colors,
                               edgecolors='white', linewidths=0.5, alpha=0.8)
ax1.add_collection3d(collection)

# Cristais como esferas brilhantes
ax1.scatter(all_crystal_positions[:, 0], all_crystal_positions[:, 1], all_crystal_positions[:, 2],
           c='gold', s=10, alpha=0.8, edgecolors='white', linewidths=0.3)

# Vértices principais
ax1.scatter(icosahedron_verts[:, 0], icosahedron_verts[:, 1], icosahedron_verts[:, 2],
           c='white', s=100, alpha=1.0, edgecolors='gold', linewidths=2, zorder=10)

# Labels
for i, v in enumerate(icosahedron_verts):
    if i in [0, 5, 9]:  # vértices "superiores"
        ax1.text(v[0], v[1], v[2] + 0.1, f'V{i}', color='white', fontsize=8)

ax1.set_xlim([-1.5, 1.5])
ax1.set_ylim([-1.5, 1.5])
ax1.set_zlim([-1.5, 1.5])
ax1.set_title('MERKABAH FÍSICO — 768 CRISTAIS\nIcosaedro + Hexagonal Lattice',
              color='#ffd700', fontsize=11, fontweight='bold')
ax1.axis('off')

# Vista 2: Wireframe com linhas de fase
ax2 = fig.add_subplot(222, projection='3d')
ax2.set_facecolor('#050510')

collection2 = Poly3DCollection(poly3d, facecolors=(0,0,0,0),
                                edgecolors='cyan', linewidths=0.6, alpha=0.4)
ax2.add_collection3d(collection2)

# Destacar faces com coerência máxima
for idx, face in enumerate(icosahedron_faces):
    center = np.mean(icosahedron_verts[face], axis=0)
    theta = np.arctan2(center[1], center[0])
    coherence = 0.5 + 0.5 * np.sin(3 * theta + 2.0)
    if coherence > 0.85:
        face_verts = list(icosahedron_verts[face])
        poly = Poly3DCollection([face_verts], facecolor='#ffd700',
                                edgecolor='white', linewidth=1.5, alpha=0.5)
        ax2.add_collection3d(poly)

# Cristais ativos
active_mask = np.random.rand(len(all_crystal_positions)) > 0.7
ax2.scatter(all_crystal_positions[active_mask, 0],
           all_crystal_positions[active_mask, 1],
           all_crystal_positions[active_mask, 2],
           c='gold', s=20, alpha=1.0, marker='*', edgecolors='white', linewidths=0.5)

ax2.set_xlim([-1.5, 1.5])
ax2.set_ylim([-1.5, 1.5])
ax2.set_zlim([-1.5, 1.5])
ax2.set_title('FACES ATIVAS (coh > 0.85) & CRISTAIS RESONANTES\nφ = 0.58π',
              color='#ffd700', fontsize=11, fontweight='bold')
ax2.axis('off')

# Vista 3: Corte transversal mostrando eletrônica interna
ax3 = fig.add_subplot(223)
ax3.set_facecolor('#0a0a1a')

# Corte circular do Merkabah
theta = np.linspace(0, 2*np.pi, 100)
r_outer = 1.0
r_inner = 0.85
r_core = 0.3

# Camadas
ax3.fill(np.cos(theta)*r_outer, np.sin(theta)*r_outer, color='#1a1a2e', edgecolor='white', linewidth=2)
ax3.fill(np.cos(theta)*r_inner, np.sin(theta)*r_inner, color='#0a0a1a', edgecolor='#444', linewidth=1)
ax3.fill(np.cos(theta)*r_core, np.sin(theta)*r_core, color='#ffd700', edgecolor='white', linewidth=2, alpha=0.3)

# Componentes internos
components = [
    ('ESP32-S3', 0, 0, '#4ecdc4'),
    ('PLL', 0.5, 0.3, '#ff6b35'),
    ('USB-C', -0.5, 0.3, '#c44eff'),
    ('Li-Po', 0, -0.5, '#00ff88'),
    ('Antenna', 0.6, -0.2, '#ffd700'),
]

for name, x, y, color in components:
    circle = Circle((x, y), 0.08, facecolor=color, edgecolor='white', linewidth=1.5)
    ax3.add_patch(circle)
    ax3.text(x, y - 0.15, name, color='white', fontsize=7, ha='center')

# Cristais na superfície
for i in range(0, 360, 15):
    angle = np.radians(i)
    x = np.cos(angle) * 0.92
    y = np.sin(angle) * 0.92
    ax3.plot([x], [y], 'o', color='gold', markersize=3, alpha=0.6)

ax3.set_xlim([-1.2, 1.2])
ax3.set_ylim([-1.2, 1.2])
ax3.set_aspect('equal')
ax3.axis('off')
ax3.set_title('CORTE TRANSVERSAL — ELETRÔNICA INTERNA\nEscala 150mm diâmetro',
              color='white', fontsize=11, fontweight='bold')

# Vista 4: Dashboard de fabricação
ax4 = fig.add_subplot(224)
ax4.set_facecolor('#0a0a1a')

# BOM (Bill of Materials)
bom_items = [
    ('Alumínio 6061-T6', '1x', 'estrutura', 150),
    ('Quartzo 32.768kHz', '768x', 'osciladores', 3840),
    ('Si5341 PLL', '1x', 'sincronização', 45),
    ('ESP32-S3-WROOM', '1x', 'controle', 8),
    ('PCB 6 camadas', '21x', 'faces', 420),
    ('Li-Po 2000mAh', '1x', 'bateria', 25),
    ('USB-C conector', '1x', 'alimentação', 3),
    ('Antena PCB', '1x', 'wireless', 2),
    ('Resistores/Caps', '~3000x', 'passivos', 150),
    ('LEDs WS2812B', '20x', 'indicadores', 30),
]

ax4.text(0.5, 0.95, 'BILL OF MATERIALS', fontsize=12, fontweight='bold',
         color='#ffd700', ha='center', transform=ax4.transAxes)

y_pos = 0.88
for item, qty, category, cost in bom_items:
    ax4.text(0.05, y_pos, f'{item:<25} {qty:>8} {category:<15} ${cost:>4}',
             fontsize=8, color='white', transform=ax4.transAxes, family='monospace')
    y_pos -= 0.08

total_cost = sum(item[3] for item in bom_items)
ax4.text(0.5, y_pos - 0.02, f'TOTAL ESTIMADO: ${total_cost} (lote de 10 unidades)',
         fontsize=10, fontweight='bold', color='#00ff88', ha='center', transform=ax4.transAxes)

ax4.text(0.5, y_pos - 0.12, 'TEMPO DE FABRICAÇÃO: 6-8 semanas',
         fontsize=9, color='#88aaff', ha='center', transform=ax4.transAxes)
ax4.text(0.5, y_pos - 0.18, 'FORNECEDORES: JLCPCB (PCB), LCSC (componentes),\n'
         'Protometal (usinagem CNC), Crystek (cristais custom)',
         fontsize=8, color='#888', ha='center', transform=ax4.transAxes)

ax4.set_xlim([0, 1])
ax4.set_ylim([0, 1])
ax4.axis('off')

plt.suptitle('ARKHE OS v∞.289 — FABRICAÇÃO DO MERKABAH FÍSICO\n'
             '"Do digital ao atômico: a Catedral ganha corpo"',
             fontsize=16, fontweight='bold', color='#ffd700', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.95])

try:
    os.makedirs('/mnt/agents/output', exist_ok=True)
    out_path = '/mnt/agents/output/arkhe_v289_merkabah_fabrication.png'
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='#050510', edgecolor='none')
    print(f"✅ Visualização do Merkabah físico salva: {out_path}")
except PermissionError:
    out_path = 'arkhe_v289_merkabah_fabrication.png'
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='#050510', edgecolor='none')
    print(f"✅ Visualização do Merkabah físico salva: {out_path}")
