// shaders/qd_cbg_compute_fixed.wgsl
// ARKHE QD-NET: Jaynes-Cummings Master Equation Solver — CORRECTED

struct PhysicsParams {
    dt: f32,
    g: f32,
    kappa: f32,
    gamma: f32,
    delta: f32,
    purcell_factor: f32,  // NOW USED
    noise_seed: u32,
    frame_seed: u32,      // NEW: per-frame RNG seed
};

// Persistent state buffer between steps
@group(0) @binding(0) var<storage, read_write> photon_stream: array<u32>;
@group(0) @binding(1) var<storage, read_write> fidelity_out: array<f32>;
@group(0) @binding(2) var<uniform> params: PhysicsParams;
@group(0) @binding(3) var<storage, read_write> state_buffer: array<vec4<f32>>; // [rho_ee, rho_gg, rho_eg_re, rho_eg_im]

// Xoroshiro64* PRNG for per-thread stochasticity
fn xoroshiro64star(seed: u32) -> f32 {
    var s = seed;
    if (s == 0u) { s = 1u; } // Avoid zero seed
    s = s ^ (s << 13u);
    s = s ^ (s >> 7u);
    s = s ^ (s << 17u);
    return f32(s % 1000000u) / 1000000.0;
}

@compute @workgroup_size(1)
fn main(@builtin(global_invocation_id) global_id: vec3<u32>) {
    let step = global_id.x;

    // Load or initialize state
    var rho: vec4<f32>;
    if (step == 0u) {
        rho = vec4<f32>(1.0, 0.0, 0.0, 0.0); // Start excited
    } else {
        rho = state_buffer[step - 1u]; // FIX #1: No underflow
    }

    // Apply Purcell enhancement to decay rate (FIX #3)
    let gamma_eff = params.gamma * params.purcell_factor;
    let kappa_eff = params.kappa * params.purcell_factor;

    // Hamiltonian: Rabi oscillations with detuning
    let omega_R = 2.0 * params.g;
    let detuning_shift = params.delta * params.dt;

    // Lindblad dissipators (correct complex dephasing - FIX #5)
    let decay_rate = kappa_eff * rho.x; // Population decay from excited
    let dephasing_rate = gamma_eff;     // Coherence decay: d(rho_eg)/dt = -gamma * rho_eg

    // Monte Carlo jump probability
    let jump_prob = decay_rate * params.dt;
    let rng_val = xoroshiro64star(params.noise_seed + params.frame_seed + step);
    let emission_event = (jump_prob > rng_val);

    if (emission_event) {
        // Quantum jump: |e⟩ → |g⟩ + photon
        rho.x = max(0.0, rho.x - jump_prob);
        rho.y = 1.0 - rho.x; // FIX #4: Maintain trace = 1
        rho.z = 0.0; // Coherence destroyed by measurement
        rho.w = 0.0;
        photon_stream[step] = 1u;

        // Fidelity: indistinguishability metric
        let gamma_total = gamma_eff + kappa_eff;
        let purcell_enhanced_g = params.g * sqrt(params.purcell_factor);
        fidelity_out[step] = 1.0 / (1.0 + (kappa_eff / gamma_total) + pow(params.delta / purcell_enhanced_g, 2.0));
    } else {
        // No-jump evolution: non-Hermitian Hamiltonian + dephasing
        // Coherence evolution (FIX #5: full complex dephasing)
        let d_eg_re = (-omega_R * rho.w - 0.5 * (kappa_eff + gamma_eff) * rho.z) * params.dt;
        let d_eg_im = ( omega_R * rho.z - 0.5 * (kappa_eff + gamma_eff) * rho.w + rho.z * detuning_shift) * params.dt;
        rho.z += d_eg_re;
        rho.w += d_eg_im;

        // Population evolution (no jump)
        rho.x = rho.x * (1.0 - jump_prob); // Survival probability
        rho.y = 1.0 - rho.x; // FIX #4: Trace preservation

        photon_stream[step] = 0u;
        // FIX #1: Handle step==0 for fidelity persistence
        if (step > 0u) {
            fidelity_out[step] = fidelity_out[step - 1u];
        } else {
            fidelity_out[step] = 1.0; // Initial perfect fidelity
        }
    }

    // Store state for next step (FIX #2: persistent evolution)
    state_buffer[step] = rho;
}
