use std::collections::HashMap;
use sha3::{Digest, Sha3_256};
use crate::{GHOST, LOOPSEAL, GAP_SOVEREIGN};

/// Represents a georeferenced sensor publication
#[derive(Debug, Clone)]
pub struct SensorData {
    pub publisher_id: String,
    pub location_hash: String,
    pub payload_hash: String,
    pub timestamp: i64,
}

impl SensorData {
    pub fn compute_leaf_hash(&self) -> String {
        let mut hasher = Sha3_256::new();
        hasher.update(format!("{}:{}:{}:{}", self.publisher_id.len(), self.publisher_id, self.location_hash, self.payload_hash));
        hex::encode(hasher.finalize())
    }
}

/// Georeferenced Topic containing aggregated sensor data
#[derive(Debug, Clone)]
pub struct GeoreferencedTopic {
    pub topic_id: String,
    pub data_streams: Vec<SensorData>,
    pub merkle_root: String,
}

impl GeoreferencedTopic {
    pub fn new(topic_id: String) -> Self {
        Self {
            topic_id,
            data_streams: Vec::new(),
            merkle_root: String::new(),
        }
    }

    pub fn publish(&mut self, data: SensorData) {
        self.data_streams.push(data);
        self.update_merkle_root();
    }

    fn update_merkle_root(&mut self) {
        if self.data_streams.is_empty() {
            self.merkle_root = String::new();
            return;
        }
        let mut current_level: Vec<String> = self.data_streams.iter().map(|d| d.compute_leaf_hash()).collect();
        while current_level.len() > 1 {
            let mut next_level = Vec::new();
            for chunk in current_level.chunks(2) {
                let mut hasher = Sha3_256::new();
                if chunk.len() == 2 {
                    hasher.update(format!("{}{}", chunk[0], chunk[1]));
                } else {
                    hasher.update(format!("{}{}", chunk[0], chunk[0]));
                }
                next_level.push(hex::encode(hasher.finalize()));
            }
            current_level = next_level;
        }
        self.merkle_root = current_level[0].clone();
    }
}

/// Planetary Sensor Middleware
pub struct PlanetarySensors {
    pub topics: HashMap<String, GeoreferencedTopic>,
    pub loopseal_depth: f64,
    pub coverage_nodes: usize,
}

impl PlanetarySensors {
    pub fn new() -> Self {
        Self {
            topics: HashMap::new(),
            loopseal_depth: 0.0,
            coverage_nodes: 0,
        }
    }

    pub fn publish_data(&mut self, topic_id: &str, data: SensorData) -> Result<(), String> {
        let topic = self.topics.entry(topic_id.to_string()).or_insert(GeoreferencedTopic::new(topic_id.to_string()));
        topic.publish(data);
        self.loopseal_depth += LOOPSEAL;
        self.coverage_nodes += 1;
        Ok(())
    }

    pub fn get_merkle_root(&self, topic_id: &str) -> Option<String> {
        self.topics.get(topic_id).map(|t| t.merkle_root.clone())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_publish_and_aggregate() {
        let mut sensors = PlanetarySensors::new();
        let data1 = SensorData {
            publisher_id: "node1".to_string(),
            location_hash: "loc1".to_string(),
            payload_hash: "payload1".to_string(),
            timestamp: 1000,
        };
        sensors.publish_data("topic1", data1).unwrap();
        assert!(!sensors.get_merkle_root("topic1").unwrap().is_empty());
        assert_eq!(sensors.coverage_nodes, 1);
        assert!((sensors.loopseal_depth - LOOPSEAL).abs() < 1e-6);
    }
}
