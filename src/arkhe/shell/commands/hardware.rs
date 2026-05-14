// ============================================================================
// ARKHE Shell — Comandos de Hardware Unificados
// Funciona em Bare Metal, WSL2, e macOS com a mesma interface
// ============================================================================
use crate::runtime::ASILayer;
use crate::consensus::TemporalAnchor;
use anyhow::Result;

/// Comando: arkh hardware status
pub async fn hardware_status(asi: &ASILayer) -> Result<()> {
    let hardware_info = asi.query_hardware().await?;

    println!("🖥️  Hardware Report — ArkheOS v{}", env!("CARGO_PKG_VERSION"));
    println!("{}", "=".repeat(60));

    // Informações do host
    println!("📋 Host: {} {}", hardware_info.os_name, hardware_info.os_version);
    println!("🔧 Arquitetura: {}", hardware_info.arch);

    // Recursos computacionais
    if let Some(gpu) = &hardware_info.gpu {
        println!("🎮 GPU: {} ({} cores, {}GB VRAM)",
                 gpu.name, gpu.cores, gpu.memory_gb);
    }

    if let Some(neural) = &hardware_info.neural_engine {
        println!("🧠 Neural Engine: {} ({:.1} TOPS)",
                 neural.name, neural.ops_per_sec as f64 / 1e12);
    }

    // Estado da coerência Φ_C
    println!("🌀 Φ_C do sistema: {:.4}", hardware_info.phi_c_coherence);

    // Conexões ASI
    println!("🔗 Conexões ASI: {}", hardware_info.asi_connections);

    // Âncora temporal da consulta
    if let Some(anchor) = &hardware_info.temporal_anchor {
        println!("🔐 Âncora temporal: {}", anchor.hash);
    }

    Ok(())
}

/// Comando: arkh hardware allocate --resource <name>
pub async fn hardware_allocate(asi: &mut ASILayer, resource: &str) -> Result<()> {
    // Solicitar alocação de recurso
    let (handle, anchor) = asi.allocate_hardware_resource(resource).await?;

    println!("✅ Recurso '{}' alocado", resource);
    println!("🔑 Handle: 0x{:x}", handle);
    println!("🔐 Âncora: {}", anchor.hash);
    println!("⏱️  Lease: 3600 segundos (configurável)");

    // Retornar handle para uso posterior
    // (em produção: armazenar em contexto da sessão)

    Ok(())
}

/// Comando: arkh hardware benchmark --type <qnc|folding|mesh>
pub async fn hardware_benchmark(asi: &ASILayer, benchmark_type: &str) -> Result<()> {
    println!("🏃 Iniciando benchmark '{}'...", benchmark_type);

    let results = match benchmark_type {
        "qnc" => asi.benchmark_qnc_inference().await?,
        "folding" => asi.benchmark_protein_folding().await?,
        "mesh" => asi.benchmark_wheeler_mesh().await?,
        _ => anyhow::bail!("Tipo de benchmark não suportado: {}", benchmark_type),
    };

    println!("\n📊 Resultados do Benchmark:");
    println!("   • Throughput: {:.2} ops/sec", results.throughput);
    println!("   • Latência p99: {:.2} ms", results.latency_p99);
    println!("   • Φ_C durante execução: {:.4}", results.phi_c_stability);
    println!("   • Energia estimada: {:.2} J/op", results.energy_per_op);

    // Ancorar resultados na cadeia temporal
    let anchor = asi.anchor_event("benchmark_complete", &results).await?;
    println!("🔐 Resultados ancorados: {}", anchor.hash);

    Ok(())
}