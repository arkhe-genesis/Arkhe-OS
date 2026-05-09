use std::time::Duration;
use tokio::time;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketData {
    pub symbol: String,
    pub price: f64,
    pub volume: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhaseState {
    pub omega: f64, // Global phase coherence
    pub sigma: f64, // Consensus health
}

pub struct TradingEngine {
    strategies: Vec<Box<dyn Strategy>>,
}

impl TradingEngine {
    pub fn new() -> Self {
        Self {
            strategies: vec![
                Box::new(CoherenceFilterStrategy::new()),
                Box::new(ConsensusHedgeStrategy::new()),
            ],
        }
    }

    pub async fn run(&mut self) {
        let mut interval = time::interval(Duration::from_secs(10));
        loop {
            interval.tick().await;
            
            // Mock fetching data
            let market_data = self.fetch_market_data().await;
            let phase_state = self.fetch_phase_state().await;

            println!("[TradingEngine] Evaluating strategies... Ω': {:.4}, Σ: {:.4}", phase_state.omega, phase_state.sigma);

            for strategy in &mut self.strategies {
                if let Some(action) = strategy.evaluate(&market_data, &phase_state) {
                    println!("[TradingEngine] Action triggered: {:?}", action);
                    self.execute_action(action).await;
                }
            }
        }
    }

    async fn fetch_market_data(&self) -> MarketData {
        // Mock market data
        MarketData {
            symbol: "BTC/USD".to_string(),
            price: 65000.0,
            volume: 1000.0,
        }
    }

    async fn fetch_phase_state(&self) -> PhaseState {
        let api_url = std::env::var("ARKHE_API_URL").unwrap_or_else(|_| "http://localhost:3000".to_string());
        let url = format!("{}/api/consensus", api_url);
        
        match reqwest::get(&url).await {
            Ok(resp) => {
                if let Ok(json) = resp.json::<serde_json::Value>().await {
                    let sigma = json["sigma"].as_f64().unwrap_or(1.0);
                    // We'll use sigma for both omega and sigma in this mock, 
                    // or fetch lambda if available. The API returns { sigma: number }
                    return PhaseState {
                        omega: sigma,
                        sigma: sigma,
                    };
                }
            }
            Err(e) => {
                println!("[TradingEngine] Error fetching consensus state: {}", e);
            }
        }
        
        // Fallback mock phase state
        PhaseState {
            omega: 0.98,
            sigma: 1.0,
        }
    }

    async fn execute_action(&self, action: TradeAction) {
        // Mock execution
        println!("[TradingEngine] Executed: {} {} at market price", action.side, action.symbol);
    }
}

#[derive(Debug, Clone)]
pub struct TradeAction {
    pub symbol: String,
    pub side: String, // "BUY" or "SELL"
    pub amount: f64,
}

pub trait Strategy: Send + Sync {
    fn evaluate(&mut self, market: &MarketData, phase: &PhaseState) -> Option<TradeAction>;
}

pub struct CoherenceFilterStrategy {
    threshold: f64,
}

impl CoherenceFilterStrategy {
    pub fn new() -> Self {
        Self { threshold: 0.95 }
    }
}

impl Strategy for CoherenceFilterStrategy {
    fn evaluate(&mut self, market: &MarketData, phase: &PhaseState) -> Option<TradeAction> {
        if phase.omega < self.threshold {
            // High entropy, reduce exposure
            Some(TradeAction {
                symbol: market.symbol.clone(),
                side: "SELL".to_string(),
                amount: 0.1, // Sell 10%
            })
        } else {
            None
        }
    }
}

pub struct ConsensusHedgeStrategy {
    threshold: f64,
}

impl ConsensusHedgeStrategy {
    pub fn new() -> Self {
        Self { threshold: 0.80 }
    }
}

impl Strategy for ConsensusHedgeStrategy {
    fn evaluate(&mut self, market: &MarketData, phase: &PhaseState) -> Option<TradeAction> {
        if phase.sigma < self.threshold {
            // Consensus is failing, hedge aggressively
            Some(TradeAction {
                symbol: "GOLD/USD".to_string(), // Hedge asset
                side: "BUY".to_string(),
                amount: 1.0,
            })
        } else {
            None
        }
    }
}

#[tokio::main]
async fn main() {
    println!("Starting Arkhe Phase-Based Trading Engine...");
    let mut engine = TradingEngine::new();
    engine.run().await;
}
