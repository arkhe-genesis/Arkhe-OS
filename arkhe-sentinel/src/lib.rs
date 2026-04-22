//! # Arkhe Sentinela
//!
//! ANEXO CX — O Sentinela de Espectro
//!
//! Driver SCPI para o HAROGIC PXN-90, bridge espectral → Multivector,
//! detector de anomalias RF via Clifford, e extensão K6O para o domínio
//! da frequência.
//!
//! > *"O Sentinela não dorme. Ele escuta o silêncio entre as portadoras."*
//! > — O Ferreiro

pub mod driver;
pub mod spectrum_bridge;
pub mod rf_anomaly;
pub mod k6o_rf;

use thiserror::Error;

/// Erros do Sentinela
#[derive(Error, Debug, Clone)]
pub enum SentinelError {
    #[error("Comunicação SCPI falhou: {0}")]
    ScpiError(String),

    #[error("Timeout na leitura de espectro após {0}ms")]
    SpectrumTimeout(u64),

    #[error("Dados IQ malformados: esperado {expected} amostras, recebido {actual}")]
    IqDataMalformed { expected: usize, actual: usize },

    #[error("Bin FFT fora dos limites: {bin} (max {max})")]
    BinOutOfBounds { bin: usize, max: usize },

    #[error("Anomalia detectada: score={score:.2}, threshold={threshold:.2}")]
    AnomalyDetected { score: f64, threshold: f64 },

    #[error("Hardware não responde: {0}")]
    HardwareOffline(String),
}

pub type SentinelResult<T> = Result<T, SentinelError>;

/// Configuração do Sentinela
#[derive(Clone, Debug)]
pub struct SentinelConfig {
    /// Endereço IP do PXN-90 (ou /dev/ttyUSB0 para serial)
    pub device_address: String,
    /// Porta SCPI (5025 para TCP, padrão)
    pub scpi_port: u16,
    /// Frequência central inicial (Hz)
    pub center_freq: f64,
    /// Span inicial (Hz)
    pub span: f64,
    /// RBW (Hz)
    pub rbw: f64,
    /// Número de pontos do trace
    pub trace_points: usize,
    /// Threshold de anomalia (dB acima do baseline)
    pub anomaly_threshold_db: f64,
    /// Modo: Spectrum ou IQ
    pub mode: AcquisitionMode,
}

impl Default for SentinelConfig {
    fn default() -> Self {
        Self {
            device_address: "192.168.1.100".to_string(),
            scpi_port: 5025,
            center_freq: 2.435e9, // 2.435 GHz (WiFi canal 6)
            span: 50.0e6,         // 50 MHz
            rbw: 120.0e3,         // 120 kHz
            trace_points: 4096,
            anomaly_threshold_db: 10.0,
            mode: AcquisitionMode::Spectrum,
        }
    }
}

/// Modo de aquisição
#[derive(Clone, Debug, Copy, PartialEq)]
pub enum AcquisitionMode {
    /// Modo espectro (amplitude vs frequência)
    Spectrum,
    /// Modo IQ (I + Q samples)
    IqStream,
    /// Modo Real-Time FFT (gapless)
    RealTime,
}

/// Um ponto do espectro
#[derive(Clone, Debug, Copy)]
pub struct SpectrumPoint {
    pub frequency_hz: f64,
    pub amplitude_dbm: f64,
}

/// Amostra IQ
#[derive(Clone, Debug, Copy)]
pub struct IqSample {
    pub i: f64,
    pub q: f64,
    pub timestamp_ns: u64,
}

impl IqSample {
    /// Amplitude
    pub fn amplitude(&self) -> f64 {
        (self.i * self.i + self.q * self.q).sqrt()
    }

    /// Fase (radianos)
    pub fn phase(&self) -> f64 {
        self.q.atan2(self.i)
    }

    /// Potência em dBm (assumindo 50Ω, referência 1mW)
    pub fn power_dbm(&self) -> f64 {
        let power_watts = self.amplitude().powi(2) / 50.0;
        10.0 * power_watts.log10() + 30.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn iq_sample_math() {
        let sample = IqSample { i: 1.0, q: 0.0, timestamp_ns: 0 };
        assert!((sample.amplitude() - 1.0).abs() < 1e-10);
        assert!(sample.phase().abs() < 1e-10);

        let sample45 = IqSample { i: 1.0, q: 1.0, timestamp_ns: 0 };
        assert!((sample45.phase() - std::f64::consts::PI / 4.0).abs() < 1e-10);
    }
}
