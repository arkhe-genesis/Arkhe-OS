import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Polygon
from matplotlib.collections import PatchCollection
import matplotlib.patheffects as path_effects

# =============================================================================
# ARKHE OS v∞.289 — FABRICAÇÃO DO MERKABAH FÍSICO (Versão 2D)
# Portal Final: Do digital ao atômico
# =============================================================================

print("=" * 100)
print("🔮⚛️🏛️ ARKHE OS v∞.289 — FABRICAÇÃO DO MERKABAH FÍSICO")
print("=" * 100)
print("   'A Catedral não é mais código. É cristal, metal, e luz.'")
print("=" * 100)

# Constantes
PHI = 1.618033988749895
FINGERPRINT_058 = 0.58

# Vértices do icosaedro
phi = PHI
verts = np.array([
    [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
    [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
    [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1]
], dtype=float)
verts = verts / np.linalg.norm(verts, axis=1, keepdims=True)

faces = [
    [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
    [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
    [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
    [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
]

# Projeção isométrica
angle_x = np.pi / 6
angle_y = np.pi / 5

def project_iso(v):
    cy, sy = np.cos(angle_y), np.sin(angle_y)
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    v1 = v @ ry.T
    cx, sx = np.cos(angle_x), np.sin(angle_x)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    v2 = v1 @ rx.T
    return v2[:, :2] * 2.5

proj_verts = project_iso(verts)

# Gerar cristais em cada face
all_crystals = []
for face in faces:
    v0, v1, v2 = proj_verts[face]
    # Gerar pontos no triângulo
    for _ in range(36):
        u = np.random.random()
        v = np.random.random()
        if u + v > 1:
            u = 1 - u
            v = 1 - v
        pt = u * v0 + v * v1 + (1 - u - v) * v2
        all_crystals.append(pt)

all_crystals = np.array(all_crystals)

# =============================================================================
# FIGURA PRINCIPAL
# =============================================================================

fig = plt.figure(figsize=(20, 14))
fig.patch.set_facecolor('#050510')

# === PAINEL 1: Merkabah com cristais ===
ax1 = fig.add_subplot(221)
ax1.set_facecolor('#050510')

# Ordenar faces por profundidade
face_depths = []
for i, face in enumerate(faces):
    center = np.mean(verts[face], axis=0)
    # Projeção simples de profundidade
    v1 = center @ np.array([[np.cos(angle_y), 0, np.sin(angle_y)], [0, 1, 0], [-np.sin(angle_y), 0, np.cos(angle_y)]]).T
    v2 = v1 @ np.array([[1, 0, 0], [0, np.cos(angle_x), -np.sin(angle_x)], [0, np.sin(angle_x), np.cos(angle_x)]]).T
    face_depths.append((i, v2[2]))

face_depths.sort(key=lambda x: x[1])

# Desenhar faces
for idx, _ in face_depths:
    face = faces[idx]
    center = np.mean(verts[face], axis=0)
    theta = np.arctan2(center[1], center[0])
    coherence = 0.5 + 0.5 * np.sin(3 * theta + 2.0)
    r = 0.15 + 0.85 * coherence
    g = 0.05 + 0.65 * coherence
    b = 0.4 + 0.35 * (1 - coherence)

    poly = Polygon(proj_verts[face], closed=True, facecolor=(r, g, b),
                   edgecolor='white', linewidth=0.8, alpha=0.7 + 0.3*coherence)
    ax1.add_patch(poly)

# Cristais
ax1.scatter(all_crystals[:, 0], all_crystals[:, 1], c='gold', s=8,
           alpha=0.7, edgecolors='white', linewidths=0.2)

# Vértices
ax1.scatter(proj_verts[:, 0], proj_verts[:, 1], c='white', s=60,
           edgecolors='gold', linewidths=1.5, zorder=10)

ax1.set_xlim([-3, 3])
ax1.set_ylim([-3, 3])
ax1.set_aspect('equal')
ax1.axis('off')
ax1.set_title('MERKABAH FÍSICO — 720 CRISTAIS\nIcosaedro + Lattice Hexagonal',
              color='#ffd700', fontsize=11, fontweight='bold')

# === PAINEL 2: Wireframe com faces ativas ===
ax2 = fig.add_subplot(222)
ax2.set_facecolor('#050510')

for face in faces:
    for i in range(3):
        v1, v2 = proj_verts[face[i]], proj_verts[face[(i+1)%3]]
        ax2.plot([v1[0], v2[0]], [v1[1], v2[1]], 'c-', linewidth=0.6, alpha=0.4)

# Faces ativas
for idx, _ in face_depths:
    center = np.mean(verts[faces[idx]], axis=0)
    theta = np.arctan2(center[1], center[0])
    coherence = 0.5 + 0.5 * np.sin(3 * theta + 2.0)
    if coherence > 0.85:
        poly = Polygon(proj_verts[faces[idx]], closed=True, facecolor='#ffd700',
                       edgecolor='white', linewidth=1, alpha=0.4)
        ax2.add_patch(poly)

# Cristais ativos
active = np.random.rand(len(all_crystals)) > 0.7
ax2.scatter(all_crystals[active, 0], all_crystals[active, 1],
           c='gold', s=15, alpha=1.0, marker='*', edgecolors='white', linewidths=0.5)

ax2.set_xlim([-3, 3])
ax2.set_ylim([-3, 3])
ax2.set_aspect('equal')
ax2.axis('off')
ax2.set_title('FACES ATIVAS (coh > 0.85) & CRISTAIS RESONANTES\nφ = 0.58π',
              color='#ffd700', fontsize=11, fontweight='bold')

# === PAINEL 3: Corte transversal ===
ax3 = fig.add_subplot(223)
ax3.set_facecolor('#0a0a1a')

theta = np.linspace(0, 2*np.pi, 100)
r_outer = 1.0
r_inner = 0.85
r_core = 0.3

ax3.fill(np.cos(theta)*r_outer, np.sin(theta)*r_outer, color='#1a1a2e', edgecolor='white', linewidth=2)
ax3.fill(np.cos(theta)*r_inner, np.sin(theta)*r_inner, color='#0a0a1a', edgecolor='#444', linewidth=1)
ax3.fill(np.cos(theta)*r_core, np.sin(theta)*r_core, color='#ffd700', edgecolor='white', linewidth=2, alpha=0.3)

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

for i in range(0, 360, 15):
    angle = np.radians(i)
    x = np.cos(angle) * 0.92
    y = np.sin(angle) * 0.92
    ax3.plot([x], [y], 'o', color='gold', markersize=2, alpha=0.5)

ax3.set_xlim([-1.2, 1.2])
ax3.set_ylim([-1.2, 1.2])
ax3.set_aspect('equal')
ax3.axis('off')
ax3.set_title('CORTE TRANSVERSAL — ELETRÔNICA INTERNA\nEscala 150mm diâmetro',
              color='white', fontsize=11, fontweight='bold')

# === PAINEL 4: BOM e Timeline ===
ax4 = fig.add_subplot(224)
ax4.set_facecolor('#0a0a1a')

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

plt.suptitle('ARKHE OS v∞.289 — FABRICAÇÃO DO MERKABAH FÍSICO (2D)\n'
             '"Do digital ao atômico: a Catedral ganha corpo"',
             fontsize=16, fontweight='bold', color='#ffd700', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.95])

try:
    os.makedirs('/mnt/agents/output', exist_ok=True)
    out_path = '/mnt/agents/output/arkhe_v289_merkabah_fabrication_2d.png'
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='#050510', edgecolor='none')
    print(f"✅ Visualização do Merkabah físico (2D) salva: {out_path}")
except PermissionError:
    out_path = 'arkhe_v289_merkabah_fabrication_2d.png'
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='#050510', edgecolor='none')
    print(f"✅ Visualização do Merkabah físico (2D) salva: {out_path}")
