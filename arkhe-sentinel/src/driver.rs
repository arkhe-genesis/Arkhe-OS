//! # driver.rs
//!
//! Driver SCPI (Standard Commands for Programmable Instruments) para o
//! HAROGIC PXN-90. Suporta comunicação TCP (Ethernet) e Serial (USB).
//!
//! Comandos SCPI implementados:
//! • *IDN? — Identificação do instrumento
//! • :FREQuency:CENTer — Define frequência central
//! • :FREQuency:SPAN — Define span
//! • :BANDwidth:RESolution — Define RBW
//! • :TRACe:DATA? TRACE1 — Lê dados do trace
//! • :INITiate:CONTinuous — Inicia/para sweep contínuo
//! • :CALCulate:MARKer:MAXimum — Encontra pico máximo
//!
//! > *"O Sentinela fala SCPI. A Catedral ouve em Rust."*

use crate::{SentinelError, SentinelResult, SentinelConfig, SpectrumPoint, IqSample, AcquisitionMode};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;
use tokio::time::{timeout, Duration};
use std::sync::Arc;
use tokio::sync::Mutex;

/// Conexão SCPI com o PXN-90
pub struct HarogicDriver {
    config: SentinelConfig,
    stream: Option<Arc<Mutex<TcpStream>>>,
    connected: bool,
}

impl HarogicDriver {
    /// Cria um novo driver (não conecta ainda)
    pub fn new(config: SentinelConfig) -> Self {
        Self {
            config,
            stream: None,
            connected: false,
        }
    }

    /// Conecta ao PXN-90 via TCP
    pub async fn connect(&mut self) -> SentinelResult<()> {
        let addr = format!("{}:{}", self.config.device_address, self.config.scpi_port);

        println!("[SENTINELA] Conectando a {}...", addr);

        let stream = timeout(
            Duration::from_secs(5),
            TcpStream::connect(&addr)
        )
        .await
        .map_err(|_| SentinelError::HardwareOffline(format!("Timeout ao conectar a {}", addr)))?
        .map_err(|e| SentinelError::ScpiError(format!("Falha TCP: {}", e)))?;

        self.stream = Some(Arc::new(Mutex::new(stream)));
        self.connected = true;

        // Identifica o instrumento
        let idn = self.query("*IDN?").await?;
        println!("[SENTINELA] Conectado: {}", idn.trim());

        // Reseta para estado conhecido
        self.command("*RST").await?;
        tokio::time::sleep(Duration::from_millis(500)).await;

        // Configura modo
        match self.config.mode {
            AcquisitionMode::Spectrum => {
                self.command(":INSTrument:SELect SA").await?;
            }
            AcquisitionMode::IqStream => {
                self.command(":INSTrument:SELect IQ").await?;
            }
            AcquisitionMode::RealTime => {
                self.command(":INSTrument:SELect RTSA").await?;
            }
        }

        // Configura frequência
        self.set_frequency(self.config.center_freq).await?;
        self.set_span(self.config.span).await?;
        self.set_rbw(self.config.rbw).await?;

        println!("[SENTINELA] Configuração completa. Centro: {:.3} MHz, Span: {:.3} MHz, RBW: {:.1} kHz",
            self.config.center_freq / 1e6,
            self.config.span / 1e6,
            self.config.rbw / 1e3
        );

        Ok(())
    }

    /// Desconecta
    pub async fn disconnect(&mut self) -> SentinelResult<()> {
        if self.connected {
            self.command(":INITiate:CONTinuous OFF").await.ok();
            self.stream = None;
            self.connected = false;
            println!("[SENTINELA] Desconectado.");
        }
        Ok(())
    }

    /// Envia um comando SCPI (sem resposta)
    pub async fn command(&self, cmd: &str) -> SentinelResult<()> {
        let stream = self.stream.as_ref()
            .ok_or_else(|| SentinelError::HardwareOffline("Não conectado".to_string()))?;

        let mut s = stream.lock().await;
        let cmd_line = format!("{}\n", cmd);

        s.write_all(cmd_line.as_bytes()).await
            .map_err(|e| SentinelError::ScpiError(format!("Falha ao enviar comando: {}", e)))?;

        Ok(())
    }

    /// Envia uma query SCPI e retorna a resposta
    pub async fn query(&self, cmd: &str) -> SentinelResult<String> {
        let stream = self.stream.as_ref()
            .ok_or_else(|| SentinelError::HardwareOffline("Não conectado".to_string()))?;

        let mut s = stream.lock().await;
        let cmd_line = format!("{}\n", cmd);

        s.write_all(cmd_line.as_bytes()).await
            .map_err(|e| SentinelError::ScpiError(format!("Falha ao enviar query: {}", e)))?;

        // Lê resposta (terminada por \n)
        let mut buf = vec![0u8; 4096];
        let n = timeout(Duration::from_secs(2), s.read(&mut buf))
            .await
            .map_err(|_| SentinelError::SpectrumTimeout(2000))?
            .map_err(|e| SentinelError::ScpiError(format!("Falha ao ler resposta: {}", e)))?;

        let response = String::from_utf8_lossy(&buf[..n]).trim().to_string();
        Ok(response)
    }

    /// Define frequência central (Hz)
    pub async fn set_frequency(&self, freq_hz: f64) -> SentinelResult<()> {
        self.command(&format!(":FREQuency:CENTer {:.0} Hz", freq_hz)).await
    }

    /// Define span (Hz)
    pub async fn set_span(&self, span_hz: f64) -> SentinelResult<()> {
        self.command(&format!(":FREQuency:SPAN {:.0} Hz", span_hz)).await
    }

    /// Define RBW (Hz)
    pub async fn set_rbw(&self, rbw_hz: f64) -> SentinelResult<()> {
        self.command(&format!(":BANDwidth:RESolution {:.0} Hz", rbw_hz)).await
    }

    /// Lê um trace completo do espectro
    ///
    /// Retorna um vetor de SpectrumPoint (frequência, amplitude dBm)
    pub async fn read_spectrum(&self) -> SentinelResult<Vec<SpectrumPoint>> {
        // Inicia sweep
        self.command(":INITiate:IMMediate").await?;

        // Aguarda sweep completar (polling *OPC?)
        let mut attempts = 0;
        loop {
            let opc = self.query("*OPC?").await?;
            if opc.trim() == "1" {
                break;
            }
            tokio::time::sleep(Duration::from_millis(50)).await;
            attempts += 1;
            if attempts > 100 {
                return Err(SentinelError::SpectrumTimeout(5000));
            }
        }

        // Lê dados do trace
        let data_str = self.query(":TRACe:DATA? TRACE1").await?;

        // Parse: dados separados por vírgula, em dBm
        let amplitudes: Vec<f64> = data_str.split(',')
            .filter_map(|s| s.trim().parse::<f64>().ok())
            .collect();

        if amplitudes.is_empty() {
            return Err(SentinelError::ScpiError("Trace vazio".to_string()));
        }

        // Calcula frequências para cada ponto
        let start_freq = self.config.center_freq - self.config.span / 2.0;
        let step = self.config.span / amplitudes.len() as f64;

        let points: Vec<SpectrumPoint> = amplitudes.iter()
            .enumerate()
            .map(|(i, &amp_dbm)| SpectrumPoint {
                frequency_hz: start_freq + i as f64 * step,
                amplitude_dbm: amp_dbm,
            })
            .collect();

        Ok(points)
    }

    /// Lê amostras IQ
    ///
    /// Em uma implementação real, usaria :READ:IQ? ou similar
    pub async fn read_iq(&self, num_samples: usize) -> SentinelResult<Vec<IqSample>> {
        // Configura aquisição IQ
        self.command(&format!(":TRACe:IQ:RLENgth {}", num_samples)).await?;
        self.command(":INITiate:IMMediate").await?;

        // Aguarda
        tokio::time::sleep(Duration::from_millis(100)).await;

        // Lê dados IQ (formato binário ou ASCII)
        let data_str = self.query(":READ:IQ?").await?;

        // Parse ASCII: I1,Q1,I2,Q2,...
        let values: Vec<f64> = data_str.split(',')
            .filter_map(|s| s.trim().parse::<f64>().ok())
            .collect();

        if values.len() < num_samples * 2 {
            return Err(SentinelError::IqDataMalformed {
                expected: num_samples,
                actual: values.len() / 2,
            });
        }

        let samples: Vec<IqSample> = values.chunks(2)
            .take(num_samples)
            .enumerate()
            .map(|(i, chunk)| IqSample {
                i: chunk[0],
                q: chunk[1],
                timestamp_ns: i as u64 * 16, // 16ns = 62.5MSPS
            })
            .collect();

        Ok(samples)
    }

    /// Encontra o pico máximo no espectro atual
    pub async fn find_peak(&self) -> SentinelResult<SpectrumPoint> {
        self.command(":CALCulate:MARKer1:MAXimum").await?;

        let freq_str = self.query(":CALCulate:MARKer1:X?").await?;
        let amp_str = self.query(":CALCulate:MARKer1:Y?").await?;

        let freq = freq_str.trim().parse::<f64>()
            .map_err(|e| SentinelError::ScpiError(format!("Falha ao parsear frequência: {}", e)))?;
        let amp = amp_str.trim().parse::<f64>()
            .map_err(|e| SentinelError::ScpiError(format!("Falha ao parsear amplitude: {}", e)))?;

        Ok(SpectrumPoint {
            frequency_hz: freq,
            amplitude_dbm: amp,
        })
    }

    /// Verifica se o hardware está respondendo
    pub async fn health_check(&self) -> SentinelResult<bool> {
        match self.query("*IDN?").await {
            Ok(idn) => {
                println!("[SENTINELA] Health check OK: {}", idn.trim());
                Ok(true)
            }
            Err(e) => {
                println!("[SENTINELA] Health check FALHOU: {}", e);
                Ok(false)
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn driver_creation() {
        let config = SentinelConfig::default();
        let driver = HarogicDriver::new(config);
        assert!(!driver.connected);
    }

    // Testes de integração requerem hardware real
    // #[tokio::test]
    // async fn test_connect() { ... }
}
