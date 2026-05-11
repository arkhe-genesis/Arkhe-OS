use reqwest;
use serde::Deserialize;
use std::time::Duration;
use tokio::time;

#[derive(Debug, Deserialize)]
pub struct BitcoinInfo {
    pub blocks: u64,
    pub difficulty: f64,
    pub networkhashps: f64,
}

pub struct ConsensusSense {
    rpc_url: String,
    sigma: f64, // Consensus health (0.0 to 1.0)
}

impl ConsensusSense {
    pub fn new(rpc_url: &str) -> Self {
        Self {
            rpc_url: rpc_url.to_string(),
            sigma: 1.0,
        }
    }

    pub async fn monitor(&mut self) {
        let mut interval = time::interval(Duration::from_secs(60));
        loop {
            interval.tick().await;
            match self.fetch_bitcoin_info().await {
                Ok(info) => {
                    self.update_sigma(&info);
                    println!("[ConsensusSense] Bitcoin Block: {}, Hashrate: {:.2} EH/s, Sigma: {:.4}", 
                             info.blocks, info.networkhashps / 1e18, self.sigma);
                }
                Err(e) => {
                    eprintln!("[ConsensusSense] Error fetching Bitcoin info: {}", e);
                    self.sigma *= 0.9; // Decay sigma on error
                }
            }
        }
    }

    async fn fetch_bitcoin_info(&self) -> Result<BitcoinInfo, reqwest::Error> {
        // Mocking a call to a Bitcoin RPC or block explorer API
        let resp = reqwest::get(&self.rpc_url).await?;
        let info = resp.json::<BitcoinInfo>().await?;
        Ok(info)
    }

    fn update_sigma(&mut self, info: &BitcoinInfo) {
        // A simple heuristic: if hashrate drops significantly, sigma decreases.
        // In a real implementation, this would compare against historical averages.
        let expected_hashrate = 500e18; // 500 EH/s baseline
        let ratio = info.networkhashps / expected_hashrate;
        
        if ratio >= 1.0 {
            self.sigma = 1.0;
        } else {
            self.sigma = ratio;
        }
    }

    pub fn get_sigma(&self) -> f64 {
        self.sigma
    }
}
