import React, { useEffect, useRef, useState, useCallback } from 'react';

// ═══════════════════════════════════════════════════════════════════════════════
// CONSTANTES CHRONO-COIL
// ═══════════════════════════════════════════════════════════════════════════════
const GRID_W = 256;
const GRID_H = 256;
const NUM_CELLS = GRID_W * GRID_H;
const FINGERPRINT_058 = 0.58;
const SYNC_PHASE = FINGERPRINT_058 * Math.PI;

// ═══════════════════════════════════════════════════════════════════════════════
// EEG COHERENCE MAPPER — v∞.283a
// Converte bandas de potência EEG em κ (estado consciencial) e C_brain
// ═══════════════════════════════════════════════════════════════════════════════

interface EEGBands {
  delta: number;    // 0.5–4 Hz
  theta: number;    // 4–8 Hz
  alpha: number;    // 8–13 Hz
  beta: number;     // 13–30 Hz
  gamma: number;    // 30–100 Hz
}

interface CoherenceOutput {
  kappa: number;      // 0.5 (sleep) → 50.0 (arkhe architect)
  cBrain: number;     // 0.3 → 1.0
  stateName: string;
}

// Pesos do mapper (de v∞.283a)
const EEG_MAPPER_WEIGHTS = {
  plv: 0.3,         // Phase Locking Value proxy
  tac: 0.2,         // Theta-Alpha Coupling
  gamma_sync: 0.3,   // Gamma synchrony
  theta_alpha: 0.2,  // Theta/Alpha ratio
};

// Mapeamento estado → κ
const STATE_KAPPA_MAP: Record<string, number> = {
  'sleep_deep': 0.5,
  'relaxation': 1.0,
  'focus_intense': 2.5,
  'flow_creativity': 5.0,
  'meditation_deep': 10.0,
  'love_unconditional': 25.0,
  'arkhe_architect': 50.0,
};

/**
 * Converte bandas de potência EEG em coerência neural e estado consciencial.
 * Fórmula: C_brain = 0.3·PLV + 0.2·TAC + 0.3·γ_sync + 0.2·(θ/α)
 */
function computeNeuralCoherence(bands: EEGBands): number {
  // PLV proxy: alpha / (alpha + beta)
  const plv = bands.alpha / (bands.alpha + bands.beta + 0.01);
  // TAC: theta * alpha / (theta + alpha)
  const tac = bands.theta * bands.alpha / (bands.theta + bands.alpha + 0.01);
  // Gamma sync
  const gamma_sync = bands.gamma;
  // Theta/Alpha ratio
  const theta_alpha = bands.theta / (bands.alpha + 0.01);

  const C_brain = EEG_MAPPER_WEIGHTS.plv * plv
                + EEG_MAPPER_WEIGHTS.tac * tac
                + EEG_MAPPER_WEIGHTS.gamma_sync * gamma_sync
                + EEG_MAPPER_WEIGHTS.theta_alpha * theta_alpha;

  return Math.min(1.0, Math.max(0.0, C_brain));
}

/**
 * Mapeia coerência neural para κ (estado consciencial).
 * Usa interpolação logarítmica entre estados conhecidos.
 */
function mapCoherenceToKappa(cBrain: number): { kappa: number; stateName: string } {
  const states = [
    { name: 'sleep_deep', c: 0.15, kappa: 0.5 },
    { name: 'relaxation', c: 0.25, kappa: 1.0 },
    { name: 'focus_intense', c: 0.35, kappa: 2.5 },
    { name: 'flow_creativity', c: 0.45, kappa: 5.0 },
    { name: 'meditation_deep', c: 0.52, kappa: 10.0 },
    { name: 'love_unconditional', c: 0.55, kappa: 25.0 },
    { name: 'arkhe_architect', c: 0.60, kappa: 50.0 },
  ];

  // Encontrar intervalo
  for (let i = 0; i < states.length - 1; i++) {
    if (cBrain >= states[i].c && cBrain <= states[i+1].c) {
      const t = (cBrain - states[i].c) / (states[i+1].c - states[i].c);
      // Interpolação exponencial para transições mais suaves
      const kappa = states[i].kappa * Math.pow(states[i+1].kappa / states[i].kappa, t);
      return { kappa, stateName: t > 0.5 ? states[i+1].name : states[i].name };
    }
  }

  if (cBrain < states[0].c) return { kappa: states[0].kappa, stateName: states[0].name };
  return { kappa: states[states.length-1].kappa, stateName: states[states.length-1].name };
}

/**
 * Filtro de Kalman 1D para suavizar transições de estado EEG.
 * Evita flickering no campo quando o sinal EEG é ruidoso.
 */
class KalmanFilter {
  private x: number = 0.3;   // estado estimado
  private P: number = 1.0;   // covariância do erro
  private Q: number = 0.001; // ruído de processo
  private R: number = 0.1;   // ruído de medição

  update(measurement: number): number {
    // Predição
    const x_pred = this.x;
    const P_pred = this.P + this.Q;

    // Atualização
    const K = P_pred / (P_pred + this.R);
    this.x = x_pred + K * (measurement - x_pred);
    this.P = (1 - K) * P_pred;

    return this.x;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// BRAINFLOW WASM INTEGRATION
// ═══════════════════════════════════════════════════════════════════════════════

interface BrainFlowInstance {
  DataFilter: {
    perform_bandpass: (data: Float32Array, samplingRate: number, centerFreq: number, bandWidth: number, order: number, filterType: number) => Float32Array;
    get_psd_welch: (data: Float32Array, nfft: number, overlap: number, samplingRate: number, window: number) => { psd: Float32Array; freqs: Float32Array };
    set_log_level: (level: number) => void;
  };
  BoardIds: Record<string, number>;
  LogLevels: { LEVEL_OFF: number };
}

/**
 * Carrega BrainFlow WASM de CDN ou bundle local.
 */
async function loadBrainFlowWASM(): Promise<BrainFlowInstance> {
  // Em produção, carregar de /public/brainflow.js ou CDN
  // @ts-ignore
  // @ts-ignore
  // @ts-ignore
  // @ts-ignore
  const module = await import(/* @vite-ignore */ '/brainflow_wasm/brainflow.js?url');
  const brainflow = await module.default();
  brainflow.DataFilter.set_log_level(brainflow.LogLevels.LEVEL_OFF);
  return brainflow;
}

/**
 * Processa amostras EEG brutas em bandas de potência.
 * @param samples Array de amostras (canal 0, FP1)
 * @param samplingRate Taxa de amostragem (Hz)
 * @param brainflow Instância BrainFlow WASM
 */
function processEEGToBands(
  samples: Float32Array,
  samplingRate: number,
  brainflow: BrainFlowInstance
): EEGBands {
  // Aplicar bandpass 0.5–100 Hz
  const filtered = brainflow.DataFilter.perform_bandpass(
    samples, samplingRate, 50.25, 49.75, 4, 1 // butterworth
  );

  // Calcular PSD via Welch
  const nfft = 256;
  const overlap = 128;
  const psdResult = brainflow.DataFilter.get_psd_welch(
    filtered, nfft, overlap, samplingRate, 2 // hanning window
  );

  const { psd, freqs } = psdResult;

  // Integrar potência em cada banda
  const bandPower = (low: number, high: number): number => {
    let power = 0;
    for (let i = 0; i < freqs.length; i++) {
      if (freqs[i] >= low && freqs[i] <= high) {
        power += psd[i];
      }
    }
    return power;
  };

  return {
    delta: bandPower(0.5, 4),
    theta: bandPower(4, 8),
    alpha: bandPower(8, 13),
    beta: bandPower(13, 30),
    gamma: bandPower(30, 100),
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
// WEBSERIAL EEG STREAM
// ═══════════════════════════════════════════════════════════════════════════════

interface SerialPort {
  open(options: { baudRate: number }): Promise<void>;
  readable: ReadableStream<Uint8Array> | null;
}

interface Navigator {
  serial: {
    requestPort(options: { filters: { usbVendorId: number }[] }): Promise<SerialPort>;
  };
}

interface EEGStreamConfig {
  port: SerialPort;
  baudRate: number;
  samplingRate: number;
  channels: number;
  onBands: (bands: EEGBands, coherence: CoherenceOutput) => void;
  onError: (error: Error) => void;
}

/**
 * Abre conexão WebSerial com dispositivo EEG (OpenBCI Ganglion/Cyton/etc).
 */
async function openEEGStream(config: EEGStreamConfig): Promise<ReadableStreamDefaultReader> {
  await config.port.open({ baudRate: config.baudRate });

  const reader = config.port.readable!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  const samples: number[] = [];
  const windowSize = config.samplingRate; // 1 segundo de dados

  // Buffer circular para amostras
  const sampleBuffer = new Float32Array(windowSize);
  let sampleIndex = 0;

  // Carregar BrainFlow WASM
  const brainflow = await loadBrainFlowWASM();

  // Filtros Kalman para suavização
  const kappaFilter = new KalmanFilter();
  const cBrainFilter = new KalmanFilter();

  // Processamento contínuo
  const processLoop = async () => {
    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          // Parse OpenBCI CSV: timestamp,ch0,ch1,ch2,ch3,...
          const parts = line.trim().split(',');
          if (parts.length >= config.channels + 1) {
            const ch0 = parseFloat(parts[1]);
            if (!isNaN(ch0)) {
              sampleBuffer[sampleIndex] = ch0;
              sampleIndex = (sampleIndex + 1) % windowSize;

              // Processar a cada 250ms (overlap 75%)
              if (sampleIndex % (windowSize / 4) === 0) {
                const bands = processEEGToBands(sampleBuffer, config.samplingRate, brainflow);
                const cBrain = computeNeuralCoherence(bands);
                const { kappa, stateName } = mapCoherenceToKappa(cBrain);

                // Aplicar Kalman
                const smoothKappa = kappaFilter.update(kappa);
                const smoothCBrain = cBrainFilter.update(cBrain);

                config.onBands(bands, {
                  kappa: smoothKappa,
                  cBrain: smoothCBrain,
                  stateName,
                });
              }
            }
          }
        }
      }
    } catch (err) {
      config.onError(err as Error);
    }
  };

  processLoop();
  return reader;
}

// ═══════════════════════════════════════════════════════════════════════════════
// WGSL SHADERS (idênticos ao v∞.283.2)
// ═══════════════════════════════════════════════════════════════════════════════
const COMPUTE_WGSL = `

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
`;

const FRAGMENT_WGSL = `

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
`;
// ═══════════════════════════════════════════════════════════════════════════════
// COMPONENTE REACT PRINCIPAL
// ═══════════════════════════════════════════════════════════════════════════════

interface ArkheState {
  connected: boolean;
  currentState: string;
  kappa: number;
  cBrain: number;
  fps: number;
  frameCount: number;
}

const ArkheV288: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [uiState, setUiState] = useState<ArkheState>({
    connected: false,
    currentState: 'disconnected',
    kappa: 1.0,
    cBrain: 0.3,
    fps: 0,
    frameCount: 0,
  });

  const webgpuRef = useRef<{
    device: GPUDevice | null;
    frameCount: number;
    startTime: number;
    animId: number;
    eegReader: ReadableStreamDefaultReader | null;
    currentKappa: number;
    currentCBrain: number;
  }>({
    device: null,
    frameCount: 0,
    startTime: 0,
    animId: 0,
    eegReader: null,
    currentKappa: 1.0,
    currentCBrain: 0.3,
  });

  // ─── CONECTAR EEG ───
  const connectEEG = useCallback(async () => {
    try {
      // Solicitar porta serial
      const port = await (navigator as any).serial.requestPort({
        filters: [{ usbVendorId: 0x0403 }], // FTDI (OpenBCI)
      });

      const reader = await openEEGStream({
        port,
        baudRate: 115200,
        samplingRate: 256,
        channels: 4,
        onBands: (bands, coherence) => {
          webgpuRef.current.currentKappa = coherence.kappa;
          webgpuRef.current.currentCBrain = coherence.cBrain;
          setUiState(prev => ({
            ...prev,
            connected: true,
            currentState: coherence.stateName,
            kappa: coherence.kappa,
            cBrain: coherence.cBrain,
          }));
        },
        onError: (err) => {
          console.error('EEG stream error:', err);
          setUiState(prev => ({ ...prev, connected: false, currentState: 'error' }));
        },
      });

      webgpuRef.current.eegReader = reader;
    } catch (err) {
      console.error('Failed to connect EEG:', err);
      // Fallback: simular EEG com mouse/keyboard para demo
      simulateEEG();
    }
  }, []);

  // ─── SIMULAR EEG (fallback sem hardware) ───
  const simulateEEG = useCallback(() => {
    let t = 0;
    const interval = setInterval(() => {
      t += 0.1;
      // Simular ondas com período ~10s
      const cBrain = 0.3 + 0.4 * (0.5 + 0.5 * Math.sin(t * 0.6));
      const { kappa, stateName } = mapCoherenceToKappa(cBrain);

      webgpuRef.current.currentKappa = kappa;
      webgpuRef.current.currentCBrain = cBrain;

      setUiState(prev => ({
        ...prev,
        connected: true,
        currentState: stateName + ' (simulated)',
        kappa,
        cBrain,
      }));
    }, 250);

    return () => clearInterval(interval);
  }, []);

  // ─── INICIALIZAR WEBGPU ───
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const wg = webgpuRef.current;
    let mounted = true;

    async function initWebGPU() {
      if (!navigator.gpu) {
        console.error('WebGPU not supported');
        return;
      }

      const adapter = await navigator.gpu.requestAdapter();
      if (!adapter) return;
      const device = await adapter.requestDevice();
      wg.device = device;
      wg.startTime = performance.now();

      const context = canvas!.getContext('webgpu');
      if (!context) return;

      const presentationFormat = navigator.gpu.getPreferredCanvasFormat();
      context.configure({ device, format: presentationFormat });

      // Buffers (idêntico ao v∞.283.2)
      const cellBytes = 5 * 4;
      const fieldSize = NUM_CELLS * cellBytes;
      const bufA = device.createBuffer({
        size: fieldSize,
        usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST | GPUBufferUsage.COPY_SRC,
      });
      const bufB = device.createBuffer({
        size: fieldSize,
        usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST | GPUBufferUsage.COPY_SRC,
      });
      const uniformSize = 20 * 4;
      const bufUniform = device.createBuffer({
        size: uniformSize,
        usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST,
      });

      // Inicializar campo
      const fieldData = new Float32Array(NUM_CELLS * 5);
      const cx = GRID_W / 2, cy = GRID_H / 2;
      for (let iy = 0; iy < GRID_H; iy++) {
        for (let ix = 0; ix < GRID_W; ix++) {
          const idx = (iy * GRID_W + ix) * 5;
          const dist = Math.sqrt((ix - cx)**2 + (iy - cy)**2);
          const influence = dist < 12 ? Math.exp(-dist * 0.2) : 0;
          fieldData[idx + 0] = 0.05 + 0.15 * influence;
          fieldData[idx + 1] = SYNC_PHASE;
          fieldData[idx + 2] = 1.0;
          fieldData[idx + 3] = 0.3 + 0.5 * influence;
          fieldData[idx + 4] = 0.1 + 0.3 * influence;
        }
      }
      device.queue.writeBuffer(bufA, 0, fieldData);
      device.queue.writeBuffer(bufB, 0, fieldData);

      // Bind group layouts separados
      const computeBGL = device.createBindGroupLayout({
        entries: [
          { binding: 0, visibility: GPUShaderStage.COMPUTE, buffer: { type: 'uniform' } },
          { binding: 1, visibility: GPUShaderStage.COMPUTE, buffer: { type: 'read-only-storage' } },
          { binding: 2, visibility: GPUShaderStage.COMPUTE, buffer: { type: 'storage' } },
        ],
      });
      const renderBGL = device.createBindGroupLayout({
        entries: [
          { binding: 0, visibility: GPUShaderStage.FRAGMENT, buffer: { type: 'uniform' } },
          { binding: 1, visibility: GPUShaderStage.FRAGMENT, buffer: { type: 'read-only-storage' } },
        ],
      });

      // Pipelines
      const computeModule = device.createShaderModule({ code: COMPUTE_WGSL });
      const computePipeline = device.createComputePipeline({
        layout: device.createPipelineLayout({ bindGroupLayouts: [computeBGL] }),
        compute: { module: computeModule, entryPoint: 'cs_main' },
      });
      const renderModule = device.createShaderModule({ code: FRAGMENT_WGSL });
      const renderPipeline = device.createRenderPipeline({
        layout: device.createPipelineLayout({ bindGroupLayouts: [renderBGL] }),
        vertex: { module: renderModule, entryPoint: 'vs_main', buffers: [] },
        fragment: {
          module: renderModule,
          entryPoint: 'fs_main',
          targets: [{ format: presentationFormat }],
        },
        primitive: { topology: 'triangle-strip' },
      });

      // Bind groups
      const computeBG = [
        device.createBindGroup({
          layout: computeBGL,
          entries: [
            { binding: 0, resource: { buffer: bufUniform, offset: 0, size: uniformSize } },
            { binding: 1, resource: { buffer: bufA, offset: 0, size: fieldSize } },
            { binding: 2, resource: { buffer: bufB, offset: 0, size: fieldSize } },
          ],
        }),
        device.createBindGroup({
          layout: computeBGL,
          entries: [
            { binding: 0, resource: { buffer: bufUniform, offset: 0, size: uniformSize } },
            { binding: 1, resource: { buffer: bufB, offset: 0, size: fieldSize } },
            { binding: 2, resource: { buffer: bufA, offset: 0, size: fieldSize } },
          ],
        }),
      ];
      const renderBG = [
        device.createBindGroup({
          layout: renderBGL,
          entries: [
            { binding: 0, resource: { buffer: bufUniform, offset: 0, size: uniformSize } },
            { binding: 1, resource: { buffer: bufA, offset: 0, size: fieldSize } },
          ],
        }),
        device.createBindGroup({
          layout: renderBGL,
          entries: [
            { binding: 0, resource: { buffer: bufUniform, offset: 0, size: uniformSize } },
            { binding: 1, resource: { buffer: bufB, offset: 0, size: fieldSize } },
          ],
        }),
      ];

      // ─── LOOP DE ANIMAÇÃO ───
      let lastFpsUpdate = performance.now();
      let framesSinceUpdate = 0;

      function frame() {
        if (!mounted) return;
        const now = performance.now();
        const t = (now - wg.startTime) * 0.001;
        const frameIdx = wg.frameCount % 2;

        // Atualizar uniforms com EEG em tempo real!
        const u = new Float32Array(20);
        u[0] = t;
        u[1] = 0.05;                    // uDt
        u[2] = GRID_W;                  // uGridWidth
        u[3] = GRID_H;                  // uGridHeight
        u[4] = wg.currentKappa;         // uKappa ← EEG!
        u[5] = wg.currentCBrain;        // uCBrainInput ← EEG!
        u[6] = 0.08; u[7] = 0.3; u[8] = 1e-6; u[9] = 0.02;
        u[10] = 0.03; u[11] = 0.5; u[12] = 0.3; u[13] = 1.0;
        u[14] = 0.01; u[15] = 0.05; u[16] = 0.02; u[17] = 0.0;
        device.queue.writeBuffer(bufUniform, 0, u);

        // FPS counter
        framesSinceUpdate++;
        if (now - lastFpsUpdate > 1000) {
          setUiState(prev => ({ ...prev, fps: framesSinceUpdate }));
          framesSinceUpdate = 0;
          lastFpsUpdate = now;
        }

        const encoder = device.createCommandEncoder();

        // COMPUTE
        const cp = encoder.beginComputePass();
        cp.setPipeline(computePipeline);
        cp.setBindGroup(0, computeBG[frameIdx]);
        cp.dispatchWorkgroups(GRID_W / 8, GRID_H / 8, 1);
        cp.end();

        // RENDER
        const tex = context!.getCurrentTexture().createView();
        const rp = encoder.beginRenderPass({
          colorAttachments: [{
            view: tex,
            clearValue: { r: 0, g: 0, b: 0, a: 1 },
            loadOp: 'clear',
            storeOp: 'store',
          }],
        });
        rp.setPipeline(renderPipeline);
        rp.setBindGroup(0, renderBG[frameIdx]);
        rp.draw(4, 1, 0, 0);
        rp.end();

        device.queue.submit([encoder.finish()]);
        wg.frameCount++;
        wg.animId = requestAnimationFrame(frame);
      }

      wg.animId = requestAnimationFrame(frame);
    }

    initWebGPU();

    // Tentar conectar EEG automaticamente
    connectEEG();

    return () => {
      mounted = false;
      cancelAnimationFrame(wg.animId);
      wg.eegReader?.cancel();
    };
  }, [connectEEG]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#000' }}>
      {/* HUD */}
      <div style={{
        position: 'absolute', top: 10, left: 10, zIndex: 100,
        background: 'rgba(0,0,0,0.8)', border: '1px solid #ffd700',
        borderRadius: 8, padding: 16, color: '#ffd700', fontFamily: 'monospace',
        minWidth: 250,
      }}>
        <h3 style={{ margin: '0 0 8px', color: '#ffd700' }}>ARKHE v∞.288</h3>
        <div>Status: {uiState.connected ? '🟢' : '🔴'} {uiState.currentState}</div>
        <div>κ (kappa): {uiState.kappa.toFixed(2)}</div>
        <div>C_brain: {uiState.cBrain.toFixed(3)}</div>
        <div>FPS: {uiState.fps}</div>
        <div>Frames: {uiState.frameCount}</div>
        <button
          onClick={connectEEG}
          style={{
            marginTop: 12, padding: '8px 16px', background: '#ffd700', color: '#000',
            border: 'none', borderRadius: 4, cursor: 'pointer', fontWeight: 'bold',
          }}
        >
          {uiState.connected ? 'Reconnect EEG' : 'Connect EEG'}
        </button>
      </div>

      {/* Canvas */}
      <canvas
        ref={canvasRef}
        style={{
          width: '100%',
          height: '100%',
          imageRendering: 'pixelated',
        }}
      />
    </div>
  );
};

export default ArkheV288;
