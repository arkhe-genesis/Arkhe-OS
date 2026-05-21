// arkhe-safe-core-sdk/src/planetary_sensors.rs
// Substrato 375 — Planetary Resilience Mesh: Sensor Middleware
// Canon: ∞.Ω.∇+++.375.planetary_sensors

use crate::{ArkheError, GHOST, GAP_SOVEREIGN, PHI};
use sha3::{Sha3_256, Digest};
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

/// Estrutura de um fluxo de sensor georreferenciado.
#[derive(Debug, Clone)]
pub struct SensorStream {
    pub node_id: String,           // Identificador do nó (ex: ORCID do proprietário)
    pub lat: f64,                  // Latitude
    pub lon: f64,                  // Longitude
    pub sensor_type: SensorType,   // Tipo de sensor
    pub value: f64,                // Valor medido
    pub timestamp: u64,            // Timestamp Unix em milissegundos
    pub merkle_root: [u8; 32],     // Raiz Merkle dos dados agregados
    pub signature: Vec<u8>,        // Assinatura do publicador
}

/// Tipos de sensores suportados na malha planetária.
#[derive(Debug, Clone, PartialEq)]
pub enum SensorType {
    Temperature,
    AirQuality,
    Seismic,
    Noise,
    Humidity,
    Radiation,
    Custom(String),
}

/// Middleware de sensores planetários.
pub struct PlanetarySensorMiddleware {
    published_streams: HashMap<String, Vec<SensorStream>>,
    active_subscriptions: HashMap<String, Vec<String>>, // subscriber_id -> [stream_ids]
}

impl PlanetarySensorMiddleware {
    pub fn new() -> Self {
        Self {
            published_streams: HashMap::new(),
            active_subscriptions: HashMap::new(),
        }
    }

    /// Publica um fluxo de sensor, ancorando sua Merkle root na TemporalChain.
    pub fn publish_sensor_data(
        &mut self,
        node_id: &str,
        lat: f64,
        lon: f64,
        sensor_type: SensorType,
        value: f64,
        private_key: &[u8], // Chave privada para assinatura (ex: ML-DSA)
    ) -> Result<SensorStream, ArkheError> {
        // 1. Criar timestamp
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_err(|e| ArkheError::InvalidSession(format!("Time error: {}", e)))?
            .as_millis() as u64;

        // 2. Construir Merkle leaf com os dados do sensor
        let mut hasher = Sha3_256::new();
        hasher.update(node_id.as_bytes());
        hasher.update(&lat.to_le_bytes());
        hasher.update(&lon.to_le_bytes());
        hasher.update(&timestamp.to_le_bytes());
        hasher.update(&value.to_le_bytes());
        hasher.update(format!("{:?}", sensor_type).as_bytes());
        let merkle_root: [u8; 32] = hasher.finalize().into();

        // 3. Assinar o fluxo (simulação: placeholder para ML-DSA)
        let mut sig_hasher = Sha3_256::new();
        sig_hasher.update(&merkle_root);
        sig_hasher.update(private_key); // Em produção: assinar com ML-DSA
        let signature = sig_hasher.finalize().to_vec();

        // 4. Registrar o fluxo
        let stream = SensorStream {
            node_id: node_id.to_string(),
            lat,
            lon,
            sensor_type,
            value,
            timestamp,
            merkle_root,
            signature,
        };

        let streams = self.published_streams
            .entry(node_id.to_string())
            .or_insert_with(Vec::new);

        streams.push(stream.clone());

        // Evict older streams to prevent resource leaks
        if streams.len() > 1000 {
            streams.drain(0..streams.len() - 1000);
        }

        // 5. Ancorar na TemporalChain (evento off‑chain → on‑chain bridge)
        // Em produção: enviar para o contrato TemporalAnchoring.sol
        // temporal_anchoring.anchorBlock(merkle_root, phi_c, 1, "sensor_data");

        Ok(stream)
    }

    /// Subscreve‑se a fluxos de sensores numa região geográfica.
    pub fn subscribe_to_region(
        &mut self,
        subscriber_id: &str,
        min_lat: f64,
        max_lat: f64,
        min_lon: f64,
        max_lon: f64,
        sensor_type: Option<SensorType>,
    ) -> Vec<SensorStream> {
        let mut results = Vec::new();
        for (_, streams) in &self.published_streams {
            for stream in streams {
                if stream.lat >= min_lat
                    && stream.lat <= max_lat
                    && stream.lon >= min_lon
                    && stream.lon <= max_lon
                {
                    if let Some(ref st) = sensor_type {
                        if stream.sensor_type == *st {
                            results.push(stream.clone());
                        }
                    } else {
                        results.push(stream.clone());
                    }
                }
            }
        }
        self.active_subscriptions
            .entry(subscriber_id.to_string())
            .or_insert_with(Vec::new)
            .extend(results.iter().map(|s| s.node_id.clone()));
        results
    }

    /// Calcula o Φ_C da cobertura sensorial (Loopseal: crescimento monotónico).
    pub fn calculate_sensor_coverage_phi_c(&self) -> f64 {
        let total_streams: usize = self.published_streams.values().map(|v| v.len()).sum();
        let unique_nodes = self.published_streams.len();
        if unique_nodes == 0 {
            return GHOST;
        }
        let coverage_ratio = total_streams as f64 / (unique_nodes as f64 * 10.0); // Normalização
        let phi_c = GHOST + coverage_ratio * (PHI - 1.0) * GHOST;
        phi_c.min(GAP_SOVEREIGN).max(GHOST)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_planetary_sensor_publish() {
        let mut middleware = PlanetarySensorMiddleware::new();
        let stream = middleware.publish_sensor_data(
            "node-aldeia-001", -23.55, -46.63, SensorType::Temperature, 25.4, b"fake_private_key"
        ).unwrap();
        assert_eq!(stream.lat, -23.55);
        assert!(middleware.calculate_sensor_coverage_phi_c() >= GHOST);
    }
}
