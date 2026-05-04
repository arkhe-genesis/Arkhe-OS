// shaders/qd_cbg_compute.wgsl
// ARKHE QD-NET: Jaynes-Cummings Master Equation Solver

struct PhysicsParams {
    dt: f32,           // Time step
    g: f32,            // QD-Cavity coupling (Vacuum Rabi frequency)
    kappa: f32,        // Cavity decay rate
    gamma: f32,        // Pure dephasing rate
    delta: f32,        // Detuning (QD - Cavity)
    purcell_factor: f32, // Enhancement factor
    noise_seed: u32,   // Seed for stochastic emission
    padding: u32,
};

@group(0) @binding(0) var<storage, read_write> photon_stream: array<u32>;
@group(0) @binding(1) var<storage, read_write> fidelity_out: array<f32>;
@group(0) @binding(2) var<uniform> params: PhysicsParams;

// Pseudo-random number generator for Monte Carlo wavefunction jumps
fn hash(u: u32) -> f32 {
    var x = u;
    x = x ^ (x >> 16u);
    x = x * 0x45d9f3bu;
    x = x ^ (x >> 16u);
    return f32(x % 10000u) / 10000.0;
}

@compute @workgroup_size(1)
fn main(@builtin(global_invocation_id) global_id: vec3<u32>) {
    let step = global_id.x;

    // Initialize state (Excited)
    var rho_ee: f32 = 1.0;
    var rho_gg: f32 = 0.0;
    var rho_eg_re: f32 = 0.0;
    var rho_eg_im: f32 = 0.0;

    // Evolution loop for this time step (simplified JC interaction)
    // dρ/dt = -i[H, ρ] + kappa D[a]ρ + gamma D[sigma_z]ρ

    // 1. Hamiltonian evolution (Rabi oscillations)
    let h_coupling = params.g * sqrt(rho_ee); // Simplified coupling term
    let rabi_freq = 2.0 * h_coupling;

    // 2. Dissipation and Dephasing (Lindblad terms)
    let decay_prob = params.kappa * rho_ee * params.dt;
    let dephasing = params.gamma * rho_eg_re * params.dt;

    // 3. Detuning effect
    let detuning_shift = params.delta * params.dt;

    // Update coherence
    rho_eg_re += ( -rabi_freq * rho_eg_im - decay_prob * rho_eg_re * 0.5 - dephasing ) * params.dt;
    rho_eg_im += ( rabi_freq * rho_eg_re - decay_prob * rho_eg_im * 0.5 + rho_eg_re * detuning_shift ) * params.dt;

    // Update populations
    let emission_event = (decay_prob > hash(params.noise_seed + step));

    if (emission_event) {
        rho_ee = max(0.0, rho_ee - decay_prob);
        rho_gg = 1.0 - rho_ee;
        photon_stream[step] = 1u; // PHOTON EMITTED

        // Fidelity calculation (simplified indistinguishability metric)
        // F = 1 / (1 + (kappa/gamma_total) + (delta/g)^2)
        let gamma_total = params.kappa + params.gamma;
        fidelity_out[step] = 1.0 / (1.0 + (params.kappa / gamma_total) + pow(params.delta / params.g, 2.0));
    } else {
        photon_stream[step] = 0u; // NO PHOTON
        if (step > 0u) {
            fidelity_out[step] = fidelity_out[step - 1u]; // Maintain previous fidelity
        } else {
            fidelity_out[step] = 0.0;
        }
    }
}