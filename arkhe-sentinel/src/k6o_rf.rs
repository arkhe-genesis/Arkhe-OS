//! # k6o_rf.rs
//!
//! Extensão do Kuramoto Oscillator para o domínio da frequência.
//!
//! Cada Sentinela (PXN-90) é um oscilador no espaço RF:
//! • Fase = ângulo da portadora dominante (atan2(Q, I))
//! • Frequência natural = frequência central do bin FFT
//! • Acoplamento = correlação espectral entre nós vizinhos
//!
//! A malha RF sincroniza fases entre múltiplos Sentinelas,
//! detectando anomalias como desincronizações espontâneas.
//!
//! > *"O K6O pulsa em 7.83 Hz. O K6O-RF pulsa em 2.435 GHz.
//! > A mesma matemática, escalada por nove ordens de magnitude."*

use arkhe_rust_core::KuramotoOscillator;
use crate::{IqSample, SpectrumPoint};

/// Oscilador Kuramoto no domínio RF
#[derive(Clone, Debug)]
pub struct RfOscillator {
    /// Oscilador base (fase, frequência, acoplamento)
    pub base: KuramotoOscillator,
    /// Frequência central do bin (Hz)
    pub center_frequency: f64,
    /// Largura de banda do bin (Hz)
    pub bandwidth: f64,
    /// Potência média no bin (dBm)
    pub power_dbm: f64,
    /// SNR estimado (dB)
    pub snr_db: f64,
    /// Coordenadas GPS (lat, lon, alt)
    pub gps_position: Option<(f64, f64, f64)>,
}

impl RfOscillator {
    /// Cria um novo oscilador RF a partir de um bin FFT
    pub fn from_spectrum_bin(
        point: &SpectrumPoint,
        bin_bandwidth: f64,
        initial_phase: f64,
        coupling: f64,
    ) -> Self {
        // Frequência natural proporcional à frequência do bin
        // Normalizada para rad/s (ω = 2πf, mas escalada para evitar overflow)
        let omega = (point.frequency_hz / 1e9) * std::f64::consts::TAU;

        Self {
            base: KuramotoOscillator::new(omega, initial_phase, coupling),
            center_frequency: point.frequency_hz,
            bandwidth: bin_bandwidth,
            power_dbm: point.amplitude_dbm,
            snr_db: 0.0, // Calculado externamente
            gps_position: None,
        }
    }

    /// Cria um oscilador RF a partir de amostras IQ
    pub fn from_iq_samples(
        samples: &[IqSample],
        center_frequency: f64,
        bandwidth: f64,
        coupling: f64,
    ) -> Self {
        let mean_phase = samples.iter().map(|s| s.phase()).sum::<f64>() / samples.len() as f64;
        let mean_power = samples.iter().map(|s| s.power_dbm()).sum::<f64>() / samples.len() as f64;

        // Frequência instantânea média (derivada da fase)
        let freq_inst = if samples.len() > 1 {
            let phase_diffs: Vec<f64> = samples.windows(2)
                .map(|w| {
                    let mut d = w[1].phase() - w[0].phase();
                    if d > std::f64::consts::PI { d -= std::f64::consts::TAU; }
                    if d < -std::f64::consts::PI { d += std::f64::consts::TAU; }
                    d
                })
                .collect();
            let mean_diff = phase_diffs.iter().sum::<f64>() / phase_diffs.len() as f64;
            mean_diff * bandwidth / std::f64::consts::TAU // Hz
        } else {
            0.0
        };

        let omega = (center_frequency + freq_inst) / 1e9 * std::f64::consts::TAU;

        Self {
            base: KuramotoOscillator::new(omega, mean_phase, coupling),
            center_frequency,
            bandwidth,
            power_dbm: mean_power,
            snr_db: 0.0,
            gps_position: None,
        }
    }

    /// Passo de sincronização com influência de vizinhos RF
    ///
    /// Além da regra de Kuramoto padrão, considera:
    /// • Diferença de potência (nós com potência similar acoplam mais)
    /// • Proximidade espectral (bins próximos acoplam mais)
    /// • Proximidade geográfica (se GPS disponível)
    pub fn step_rf(&mut self, dt: f64, neighbors: &[&RfOscillator], r_global: f64, _psi_global: f64) {
        // Calcula acoplamento efetivo ponderado
        let mut weighted_coupling = 0.0;
        let mut total_weight = 0.0;

        for neighbor in neighbors {
            // Peso por proximidade espectral (Gaussian)
            let freq_diff = (self.center_frequency - neighbor.center_frequency).abs();
            let spectral_weight = (-(freq_diff / self.bandwidth).powi(2)).exp();

            // Peso por similaridade de potência
            let power_diff = (self.power_dbm - neighbor.power_dbm).abs();
            let power_weight = (-(power_diff / 10.0).powi(2)).exp();

            // Peso por proximidade geográfica
            let geo_weight = match (self.gps_position, neighbor.gps_position) {
                (Some((lat1, lon1, _)), Some((lat2, lon2, _))) => {
                    let dist = haversine_distance(lat1, lon1, lat2, lon2);
                    (-(dist / 1000.0).powi(2)).exp() // 1km scale
                }
                _ => 1.0,
            };

            let weight = spectral_weight * power_weight * geo_weight;
            let delta = neighbor.base.phase - self.base.phase;
            weighted_coupling += weight * delta.sin();
            total_weight += weight;
        }

        let effective_coupling = if total_weight > 0.0 {
            self.base.coupling * weighted_coupling / total_weight
        } else {
            0.0
        };

        // Passo de Kuramoto modificado
        self.base.phase += dt * (self.base.natural_frequency + effective_coupling * r_global);
        self.base.phase = self.base.phase.rem_euclid(std::f64::consts::TAU);
        self.base.local_coherence = r_global;
    }

    /// Atualiza potência e SNR a partir de nova leitura
    pub fn update_power(&mut self, power_dbm: f64, noise_floor_dbm: f64) {
        self.power_dbm = power_dbm;
        self.snr_db = power_dbm - noise_floor_dbm;
    }
}

/// Malha RF de múltiplos osciladores
pub struct RfMesh {
    oscillators: Vec<RfOscillator>,
    global_order: f64,
    global_phase: f64,
}

impl RfMesh {
    /// Cria uma malha vazia
    pub fn new() -> Self {
        Self {
            oscillators: Vec::new(),
            global_order: 0.0,
            global_phase: 0.0,
        }
    }

    /// Adiciona um oscilador
    pub fn add(&mut self, osc: RfOscillator) {
        self.oscillators.push(osc);
    }

    /// Sincroniza todos os osciladores
    pub fn sync(&mut self, dt: f64) {
        if self.oscillators.is_empty() {
            return;
        }

        // Calcula vetor de ordem global
        let mut sum_cos = 0.0;
        let mut sum_sin = 0.0;
        for osc in &self.oscillators {
            let (c, s) = osc.base.order_contribution();
            sum_cos += c;
            sum_sin += s;
        }

        let n = self.oscillators.len() as f64;
        self.global_order = ((sum_cos / n).powi(2) + (sum_sin / n).powi(2)).sqrt();
        self.global_phase = (sum_sin / n).atan2(sum_cos / n);

        // Atualiza cada oscilador com seus vizinhos
        for i in 0..self.oscillators.len() {
            // Vizinhos = todos os outros (em produção, usar k-NN espacial)
            let neighbors: Vec<&RfOscillator> = self.oscillators.iter()
                .enumerate()
                .filter(|(j, _)| *j != i)
                .map(|(_, osc)| osc)
                .collect();

            let osc = &mut self.oscillators[i];
            osc.step_rf(dt, &neighbors, self.global_order, self.global_phase);
        }
    }

    /// Coerência global
    pub fn coherence(&self) -> f64 {
        self.global_order
    }

    /// Detecta anomalias: osciladores com coerência local muito baixa
    pub fn detect_anomalies(&self, threshold: f64) -> Vec<(usize, f64, f64)> {
        // Anomalia = oscilador cuja fase difere muito da fase global
        self.oscillators.iter()
            .enumerate()
            .map(|(i, osc)| {
                let phase_diff = (osc.base.phase - self.global_phase).abs();
                let phase_diff = if phase_diff > std::f64::consts::PI {
                    std::f64::consts::TAU - phase_diff
                } else {
                    phase_diff
                };
                (i, osc.center_frequency, phase_diff)
            })
            .filter(|(_, _, diff)| *diff > threshold)
            .collect()
    }

    /// Número de osciladores
    pub fn len(&self) -> usize {
        self.oscillators.len()
    }

    pub fn is_empty(&self) -> bool {
        self.oscillators.is_empty()
    }
}

impl Default for RfMesh {
    fn default() -> Self {
        Self::new()
    }
}

/// Distância Haversine entre dois pontos GPS (km)
fn haversine_distance(lat1: f64, lon1: f64, lat2: f64, lon2: f64) -> f64 {
    let r = 6371.0; // Raio da Terra em km
    let dlat = (lat2 - lat1).to_radians();
    let dlon = (lon2 - lon1).to_radians();
    let a = (dlat / 2.0).sin().powi(2)
        + lat1.to_radians().cos() * lat2.to_radians().cos() * (dlon / 2.0).sin().powi(2);
    let c = 2.0 * a.sqrt().atan2((1.0 - a).sqrt());
    r * c
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rf_oscillator_from_spectrum() {
        let point = SpectrumPoint {
            frequency_hz: 2.435e9,
            amplitude_dbm: -60.0,
        };

        let osc = RfOscillator::from_spectrum_bin(&point, 120e3, 0.0, 0.1);

        assert!((osc.center_frequency - 2.435e9).abs() < 1.0);
        assert!((osc.power_dbm - (-60.0)).abs() < 1e-6);
        assert_eq!(osc.bandwidth, 120e3);
    }

    #[test]
    fn rf_mesh_sync() {
        let mut mesh = RfMesh::new();

        for i in 0..8 {
            let point = SpectrumPoint {
                frequency_hz: 2.4e9 + i as f64 * 10e6,
                amplitude_dbm: -70.0,
            };
            let osc = RfOscillator::from_spectrum_bin(&point, 10e6, i as f64 * 0.1, 0.5);
            mesh.add(osc);
        }

        let initial_coherence = mesh.coherence();
        for _ in 0..500 {
            mesh.sync(0.01);
        }

        assert!(mesh.coherence() > initial_coherence,
            "Malha RF deve sincronizar: {} > {}", mesh.coherence(), initial_coherence);
    }

    #[test]
    fn haversine_distance_test() {
        // Distância aproximada entre São Paulo e Rio de Janeiro
        let dist = haversine_distance(-23.5505, -46.6333, -22.9068, -43.1729);
        assert!(dist > 300.0 && dist < 400.0, "Distância SP-RJ: {} km", dist);
    }
}
