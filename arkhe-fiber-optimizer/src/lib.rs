use tonic::{Request, Response, Status};
use tokio_stream::Stream;
use std::pin::Pin;

pub mod fiber {
    tonic::include_proto!("arkhe.fiber");
}

pub struct FiberOptimizerService {}

impl FiberOptimizerService {
    pub fn new() -> Self {
        Self {}
    }
}

impl Default for FiberOptimizerService {
    fn default() -> Self {
        Self::new()
    }
}

#[tonic::async_trait]
impl fiber::fiber_optimizer_server::FiberOptimizer for FiberOptimizerService {
    type OptimizeLinkStream = Pin<Box<dyn Stream<Item = Result<fiber::OptimizationUpdate, Status>> + Send>>;

    async fn optimize_link(
        &self,
        req: Request<fiber::LinkRequest>,
    ) -> Result<Response<Self::OptimizeLinkStream>, Status> {
        let req = req.into_inner();
        let mut updates = Vec::new();

        // 1. Calcular correção de clock via EPR (simulada)
        let clock_offset = if req.epr_sample.len() > 8 {
            let correlation = req.epr_sample[0..8].iter().fold(0u64, |acc, b| (acc << 8) | *b as u64);
            (correlation.wrapping_mul(100) % 1000) as i32 - 500 // offset simulado em ps
        } else {
            0
        };

        // 2. Decidir esquema de FEC baseado na correlação EPR
        let fec = if clock_offset.abs() < 100 {
            "LDPC_EPR_BOOSTED".to_string()
        } else {
            "LDPC_STANDARD".to_string()
        };

        // 3. Ajuste de OSNR alvo e dithering
        let new_osnr = req.current_osnr + (if fec.starts_with("LDPC_EPR") { 2.0 } else { 0.0 });
        let dithering_amp = 0.05 * (req.current_ber / 1e-6).sqrt();

        let update = fiber::OptimizationUpdate {
            new_osnr_target: new_osnr,
            dithering_amplitude: dithering_amp,
            fec_scheme: fec,
            clock_sync_adjust: clock_offset.abs() > 10,
            clock_offset_correction_ps: clock_offset as f64,
        };
        updates.push(Ok(update));

        let output = tokio_stream::iter(updates);
        Ok(Response::new(Box::pin(output)))
    }

    async fn get_clock_sync_status(&self, req: Request<fiber::NodeId>) -> Result<Response<fiber::ClockStatus>, Status> {
        let _node = req.into_inner().id;
        Ok(Response::new(fiber::ClockStatus {
            drift_ps: 12.3,
            epr_correlation: 0.998,
        }))
    }
}
