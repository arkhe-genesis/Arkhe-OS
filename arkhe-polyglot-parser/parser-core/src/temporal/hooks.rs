// ============================================================================
// ARKHE P³ — TemporalHashChain Registration Hooks
// ============================================================================
// Hooks que são chamados automaticamente durante o parsing para registrar
// eventos na cadeia temporal do ARKHE.
//
// Isso garante que CADA operação de parsing/transpilação é:
//   1. Registrada na cadeia temporal
//   2. Verificada por consenso
//   3. Protegida por prova Merkle
// ============================================================================

/// Tipo de hook de registro temporal
#[derive(Clone, Debug)]
pub enum TemporalHookEvent {
    /// Um parsing foi realizado
    ParseCompleted {
        language: String,
        source_hash: Vec<u8>,
        uast_hash: Vec<u8>,
        node_count: usize,
        timestamp_ns: u64,
    },

    /// Uma transpilação foi realizada
    TranspileCompleted {
        source_language: String,
        target_language: String,
        source_hash: Vec<u8>,
        output_hash: Vec<u8>,
        timestamp_ns: u64,
    },

    /// Uma análise semântica foi realizada
    AnalysisCompleted {
        language: String,
        uast_hash: Vec<u8>,
        semantic_score: f64,
        issues_count: usize,
        timestamp_ns: u64,
    },

    /// Um rollback foi executado
    RollbackExecuted {
        from_version: u64,
        to_version: u64,
        delta_hash: Vec<u8>,
        timestamp_ns: u64,
    },

    /// Um plugin foi carregado
    PluginLoaded {
        plugin_name: String,
        plugin_type: String, // "native", "wasm", "virtual"
        languages_added: Vec<String>,
        timestamp_ns: u64,
    },

    /// Código foi executado
    CodeExecuted {
        language: String,
        uast_hash: Vec<u8>,
        execution_time_ms: u64,
        sandbox_level: String,
        timestamp_ns: u64,
    },
}

/// Resultado do registro temporal
#[derive(Clone, Debug)]
pub struct TemporalRegistration {
    /// Hash da transação na cadeia temporal
    pub tx_hash: Vec<u8>,

    /// Versão atribuída pelo Oracle
    pub oracle_version: u64,

    /// Score de consenso para este registro
    pub consensus_score: f64,

    /// Timestamp do registro
    pub registered_at_ns: u64,

    /// Merkle proof do registro
    pub merkle_proof: Option<Vec<u8>>,
}

/// Configuração dos hooks temporais
#[derive(Clone, Debug)]
pub struct TemporalHookConfig {
    /// Habilitar registro temporal automático
    pub enabled: bool,

    /// Endereço ARKHE do autor (para assinatura)
    pub author_address: Option<Vec<u8>>,

    /// Modo de registro
    pub mode: TemporalHookMode,

    /// Buffer de eventos antes de flush
    pub buffer_size: usize,

    /// Intervalo de flush (ms)
    pub flush_interval_ms: u64,

    /// Mínimo de eventos para flush
    pub min_events_for_flush: usize,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum TemporalHookMode {
    /// Registra cada evento individualmente
    Immediate,

    /// Agrupa eventos e registra em lote
    Batched,

    /// Registra apenas resumos periódicos
    Summary,
}
