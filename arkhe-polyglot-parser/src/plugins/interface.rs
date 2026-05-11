// ============================================================================
// ARKHE P³ — Plugin Interface Definition
// ============================================================================

use std::any::Any;
use crate::plugins::loader::PluginError;
use crate::runtime::polyglot_vm::SandboxLevel;

/// Trait que cada plugin DEVE implementar para ser carregado
pub trait LanguagePlugin: Send + Sync {
    /// Nome único da linguagem
    fn name(&self) -> &str;

    /// Versão do plugin (semâver)
    fn version(&self) -> &str;

    /// Retorna a gramática no formato esperado pelo GrammarPool
    fn grammar(&self) -> Result<Vec<u8>, PluginError>;

    /// Tokeniza código fonte — retorna tokens serializados
    fn tokenize(&self, source: &str) -> Result<Vec<u8>, PluginError>;

    /// Parse completo — retorna UAST serializada
    fn parse(&self, source: &str) -> Result<Vec<u8>, PluginError>;

    /// Transpilação — retorna código na linguagem de destino
    fn transpile(&self, source: &str, target_lang: &str) -> Result<String, PluginError>;

    /// Verificação de integridade do plugin
    fn verify(&self) -> Result<(), PluginError>;

    /// Informações do plugin
    fn info(&self) -> PluginInfo;

    /// Cast para Any (para downcasting)
    fn as_any(&self) -> &dyn Any;
}

/// Metadados do plugin
pub struct PluginInfo {
    pub name: String,
    pub version: String,
    pub author: String,
    pub description: String,
    pub license: String,
    pub supported_versions: Vec<String>,
    pub dependencies: Vec<String>,
    pub checksum: Vec<u8>,
}

/// Perfil de segurança do plugin
pub struct PluginSecurityProfile {
    pub permissions: Vec<PluginPermission>,
    pub sandbox_level: SandboxLevel,
    pub max_memory_mb: u64,
    pub max_execution_time_ms: u64,
    pub requires_signature: bool,
    pub trusted_publishers: Vec<Vec<u8>>, // Endereços ARKHE
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum PluginPermission {
    FilesystemRead,
    FilesystemWrite,
    NetworkAccess,
    EnvironmentAccess,
    ProcessSpawn,
    SharedMemory,
    GpuAccess,
    TemporalChainWrite,
    OracleAccess,
}
