//! # spectrum_bridge.rs
//!
//! Converte traces de espectro (amplitude vs frequência) e amostras IQ
//! em Multivectors Clifford. Cada bin FFT ou banda espectral vira uma
//! componente do multivetor, criando uma "assinatura espectral" única.
//!
//! > *"O espectro é uma sinfonia de 4096 notas. A Ponte a condensa
//! > em 16 acordes que o Inquisidor pode julgar."*

use crate::{SentinelResult, SpectrumPoint, IqSample};
use arkhe_rust_core::Multivector;

/// Bridge entre dados espectrais e álgebra de Clifford
pub struct SpectrumBridge {
    /// Número de bins FFT por componente Clifford
    bins_per_component: usize,
    /// Frequência central de referência (Hz)
    center_freq: f64,
    /// Span de referência (Hz)
    span: f64,
}

impl SpectrumBridge {
    /// Cria uma nova Ponte Espectral
    ///
    /// `trace_points` é o número total de pontos do trace (ex: 4096)
    pub fn new(trace_points: usize, center_freq: f64, span: f64) -> Self {
        let bins_per_component = trace_points / 16;
        Self {
            bins_per_component: bins_per_component.max(1),
            center_freq,
            span,
        }
    }

    /// Converte um trace de espectro em Multivector
    ///
    /// Estratégia:
    /// 1. Divide o espectro em 16 bandas (uma por componente Clifford)
    /// 2. Para cada banda, calcula: potência média (dBm → linear),
    ///    frequência central, e largura de banda efetiva
    /// 3. Mapeia: escalar = potência total, vetor = centroides de frequência,
    ///    bivector = larguras de banda, trivector = assimetrias
    pub fn spectrum_to_multivector(&self, points: &[SpectrumPoint]) -> SentinelResult<Multivector> {
        if points.len() < 16 {
            // Interpola ou preenche com zeros se necessário
            return self.interpolate_and_convert(points);
        }

        let mut mv = Multivector::zero();

        // 1. ESCALAR (componente 0): potência total do espectro
        let total_power_linear: f64 = points.iter()
            .map(|p| dbm_to_linear(p.amplitude_dbm))
            .sum();
        mv.data[0] = total_power_linear.log10().clamp(-10.0, 10.0);

        // 2. VETOR (componentes 1-4): centroides de 4 bandas principais
        let band_width = points.len() / 4;
        for band in 0..4 {
            let start = band * band_width;
            let end = ((band + 1) * band_width).min(points.len());
            let band_points = &points[start..end];

            // Centroide de frequência ponderado por potência
            let (weighted_freq, total_power) = band_points.iter()
                .fold((0.0, 0.0), |(wf, tp), p| {
                    let lin = dbm_to_linear(p.amplitude_dbm);
                    (wf + p.frequency_hz * lin, tp + lin)
                });

            let centroid = if total_power > 0.0 {
                (weighted_freq / total_power - self.center_freq) / (self.span / 2.0)
            } else {
                0.0
            };

            mv.data[1 + band] = centroid.clamp(-1.0, 1.0);
        }

        // 3. BIVECTOR (componentes 5-10): larguras de banda efetivas
        // e correlações entre bandas adjacentes
        for band in 0..6 {
            let start = band * self.bins_per_component;
            let end = ((band + 1) * self.bins_per_component).min(points.len());
            let band_points = &points[start..end];

            // Largura de banda efetiva (desvio padrão das frequências)
            let freqs: Vec<f64> = band_points.iter().map(|p| p.frequency_hz).collect();
            let amps: Vec<f64> = band_points.iter()
                .map(|p| dbm_to_linear(p.amplitude_dbm))
                .collect();

            let bw_eff = effective_bandwidth(&freqs, &amps);
            mv.data[5 + band] = (bw_eff / self.span).clamp(0.0, 1.0);
        }

        // 4. TRIVECTOR (componentes 11-14): assimetria e curtose espectral
        for band in 0..4 {
            let start = band * band_width;
            let end = ((band + 1) * band_width).min(points.len());
            let band_points = &points[start..end];

            let skew = spectral_skewness(band_points);
            mv.data[11 + band] = skew.clamp(-1.0, 1.0);
        }

        // 5. PSEUDOSCALAR (componente 15): coerência espectral global
        // Medida de quão "organizado" o espectro está
        mv.data[15] = spectral_coherence(points);

        // Normaliza
        let norm_sq = mv.norm_squared();
        if norm_sq > 1e-20 {
            let norm = norm_sq.sqrt();
            for i in 0..16 {
                mv.data[i] /= norm;
            }
        }

        Ok(mv)
    }

    /// Converte amostras IQ em Multivector
    ///
    /// Estratégia:
    /// 1. Calcula estatísticas de I e Q
    /// 2. Extrai 16 features: médias, variâncias, correlações, fases
    pub fn iq_to_multivector(&self, samples: &[IqSample]) -> SentinelResult<Multivector> {
        if samples.is_empty() {
            return Ok(Multivector::zero());
        }

        let mut mv = Multivector::zero();

        let n = samples.len() as f64;

        // Estatísticas básicas
        let mean_i = samples.iter().map(|s| s.i).sum::<f64>() / n;
        let mean_q = samples.iter().map(|s| s.q).sum::<f64>() / n;
        let var_i = samples.iter().map(|s| (s.i - mean_i).powi(2)).sum::<f64>() / n;
        let var_q = samples.iter().map(|s| (s.q - mean_q).powi(2)).sum::<f64>() / n;
        let cov_iq = samples.iter().map(|s| (s.i - mean_i) * (s.q - mean_q)).sum::<f64>() / n;

        // Fase média
        let mean_phase = samples.iter().map(|s| s.phase()).sum::<f64>() / n;
        let phase_var = samples.iter()
            .map(|s| {
                let diff = (s.phase() - mean_phase).rem_euclid(std::f64::consts::TAU);
                let diff = if diff > std::f64::consts::PI { diff - std::f64::consts::TAU } else { diff };
                diff.powi(2)
            })
            .sum::<f64>() / n;

        // Amplitude média e variância
        let mean_amp = samples.iter().map(|s| s.amplitude()).sum::<f64>() / n;
        let var_amp = samples.iter().map(|s| (s.amplitude() - mean_amp).powi(2)).sum::<f64>() / n;

        // Mapeia para componentes
        mv.data[0] = mean_amp;                                    // escalar = amplitude média
        mv.data[1] = mean_i;                                      // e1 = média I
        mv.data[2] = mean_q;                                      // e2 = média Q
        mv.data[3] = mean_phase / std::f64::consts::PI;           // e3 = fase média normalizada
        mv.data[4] = (var_i + var_q).sqrt();                      // e0 = desvio padrão total
        mv.data[5] = var_i;                                       // e12 = variância I
        mv.data[6] = var_q;                                       // e13 = variância Q
        mv.data[7] = cov_iq;                                      // e23 = covariância IQ
        mv.data[8] = phase_var / std::f64::consts::PI;            // e01 = variância de fase
        mv.data[9] = mean_amp.log10().clamp(-5.0, 5.0);           // e02 = log amplitude
        mv.data[10] = (mean_i * mean_q).signum();                 // e03 = sinal do produto
        mv.data[11] = spectral_flatness_iq(samples);              // e123 = flatness espectral
        mv.data[12] = crest_factor(samples);                      // e012 = crest factor
        mv.data[13] = correlation_iq(samples);                    // e013 = correlação I-Q
        mv.data[14] = instantaneous_bandwidth(samples);           // e023 = largura de banda instantânea
        mv.data[15] = phase_coherence(samples);                   // pseudoscalar = coerência de fase

        // Normaliza
        let norm_sq = mv.norm_squared();
        if norm_sq > 1e-20 {
            let norm = norm_sq.sqrt();
            for i in 0..16 {
                mv.data[i] /= norm;
            }
        }

        Ok(mv)
    }

    /// Interpola um trace pequeno para 16 pontos e converte
    fn interpolate_and_convert(&self, points: &[SpectrumPoint]) -> SentinelResult<Multivector> {
        // Interpolação linear simples
        let mut interpolated = vec![SpectrumPoint { frequency_hz: 0.0, amplitude_dbm: -120.0 }; 16];

        for i in 0..16 {
            let t = i as f64 / 15.0;
            let idx_f = t * (points.len() - 1) as f64;
            let idx_low = idx_f.floor() as usize;
            let idx_high = idx_f.ceil() as usize;
            let frac = idx_f - idx_low as f64;

            if idx_high >= points.len() {
                interpolated[i] = points[points.len() - 1];
            } else {
                let amp = points[idx_low].amplitude_dbm * (1.0 - frac)
                        + points[idx_high].amplitude_dbm * frac;
                let freq = points[idx_low].frequency_hz * (1.0 - frac)
                         + points[idx_high].frequency_hz * frac;
                interpolated[i] = SpectrumPoint { frequency_hz: freq, amplitude_dbm: amp };
            }
        }

        self.spectrum_to_multivector(&interpolated)
    }
}

// ============================================================
// Funções auxiliares
// ============================================================

/// Converte dBm para potência linear (mW)
fn dbm_to_linear(dbm: f64) -> f64 {
    10.0f64.powf(dbm / 10.0)
}

/// Largura de banda efetiva (desvio padrão ponderado)
fn effective_bandwidth(freqs: &[f64], powers: &[f64]) -> f64 {
    let total_power: f64 = powers.iter().sum();
    if total_power < 1e-20 {
        return 0.0;
    }

    let mean_freq: f64 = freqs.iter().zip(powers.iter())
        .map(|(f, p)| f * p)
        .sum::<f64>() / total_power;

    let variance: f64 = freqs.iter().zip(powers.iter())
        .map(|(f, p)| p * (f - mean_freq).powi(2))
        .sum::<f64>() / total_power;

    variance.sqrt()
}

/// Assimetria espectral (skewness)
fn spectral_skewness(points: &[SpectrumPoint]) -> f64 {
    let n = points.len() as f64;
    let freqs: Vec<f64> = points.iter().map(|p| p.frequency_hz).collect();
    let mean = freqs.iter().sum::<f64>() / n;

    let variance = freqs.iter().map(|f| (f - mean).powi(2)).sum::<f64>() / n;
    let std_dev = variance.sqrt();

    if std_dev < 1e-10 {
        return 0.0;
    }

    let skewness = freqs.iter().map(|f| ((f - mean) / std_dev).powi(3)).sum::<f64>() / n;
    skewness.clamp(-3.0, 3.0)
}

/// Coerência espectral (medida de organização)
fn spectral_coherence(points: &[SpectrumPoint]) -> f64 {
    // Razão entre potência do pico e potência total
    let max_power = points.iter()
        .map(|p| dbm_to_linear(p.amplitude_dbm))
        .fold(0.0f64, |a, b| a.max(b));

    let total_power: f64 = points.iter()
        .map(|p| dbm_to_linear(p.amplitude_dbm))
        .sum();

    if total_power < 1e-20 {
        return 0.0;
    }

    (max_power / total_power * points.len() as f64).clamp(0.0, 1.0)
}

/// Flatness espectral (razão entre média geométrica e aritmética)
fn spectral_flatness_iq(samples: &[IqSample]) -> f64 {
    let amps: Vec<f64> = samples.iter().map(|s| s.amplitude()).collect();

    let arithmetic_mean = amps.iter().sum::<f64>() / amps.len() as f64;
    if arithmetic_mean < 1e-20 {
        return 0.0;
    }

    let log_sum: f64 = amps.iter()
        .map(|a| if *a > 0.0 { a.ln() } else { -50.0 })
        .sum();
    let geometric_mean = (log_sum / amps.len() as f64).exp();

    (geometric_mean / arithmetic_mean).clamp(0.0, 1.0)
}

/// Crest factor (pico / RMS)
fn crest_factor(samples: &[IqSample]) -> f64 {
    let peak = samples.iter().map(|s| s.amplitude()).fold(0.0f64, |a, b| a.max(b));
    let rms = (samples.iter().map(|s| s.amplitude().powi(2)).sum::<f64>() / samples.len() as f64).sqrt();

    if rms < 1e-20 {
        return 1.0;
    }

    (peak / rms).clamp(1.0, 100.0)
}

/// Correlação entre I e Q
fn correlation_iq(samples: &[IqSample]) -> f64 {
    let n = samples.len() as f64;
    let mean_i = samples.iter().map(|s| s.i).sum::<f64>() / n;
    let mean_q = samples.iter().map(|s| s.q).sum::<f64>() / n;

    let cov = samples.iter().map(|s| (s.i - mean_i) * (s.q - mean_q)).sum::<f64>() / n;
    let var_i = samples.iter().map(|s| (s.i - mean_i).powi(2)).sum::<f64>() / n;
    let var_q = samples.iter().map(|s| (s.q - mean_q).powi(2)).sum::<f64>() / n;

    let denom = (var_i * var_q).sqrt();
    if denom < 1e-20 {
        return 0.0;
    }

    (cov / denom).clamp(-1.0, 1.0)
}

/// Largura de banda instantânea (estimada pela variância de fase)
fn instantaneous_bandwidth(samples: &[IqSample]) -> f64 {
    let phases: Vec<f64> = samples.iter().map(|s| s.phase()).collect();
    let _n = phases.len() as f64;

    // Diferenças de fase (frequência instantânea)
    let diffs: Vec<f64> = phases.windows(2)
        .map(|w| {
            let mut d = w[1] - w[0];
            if d > std::f64::consts::PI { d -= std::f64::consts::TAU; }
            if d < -std::f64::consts::PI { d += std::f64::consts::TAU; }
            d
        })
        .collect();

    let mean_diff = diffs.iter().sum::<f64>() / diffs.len() as f64;
    let variance = diffs.iter().map(|d| (d - mean_diff).powi(2)).sum::<f64>() / diffs.len() as f64;

    variance.sqrt().clamp(0.0, std::f64::consts::PI)
}

/// Coerência de fase (quão constante é a fase ao longo do tempo)
fn phase_coherence(samples: &[IqSample]) -> f64 {
    let phases: Vec<f64> = samples.iter().map(|s| s.phase()).collect();

    // Vetor de ordem (Kuramoto simplificado)
    let sum_cos: f64 = phases.iter().map(|p| p.cos()).sum();
    let sum_sin: f64 = phases.iter().map(|p| p.sin()).sum();

    let n = phases.len() as f64;
    let r = ((sum_cos / n).powi(2) + (sum_sin / n).powi(2)).sqrt();

    r.clamp(0.0, 1.0)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_test_spectrum() -> Vec<SpectrumPoint> {
        (0..4096)
            .map(|i| {
                let freq = 2.4e9 + i as f64 * 50.0e6 / 4096.0;
                let amp = -80.0 + 20.0 * (-((i as f64 - 2048.0) / 200.0).powi(2)).exp();
                SpectrumPoint { frequency_hz: freq, amplitude_dbm: amp }
            })
            .collect()
    }

    #[test]
    fn spectrum_to_mv() {
        let bridge = SpectrumBridge::new(4096, 2.435e9, 50.0e6);
        let spectrum = make_test_spectrum();
        let mv = bridge.spectrum_to_multivector(&spectrum).unwrap();

        let norm_sq = mv.norm_squared();
        assert!((norm_sq - 1.0).abs() < 1e-6, "Norma deve ser 1 após normalização: {}", norm_sq);
    }

    #[test]
    fn iq_to_mv() {
        let bridge = SpectrumBridge::new(4096, 2.435e9, 50.0e6);
        let samples: Vec<IqSample> = (0..1024)
            .map(|i| IqSample {
                i: (i as f64 * 0.01).cos(),
                q: (i as f64 * 0.01).sin(),
                timestamp_ns: i as u64 * 16,
            })
            .collect();

        let mv = bridge.iq_to_multivector(&samples).unwrap();
        let norm_sq = mv.norm_squared();
        assert!((norm_sq - 1.0).abs() < 1e-6);
    }

    #[test]
    fn phase_coherence_test() {
        // Amostras com fase constante → alta coerência
        let coherent: Vec<IqSample> = (0..100)
            .map(|i| IqSample {
                i: 1.0,
                q: 0.0,
                timestamp_ns: i as u64 * 16,
            })
            .collect();

        let c1 = phase_coherence(&coherent);
        assert!(c1 > 0.99, "Fase constante deve ter coerência ~1.0: {}", c1);

        // Amostras com fase aleatória → baixa coerência
        let random: Vec<IqSample> = (0..100)
            .map(|i| IqSample {
                i: (i as f64 * 1.57).cos(),
                q: (i as f64 * 1.57).sin(),
                timestamp_ns: i as u64 * 16,
            })
            .collect();

        let c2 = phase_coherence(&random);
        assert!(c2 < c1, "Fase variável deve ter coerência menor que constante: {} < {}", c2, c1);
    }
}
