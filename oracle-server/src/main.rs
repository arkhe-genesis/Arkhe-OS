use tonic::{ transport::Server, Request, Response, Status };
use arkhe_oracle::{ oracle_server::{ Oracle, OracleServer }, Shard, CreateShardRequest, ListShardsRequest, ListShardsResponse, DestroyShardRequest, GetShardStatusRequest, ShardStatus, Empty };

pub mod arkhe_oracle {
    tonic::include_proto!("arkhe.oracle");
}

pub struct OracleService;

#[tonic::async_trait]
impl Oracle for OracleService {
    async fn create_shard(
        &self,
        request: Request<CreateShardRequest>,
    ) -> Result<Response<Shard>, Status> {
        let req = request.into_inner();
        let shard = Shard {
            shard_id: uuid::Uuid::new_v4().to_string(),
            substrate_id: req.substrate_id,
            motor: req.motor,
            status: "running".into(),
            endpoint: format!("shard-{}.local:50051", req.labels.get("name").unwrap_or(&"default".to_string())),
        };
        Ok(Response::new(shard))
    }

    async fn list_shards(&self, _request: Request<ListShardsRequest>) -> Result<Response<ListShardsResponse>, Status> {
        Ok(Response::new(ListShardsResponse { shards: vec![] }))
    }

    async fn destroy_shard(&self, _request: Request<DestroyShardRequest>) -> Result<Response<Empty>, Status> {
        Ok(Response::new(Empty {}))
    }

    async fn get_shard_status(&self, _request: Request<GetShardStatusRequest>) -> Result<Response<ShardStatus>, Status> {
        Ok(Response::new(ShardStatus { status: "unknown".into() }))
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();
    let addr = "[::1]:50051".parse()?;
    tracing::info!("Oracle listening on {}", addr);
    Server::builder()
        .add_service(OracleServer::new(OracleService))
        .serve(addr)
        .await?;
    Ok(())
}
