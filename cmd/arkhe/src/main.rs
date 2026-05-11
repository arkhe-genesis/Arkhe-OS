use clap::Parser;
use anyhow::Result;

mod commands;

#[derive(Parser)]
enum Commands {
    Shard(commands::shard::ShardCreateArgs),
    SelfComplete(commands::self_complete::SelfCompleteArgs),
    // Connect(ConnectArgs),
    // Block(BlockArgs),
    // Portal(PortalArgs),
    // Substrate(SubstrateArgs),
}

#[derive(Parser)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Shard(args) => commands::shard::handle_shard_create(args).await,
        Commands::SelfComplete(args) => commands::self_complete::handle_self_complete(args).await,
    }
}
