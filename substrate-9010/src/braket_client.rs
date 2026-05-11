use anyhow::Result;
use aws_sdk_braket::Client;
use aws_config::BehaviorVersion;

pub struct ArkheBraketClient {
    client: Client,
}

impl ArkheBraketClient {
    pub async fn new() -> Self {
        let config = aws_config::load_defaults(BehaviorVersion::latest()).await;
        let client = Client::new(&config);
        Self { client }
    }

    pub async fn run_qft_on_braket(&self, circuit: &str) -> Result<String> {
        let response = self.client.create_quantum_task()
            .action(circuit)
            .device_arn("arn:aws:braket:::device/quantum-simulator/amazon/sv1")
            .output_s3_bucket("arkhe-quantum-results")
            .output_s3_key_prefix("tasks/")
            .shots(1000)
            .send()
            .await?;

        Ok(response.quantum_task_arn().to_string())
    }
}
