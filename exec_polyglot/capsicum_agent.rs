use sha3::{Digest, Sha3_256};
use std::time::{SystemTime, UNIX_EPOCH};

fn main() {
    let agent_id = "rust_agent_01";
    let operation = "verify_identity";
    let payload = b"arkhe_canon";

    let mut hasher = Sha3_256::new();
    hasher.update(agent_id.as_bytes());
    hasher.update(operation.as_bytes());
    hasher.update(payload);
    hasher.update(
        &SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs()
            .to_be_bytes(),
    );

    let seal = format!("{:x}", hasher.finalize());
    println!("🦀 Rust Agent: {} executou '{}' | Selo={}", agent_id, operation, &seal[..16]);
}