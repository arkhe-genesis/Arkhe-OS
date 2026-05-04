// build/wasm/src/lib.rs — Bindings WebAssembly para ARKHE OS
#![allow(clippy::new_without_default)]

use wasm_bindgen::prelude::*;
use serde_wasm_bindgen;
use arkhe_unified::core::orchestrator::UnifiedOrchestrator;
use arkhe_unified::core::config::Config;

/// Inicializa o orquestrador ARKHE no ambiente WASM
#[wasm_bindgen]
pub struct ArkheWasm {
    orchestrator: Option<UnifiedOrchestrator>,
    config_json: String,
}

#[wasm_bindgen]
impl ArkheWasm {
    /// Cria nova instância do ARKHE WASM
    #[wasm_bindgen(constructor)]
    pub fn new(config_json: String) -> Result<ArkheWasm, JsValue> {
        // Configurar panic hook para debugging
        #[cfg(feature = "console_error_panic_hook")]
        console_error_panic_hook::set_once();

        Ok(ArkheWasm {
            orchestrator: None,
            config_json,
        })
    }

    /// Inicializa o orquestrador com a configuração fornecida
    #[wasm_bindgen]
    pub async fn initialize(&mut self) -> Result<JsValue, JsValue> {
        let config: Config = serde_yaml::from_str(&self.config_json)
            .map_err(|e| JsValue::from_str(&format!("Config parse error: {}", e)))?;

        // Criar orchestrator (simplificado para WASM)
        let orchestrator = UnifiedOrchestrator::new_wasm(config)
            .map_err(|e| JsValue::from_str(&format!("Orchestrator init failed: {}", e)))?;

        self.orchestrator = Some(orchestrator);

        Ok(serde_wasm_bindgen::to_value(&serde_json::json!({
            "status": "initialized",
            "version": env!("CARGO_PKG_VERSION")
        }))?)
    }

    /// Executa uma missão via WASM
    #[wasm_bindgen]
    pub async fn execute_mission(
        &self,
        mission_id: String,
        zones_json: String
    ) -> Result<JsValue, JsValue> {
        let orchestrator = self.orchestrator.as_ref()
            .ok_or_else(|| JsValue::from_str("Orchestrator not initialized"))?;

        let zones: Vec<String> = serde_json::from_str(&zones_json)
            .map_err(|e| JsValue::from_str(&format!("Zones parse error: {}", e)))?;

        let result = orchestrator.execute_mission_wasm(&mission_id, &zones).await
            .map_err(|e| JsValue::from_str(&format!("Mission execution failed: {}", e)))?;

        Ok(serde_wasm_bindgen::to_value(&result)?)
    }

    /// Otimiza alocação de potência NOMA 6G via WASM
    #[wasm_bindgen]
    pub fn optimize_noma_power(
        &self,
        num_devices: u32,
        num_subchannels: u32,
        channels_json: String
    ) -> Result<JsValue, JsValue> {
        #[cfg(feature = "nomad")]
        {
            use arkhe_unified::substrates::v168_noma::NOMAManifold;
            use arkhe_unified::substrates::v168_noma::MOGAOptimizer;

            let channels: Vec<Vec<f64>> = serde_json::from_str(&channels_json)
                .map_err(|e| JsValue::from_str(&format!("Channels parse error: {}", e)))?;

            let config = arkhe_unified::substrates::v168_noma::SimulationConfig {
                total_iot_devices: num_devices as usize,
                sub_channels: num_subchannels as usize,
                ..Default::default()
            };

            let manifold = NOMAManifold::new(config);
            let mut moga = MOGAOptimizer::new(&manifold);

            // Executar otimização (simplificada para WASM)
            let (power_matrix, fitness) = moga.optimize_wasm(&channels);

            Ok(serde_wasm_bindgen::to_value(&serde_json::json!({
                "power_allocation": power_matrix,
                "fitness": fitness,
                "total_power": fitness.0,
                "avg_rate": fitness.1,
                "qos_violations": fitness.2
            }))?)
        }

        #[cfg(not(feature = "nomad"))]
        {
            Err(JsValue::from_str("NOMA feature not enabled in this build"))
        }
    }

    /// Obtém métricas de saúde do sistema
    #[wasm_bindgen]
    pub fn get_health(&self) -> Result<JsValue, JsValue> {
        let orchestrator = self.orchestrator.as_ref()
            .ok_or_else(|| JsValue::from_str("Orchestrator not initialized"))?;

        let health = orchestrator.get_system_health_wasm();
        Ok(serde_wasm_bindgen::to_value(&health)?)
    }
}

/// Função helper para logging no console do navegador
#[wasm_bindgen]
extern "C" {
    #[wasm_bindgen(js_namespace = console)]
    fn log(s: &str);
}

#[allow(dead_code)]
fn console_log(msg: &str) {
    log(msg);
}
