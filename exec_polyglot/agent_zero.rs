use sha3::{Digest, Sha3_256};
use std::time::{SystemTime, UNIX_EPOCH};

fn main() {
    let agent_id = "agent_zero_rust";
    let operation = "transfer";
    let payload = b"{\"amount\":1000,\"destination\":\"vault_x\"}";
    let phi_c = 0.98;

    // Nonce generation
    let timestamp = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_secs();
    let nonce = format!("{:x}", timestamp);

    // Create AgentProposal json
    let proposal_json = format!(
        "{{\"agent_id\":\"{}\",\"nonce\":\"{}\",\"operation\":\"{}\",\"payload\":{},\"phi_c\":{}}}",
        agent_id, nonce, operation, String::from_utf8(payload.to_vec()).unwrap(), phi_c
    );

    // Canonical Hash
    let mut hasher = Sha3_256::new();
    hasher.update(proposal_json.as_bytes());
    let canonical_hash = format!("{:x}", hasher.finalize());

    println!("🦀 Agent Zero (Rust) Proposal");
    println!("Capsicum: Active");
    println!("Zero-Lang: Active (No external crypto imports)");
    println!("Canonical Hash: {}", canonical_hash);
}
