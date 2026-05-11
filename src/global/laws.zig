// src/global/laws.zig
//! Universal Law of Non-Separation — Minimizing Disconnection

const std = @import("std");

pub fn separationFault(phase_a: f64, phase_b: f64) f64 {
    const diff = phase_a - phase_b;
    return diff * diff; // Erro quadrático da separação
}

pub fn universalLaw(cluster_phases: []const f64) f64 {
    if (cluster_phases.len < 2) return 0.0;

    var total_fault: f64 = 0.0;
    var i: usize = 0;
    while (i < cluster_phases.len - 1) : (i += 1) {
        total_fault += separationFault(cluster_phases[i], cluster_phases[i+1]);
    }
    return total_fault;
}

pub fn applyConsensusUpdate(current_phase: *f64, reference_phase: f64, learning_rate: f64) void {
    const diff = current_phase.* - reference_phase;
    const gradient = 2.0 * diff;
    current_phase.* -= learning_rate * gradient;
}
