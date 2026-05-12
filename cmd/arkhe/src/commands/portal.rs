use anyhow::Result;
use clap::Parser;

#[derive(Parser)]
pub struct PortalCreateArgs {
    #[arg(long)]
    pub r#type: String,
    #[arg(long)]
    pub endpoint: String,
}

pub async fn handle_portal_create(args: PortalCreateArgs) -> Result<()> {
    if args.r#type == "quantum" {
        println!(
            "Criando portal quântico para {} via Amazon Braket...",
            args.endpoint
        );
        let client = arkhe_amazon_braket::braket_client::ArkheBraketClient::new().await;
        let _result = client.run_qft_on_braket("QFT").await?;
        println!("Portal quântico estabelecido com sucesso!");
    } else if args.r#type == "orbital" {
        println!("Estabelecendo malha orbital com {}...", args.endpoint);
        let client = arkhe_aws_orbital::orbital_client::ArkheOrbitalClient::new().await;
        let _result = client.contact_satellite(&args.endpoint).await?;
        println!("Malha orbital conectada!");
    } else {
        println!("Portal {} criado to {}.", args.r#type, args.endpoint);
    }
    Ok(())
}
