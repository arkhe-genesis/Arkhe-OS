use dashmap::DashMap;

pub struct MeshConfig {
    pub bind_addr: std::net::SocketAddr,
    pub static_nodes: Vec<NodeId>,
}

impl MeshConfig {
    pub fn static_nodes(&self) -> Vec<NodeId> {
        self.static_nodes.clone()
    }
}

#[derive(Clone, Eq, PartialEq, Hash)]
pub struct NodeId {
    pub addr: std::net::SocketAddr,
}

pub struct OrbitalMesh {
    pub listener: quinn::Endpoint,
    pub clients: DashMap<NodeId, quinn::Connection>,
    pub config: MeshConfig,
}

lazy_static::lazy_static! {
    static ref SERVER_CONFIG: quinn::ServerConfig = {
        let cert = rcgen::generate_simple_self_signed(vec!["localhost".into()]).unwrap();
        let cert_der = rustls::Certificate(cert.serialize_der().unwrap());
        let priv_key = rustls::PrivateKey(cert.serialize_private_key_der());
        let mut server_crypto = rustls::ServerConfig::builder()
            .with_safe_defaults()
            .with_no_client_auth()
            .with_single_cert(vec![cert_der], priv_key)
            .unwrap();
        server_crypto.alpn_protocols = vec![b"hq-29".to_vec()];
        quinn::ServerConfig::with_crypto(std::sync::Arc::new(server_crypto))
    };

    static ref CLIENT_CONFIG: quinn::ClientConfig = {
        // We will just use the standard rustls cert verifier or no config if the original code didn't specify one
        let mut client_crypto = rustls::ClientConfig::builder()
            .with_safe_defaults()
            .with_root_certificates(rustls::RootCertStore::empty())
            .with_no_client_auth();
        client_crypto.alpn_protocols = vec![b"hq-29".to_vec()];
        quinn::ClientConfig::new(std::sync::Arc::new(client_crypto))
    };
}

impl OrbitalMesh {
    /// Creates a mesh using the QUIC transport protocol.
    pub async fn new(config: MeshConfig) -> Self {
        let listener = quinn::Endpoint::server(SERVER_CONFIG.clone(), config.bind_addr)
            .expect("Failed to bind orbital mesh endpoint");
        let clients = DashMap::new();
        // Populate known nodes from constellation database
        for node_id in config.static_nodes() {
            let endpoint = quinn::Endpoint::client("0.0.0.0:0".parse().unwrap()).expect("client");
            // The original code passed SERVER_CONFIG to connect_with. Let's cast it to ClientConfig if possible,
            // or just use connect_with(CLIENT_CONFIG)
            let conn = endpoint
                .connect_with(CLIENT_CONFIG.clone(), node_id.addr, "localhost")
                .expect("connection failed");
            clients.insert(node_id, conn.await.unwrap());
        }
        Self {
            listener,
            clients,
            config,
        }
    }
}
