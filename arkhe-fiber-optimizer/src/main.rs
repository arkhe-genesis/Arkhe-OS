use arkhe_fiber_optimizer::FiberOptimizerService;
use arkhe_fiber_optimizer::fiber::fiber_optimizer_server::FiberOptimizerServer;
use tonic::transport::Server;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let addr = "[::1]:50051".parse()?;
    let optimizer = FiberOptimizerService::new();

    println!("FiberOptimizerService listening on {}", addr);

    Server::builder()
        .add_service(FiberOptimizerServer::new(optimizer))
        .serve(addr)
        .await?;

    Ok(())
}
