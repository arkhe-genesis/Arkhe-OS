// src/main.rs — Entry point do binário unificado ARKHE OS v168
#![deny(unused_must_use)]
#![allow(unsafe_code)]
use std::path::PathBuf;
use std::sync::Arc;
use clap::{Parser, Subcommand};

// Importar módulos do core
use crate::core::orchestrator::UnifiedOrchestrator;
use crate::core::integrity::IntegrityVerifier;
use crate::core::plugin::PluginManager;
use crate::cli::parser::CommandArgs;

mod core;
mod substrates;
mod quantum;
mod privacy;
mod cosmic;
mod cli;

/// ARKHE OS v∞.Ω.∇++++++++++++++++.168 — Orquestrador Unificado
#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Cli {
    /// Caminho para arquivo de configuração YAML
    #[arg(short, long, default_value = "config/default.yaml")]
    config: PathBuf,

    /// Nível de log: trace, debug, info, warn, error
    #[arg(short, long, default_value = "info")]
    log_level: String,

    /// Habilitar modo de verificação de integridade estrita
    #[arg(long)]
    strict_integrity: bool,

    /// Subcomando a executar
    #[command(subcommand)]
    command: Option<Commands>,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Executar missão especificada
    Run {
        /// ID da missão a executar
        #[arg(short, long)]
        mission_id: String,

        /// Zonas alvo para a missão
        #[arg(short, long, num_args = 1..)]
        zones: Vec<String>,
    },

    /// Validar integridade do binário e módulos
    Verify {
        /// Caminho para arquivo de assinaturas
        #[arg(short, long)]
        signatures: Option<PathBuf>,
    },

    /// Listar plugins disponíveis
    Plugins {
        /// Filtrar por nome ou categoria
        #[arg(short, long)]
        filter: Option<String>,
    },

    /// Modo REPL interativo para debugging
    Repl,

    /// Exportar métricas de saúde do sistema
    Health {
        /// Formato de saída: json, yaml, prometheus
        #[arg(short, long, default_value = "json")]
        format: String,
    },
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Parse argumentos de linha de comando
    let cli = Cli::parse();

    // Inicializar logging estruturado
    init_logging(&cli.log_level)?;
    tracing::info!("🚀 ARKHE OS v168 — Inicializando orquestrador unificado");

    // Carregar configuração
    let config = load_config(&cli.config)?;
    tracing::debug!("📋 Configuração carregada: {:?}", config);

    // Verificar integridade se habilitado
    if cli.strict_integrity {
        let verifier = IntegrityVerifier::new(&config)?;
        verifier.verify_all()?;
        tracing::info!("✅ Verificação de integridade concluída");
    }

    // Inicializar gerenciador de plugins
    let mut plugin_manager = PluginManager::new(&config.plugins_dir)?;
    plugin_manager.load_discovered_plugins()?;
    tracing::info!("🔌 Plugins carregados: {}", plugin_manager.count());

    // Instanciar orquestrador unificado
    let orchestrator = UnifiedOrchestrator::new(
        config,
        Arc::new(plugin_manager),
    )?;

    // Executar comando ou modo padrão
    match cli.command {
        Some(Commands::Run { mission_id, zones }) => {
            tracing::info!("🎯 Executando missão: {} em {:?}", mission_id, zones);
            let result: crate::core::orchestrator::MissionResult = orchestrator.execute_mission(&mission_id, &zones).await?;
            println!("{}", serde_json::to_string_pretty(&result)?);
        }
        Some(Commands::Verify { signatures }) => {
            tracing::info!("🔐 Validando integridade...");
            let verifier = IntegrityVerifier::new(&orchestrator.config())?;
            let report = verifier.generate_report(signatures.as_deref())?;
            println!("{}", serde_json::to_string_pretty(&report)?);
        }
        Some(Commands::Plugins { filter }) => {
            let plugins = orchestrator.list_plugins(filter.as_deref());
            println!("{}", serde_yaml::to_string(&plugins)?);
        }
        Some(Commands::Repl) => {
            tracing::info!("🔧 Entrando em modo REPL...");
            cli::repl::start_repl(orchestrator).await?;
        }
        Some(Commands::Health { format }) => {
            let health: crate::core::orchestrator::SystemHealth = orchestrator.get_system_health().await?;
            match format.as_str() {
                "json" => println!("{}", serde_json::to_string_pretty(&health)?),
                "yaml" => println!("{}", serde_yaml::to_string(&health)?),
                "prometheus" => println!("uptime_seconds {}", health.uptime_seconds),
                _ => return Err(format!("Formato não suportado: {}", format).into()),
            }
        }
        None => {
            // Modo padrão: aguardar comandos via socket ou executar missão default
            tracing::info!("🔄 Modo padrão: aguardando comandos...");
            orchestrator.run_default_loop().await?;
        }
    }

    tracing::info!("✅ ARKHE OS v168 — Encerramento limpo");
    Ok(())
}

fn init_logging(level: &str) -> Result<(), Box<dyn std::error::Error>> {
    use tracing_subscriber::{fmt, EnvFilter};

    let filter = EnvFilter::try_from_default_env()
        .or_else(|_| EnvFilter::try_new(level))
        .unwrap_or_else(|_| EnvFilter::new("info"));

    fmt()
        .with_env_filter(filter)
        .with_target(true)
        .with_thread_ids(true)
        .with_file(true)
        .with_line_number(true)
        .init();

    Ok(())
}

fn load_config(path: &PathBuf) -> Result<crate::core::config::Config, Box<dyn std::error::Error>> {
    let content = std::fs::read_to_string(path)?;
    let config: crate::core::config::Config = serde_yaml::from_str(&content)?;
    Ok(config)
}
