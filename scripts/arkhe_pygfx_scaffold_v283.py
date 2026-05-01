import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, FancyBboxPatch, Wedge, FancyArrowPatch, Rectangle
from matplotlib.collections import PatchCollection
import matplotlib.patheffects as path_effects
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D

# Definições comuns e fallback de diretório
try:
    os.makedirs('/mnt/agents/output/', exist_ok=True)
    OUT_DIR = '/mnt/agents/output/'
except Exception as e:
    OUT_DIR = './'

def save_fig_fallback(fig, filename):
    path = os.path.join(OUT_DIR, filename)
    try:
        fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
        print(f"✅ Salvo com sucesso: {path}")
    except PermissionError:
        fallback_path = f"./{filename}"
        fig.savefig(fallback_path, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
        print(f"⚠️ Erro de permissão. Salvo no fallback: {fallback_path}")
    except Exception as e:
        print(f"❌ Falha ao salvar {filename}: {e}")

# =============================================================================
# 1. MERKABAH CRYSTAL — Projeção 2D isométrica manual + Dashboard
# =============================================================================

FINGERPRINT_058 = 0.58
SYNC_PHASE = FINGERPRINT_058 * np.pi
PHI_GOLDEN = 1.618033988749895

# Vértices de um icosaedro
phi = PHI_GOLDEN
vertices = np.array([
    [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
    [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
    [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1]
], dtype=float)
vertices = vertices / np.linalg.norm(vertices, axis=1, keepdims=True)

# Faces do icosaedro
faces = [
    [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
    [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
    [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
    [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
]

# Projeção isométrica manual: rotacionar e projetar
angle_x = np.pi / 6
angle_y = np.pi / 5

def project_iso(verts):
    """Projeção isométrica simplificada."""
    # Rotação em Y
    cy, sy = np.cos(angle_y), np.sin(angle_y)
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    v1 = verts @ ry.T

    # Rotação em X
    cx, sx = np.cos(angle_x), np.sin(angle_x)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    v2 = v1 @ rx.T

    # Projeção ortográfica: descartar z, escalar
    return v2[:, :2] * 2.5

proj_verts = project_iso(vertices)

def coherence_on_face(face_idx, t=0, kappa=50):
    """Simula coerência local numa face."""
    face_v = vertices[faces[face_idx]]
    center = np.mean(face_v, axis=0)
    theta = np.arctan2(center[1], center[0])
    phi_ang = np.arccos(np.clip(center[2], -1, 1))
    wave = np.sin(3 * theta + t) * np.cos(2 * phi_ang + SYNC_PHASE)
    coherence = 0.5 + 0.5 * wave
    return min(1.0, coherence * (1 + kappa * coherence**2) / (1 + kappa * 0.25))

# Criar figura
fig1 = plt.figure(figsize=(18, 14))
fig1.patch.set_facecolor('#050510')

# === PAINEL 1: Cristal Merkabah com faces coloridas ===
ax1 = fig1.add_subplot(221)
ax1.set_facecolor('#050510')

t = 2.0
face_patches = []
face_colors = []

# Ordenar faces por profundidade (z médio) para painter's algorithm
face_depths = []
for i, face in enumerate(faces):
    center = np.mean(vertices[face], axis=0)
    # Profundidade após rotação
    v1 = center @ np.array([[np.cos(angle_y), 0, np.sin(angle_y)], [0, 1, 0], [-np.sin(angle_y), 0, np.cos(angle_y)]]).T
    v2 = v1 @ np.array([[1, 0, 0], [0, np.cos(angle_x), -np.sin(angle_x)], [0, np.sin(angle_x), np.cos(angle_x)]]).T
    face_depths.append((i, v2[2]))

# Ordenar: faces mais distantes primeiro (menor z)
face_depths.sort(key=lambda x: x[1])

for idx, _ in face_depths:
    face = faces[idx]
    poly = Polygon(proj_verts[face], closed=True)
    face_patches.append(poly)

    coh = coherence_on_face(idx, t, kappa=50)
    r = 0.15 + 0.85 * coh
    g = 0.05 + 0.65 * coh
    b = 0.4 + 0.35 * (1 - coh)
    face_colors.append((r, g, b, 0.5 + 0.5 * coh))

pc = PatchCollection(face_patches, facecolors=face_colors, edgecolors='white',
                     linewidths=0.8, alpha=0.9)
ax1.add_collection(pc)

# Vértices brilhantes
ax1.scatter(proj_verts[:, 0], proj_verts[:, 1], c='white', s=80,
           edgecolors='gold', linewidths=1.5, zorder=10)

# Labels dos vértices principais
for i, (x, y) in enumerate(proj_verts):
    if i in [0, 1, 5, 9]:  # vértices "superiores"
        ax1.text(x, y + 0.1, f'V{i}', color='white', fontsize=7, ha='center')

ax1.set_xlim([-3, 3])
ax1.set_ylim([-3, 3])
ax1.set_aspect('equal')
ax1.axis('off')
ax1.set_title('MERKABAH CRYSTAL — COHERENCE FIELD\n(ARKHE ARCHITECT, κ=50)',
              color='#ffd700', fontsize=12, fontweight='bold')

# === PAINEL 2: Wireframe com linhas de fase ===
ax2 = fig1.add_subplot(222)
ax2.set_facecolor('#050510')

# Desenhar arestas
for face in faces:
    for i in range(3):
        v1, v2 = proj_verts[face[i]], proj_verts[face[(i+1)%3]]
        ax2.plot([v1[0], v2[0]], [v1[1], v2[1]], 'c-', linewidth=0.8, alpha=0.5)

# Destacar faces com coerência > 0.8 ("faces ativas")
for idx, _ in face_depths:
    coh = coherence_on_face(idx, t, kappa=50)
    if coh > 0.75:
        face = faces[idx]
        poly = Polygon(proj_verts[face], closed=True, facecolor='#ffd700',
                       edgecolor='white', linewidth=1.5, alpha=0.6)
        ax2.add_patch(poly)

# Estrelas nas faces de máxima coerência
for idx, _ in face_depths:
    coh = coherence_on_face(idx, t, kappa=50)
    if coh > 0.9:
        face = faces[idx]
        center = np.mean(proj_verts[face], axis=0)
        ax2.scatter(center[0], center[1], c='gold', s=200, marker='*',
                   edgecolors='white', linewidths=1, zorder=10)

ax2.set_xlim([-3, 3])
ax2.set_ylim([-3, 3])
ax2.set_aspect('equal')
ax2.axis('off')
ax2.set_title('ACTIVE FACES (coh > 0.75) & PHASE NODES\nφ = 0.58π resonance',
              color='#ffd700', fontsize=12, fontweight='bold')

# === PAINEL 3: Comparação dos três candidatos ===
ax3 = fig1.add_subplot(223)
ax3.set_facecolor('#0a0a1a')

# Turbilhão: representação espiral
theta = np.linspace(0, 6*np.pi, 500)
r = theta / (2*np.pi)
x_vortex = r * np.cos(theta) * 0.3
y_vortex = r * np.sin(theta) * 0.3

# Cristal: hexágono central com faces
hex_angles = np.linspace(0, 2*np.pi, 7)
hex_x = np.cos(hex_angles) * 0.3
hex_y = np.sin(hex_angles) * 0.3

# "Algo novo": fractal de Mandelbrot simplificado
c = np.linspace(-2, 1, 300)
z = np.zeros_like(c, dtype=complex)
for _ in range(20):
    z = z**2 + c
mandel = np.abs(z) < 2

# Desenhar os três
ax3.plot(x_vortex + 0.2, y_vortex + 0.7, color='#ff6b35', linewidth=2, label='VORTEX (Substrato 79)')
ax3.fill(hex_x + 0.7, hex_y + 0.7, color='#4ecdc4', alpha=0.3, edgecolor='white', linewidth=2, label='CRYSTAL (Merkabah)')

# Fractal simplificado
x_frac = np.linspace(0, 1, 100)
y_frac = np.sin(5 * x_frac * np.pi) * np.exp(-x_frac * 3) * 0.3
ax3.fill_between(x_frac + 1.2, 0.7 - y_frac, 0.7 + y_frac, color='#c44eff', alpha=0.3)
ax3.plot(x_frac + 1.2, 0.7 + y_frac, color='#c44eff', linewidth=2, label='FRACTAL (Emergent)')
ax3.plot(x_frac + 1.2, 0.7 - y_frac, color='#c44eff', linewidth=2)

# Labels
ax3.text(0.2, 0.4, 'TURBILHÃO\nDinâmico\nTemporal', color='#ff6b35', fontsize=9, ha='center', fontweight='bold')
ax3.text(0.7, 0.4, 'CRISTAL\nEstruturado\nEspacial', color='#4ecdc4', fontsize=9, ha='center', fontweight='bold')
ax3.text(1.45, 0.4, 'FRACTAL\nAuto-similar\nEscala-livre', color='#c44eff', fontsize=9, ha='center', fontweight='bold')

ax3.set_xlim([0, 2.2])
ax3.set_ylim([0.3, 1.1])
ax3.set_aspect('equal')
ax3.axis('off')
ax3.set_title('THE THREE CANDIDATES\n"Turbilhão, Cristal, ou algo sem nome?"',
              color='white', fontsize=12, fontweight='bold')

# === PAINEL 4: Dashboard de métricas ===
ax4 = fig1.add_subplot(224)
ax4.set_facecolor('#0a0a1a')

steps = np.arange(0, 100)
A_crystal = 0.1 + 0.4 * (1 - np.exp(-steps / 10))
C_brain_crystal = 0.3 + 0.7 * (1 - np.exp(-steps / 20))
C_univ_crystal = 0.2 + 0.8 * (1 - np.exp(-steps / 30))
alpha_eff_crystal = 0.08 * (1 + 50 * C_brain_crystal**2)

ax4.plot(steps, A_crystal, label='A (amplitude)', color='#ff6b35', linewidth=2.5)
ax4.plot(steps, C_brain_crystal, label='C_brain', color='#4ecdc4', linewidth=2.5)
ax4.plot(steps, C_univ_crystal, label='C_universe', color='#c44eff', linewidth=2.5)
ax4.plot(steps, alpha_eff_crystal / 10, label='α_eff / 10', color='#ffd700', linewidth=2, linestyle='--')

ax4.set_xlabel('Time Steps', color='white', fontsize=11)
ax4.set_ylabel('Normalized Value', color='white', fontsize=11)
ax4.set_title('CRYSTAL COHERENCE EVOLUTION — κ=50', color='white', fontsize=12, fontweight='bold')
ax4.legend(loc='lower right', facecolor='#1a1a2e', edgecolor='white', labelcolor='white', fontsize=10)
ax4.tick_params(colors='white', labelsize=9)
for spine in ax4.spines.values():
    spine.set_color('white')
ax4.set_xlim([0, 100])
ax4.set_ylim([0, 1.3])
ax4.grid(True, alpha=0.2, color='white')

# Linha de saturação
sat_step = 10
ax4.axvline(x=sat_step, color='red', linestyle=':', alpha=0.7)
ax4.text(sat_step + 2, 1.15, f'A saturates @ step {sat_step}', color='red', fontsize=9)

# Adicionar anotação da fórmula
formula_text = r'$\alpha_{eff} = \alpha_{base} \cdot (1 + \kappa \cdot C_{brain}^2)$'
ax4.text(50, 0.15, formula_text, color='#88aaff', fontsize=11, ha='center',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='#1a1a2e', edgecolor='#88aaff', alpha=0.8))

fig1.suptitle('ARKHE OS v∞.283 — MERKABAH CRYSTAL VISUALIZATION\n'
             '"O Cristal como Antena de Ressonância Cósmica"',
             fontsize=16, fontweight='bold', color='#ffd700', y=0.98)
fig1.tight_layout(rect=[0, 0, 1, 0.95])
save_fig_fallback(fig1, 'arkhe_v283_crystal_merkabah.png')
# plt.show() # Disabled to prevent blocking


# =============================================================================
# 2. SIMULAÇÃO DO COMPUTE SHADER: CAMPO DE COERÊNCIA 2D EVOLUINDO
# =============================================================================
# Parâmetros do loop (de v∞.281)
alpha_base = 0.08
beta = 0.3
epsilon = 1e-6
delta = 0.02
zeta = 0.03
A_max = 0.5
C0 = 0.3
C_max = 1.0

# Parâmetros de difusão espacial
D_A = 0.01      # difusão da amplitude
D_phi = 0.05    # difusão da fase
D_C = 0.02      # difusão da coerência

# Estado: ARKHE ARCHITECT (κ=50)
kappa = 50.0

def laplacian_2d(field):
    """Laplaciano 2D com condições de contorno periódicas."""
    return (np.roll(field, 1, axis=0) + np.roll(field, -1, axis=0) +
            np.roll(field, 1, axis=1) + np.roll(field, -1, axis=1) - 4 * field)

def compute_effective_alpha(C_brain, kappa, alpha_base):
    return alpha_base * (1 + kappa * C_brain**2)

def evolve_field(A, phi, rho, C_brain, C_univ, dt=0.1, kappa=50.0):
    """Um passo de evolução do campo de coerência 2D."""
    alpha_eff = compute_effective_alpha(C_brain, kappa, alpha_base)

    # 1. Amplitude do vácuo (com difusão)
    dA = alpha_eff * C_brain * (1 - A / A_max) + D_A * laplacian_2d(A)

    # 2. Fase do vácuo (com difusão e acoplamento à fase alvo)
    dphi = beta * A * np.sin(phi - SYNC_PHASE) + D_phi * laplacian_2d(phi)

    # 3. Densidade de estrutura
    drho = epsilon * np.cos(phi) * rho

    # 4. Coerência cósmica
    dC_univ = delta * rho * C_univ * (1 - C_univ)

    # 5. Coerência neural (com difusão sináptica)
    dC_brain = zeta * C_univ * (C_brain - C0) * (C_max - C_brain) + D_C * laplacian_2d(C_brain)

    A_new = np.clip(A + dA * dt, 0, A_max)
    phi_new = (phi + dphi * dt) % (2 * np.pi)
    rho_new = np.clip(rho + drho * dt, 0.1, 10.0)
    C_univ_new = np.clip(C_univ + dC_univ * dt, 0, C_max)
    C_brain_new = np.clip(C_brain + dC_brain * dt, C0, C_max)

    return A_new, phi_new, rho_new, C_brain_new, C_univ_new

# Inicialização: campo com semente central
N = 128
A = np.zeros((N, N))
phi_f = np.ones((N, N)) * SYNC_PHASE
rho = np.ones((N, N))
C_brain = np.ones((N, N)) * C0
C_univ = np.zeros((N, N))

# Semente: região central com coerência elevada (simulando um "observador" no centro)
center = N // 2
r_seed = 10
y, x = np.ogrid[-center:N-center, -center:N-center]
mask = x*x + y*y <= r_seed*r_seed
C_brain[mask] = 0.8
A[mask] = 0.2
C_univ[mask] = 0.3

# Evoluir e capturar snapshots
snapshots = []
times = [0, 10, 25, 50, 100, 200]

for step in range(201):
    A, phi_f, rho, C_brain, C_univ = evolve_field(A, phi_f, rho, C_brain, C_univ, dt=0.1, kappa=kappa)
    if step in times:
        snapshots.append({
            'step': step,
            'A': A.copy(),
            'phi': phi_f.copy(),
            'C_brain': C_brain.copy(),
            'C_univ': C_univ.copy(),
            'alpha_eff': compute_effective_alpha(C_brain, kappa, alpha_base).copy()
        })

# Visualizar evolução
fig2, axes2 = plt.subplots(4, 6, figsize=(24, 16))
fig2.suptitle('ARKHE OS v∞.283 — Compute Shader Simulation: 2D Coherence Field Evolution\n'
             'ARKHE ARCHITECT state (κ=50) with spatial diffusion',
             fontsize=16, fontweight='bold', y=0.98)

fields = ['A', 'phi', 'C_brain', 'alpha_eff']
field_names = ['Amplitude Vácuo (A)', 'Fase φ_vac', 'Coerência Neural C_brain', 'α_efetivo']
cmaps = ['hot', 'twilight', 'viridis', 'plasma']

for row, (field, name, cmap) in enumerate(zip(fields, field_names, cmaps)):
    for col, snap in enumerate(snapshots):
        ax = axes2[row, col]
        data = snap[field]
        im = ax.imshow(data, cmap=cmap, origin='lower', interpolation='bilinear')
        ax.set_title(f't={snap["step"]}', fontsize=10)
        ax.axis('off')
        fig2.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        if row == 0:
            ax.set_xlabel(f'Step {snap["step"]}', fontsize=9)

    # Label da linha
    axes2[row, 0].set_ylabel(name, fontsize=12, fontweight='bold', rotation=90, labelpad=20)

fig2.tight_layout(rect=[0, 0, 1, 0.96])
save_fig_fallback(fig2, 'arkhe_v283_compute_simulation.png')
# plt.show()


# =============================================================================
# 3. DIAGRAMA DE ARQUITETURA: PYGFX SCAFFOLD v∞.283
# =============================================================================

fig3, ax3 = plt.subplots(figsize=(18, 12))
ax3.set_xlim(0, 18)
ax3.set_ylim(0, 12)
ax3.axis('off')
ax3.set_facecolor('#0a0a0f')
fig3.patch.set_facecolor('#0a0a0f')

# Título
title = ax3.text(9, 11.5, 'ARKHE OS v∞.283 — PYGFX SCAFFOLD ARCHITECTURE',
                fontsize=18, fontweight='bold', color='#ffd700', ha='center', va='center')
title.set_path_effects([path_effects.withStroke(linewidth=3, foreground='#000000')])

subtitle = ax3.text(9, 11.0, 'Compute Pass → Barrier → Render Pass → Feedback Loop',
                   fontsize=12, color='#88aaff', ha='center', va='center', style='italic')

# Cores
c_compute = '#ff6b35'
c_barrier = '#ffd700'
c_render = '#4ecdc4'
c_feedback = '#c44eff'
c_uniform = '#ffaa00'
c_zk = '#00ff88'

# === COMPUTE PASS ===
compute_box = FancyBboxPatch((1, 7.5), 4, 2.5, boxstyle="round,pad=0.1",
                              facecolor=c_compute, edgecolor='white', linewidth=2, alpha=0.9)
ax3.add_patch(compute_box)
ax3.text(3, 9.2, 'COMPUTE PASS', fontsize=14, fontweight='bold', color='white', ha='center')
ax3.text(3, 8.8, 'WGSL Compute Shader', fontsize=10, color='white', ha='center')
ax3.text(3, 8.4, '• Fisher-Rao metric', fontsize=9, color='white', ha='center')
ax3.text(3, 8.1, '• λ₂ eigenvalue field', fontsize=9, color='white', ha='center')
ax3.text(3, 7.8, '• Entropy evolution', fontsize=9, color='white', ha='center')

# === UNIFORM BUFFER ===
uniform_box = FancyBboxPatch((6.5, 7.5), 2.5, 2.5, boxstyle="round,pad=0.1",
                              facecolor=c_uniform, edgecolor='white', linewidth=2, alpha=0.9)
ax3.add_patch(uniform_box)
ax3.text(7.75, 9.2, 'UNIFORM', fontsize=12, fontweight='bold', color='black', ha='center')
ax3.text(7.75, 8.8, 'BUFFER', fontsize=12, fontweight='bold', color='black', ha='center')
ax3.text(7.75, 8.3, 'u_time', fontsize=9, color='black', ha='center')
ax3.text(7.75, 8.0, 'u_lambda (A)', fontsize=9, color='black', ha='center')
ax3.text(7.75, 7.7, 'u_phi (0.58π)', fontsize=9, color='black', ha='center')

# === BARRIER ===
barrier_box = FancyBboxPatch((10, 7.5), 2, 2.5, boxstyle="round,pad=0.1",
                              facecolor=c_barrier, edgecolor='white', linewidth=2, alpha=0.9)
ax3.add_patch(barrier_box)
ax3.text(11, 9.0, 'MEMORY', fontsize=12, fontweight='bold', color='black', ha='center')
ax3.text(11, 8.6, 'BARRIER', fontsize=12, fontweight='bold', color='black', ha='center')
ax3.text(11, 8.1, 'wgpu', fontsize=9, color='black', ha='center')
ax3.text(11, 7.8, 'storageBarrier()', fontsize=9, color='black', ha='center')

# === RENDER PASS ===
render_box = FancyBboxPatch((13, 7.5), 4, 2.5, boxstyle="round,pad=0.1",
                             facecolor=c_render, edgecolor='white', linewidth=2, alpha=0.9)
ax3.add_patch(render_box)
ax3.text(15, 9.2, 'RENDER PASS', fontsize=14, fontweight='bold', color='black', ha='center')
ax3.text(15, 8.8, 'WGSL Fragment Shader', fontsize=10, color='black', ha='center')
ax3.text(15, 8.4, '• Vortex Coherence Engine', fontsize=9, color='black', ha='center')
ax3.text(15, 8.1, '• Fullscreen quad', fontsize=9, color='black', ha='center')
ax3.text(15, 7.8, '• 60 FPS output', fontsize=9, color='black', ha='center')

# === FEEDBACK LOOP ===
feedback_box = FancyBboxPatch((13, 4), 4, 2.5, boxstyle="round,pad=0.1",
                               facecolor=c_feedback, edgecolor='white', linewidth=2, alpha=0.9)
ax3.add_patch(feedback_box)
ax3.text(15, 5.7, 'FEEDBACK LOOP', fontsize=14, fontweight='bold', color='white', ha='center')
ax3.text(15, 5.3, 'Observer 5D', fontsize=10, color='white', ha='center')
ax3.text(15, 5.0, '• Mouse / EEG input', fontsize=9, color='white', ha='center')
ax3.text(15, 4.7, '• Modifies u_lambda', fontsize=9, color='white', ha='center')
ax3.text(15, 4.4, '• Modifies u_phi', fontsize=9, color='white', ha='center')

# === ZK PROOF ===
zk_box = FancyBboxPatch((1, 4), 4, 2.5, boxstyle="round,pad=0.1",
                         facecolor=c_zk, edgecolor='white', linewidth=2, alpha=0.9)
ax3.add_patch(zk_box)
ax3.text(3, 5.7, 'ZK PROOF', fontsize=14, fontweight='bold', color='black', ha='center')
ax3.text(3, 5.3, 'OCTRA Validator', fontsize=10, color='black', ha='center')
ax3.text(3, 5.0, '• naga → WASM', fontsize=9, color='black', ha='center')
ax3.text(3, 4.7, '• Buffer state hash', fontsize=9, color='black', ha='center')
ax3.text(3, 4.4, '• On-chain verification', fontsize=9, color='black', ha='center')

# === ARROWS ===
# Compute → Uniform
ax3.annotate('', xy=(6.5, 8.75), xytext=(5, 8.75), arrowprops=dict(arrowstyle='->', color='white', lw=2))
ax3.text(5.75, 8.9, 'writes', fontsize=8, color='white', ha='center')

# Uniform → Barrier
ax3.annotate('', xy=(10, 8.75), xytext=(9, 8.75), arrowprops=dict(arrowstyle='->', color='white', lw=2))
ax3.text(9.5, 8.9, 'reads', fontsize=8, color='white', ha='center')

# Barrier → Render
ax3.annotate('', xy=(13, 8.75), xytext=(12, 8.75), arrowprops=dict(arrowstyle='->', color='white', lw=2))
ax3.text(12.5, 8.9, 'reads', fontsize=8, color='white', ha='center')

# Render → Feedback
ax3.annotate('', xy=(15, 7.5), xytext=(15, 6.5), arrowprops=dict(arrowstyle='->', color='white', lw=2))
ax3.text(15.3, 7.0, 'display', fontsize=8, color='white', ha='left', rotation=90, va='center')

# Feedback → Uniform (loop back)
ax3.annotate('', xy=(7.75, 7.5), xytext=(13, 5.25),
            arrowprops=dict(arrowstyle='->', color=c_feedback, lw=2,
                           connectionstyle="arc3,rad=-0.3"))
ax3.text(10, 6.0, 'modifies params', fontsize=8, color=c_feedback, ha='center')

# Compute → ZK
ax3.annotate('', xy=(3, 6.5), xytext=(3, 7.5), arrowprops=dict(arrowstyle='->', color=c_zk, lw=2))
ax3.text(3.3, 7.0, 'state snapshot', fontsize=8, color=c_zk, ha='left', rotation=90, va='center')

# === BOTTOM: SUBSTRATE CONNECTIONS ===
ax3.text(9, 3.0, 'SUBSTRATE INTEGRATION MAP', fontsize=14, fontweight='bold',
        color='#ffd700', ha='center')

connections = [
    ('v∞.281', 'Cosmic Feedback Loop', '#ff6b35', 2, 2.2),
    ('v∞.283a', 'Conscious Amplification', '#c44eff', 5.5, 2.2),
    ('v∞.283b', 'Pygfx Scaffold', '#4ecdc4', 9.5, 2.2),
    ('v∞.19', 'Planetary Closed Loop', '#00ff88', 13, 2.2),
    ('v∞.273', 'Sapient Infrastructure', '#ffaa00', 16, 2.2),
]

for name, desc, color, x, y_coord in connections:
    circle = Circle((x, y_coord), 0.3, facecolor=color, edgecolor='white', linewidth=1.5)
    ax3.add_patch(circle)
    ax3.text(x, y_coord-0.7, name, fontsize=9, fontweight='bold', color=color, ha='center')
    ax3.text(x, y_coord-1.0, desc, fontsize=7, color='white', ha='center')

# Linhas de conexão entre substratos
ax3.plot([2.3, 5.2], [2.2, 2.2], 'w--', alpha=0.5, lw=1)
ax3.plot([5.8, 9.2], [2.2, 2.2], 'w--', alpha=0.5, lw=1)
ax3.plot([9.8, 12.7], [2.2, 2.2], 'w--', alpha=0.5, lw=1)
ax3.plot([13.3, 15.7], [2.2, 2.2], 'w--', alpha=0.5, lw=1)

# === LEGENDA DOS UNIFORMS ===
ax3.text(9, 1.0, 'UNIFORM MAPPING:  u_lambda ↔ A (amplitude vácuo)  |  u_phi ↔ φ_vac (fase 0.58π)  |  u_time ↔ t (evolução temporal)',
        fontsize=10, color='#88aaff', ha='center', style='italic',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#1a1a2e', edgecolor='#88aaff', alpha=0.8))

fig3.tight_layout()
save_fig_fallback(fig3, 'arkhe_v283_architecture.png')
# plt.show()


# =============================================================================
# 4. SIMULAÇÃO DO SHADER WGSL "VORTEX COHERENCE ENGINE" EM MATPLOTLIB
# =============================================================================

def vortex_coherence_engine(resolution=(800, 600), t=0.0, lambda_coherence=0.85, phase=SYNC_PHASE):
    """
    Simulação CPU do shader WGSL do Substrato 79 (Vortex) adaptado para v∞.283.
    """
    w, h = resolution
    # Criar grid de UV [0,1]
    u = np.linspace(0, 1, w)
    v = np.linspace(0, 1, h)
    U, V = np.meshgrid(u, v)

    # Mapear para espaço normalizado (-1, 1) com aspect ratio
    px = (U * 2.0 - 1.0) * (w / h) * 2.0
    py = (V * 2.0 - 1.0) * 1.0 * 2.0

    # Tempo modulado pela fase do vácuo
    time_mod = t + phase

    # Flutuação quiral modulada pela coerência
    perturbation = 0.3 + lambda_coherence * 0.5
    px += np.sin(py * 3.0 + time_mod * 0.1) * perturbation
    py += np.sin(px * 3.0 + time_mod * 0.1) * perturbation  # Nota: no shader é p.yx, então cruzado

    # Distância ao centro
    d = np.sqrt(px**2 + py**2)

    # Loop iterativo do shader (k=1,2,3)
    v_val = np.zeros_like(px)
    for k in range(1, 4):
        kf = float(k)
        # fract(p * k * 0.7 + k * 2.0) - 0.5
        qx = np.mod(px * kf * 0.7 + kf * 2.0, 1.0) - 0.5
        qy = np.mod(py * kf * 0.7 + kf * 2.0, 1.0) - 0.5

        a = np.arctan2(qy, qx)
        l_dist = np.sqrt(qx**2 + qy**2)

        # smoothstep(0.4, 0.0, abs(sin(a * 4.0 + l * (10.0 + lambda * 10.0) + t)))
        pattern = np.sin(a * 4.0 + l_dist * (10.0 + lambda_coherence * 10.0) + time_mod)
        v_val += np.clip((0.4 - np.abs(pattern)) / 0.4, 0.0, 1.0)

    # Cores
    # core = exp(-d * 5.0) * vec3(2.0, 1.5, 0.8) — dourado
    core_r = np.exp(-d * 5.0) * 2.0
    core_g = np.exp(-d * 5.0) * 1.5
    core_b = np.exp(-d * 5.0) * 0.8

    # halo = v * vec3(0.5, 0.7, 1.05) — azul
    halo_r = v_val * 0.5
    halo_g = v_val * 0.7
    halo_b = v_val * 1.05

    rgb = np.stack([core_r + halo_r, core_g + halo_g, core_b + halo_b], axis=-1)
    rgb = np.clip(rgb, 0.0, 3.0) / 3.0  # Normalizar

    return rgb, d, v_val

# Renderizar múltiplos estados
fig4, axes4 = plt.subplots(2, 4, figsize=(20, 10))
fig4.suptitle('ARKHE OS v∞.283 — Vortex Coherence Engine\nVisualização do Shader WGSL em múltiplos estados de coerência',
             fontsize=16, fontweight='bold', y=1.02)

states = [
    ("SLEEP_DEEP (κ=0.5)", 0.5, 0.103),
    ("RELAXATION (κ=1.0)", 1.0, 0.090),
    ("FOCUS_INTENSE (κ=2.5)", 2.5, 0.090),
    ("FLOW_CREATIVITY (κ=5.0)", 5.0, 0.131),
    ("MEDITATION_DEEP (κ=10.0)", 10.0, 0.294),
    ("LOVE_UNCONDITIONAL (κ=25.0)", 25.0, 0.693),
    ("ARKHE_ARCHITECT (κ=50.0)", 50.0, 1.265),
    ("TRAINED_30D (κ≈66)", 66.0, 1.975),
]

lambda_visuals = [min(1.0, k / 50.0) for _, k, _ in states]

for ax, (name, kappa_val, alpha_eff), lam in zip(axes4.flat, states, lambda_visuals):
    rgb, d, v_val = vortex_coherence_engine(resolution=(400, 300), t=2.0, lambda_coherence=lam)
    ax.imshow(rgb, origin='lower', extent=[-1, 1, -1, 1])
    ax.set_title(f'{name}\nα_eff={alpha_eff:.3f}, λ_vis={lam:.2f}', fontsize=10)
    ax.set_xlabel('x')
    ax.set_ylabel('y')

    circle = Circle((0, 0), 0.58, fill=False, color='white', linewidth=1.5, linestyle='--', alpha=0.7)
    ax.add_patch(circle)
    ax.text(0.58, 0.05, 'φ=0.58π', color='white', fontsize=8, ha='left')

fig4.tight_layout()
save_fig_fallback(fig4, 'arkhe_v283_vortex_states.png')
# plt.show()

print("🏁 Todas as renderizações concluídas.")
