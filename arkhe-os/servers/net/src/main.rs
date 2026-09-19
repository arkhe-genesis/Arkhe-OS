// servers/net/src/main.rs

pub struct NetworkServer {
    tcp_quic: bool,
    tor_onion: bool,
    nvpn: bool,
    nostr_relay: &'static str,
    ipfs_gateway: &'static str,
    magic_dns: &'static str,
}

impl NetworkServer {
    pub fn new() -> Self {
        Self {
            tcp_quic: true,
            tor_onion: true,
            nvpn: true,
            nostr_relay: "wss://localhost:4737",
            ipfs_gateway: "http://localhost:8080/ipfs/",
            magic_dns: ".arkhe.vpn",
        }
    }

    pub fn start(&self) {
        println!("Starting ARKHE OS Network Server...");
        println!("TCP/QUIC, Tor Onion, NVPN: ON");
        println!("Internal Nostr Relay: {}", self.nostr_relay);
        println!("IPFS Gateway: {}", self.ipfs_gateway);
        println!("MagicDNS Zone: {}", self.magic_dns);
    }
}

fn main() {
    let net = NetworkServer::new();
    net.start();
}
