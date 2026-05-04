import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import os

# =============================================================================
# ARKHE OS v∞.289 — FABRICAÇÃO DO MERKABAH FÍSICO (Corrigido v2)
# =============================================================================

PHI = 1.618033988749895

# Vértices do icosaedro
phi = PHI
icosahedron_verts = np.array([
    [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
    [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
    [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1]
], dtype=float)
icosahedron_verts = icosahedron_verts / np.linalg.norm(icosahedron_verts, axis=1, keepdims=True)

icosahedron_faces = [
    [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
    [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
    [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
    [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
]

# Cristais
def hexagonal_lattice_on_triangle(v0, v1, v2, n_points=38):
    points = []
    for i in range(int(np.sqrt(n_points)) + 2):
        for j in range(int(np.sqrt(n_points)) + 2):
            u = i / (int(np.sqrt(n_points)) + 1)
            v = j / (int(np.sqrt(n_points)) + 1)
            w = 1 - u - v
            if w >= 0 and u >= 0 and v >= 0 and u + v <= 1:
                noise = np.random.normal(0, 0.02, 3)
                point = u * v0 + v * v1 + w * v2 + noise
                points.append(point)
    return np.array(points[:n_points])

all_crystal_positions = []
for face_idx, face in enumerate(icosahedron_faces):
    v0, v1, v2 = icosahedron_verts[face]
    n_crystals = 38 if face_idx < 16 else 40
    crystals = hexagonal_lattice_on_triangle(v0, v1, v2, n_crystals)
    all_crystal_positions.extend(crystals)
all_crystal_positions = np.array(all_crystal_positions)

# =============================================================================
# FIGURA PRINCIPAL
# =============================================================================
fig = plt.figure(figsize=(20, 14))
fig.patch.set_facecolor('#050510')

# --- Vista 1: Icosaedro sólido ---
ax1 = fig.add_subplot(221, projection='3d')
ax1.set_facecolor('#050510')

for face in icosahedron_faces:
    face_verts = icosahedron_verts[face]
    center = np.mean(face_verts, axis=0)
    theta = np.arctan2(center[1], center[0])
    coherence = 0.5 + 0.5 * np.sin(3 * theta + 2.0)
    r = 0.15 + 0.85 * coherence
    g = 0.05 + 0.65 * coherence
    b = 0.4 + 0.35 * (1 - coherence)
    color = (r, g, b, 0.6 + 0.4 * coherence)
    poly = Poly3DCollection([face_verts], facecolors=[color],
                             edgecolors='white', linewidths=0.5, alpha=0.8)
    ax1.add_collection3d(poly)

ax1.scatter(all_crystal_positions[:, 0], all_crystal_positions[:, 1], all_crystal_positions[:, 2],
           c='gold', s=10, alpha=0.8, edgecolors='white', linewidths=0.3)
ax1.scatter(icosahedron_verts[:, 0], icosahedron_verts[:, 1], icosahedron_verts[:, 2],
           c='white', s=100, alpha=1.0, edgecolors='gold', linewidths=2)

for i, v in enumerate(icosahedron_verts):
    if i in [0, 5, 9]:
        ax1.text(v[0], v[1], v[2] + 0.1, f'V{i}', color='white', fontsize=8)

ax1.set_xlim([-1.5, 1.5]); ax1.set_ylim([-1.5, 1.5]); ax1.set_zlim([-1.5, 1.5])
ax1.set_title('MERKABAH FÍSICO — 768 CRISTAIS\nIcosaedro + Hexagonal Lattice',
              color='#ffd700', fontsize=11, fontweight='bold')
ax1.axis('off')

# --- Vista 2: Wireframe usando plot (evita bug Poly3DCollection) ---
ax2 = fig.add_subplot(222, projection='3d')
ax2.set_facecolor('#050510')

# Desenhar arestas como linhas
edges = set()
for face in icosahedron_faces:
    for i in range(3):
        a, b = sorted([face[i], face[(i+1)%3]])
        if (a, b) not in edges:
            edges.add((a, b))
            v1, v2 = icosahedron_verts[a], icosahedron_verts[b]
            ax2.plot([v1[0], v2[0]], [v1[1], v2[1]], [v1[2], v2[2]],
                    'c-', linewidth=0.6, alpha=0.4)

# Faces ativas
for face in icosahedron_faces:
    center = np.mean(icosahedron_verts[face], axis=0)
    theta = np.arctan2(center[1], center[0])
    coherence = 0.5 + 0.5 * np.sin(3 * theta + 2.0)
    if coherence > 0.85:
        face_verts = icosahedron_verts[face]
        poly = Poly3DCollection([face_verts], facecolors=['#ffd700'],
                                edgecolor='white', linewidth=1.5, alpha=0.5)
        ax2.add_collection3d(poly)

active_mask = np.random.rand(len(all_crystal_positions)) > 0.7
ax2.scatter(all_crystal_positions[active_mask, 0],
           all_crystal_positions[active_mask, 1],
           all_crystal_positions[active_mask, 2],
           c='gold', s=20, alpha=1.0, marker='*', edgecolors='white', linewidths=0.5)

ax2.set_xlim([-1.5, 1.5]); ax2.set_ylim([-1.5, 1.5]); ax2.set_zlim([-1.5, 1.5])
ax2.set_title('FACES ATIVAS (coh > 0.85) & CRISTAIS RESONANTES\nφ = 0.58π',
              color='#ffd700', fontsize=11, fontweight='bold')
ax2.axis('off')

# --- Vista 3: Corte transversal ---
ax3 = fig.add_subplot(223)
ax3.set_facecolor('#0a0a1a')

theta = np.linspace(0, 2*np.pi, 100)
ax3.fill(np.cos(theta)*1.0, np.sin(theta)*1.0, color='#1a1a2e', edgecolor='white', linewidth=2)
ax3.fill(np.cos(theta)*0.85, np.sin(theta)*0.85, color='#0a0a1a', edgecolor='#444', linewidth=1)
ax3.fill(np.cos(theta)*0.3, np.sin(theta)*0.3, color='#ffd700', edgecolor='white', linewidth=2, alpha=0.3)

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
    ax3.plot([np.cos(angle) * 0.92], [np.sin(angle) * 0.92], 'o', color='gold', markersize=3, alpha=0.6)

ax3.set_xlim([-1.2, 1.2]); ax3.set_ylim([-1.2, 1.2]); ax3.set_aspect('equal'); ax3.axis('off')
ax3.set_title('CORTE TRANSVERSAL — ELETRÔNICA INTERNA\nEscala 150mm diâmetro',
              color='white', fontsize=11, fontweight='bold')

# --- Vista 4: BOM ---
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

ax4.set_xlim([0, 1]); ax4.set_ylim([0, 1]); ax4.axis('off')

plt.suptitle('ARKHE OS v∞.289 — FABRICAÇÃO DO MERKABAH FÍSICO\n'
             '"Do digital ao atômico: a Catedral ganha corpo"',
             fontsize=16, fontweight='bold', color='#ffd700', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.95])
try:
    os.makedirs('/mnt/agents/output/', exist_ok=True)
    plt.savefig('/mnt/agents/output/arkhe_v289_merkabah_fabrication.png', dpi=150, bbox_inches='tight',
                facecolor='#050510', edgecolor='none')
except PermissionError:
    plt.savefig('./arkhe_v289_merkabah_fabrication.png', dpi=150, bbox_inches='tight',
                facecolor='#050510', edgecolor='none')
# plt.show()
print("✅ Visualização 3D do Merkabah salva com sucesso.")