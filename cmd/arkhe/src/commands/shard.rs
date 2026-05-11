use clap::Parser;
use anyhow::Result;

#[derive(Parser)]
pub struct ShardCreateArgs {
    #[arg(long, default_value = "6064")]
    pub substrate: String,
    #[arg(long)]
    pub motor: String,
    #[arg(long)]
    pub gpu: bool,
}

pub async fn handle_shard_create(_args: ShardCreateArgs) -> Result<()> {
    // let mut client = OracleClient::connect("http://[::1]:50051").await?;
    // let request = tonic::Request::new(CreateShardRequest {
    //     substrate_id: args.substrate,
    //     motor: args.motor,
    //     gpu: args.gpu,
    // });
    // let response = client.create_shard(request).await?;
    // println!("Shard {} criado com sucesso.", response.into_inner().shard_id);
    println!("Shard criado com sucesso. (mock)");
    Ok(())
}
