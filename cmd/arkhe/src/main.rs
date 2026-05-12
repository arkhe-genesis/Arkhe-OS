use anyhow::Result;
use clap::Parser;

mod commands;

#[derive(Parser)]
enum Commands {
    Shard(commands::shard::ShardCreateArgs),
    SelfComplete(commands::self_complete::SelfCompleteArgs),
    Portal(commands::portal::PortalCreateArgs),
    // Connect(ConnectArgs),
    // Block(BlockArgs),
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
        Commands::Portal(args) => commands::portal::handle_portal_create(args).await,
    }
}
