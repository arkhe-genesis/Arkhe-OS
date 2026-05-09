// src/vm/qnet.zig
//! Módulo QNET: Simulação Física de Fibra Óptica baseada em NIST 2026.
//! Implementa PMD, Dispersão Cromática e Ruído Raman.

const std = @import("std");

/// Constantes Físicas (Baseado no artigo NIST)
pub const NIST = struct {
    // Coeficientes de Espalhamento Raman (ex: 1270nm clássico, 1550nm quântico)
    pub const beta_BS: f64 = 0.058e-23; // m^-1 Hz^-1 (Backward Scattering)
    pub const beta_FS: f64 = 3.7e-23;  // m^-1 Hz^-1 (Forward Scattering)

    // Parâmetros de Dispersão Cromática (Silica Padrão)
    pub const zero_dispersion_wavelength: f64 = 1310e-9; // 1310 nm
    pub const dispersion_slope: f64 = 0.092; // ps / (nm^2 * km)

    // PMD (Polarization Mode Dispersion)
    pub const pmd_coefficient: f64 = 0.5; // ps / sqrt(km)
};

/// Estado de um fóton viajando pela fibra
pub const PhotonState = struct {
    polarization: f64,       // Ângulo de polarização (rad)
    wavelength: f64,        // Comprimento de onda (m)
    position: f64,          // Posição na fibra (km)
    phase_shift: f64,       // Acumulado por CD e PMD
    is_lost: bool,         // Detectado se absorvido ou espalhado
};

/// Aplica Dispersão Cromática ao fóton
pub fn applyChromaticDispersion(photon: *PhotonState, length_km: f64) void {
    const delta_lambda = photon.wavelength - NIST.zero_dispersion_wavelength;
    const delay = NIST.dispersion_slope * delta_lambda * delta_lambda * length_km * 1e-12; // ps

    photon.phase_shift += delay;
    // Fase convertida para radianos para uso nos cálculos de coerência
    photon.polarization += delay * 2.0 * std.math.pi * 3e8 / photon.wavelength;
}

/// Aplica PMD (Polarization Mode Dispersion)
/// Randomiza a polarização baseado no comprimento da fibra e estresse.
pub fn applyPMD(photon: *PhotonState, length_km: f64, seed: u64) void {
    var prng = std.rand.DefaultPrng.init(seed);
    const random = prng.random();

    // Simplificação da estatística de Maxwell-Boltzmann
    const delta_psi = NIST.pmd_coefficient * std.math.sqrt(length_km);

    // Rotação estocástica do vetor de polarização
    photon.polarization += (random.float(f64) - 0.5) * delta_psi;
}

/// Adiciona Ruído Raman (Baseado na potência clássica)
pub fn applyRamanNoise(photon: *PhotonState, classic_power_mw: f64, length_km: f64, seed: u64) f64 {
    var prng = std.rand.DefaultPrng.init(seed);
    const random = prng.random();

    // Probabilidade de scattering * Potência * Comprimento
    const scattering_prob = (NIST.beta_FS + NIST.beta_BS) * length_km;
    const noise_photons = classic_power_mw * scattering_prob;

    // Modelo simples: Ruído adiciona aleatoriedade à fase
    const noise_phase = (random.float(f64) - 0.5) * 0.1; // 10% de jitter de fase
    photon.polarization += noise_phase;

    return noise_photons;
}
