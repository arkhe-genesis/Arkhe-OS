use clap::{Parser, Subcommand};
use pacir_agi_core::{falsifiers::*, GgufManifest};
#[derive(Parser)]
#[command(name = "pacir-agi", about = "PACIR-AGI routing-manifest framework")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}
#[derive(Subcommand)]
enum Command {
    List,
    Verify {
        #[arg(long)]
        manifest: String,
    },
    Falsify {
        #[arg(long)]
        id: String,
        #[arg(long)]
        value: Option<f64>,
    },
}
#[tokio::main]
async fn main() {
    match Cli::parse().command {
        Command::List => {
            for id in 1..=12 {
                println!("AGI-{id:02}");
            }
        }
        Command::Verify { manifest } => {
            let result = std::fs::read_to_string(manifest)
                .map_err(|e| e.to_string())
                .and_then(|contents| {
                    serde_json::from_str::<GgufManifest>(&contents).map_err(|e| e.to_string())
                });
            match result {
                Ok(m) => match pacir_agi_verify::verify_manifest(&m).await {
                    Ok(()) => println!("manifest verified"),
                    Err(e) => {
                        eprintln!("verification failed: {e}");
                        std::process::exit(1)
                    }
                },
                Err(e) => {
                    eprintln!("invalid manifest: {e}");
                    std::process::exit(2)
                }
            }
        }
        Command::Falsify { id, value } => {
            let v = value.unwrap_or_default();
            let failed = match id.as_str() {
                "AGI-02" => falsify_agi_02(true, v > 0.),
                "AGI-06" => falsify_agi_06(v, 100.),
                "AGI-07" => falsify_agi_07(v),
                "AGI-09" => falsify_agi_09(v as u64, 1_000_000),
                _ => {
                    eprintln!("unsupported falsifier: {id}");
                    std::process::exit(2)
                }
            };
            println!("{id} = {}", if failed { "FALSIFIED" } else { "OK" });
        }
    }
}
