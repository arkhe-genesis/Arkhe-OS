use aws_sdk_braket::Client;
use aws_config::meta::region::RegionProviderChain;

pub async fn run_on_braket(circuit_qasm: &str) -> Result<String, Box<dyn std::error::Error>> {
    let region_provider = RegionProviderChain::default_provider().or_else("us-east-1");
    let config = aws_config::from_env().region(region_provider).load().await;
    let client = Client::new(&config);

    let task = client.create_quantum_task()
        .set_action(Some(circuit_qasm.into()))
        .device_arn("arn:aws:braket:::device/quantum-simulator/amazon/sv1")
        .output_s3_bucket("arkhe-quantum-results")
        .output_s3_key_prefix("tasks/")
        .shots(1000)
        .send()
        .await?;

    // Return ARN
    let arn = task.quantum_task_arn;
    Ok(arn)
}
