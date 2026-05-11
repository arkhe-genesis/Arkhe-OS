use std::path::PathBuf;
use std::collections::HashMap;

fn default_instant() -> std::time::Instant {
    std::time::Instant::now()
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Config {
    #[serde(default)]
    pub zones: Vec<String>,
    #[serde(default)]
    pub plugins_dir: PathBuf,
    #[serde(default)]
    pub missions: HashMap<String, MissionConfig>,
    #[serde(default)]
    pub security: SecurityConfig,
    #[serde(default)]
    pub scheduling: SchedulerConfig,
    #[serde(default)]
    pub manifold: serde_json::Value,
    #[serde(default)]
    pub marl: serde_json::Value,
    #[serde(default)]
    pub meta_learning: serde_json::Value,
    #[serde(default)]
    pub default_mission: Option<DefaultMissionConfig>,
    #[serde(skip, default = "default_instant")]
    pub start_time: std::time::Instant,
    pub config_path: Option<PathBuf>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct MissionConfig {
    pub requires_resources: bool,
    pub resource_requirements: serde_json::Value,
    pub max_steps: Option<u64>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
pub struct SecurityConfig {
    pub strict_integrity: bool,
    pub public_key_path: Option<PathBuf>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
pub struct SchedulerConfig {
    pub default_timeout_ms: u64,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct DefaultMissionConfig {
    pub id: String,
    pub target_zones: Vec<String>,
}

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct PluginConfig {
}
