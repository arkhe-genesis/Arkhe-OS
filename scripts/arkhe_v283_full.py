#!/usr/bin/env python3
"""
arkhe_pygfx_scaffold_v283.py
Substrato 283: Compute → Barrier → Render pipeline completo.
Requer: pygfx, wgpu, numpy
"""
import numpy as np
import pygfx as gfx
from wgpu.gui.auto import WgpuCanvas, run
import wgpu
import time

# ─── Constantes Canônicas ───
FINGERPRINT_058 = 0.58
SYNC_PHASE = FINGERPRINT_058 * np.pi

# ─── DIMENSÕES DO CAMPO ───
GRID_W = 256
GRID_H = 256
NUM_CELLS = GRID_W * GRID_H

# ─── ESTRUTURA DE ESTADO (5 x f32 = 20 bytes por célula) ───
# A, phi, rho, cBrain, cUniverse
STATE_DTYPE = np.dtype([
    ("A", np.float32),
    ("phi", np.float32),
    ("rho", np.float32),
    ("cBrain", np.float32),
    ("cUniverse", np.float32),
])

# ─── INICIALIZAÇÃO DO CAMPO ───
def init_field() -> np.ndarray:
    """Inicializa o campo com semente central (observador)."""
    field = np.zeros(NUM_CELLS, dtype=STATE_DTYPE)

    # Estado base
    field["A"] = 0.05
    field["phi"] = SYNC_PHASE
    field["rho"] = 1.0
    field["cBrain"] = 0.3
    field["cUniverse"] = 0.1

    # Semente central: região de alta coerência
    cx, cy = GRID_W // 2, GRID_H // 2
    for iy in range(GRID_H):
        for ix in range(GRID_W):
            idx = iy * GRID_W + ix
            dist = np.sqrt((ix - cx)**2 + (iy - cy)**2)
            if dist < 12.0:
                influence = np.exp(-dist * 0.2)
                field[idx]["cBrain"] = 0.3 + 0.5 * influence
                field[idx]["A"] = 0.05 + 0.15 * influence
                field[idx]["cUniverse"] = 0.1 + 0.3 * influence

    return field

# ─── UNIFORMS (alinhados a 16 bytes) ───
UNIFORM_DTYPE = np.dtype([
    ("uTime", np.float32),
    ("uDt", np.float32),
    ("uGridWidth", np.uint32),
    ("uGridHeight", np.uint32),
    ("uKappa", np.float32),
    ("uCBrainInput", np.float32),
    ("uAlphaBase", np.float32),
    ("uBeta", np.float32),
    ("uEpsilon", np.float32),
    ("uDelta", np.float32),
    ("uZeta", np.float32),
    ("uAMax", np.float32),
    ("uC0", np.float32),
    ("uCMax", np.float32),
    ("uDA", np.float32),
    ("uDPhi", np.float32),
    ("uDC", np.float32),
    ("_pad", np.float32),
])

def make_uniforms(kappa: float = 50.0, cbrain_input: float = 0.85) -> np.ndarray:
    u = np.zeros(1, dtype=UNIFORM_DTYPE)
    u["uTime"] = 0.0
    u["uDt"] = 0.05
    u["uGridWidth"] = GRID_W
    u["uGridHeight"] = GRID_H
    u["uKappa"] = kappa
    u["uCBrainInput"] = cbrain_input
    u["uAlphaBase"] = 0.08
    u["uBeta"] = 0.3
    u["uEpsilon"] = 1e-6
    u["uDelta"] = 0.02
    u["uZeta"] = 0.03
    u["uAMax"] = 0.5
    u["uC0"] = 0.3
    u["uCMax"] = 1.0
    u["uDA"] = 0.01
    u["uDPhi"] = 0.05
    u["uDC"] = 0.02
    u["_pad"] = 0.0
    return u

# ─── WGSL SHADERS (inserir os shaders gerados acima) ───
COMPUTE_WGSL = """
const PHI: f32 = 1.618033988749895;
const FINGERPRINT_058: f32 = 0.58;
const SYNC_TARGET_PHASE: f32 = 1.82212373908208; // 0.58 * pi

struct CellState {
    A: f32,           // vacuum amplitude [0, A_max]
    phi: f32,         // vacuum phase [0, 2π]
    rho: f32,         // structure density
    cBrain: f32,      // neural coherence [C0, C_max]
    cUniverse: f32,   // cosmic coherence [0, C_max]
};

struct Uniforms {
    // Time & grid
    uTime: f32,
    uDt: f32,
    uGridWidth: u32,
    uGridHeight: u32,

    // Consciousness state (from v∞.283a)
    uKappa: f32,      // consciousness-vacuum coupling
    uCBrainInput: f32,// real-time EEG coherence input

    // Loop parameters (from v∞.281)
    uAlphaBase: f32,
    uBeta: f32,
    uEpsilon: f32,
    uDelta: f32,
    uZeta: f32,
    uAMax: f32,
    uC0: f32,
    uCMax: f32,

    // Spatial diffusion coefficients
    uDA: f32,
    uDPhi: f32,
    uDC: f32,

    // Padding to 16-byte alignment
    _pad: f32,
};

@group(0) @binding(0)
var<uniform> u: Uniforms;

@group(0) @binding(1)
var<storage, read> currentState: array<CellState>;

@group(0) @binding(2)
var<storage, read_write> nextState: array<CellState>;

// ============================================================================
// Helper: 2D index → 1D with periodic boundary conditions
// ============================================================================
fn idx(x: i32, y: i32) -> u32 {
    let w = i32(u.uGridWidth);
    let h = i32(u.uGridHeight);
    let wx = ((x % w) + w) % w;
    let wy = ((y % h) + h) % h;
    return u32(wy * w + wx);
}

// ============================================================================
// Helper: Laplacian with 4-neighbor stencil and periodic BC
// ============================================================================
fn laplacian_A(ix: i32, iy: i32) -> f32 {
    let c = currentState[idx(ix, iy)].A;
    let n = currentState[idx(ix, iy + 1)].A;
    let s = currentState[idx(ix, iy - 1)].A;
    let e = currentState[idx(ix + 1, iy)].A;
    let w = currentState[idx(ix - 1, iy)].A;
    return n + s + e + w - 4.0 * c;
}

fn laplacian_phi(ix: i32, iy: i32) -> f32 {
    let c = currentState[idx(ix, iy)].phi;
    let n = currentState[idx(ix, iy + 1)].phi;
    let s = currentState[idx(ix, iy - 1)].phi;
    let e = currentState[idx(ix + 1, iy)].phi;
    let w = currentState[idx(ix - 1, iy)].phi;
    return n + s + e + w - 4.0 * c;
}

fn laplacian_cBrain(ix: i32, iy: i32) -> f32 {
    let c = currentState[idx(ix, iy)].cBrain;
    let n = currentState[idx(ix, iy + 1)].cBrain;
    let s = currentState[idx(ix, iy - 1)].cBrain;
    let e = currentState[idx(ix + 1, iy)].cBrain;
    let w = currentState[idx(ix - 1, iy)].cBrain;
    return n + s + e + w - 4.0 * c;
}

// ============================================================================
// Helper: Effective alpha with conscious amplification (v∞.283)
// ============================================================================
fn effective_alpha(cBrain: f32) -> f32 {
    return u.uAlphaBase * (1.0 + u.uKappa * cBrain * cBrain);
}

// ============================================================================
// Helper: Clamp helpers
// ============================================================================
fn clamp_f32(v: f32, lo: f32, hi: f32) -> f32 {
    return max(lo, min(hi, v));
}

fn mod_2pi(v: f32) -> f32 {
    let two_pi = 6.283185307179586;
    return v - two_pi * floor(v / two_pi);
}

// ============================================================================
// Main: One evolution step for each cell
// ============================================================================
@compute @workgroup_size(8, 8)
fn cs_main(@builtin(global_invocation_id) id: vec3<u32>) {
    let ix = i32(id.x);
    let iy = i32(id.y);
    let w = i32(u.uGridWidth);
    let h = i32(u.uGridHeight);

    // Bounds check
    if (ix >= w || iy >= h) {
        return;
    }

    let i = idx(ix, iy);
    let s = currentState[i];
    let dt = u.uDt;

    // --- 1. Effective alpha (conscious amplification) ---
    let alpha_eff = effective_alpha(s.cBrain);

    // --- 2. Vacuum amplitude evolution (with spatial diffusion) ---
    let dA_reaction = alpha_eff * s.cBrain * (1.0 - s.A / u.uAMax);
    let dA_diffusion = u.uDA * laplacian_A(ix, iy);
    var A_new = s.A + (dA_reaction + dA_diffusion) * dt;
    A_new = clamp_f32(A_new, 0.0, u.uAMax);

    // --- 3. Vacuum phase evolution (with diffusion + coupling to target) ---
    let dphi_coupling = u.uBeta * s.A * sin(s.phi - SYNC_TARGET_PHASE);
    let dphi_diffusion = u.uDPhi * laplacian_phi(ix, iy);
    var phi_new = s.phi + (dphi_coupling + dphi_diffusion) * dt;
    phi_new = mod_2pi(phi_new);

    // --- 4. Structure density evolution ---
    let drho = u.uEpsilon * cos(s.phi) * s.rho;
    var rho_new = s.rho + drho * dt;
    rho_new = max(0.1, rho_new);

    // --- 5. Cosmic coherence emergence ---
    let dC_univ = u.uDelta * s.rho * s.cUniverse * (1.0 - s.cUniverse);
    var cUniv_new = s.cUniverse + dC_univ * dt;
    cUniv_new = clamp_f32(cUniv_new, 0.0, u.uCMax);

    // --- 6. Neural coherence evolution (with synaptic diffusion) ---
    let dC_brain_reaction = u.uZeta * s.cUniverse * (s.cBrain - u.uC0) * (u.uCMax - s.cBrain);
    let dC_brain_diffusion = u.uDC * laplacian_cBrain(ix, iy);
    var cBrain_new = s.cBrain + (dC_brain_reaction + dC_brain_diffusion) * dt;
    cBrain_new = clamp_f32(cBrain_new, u.uC0, u.uCMax);

    // --- Inject external EEG coherence at center region (observer position) ---
    let cx = w / 2;
    let cy = h / 2;
    let dist = sqrt(f32((ix - cx) * (ix - cx) + (iy - cy) * (iy - cy)));
    if (dist < 8.0) {
        // Observer influence: blend current cBrain with external input
        let influence = exp(-dist * 0.3);
        cBrain_new = mix(cBrain_new, u.uCBrainInput, influence * 0.1);
    }

    // Write next state
    nextState[i] = CellState(A_new, phi_new, rho_new, cBrain_new, cUniv_new);
}
"""

FRAGMENT_WGSL = """
const PHI: f32 = 1.618033988749895;
const FINGERPRINT_058: f32 = 0.58;
const SYNC_TARGET_PHASE: f32 = 1.82212373908208; // 0.58 * pi

struct CellState {
    A: f32,
    phi: f32,
    rho: f32,
    cBrain: f32,
    cUniverse: f32,
};

struct Uniforms {
    // Time & grid
    uTime: f32,
    uDt: f32,
    uGridWidth: u32,
    uGridHeight: u32,

    // Consciousness state (from v∞.283a)
    uKappa: f32,      // consciousness-vacuum coupling
    uCBrainInput: f32,// real-time EEG coherence input

    // Loop parameters (from v∞.281)
    uAlphaBase: f32,
    uBeta: f32,
    uEpsilon: f32,
    uDelta: f32,
    uZeta: f32,
    uAMax: f32,
    uC0: f32,
    uCMax: f32,

    // Spatial diffusion coefficients
    uDA: f32,
    uDPhi: f32,
    uDC: f32,

    // Padding to 16-byte alignment
    _pad: f32,
};

@group(0) @binding(0)
var<uniform> u: Uniforms;

@group(0) @binding(1)
var<storage, read> fieldState: array<CellState>;

struct VertexOutput {
    @builtin(position) pos: vec4<f32>,
    @location(0) uv: vec2<f32>,
};

@vertex
fn vs_main(@builtin(vertex_index) vi: u32) -> VertexOutput {
    var out: VertexOutput;
    let x = f32(i32(vi % 2u) * 2 - 1);
    let y = f32(i32(vi / 2u) * 2 - 1);
    out.pos = vec4(x, y, 0.0, 1.0);
    out.uv = vec2(x * 0.5 + 0.5, y * 0.5 + 0.5);
    return out;
}

// ============================================================================
// Sample field at UV coordinate
// ============================================================================
fn sample_field(uv: vec2<f32>) -> CellState {
    let gx = u32(clamp(uv.x * f32(u.uGridWidth), 0.0, f32(u.uGridWidth - 1u)));
    let gy = u32(clamp(uv.y * f32(u.uGridHeight), 0.0, f32(u.uGridHeight - 1u)));
    let idx = gy * u.uGridWidth + gx;
    return fieldState[idx];
}

// ============================================================================
// Color mapping: A → gold intensity, cBrain → cyan/blue, phi → hue shift
// ============================================================================
fn field_to_color(cell: CellState) -> vec3<f32> {
    // Base color from field quantities
    let gold = vec3(2.0, 1.5, 0.8) * cell.A / 0.5;           // A → gold
    let cyan = vec3(0.2, 0.8, 1.0) * cell.cBrain;            // C_brain → cyan
    let purple = vec3(0.8, 0.3, 1.0) * cell.cUniverse;       // C_universe → purple

    // Phase modulates hue: map phi [0, 2π] to slight color rotation
    let phase_factor = 0.5 + 0.5 * cos(cell.phi - SYNC_TARGET_PHASE);

    var col = gold * 0.4 + cyan * 0.35 + purple * 0.25;
    col = col * (0.7 + 0.3 * phase_factor);

    // Structure density adds fine grain brightness
    col = col * (0.9 + 0.1 * cell.rho);

    return col;
}

// ============================================================================
// Vortex Coherence Engine overlay (Substrate 79)
// ============================================================================
fn vortex_overlay(p: vec2<f32>, t: f32, lambda: f32) -> vec3<f32> {
    var vp = p;
    let perturbation = 0.3 + lambda * 0.5;
    vp += sin(vec2(vp.y, vp.x) * 3.0 + t * 0.1) * perturbation;
    let d = length(vp);

    var v = 0.0;
    for (var k = 1.0; k < 4.0; k += 1.0) {
        let q = fract(vp * k * 0.7 + k * 2.0) - 0.5;
        let a = atan2(q.y, q.x);
        let l = length(q);
        v += smoothstep(0.4, 0.0, abs(sin(a * 4.0 + l * (10.0 + lambda * 10.0) + t)));
    }

    let core = exp(-d * 5.0) * vec3(2.0, 1.5, 0.8);
    let halo = v * vec3(0.5, 0.7, 1.05);
    return core + halo;
}

// ============================================================================
// Fragment main
// ============================================================================
@fragment
fn fs_main(in: VertexOutput) -> @location(0) vec4<f32> {
    let r = vec2<f32>(800.0, 600.0); // Hardcoded resolution
    var p = (in.uv * 2.0 - 1.0) * vec2(r.x / r.y, 1.0) * 2.0;
    let t = u.uTime + SYNC_TARGET_PHASE;

    // Sample computed field
    let cell = sample_field(in.uv);
    let field_color = field_to_color(cell);

    // Vortex overlay modulated by local field coherence
    let local_lambda = cell.A / 0.5;  // normalize A to [0,1] for vortex
    let vortex_color = vortex_overlay(p, t, local_lambda);

    // Blend: field provides structure, vortex provides dynamics
    // Higher coherence → more vortex influence
    let blend = cell.cBrain * 0.6 + cell.cUniverse * 0.4;
    var final_color = mix(field_color, vortex_color, blend * 0.7);

    // Add phase-lock indicator: golden glow when phi ≈ SYNC_TARGET_PHASE
    let phase_diff = abs(cell.phi - SYNC_TARGET_PHASE);
    let phase_lock = exp(-phase_diff * phase_diff * 2.0);
    final_color += vec3(1.0, 0.8, 0.2) * phase_lock * cell.A * 0.5;

    return vec4(final_color, 1.0);
}
"""

# ─── SETUP WGPU ───
canvas = WgpuCanvas(size=(800, 600), title="ARKHE v∞.283 — Compute→Render")
adapter = wgpu.request_adapter(canvas=canvas)
device = adapter.request_device()

# ─── BUFFERS ───
# Double-buffered storage: currentState e nextState
field_a = init_field()
field_b = init_field()

buffer_field_a = device.create_buffer(
    size=field_a.nbytes,
    usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_DST | wgpu.BufferUsage.COPY_SRC,
)
buffer_field_b = device.create_buffer(
    size=field_b.nbytes,
    usage=wgpu.BufferUsage.STORAGE | wgpu.BufferUsage.COPY_DST | wgpu.BufferUsage.COPY_SRC,
)

uniform_data = make_uniforms(kappa=50.0)
buffer_uniform = device.create_buffer(
    size=uniform_data.nbytes,
    usage=wgpu.BufferUsage.UNIFORM | wgpu.BufferUsage.COPY_DST,
)

# Escrever dados iniciais
device.queue.write_buffer(buffer_field_a, 0, field_a.tobytes())
device.queue.write_buffer(buffer_field_b, 0, field_b.tobytes())
device.queue.write_buffer(buffer_uniform, 0, uniform_data.tobytes())

# ─── BIND GROUP LAYOUT (compartilhado entre compute e render) ───
bind_group_layout = device.create_bind_group_layout(
    entries=[
        # binding 0: uniform
        {"binding": 0, "visibility": wgpu.ShaderStage.COMPUTE | wgpu.ShaderStage.FRAGMENT,
         "buffer": {"type": wgpu.BufferBindingType.uniform}},
        # binding 1: storage read (current state)
        {"binding": 1, "visibility": wgpu.ShaderStage.COMPUTE | wgpu.ShaderStage.FRAGMENT,
         "buffer": {"type": wgpu.BufferBindingType.read_only_storage}},
        # binding 2: storage read_write (next state) — apenas compute
        {"binding": 2, "visibility": wgpu.ShaderStage.COMPUTE,
         "buffer": {"type": wgpu.BufferBindingType.storage}},
    ]
)

# ─── COMPUTE PIPELINE ───
compute_shader = device.create_shader_module(code=COMPUTE_WGSL)
compute_pipeline = device.create_compute_pipeline(
    layout=device.create_pipeline_layout(bind_group_layouts=[bind_group_layout]),
    compute={"module": compute_shader, "entry_point": "cs_main"},
)

# ─── RENDER PIPELINE ───
render_shader = device.create_shader_module(code=FRAGMENT_WGSL)
render_pipeline = device.create_render_pipeline(
    layout=device.create_pipeline_layout(bind_group_layouts=[bind_group_layout]),
    vertex={"module": render_shader, "entry_point": "vs_main", "buffers": []},
    fragment={
        "module": render_shader,
        "entry_point": "fs_main",
        "targets": [{"format": wgpu.TextureFormat.bgra8unorm_srgb}],
    },
    primitive={"topology": wgpu.PrimitiveTopology.triangle_strip},
)

# ─── BIND GROUPS (alternam field_a/b como read/write) ───
# Frame par: read from A, write to B
# Frame ímpar: read from B, write to A
bind_groups = [
    device.create_bind_group(
        layout=bind_group_layout,
        entries=[
            {"binding": 0, "resource": {"buffer": buffer_uniform, "offset": 0, "size": uniform_data.nbytes}},
            {"binding": 1, "resource": {"buffer": buffer_field_a, "offset": 0, "size": field_a.nbytes}},
            {"binding": 2, "resource": {"buffer": buffer_field_b, "offset": 0, "size": field_b.nbytes}},
        ],
    ),
    device.create_bind_group(
        layout=bind_group_layout,
        entries=[
            {"binding": 0, "resource": {"buffer": buffer_uniform, "offset": 0, "size": uniform_data.nbytes}},
            {"binding": 1, "resource": {"buffer": buffer_field_b, "offset": 0, "size": field_b.nbytes}},
            {"binding": 2, "resource": {"buffer": buffer_field_a, "offset": 0, "size": field_a.nbytes}},
        ],
    ),
]

# ─── LOOP DE ANIMAÇÃO ───
frame_count = 0
start_time = time.time()

def draw():
    global frame_count
    t = time.time() - start_time

    # ─── PASSO 1: ATUALIZAR UNIFORMS ───
    uniform_data["uTime"] = t
    # Aqui: ler EEG, mouse, etc. para modificar kappa e cBrainInput
    # uniform_data["uKappa"] = get_kappa_from_eeg()
    # uniform_data["uCBrainInput"] = get_cbrain_from_eeg()
    device.queue.write_buffer(buffer_uniform, 0, uniform_data.tobytes())

    # ─── PASSO 2: COMPUTE PASS ───
    command_encoder = device.create_command_encoder()
    compute_pass = command_encoder.begin_compute_pass()
    compute_pass.set_pipeline(compute_pipeline)
    compute_pass.set_bind_group(0, bind_groups[frame_count % 2], [], 0, 999999)
    compute_pass.dispatch_workgroups(GRID_W // 8, GRID_H // 8, 1)
    compute_pass.end()

    # ─── PASSO 3: MEMORY BARRIER (implícita no submit) ───
    # O submit da queue garante que o compute termina antes do render começar

    # ─── PASSO 4: RENDER PASS ───
    current_texture = canvas.get_context().get_current_texture()
    render_pass = command_encoder.begin_render_pass(
        color_attachments=[{
            "view": current_texture.create_view(),
            "resolve_target": None,
            "clear_value": (0.0, 0.0, 0.0, 1.0),
            "load_op": wgpu.LoadOp.clear,
            "store_op": wgpu.StoreOp.store,
        }]
    )
    render_pass.set_pipeline(render_pipeline)
    render_pass.set_bind_group(0, bind_groups[frame_count % 2], [], 0, 999999)
    render_pass.draw(4, 1, 0, 0)  # fullscreen quad (triangle strip)
    render_pass.end()

    device.queue.submit([command_encoder.finish()])

    frame_count += 1
    canvas.request_draw()

# ─── INICIAR ───
if __name__ == "__main__":
    canvas.request_draw(draw)
    print("🔺 ARKHE v∞.283 — PYGFX SCAFFOLD ATIVADO")
    print(f"   Grid: {GRID_W}x{GRID_H} = {NUM_CELLS} células")
    print(f"   Workgroups: {GRID_W//8}x{GRID_H//8}")
    print(f"   Double-buffered storage swap")
    print(f"   Compute → Barrier → Render pipeline pronto")
    run()  # Descomentar para executar
