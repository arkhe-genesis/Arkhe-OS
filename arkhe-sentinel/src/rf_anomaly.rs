//! # rf_anomaly.rs
//!
//! Detector de anomalias no espectro RF usando álgebra de Clifford.
//!
/// O detector mantém uma "assinatura de baseline" (Multivector de referência)
/// e compara cada nova leitura com ela via Produto Geométrico. Anomalias são
/// detectadas quando a distância geométrica excede um threshold adaptativo.
//!
//! > *"O normal tem uma forma. O anômalo distorce essa forma.
//! > O Inquisidor vê a distorção antes que ela se torne ameaça."*

use crate::{SentinelResult, SpectrumPoint, IqSample};
use crate::spectrum_bridge::SpectrumBridge;
use arkhe_rust_core::Multivector;

/// Veredito do Inquisidor RF
#[derive(Clone, Debug, Copy, PartialEq)]
pub enum RfVerdict {
    /// Espectro dentro dos parâmetros normais
    Allow,
    /// Anomalia detectada — investigar
    Investigate,
    /// Ameaça confirmada — bloquear/isolar
    Deny,
}

impl std::fmt::Display for RfVerdict {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            RfVerdict::Allow => write!(f, "ALLOW"),
            RfVerdict::Investigate => write!(f, "INVESTIGATE"),
            RfVerdict::Deny => write!(f, "DENY"),
        }
    }
}

/// Resultado da análise de anomalia
#[derive(Clone, Debug)]
pub struct AnomalyReport {
    pub verdict: RfVerdict,
    pub anomaly_score: f64,
    pub threshold: f64,
    pub baseline_distance: f64,
    pub spectral_signature: Multivector,
    pub frequency_peaks: Vec<(f64, f64)>, // (freq_hz, amplitude_dbm)
    pub description: String,
}

/// Detector de anomalias RF
pub struct RfAnomalyDetector {
    bridge: SpectrumBridge,
    /// Assinatura de baseline (normal)
    baseline: Option<Multivector>,
    /// Threshold de detecção (distância geométrica)
    threshold: f64,
    /// Fator de adaptação do baseline (EWMA)
    alpha: f64,
    /// Número de amostras para estabelecer baseline
    baseline_samples_required: usize,
    /// Amostras coletadas para baseline
    baseline_samples: Vec<Multivector>,
    /// Histórico de scores para adaptação dinâmica
    score_history: Vec<f64>,
}

impl RfAnomalyDetector {
    /// Cria um novo detector
    pub fn new(bridge: SpectrumBridge, threshold: f64) -> Self {
        Self {
            bridge,
            baseline: None,
            threshold,
            alpha: 0.1,
            baseline_samples_required: 10,
            baseline_samples: Vec::new(),
            score_history: Vec::with_capacity(100),
        }
    }

    /// Alimenta uma leitura de espectro e retorna veredito
    pub fn analyze_spectrum(&mut self, points: &[SpectrumPoint]) -> SentinelResult<AnomalyReport> {
        let mv = self.bridge.spectrum_to_multivector(points)?;

        // Se ainda não tem baseline, acumula amostras
        if self.baseline.is_none() {
            self.baseline_samples.push(mv);

            if self.baseline_samples.len() >= self.baseline_samples_required {
                self.establish_baseline();
                println!("[SENTINELA] Baseline estabelecido com {} amostras", self.baseline_samples.len());
            }

            return Ok(AnomalyReport {
                verdict: RfVerdict::Allow,
                anomaly_score: 0.0,
                threshold: self.threshold,
                baseline_distance: 0.0,
                spectral_signature: mv,
                frequency_peaks: Vec::new(),
                description: "Coletando baseline...".to_string(),
            });
        }

        let baseline = self.baseline.as_ref().unwrap();

        // Calcula distância geométrica entre assinatura atual e baseline
        let distance = geometric_distance(baseline, &mv);

        // Enconca picos espectrais anômalos
        let peaks = self.find_anomalous_peaks(points, baseline);

        // Calcula score composto
        let peak_score = (peaks.len() as f64 * 2.0).min(10.0);
        let distance_score = (distance * 10.0).min(10.0);
        let anomaly_score = (peak_score + distance_score) / 2.0;

        // Adapta threshold baseado no histórico
        self.score_history.push(anomaly_score);
        if self.score_history.len() > 100 {
            self.score_history.remove(0);
        }

        let adaptive_threshold = self.calculate_adaptive_threshold();

        // Veredito
        let verdict = if anomaly_score > adaptive_threshold * 1.5 {
            RfVerdict::Deny
        } else if anomaly_score > adaptive_threshold {
            RfVerdict::Investigate
        } else {
            // Atualiza baseline suavemente (EWMA)
            self.update_baseline(&mv);
            RfVerdict::Allow
        };

        let description = self.generate_description(verdict, &peaks, distance, anomaly_score);

        Ok(AnomalyReport {
            verdict,
            anomaly_score,
            threshold: adaptive_threshold,
            baseline_distance: distance,
            spectral_signature: mv,
            frequency_peaks: peaks,
            description,
        })
    }

    /// Alimenta amostras IQ
    pub fn analyze_iq(&mut self, samples: &[IqSample]) -> SentinelResult<AnomalyReport> {
        let mv = self.bridge.iq_to_multivector(samples)?;

        if self.baseline.is_none() {
            self.baseline_samples.push(mv);
            if self.baseline_samples.len() >= self.baseline_samples_required {
                self.establish_baseline();
            }
            return Ok(AnomalyReport {
                verdict: RfVerdict::Allow,
                anomaly_score: 0.0,
                threshold: self.threshold,
                baseline_distance: 0.0,
                spectral_signature: mv,
                frequency_peaks: Vec::new(),
                description: "Coletando baseline IQ...".to_string(),
            });
        }

        let baseline = self.baseline.as_ref().unwrap();
        let distance = geometric_distance(baseline, &mv);

        // Para IQ, focamos em métricas de modulação anômala
        let phase_coherence = spectrum_bridge_phase_coherence(samples);
        let crest = spectrum_bridge_crest_factor(samples);

        let anomaly_score = if phase_coherence < 0.3 {
            // Baixa coerência de fase pode indicar jamming ou spoofing
            distance * 2.0 + (0.5 - phase_coherence) * 5.0
        } else {
            distance * 2.0
        };

        let adaptive_threshold = self.calculate_adaptive_threshold();

        let verdict = if anomaly_score > adaptive_threshold * 1.5 {
            RfVerdict::Deny
        } else if anomaly_score > adaptive_threshold {
            RfVerdict::Investigate
        } else {
            self.update_baseline(&mv);
            RfVerdict::Allow
        };

        let description = format!(
            "IQ: coerência={:.3}, crest={:.2}, dist={:.3}, score={:.2}",
            phase_coherence, crest, distance, anomaly_score
        );

        Ok(AnomalyReport {
            verdict,
            anomaly_score,
            threshold: adaptive_threshold,
            baseline_distance: distance,
            spectral_signature: mv,
            frequency_peaks: Vec::new(),
            description,
        })
    }

    /// Estabelece baseline a partir das amostras coletadas
    fn establish_baseline(&mut self) {
        if self.baseline_samples.is_empty() {
            return;
        }

        // Média dos Multivectors de baseline
        let mut avg = Multivector::zero();
        for mv in &self.baseline_samples {
            for i in 0..16 {
                avg.data[i] += mv.data[i];
            }
        }

        let n = self.baseline_samples.len() as f64;
        for i in 0..16 {
            avg.data[i] /= n;
        }

        // Normaliza
        let norm_sq = avg.norm_squared();
        if norm_sq > 1e-20 {
            let norm = norm_sq.sqrt();
            for i in 0..16 {
                avg.data[i] /= norm;
            }
        }

        self.baseline = Some(avg);
        self.baseline_samples.clear();
    }

    /// Atualiza baseline com EWMA (Exponentially Weighted Moving Average)
    fn update_baseline(&mut self, new_mv: &Multivector) {
        if let Some(ref mut baseline) = self.baseline {
            for i in 0..16 {
                baseline.data[i] = self.alpha * new_mv.data[i]
                    + (1.0 - self.alpha) * baseline.data[i];
            }

            // Re-normaliza
            let norm_sq = baseline.norm_squared();
            if norm_sq > 1e-20 {
                let norm = norm_sq.sqrt();
                for i in 0..16 {
                    baseline.data[i] /= norm;
                }
            }
        }
    }

    /// Calcula threshold adaptativo baseado no histórico
    fn calculate_adaptive_threshold(&self) -> f64 {
        if self.score_history.len() < 5 {
            return self.threshold;
        }

        let mean = self.score_history.iter().sum::<f64>() / self.score_history.len() as f64;
        let variance = self.score_history.iter()
            .map(|s| (s - mean).powi(2))
            .sum::<f64>() / self.score_history.len() as f64;
        let std_dev = variance.sqrt();

        // Threshold = média + 3σ (regra dos 3 sigmas)
        let adaptive = mean + 3.0 * std_dev;
        adaptive.max(self.threshold * 0.5).min(self.threshold * 3.0)
    }

    /// Encontra picos espectrais que divergem do baseline
    fn find_anomalous_peaks(&self, points: &[SpectrumPoint], _baseline: &Multivector) -> Vec<(f64, f64)> {
        // Simples: encontra picos locais acima de um threshold
        let threshold_db = -70.0; // dBm
        let mut peaks = Vec::new();

        for window in points.windows(3) {
            if window[1].amplitude_dbm > window[0].amplitude_dbm
                && window[1].amplitude_dbm > window[2].amplitude_dbm
                && window[1].amplitude_dbm > threshold_db {
                peaks.push((window[1].frequency_hz, window[1].amplitude_dbm));
            }
        }

        // Mantém apenas os 5 picos mais fortes
        peaks.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
        peaks.truncate(5);

        peaks
    }

    /// Gera descrição textual do veredito
    fn generate_description(&self, verdict: RfVerdict, peaks: &[(f64, f64)],
                           distance: f64, score: f64) -> String {
        match verdict {
            RfVerdict::Allow => {
                format!("Espectro normal. Distância baseline: {:.4}. Score: {:.2}", distance, score)
            }
            RfVerdict::Investigate => {
                let peak_str = if peaks.is_empty() {
                    "Nenhum pico anômalo detectado.".to_string()
                } else {
                    format!("Picos suspeitos: {}.", peaks.iter()
                        .map(|(f, a)| format!("{:.3} MHz @ {:.1} dBm", f / 1e6, a))
                        .collect::<Vec<_>>()
                        .join(", "))
                };
                format!("ANOMALIA DETECTADA (Investigar). Score: {:.2}. {} Distância: {:.4}",
                    score, peak_str, distance)
            }
            RfVerdict::Deny => {
                let peak_str = if peaks.is_empty() {
                    "Padrão espectral anômalo (sem picos isolados).".to_string()
                } else {
                    format!("Picos críticos: {}.", peaks.iter()
                        .map(|(f, a)| format!("{:.3} MHz @ {:.1} dBm", f / 1e6, a))
                        .collect::<Vec<_>>()
                        .join(", "))
                };
                format!("AMEAÇA CONFIRMADA (Deny). Score: {:.2}. {} Distância: {:.4}",
                    score, peak_str, distance)
            }
        }
    }
}

// Helper wrappers since the original code tried to access them via a crate path that doesn't exist this way or as functions
fn spectrum_bridge_phase_coherence(samples: &[IqSample]) -> f64 {
    // In a real scenario we'd use the ones from spectrum_bridge, but they are not public.
    // For now, let's assume they are available or reimplement.
    let phases: Vec<f64> = samples.iter().map(|s| s.phase()).collect();
    let sum_cos: f64 = phases.iter().map(|p| p.cos()).sum();
    let sum_sin: f64 = phases.iter().map(|p| p.sin()).sum();
    let n = phases.len() as f64;
    let r = ((sum_cos / n).powi(2) + (sum_sin / n).powi(2)).sqrt();
    r.clamp(0.0, 1.0)
}

fn spectrum_bridge_crest_factor(samples: &[IqSample]) -> f64 {
    let peak = samples.iter().map(|s| s.amplitude()).fold(0.0f64, |a, b| a.max(b));
    let rms = (samples.iter().map(|s| s.amplitude().powi(2)).sum::<f64>() / samples.len() as f64).sqrt();
    if rms < 1e-20 { 1.0 } else { (peak / rms).clamp(1.0, 100.0) }
}

/// Distância geométrica entre dois Multivectors (norma da diferença)
fn geometric_distance(a: &Multivector, b: &Multivector) -> f64 {
    let mut diff = Multivector::zero();
    for i in 0..16 {
        diff.data[i] = a.data[i] - b.data[i];
    }
    diff.norm_squared().sqrt()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_bridge() -> SpectrumBridge {
        SpectrumBridge::new(4096, 2.435e9, 50.0e6)
    }

    fn make_normal_spectrum() -> Vec<SpectrumPoint> {
        (0..4096)
            .map(|i| {
                let freq = 2.4e9 + i as f64 * 50.0e6 / 4096.0;
                let amp = -90.0 + 5.0 * (-((i as f64 - 2048.0) / 500.0).powi(2)).exp();
                SpectrumPoint { frequency_hz: freq, amplitude_dbm: amp }
            })
            .collect()
    }

    fn make_anomalous_spectrum() -> Vec<SpectrumPoint> {
        let mut points = make_normal_spectrum();
        // Adiciona um pico anômalo forte
        for i in 1900..2100 {
            if i < points.len() {
                points[i].amplitude_dbm += 30.0; // +30 dBm spike
            }
        }
        points
    }

    #[test]
    fn detector_baseline_and_detect() {
        let bridge = make_bridge();
        let mut detector = RfAnomalyDetector::new(bridge, 2.5);

        // Alimenta 10 amostras normais para estabelecer baseline
        for _ in 0..10 {
            let spectrum = make_normal_spectrum();
            let report = detector.analyze_spectrum(&spectrum).unwrap();
            assert_eq!(report.verdict, RfVerdict::Allow);
        }

        // Agora alimenta uma anômala
        let anomalous = make_anomalous_spectrum();
        let report = detector.analyze_spectrum(&anomalous).unwrap();

        println!("Veredito: {}", report.verdict);
        println!("Score: {:.2}", report.anomaly_score);
        println!("Descrição: {}", report.description);

        assert!(report.verdict != RfVerdict::Allow, "Deveria detectar anomalia!");
        assert!(report.anomaly_score > 0.0);
    }

    #[test]
    fn geometric_distance_test() {
        let a = Multivector::from_scalar(1.0);
        let b = Multivector::from_scalar(0.0);
        let d = geometric_distance(&a, &b);
        assert!((d - 1.0).abs() < 1e-6);
    }
}
