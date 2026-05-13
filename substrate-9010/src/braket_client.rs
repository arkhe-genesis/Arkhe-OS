pub struct ArkheBraketClient;
impl ArkheBraketClient {
    pub async fn new() -> Self { Self }
    pub async fn run_qft_on_braket(&self, _s: &str) -> anyhow::Result<()> { Ok(()) }
}
