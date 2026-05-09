// src/core/plugin.rs — Sistema de plugins com carregamento seguro e sandboxing
use anyhow::{Result, Context, bail};
use libloading::{Library, Symbol};
use std::collections::HashMap;
use std::ffi::OsStr;
use std::path::{Path, PathBuf};
use std::sync::Arc;

use crate::core::config::PluginConfig;

/// Plugin dinâmico com interface padronizada
pub trait Plugin: Send + Sync {
    /// Nome único do plugin
    fn name(&self) -> &str;

    /// Versão do plugin (semver)
    fn version(&self) -> &str;

    /// Inicializar plugin com configuração
    fn initialize(&mut self, config: &serde_json::Value) -> Result<()>;

    /// Executar função principal do plugin
    fn execute(&self, input: PluginInput) -> Result<PluginOutput>;

    /// Verificar saúde do plugin
    fn health_check(&self) -> PluginHealth;

    /// Shutdown limpo
    fn shutdown(&mut self) -> Result<()>;
}

/// Entrada para execução de plugin
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct PluginInput {
    pub mission_id: Option<String>,
    pub zone_id: Option<String>,
    pub parameters: serde_json::Value,
    pub context: HashMap<String, serde_json::Value>,
}

/// Saída de execução de plugin
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct PluginOutput {
    pub success: bool,
    pub result: serde_json::Value,
    pub metrics: HashMap<String, f64>,
    pub errors: Vec<String>,
}

/// Status de saúde do plugin
#[derive(Debug, Clone, serde::Serialize)]
pub struct PluginHealth {
    pub status: HealthStatus,
    pub message: Option<String>,
    pub metrics: HashMap<String, f64>,
}

#[derive(Debug, Clone, PartialEq, serde::Serialize)]
#[serde(rename_all = "snake_case")]
pub enum HealthStatus {
    Healthy,
    Degraded,
    Failed,
    Unknown,
}

/// Gerenciador de plugins com carregamento seguro
pub struct PluginManager {
    /// Diretório de plugins
    plugin_dir: PathBuf,

    /// Plugins carregados: nome → instância
    loaded_plugins: HashMap<String, Box<dyn Plugin>>,

    /// Bibliotecas dinâmicas abertas (para manter handles válidos)
    _libraries: Vec<Library>,

    /// Configuração de sandboxing
    sandbox_config: SandboxConfig,
}

#[derive(Debug, Clone)]
pub struct SandboxConfig {
    /// Habilitar sandboxing via seccomp/AppArmor
    pub enable_sandbox: bool,

    /// Timeout para execução de plugin (segundos)
    pub execution_timeout_secs: u64,

    /// Memória máxima por plugin (MB)
    pub max_memory_mb: usize,

    /// Permitir acesso à rede
    pub allow_network: bool,

    /// Permitir acesso ao filesystem
    pub allow_filesystem: bool,
}

impl Default for SandboxConfig {
    fn default() -> Self {
        Self {
            enable_sandbox: true,
            execution_timeout_secs: 30,
            max_memory_mb: 256,
            allow_network: false,
            allow_filesystem: false,
        }
    }
}

impl PluginManager {
    /// Criar gerenciador com diretório de plugins
    pub fn new(plugin_dir: &Path) -> Result<Self> {
        if !plugin_dir.exists() {
            std::fs::create_dir_all(plugin_dir)
                .context(format!("Failed to create plugin directory: {:?}", plugin_dir))?;
        }

        Ok(Self {
            plugin_dir: plugin_dir.to_path_buf(),
            loaded_plugins: HashMap::new(),
            _libraries: Vec::new(),
            sandbox_config: SandboxConfig::default(),
        })
    }

    /// Carregar todos os plugins descobertos no diretório
    pub fn load_discovered_plugins(&mut self) -> Result<usize> {
        let mut loaded = 0;

        for entry in std::fs::read_dir(&self.plugin_dir)
            .context("Failed to read plugin directory")?
        {
            let entry = entry?;
            let path = entry.path();

            // Verificar se é biblioteca dinâmica válida
            if is_dynamic_library(&path) {
                match self.load_plugin_from_path(&path) {
                    Ok(name) => {
                        tracing::info!("✅ Plugin loaded: {} from {:?}", name, path);
                        loaded += 1;
                    }
                    Err(e) => {
                        tracing::warn!("❌ Failed to load plugin {:?}: {}", path, e);
                    }
                }
            }
        }

        Ok(loaded)
    }

    /// Carregar plugin específico por caminho
    pub fn load_plugin_from_path(&mut self, path: &Path) -> Result<String> {
        // Carregar biblioteca dinâmica com segurança
        // Nota: em produção, usar sandboxing (seccomp, AppArmor, etc.)
        let lib = unsafe {
            Library::new(path)
                .context(format!("Failed to load library: {:?}", path))?
        };

        // Buscar símbolo de factory do plugin
        // Convenção: fn create_plugin() -> *mut dyn Plugin
        let factory: Symbol<unsafe extern "C" fn() -> *mut dyn Plugin> = unsafe {
            lib.get(b"create_plugin\0")
                .context("Plugin missing 'create_plugin' factory symbol")?
        };

        // Criar instância do plugin
        let plugin_ptr = unsafe { factory() };
        if plugin_ptr.is_null() {
            bail!("Plugin factory returned null pointer");
        }

        // Converter para Box<dyn Plugin> com cuidado de memória
        // Nota: requer que o plugin use allocator compatível
        let mut plugin: Box<dyn Plugin> = unsafe { Box::from_raw(plugin_ptr) };

        let name = plugin.name().to_string();

        // Inicializar plugin com config default
        let default_config = serde_json::json!({});
        plugin.initialize(&default_config)
            .context(format!("Failed to initialize plugin: {}", name))?;

        // Armazenar plugin e manter library handle vivo
        self.loaded_plugins.insert(name.clone(), plugin);
        self._libraries.push(lib);

        Ok(name)
    }

    /// Executar plugin por nome
    pub async fn execute_plugin(
        &self,
        name: &str,
        input: PluginInput,
    ) -> Result<PluginOutput> {
        let plugin = self.loaded_plugins.get(name)
            .ok_or_else(|| anyhow::anyhow!("Plugin not found: {}", name))?;

        // Aplicar sandboxing se habilitado
        if self.sandbox_config.enable_sandbox {
            #[cfg(target_os = "linux")]
            {
                // Aplicar seccomp-bpf filter em produção
                // Para exemplo: apenas log
                tracing::debug!("🔒 Executing plugin {} with sandbox", name);
            }
        }

        // Executar com timeout
        let output = tokio::time::timeout(
            std::time::Duration::from_secs(self.sandbox_config.execution_timeout_secs),
            async { plugin.execute(input) }
        ).await
            .map_err(|_| anyhow::anyhow!("Plugin execution timed out"))?
            .context("Plugin execution failed")?;

        Ok(output)
    }

    /// Listar plugins disponíveis
    pub fn list_plugins(&self, filter: Option<&str>) -> Vec<PluginInfo> {
        self.loaded_plugins.values()
            .filter(|p| filter.map_or(true, |f| p.name().contains(f)))
            .map(|p| PluginInfo {
                name: p.name().to_string(),
                version: p.version().to_string(),
                health: p.health_check(),
            })
            .collect()
    }

    /// Obter contador de plugins carregados
    pub fn count(&self) -> usize {
        self.loaded_plugins.len()
    }

    /// Configurar sandboxing
    pub fn configure_sandbox(&mut self, config: SandboxConfig) {
        self.sandbox_config = config;
    }
}

/// Informações públicas sobre plugin
#[derive(Debug, Clone, serde::Serialize)]
pub struct PluginInfo {
    pub name: String,
    pub version: String,
    pub health: PluginHealth,
}

/// Verificar se arquivo é biblioteca dinâmica
fn is_dynamic_library(path: &Path) -> bool {
    path.extension().map_or(false, |ext| {
        ext == "so" ||    // Linux
        ext == "dylib" || // macOS
        ext == "dll"      // Windows
    })
}

/// Macro para facilitar implementação de plugins em Rust
#[macro_export]
macro_rules! export_plugin {
    ($plugin_type:ty) => {
        #[no_mangle]
        pub extern "C" fn create_plugin() -> *mut dyn $crate::core::plugin::Plugin {
            Box::into_raw(Box::new(<$plugin_type>::default()))
        }
    };
}

/// Exemplo de plugin mínimo
#[cfg(test)]
mod tests {
    use super::*;

    #[derive(Default)]
    struct HelloPlugin;

    impl Plugin for HelloPlugin {
        fn name(&self) -> &str { "hello" }
        fn version(&self) -> &str { "0.1.0" }

        fn initialize(&mut self, _config: &serde_json::Value) -> Result<()> {
            Ok(())
        }

        fn execute(&self, input: PluginInput) -> Result<PluginOutput> {
            Ok(PluginOutput {
                success: true,
                result: serde_json::json!({"message": "Hello from plugin!"}),
                metrics: HashMap::new(),
                errors: Vec::new(),
            })
        }

        fn health_check(&self) -> PluginHealth {
            PluginHealth {
                status: HealthStatus::Healthy,
                message: None,
                metrics: HashMap::new(),
            }
        }

        fn shutdown(&mut self) -> Result<()> { Ok(()) }
    }

    export_plugin!(HelloPlugin);
}
