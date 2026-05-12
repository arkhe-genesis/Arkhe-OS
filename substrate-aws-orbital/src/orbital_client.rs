use anyhow::Result;
use aws_config::BehaviorVersion;
use aws_sdk_groundstation::primitives::DateTime;
use aws_sdk_groundstation::Client;

pub struct ArkheOrbitalClient {
    client: Client,
}

impl ArkheOrbitalClient {
    pub async fn new() -> Self {
        let config = aws_config::load_defaults(BehaviorVersion::latest()).await;
        let client = Client::new(&config);
        Self { client }
    }

    pub async fn contact_satellite(&self, satellite_id: &str) -> Result<String> {
        let start_time = DateTime::from_secs(0);
        let end_time = DateTime::from_secs(1000000000);
        let response = self
            .client
            .list_contacts()
            .start_time(start_time)
            .end_time(end_time)
            .satellite_arn(satellite_id)
            .send()
            .await?;

        Ok(format!("Contatou satélite {:?}", response))
    }
}
