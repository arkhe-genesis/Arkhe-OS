// src/main.rs — ARKHE Serv Client (Substrate 631)
use ed25519_dalek::{Verifier, VerifyingKey, Signature};
use sha3::{Sha3_256, Digest};
use base64::Engine as _;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
struct SignedEnvelope {
    input_hash: String,
    output_hash: String,
    output: String,
    phi_score: f64,
    timestamp: String,
    gateway_id: String,
    signature: String,
}

#[derive(Debug, Deserialize)]
struct PubkeyResponse {
    gateway_id: String,
    public_key_hex: String,
}

#[derive(Debug, Serialize)]
struct InvokeRequest {
    input: String,
    time_direction: String,
}

fn sha3_256(data: &[u8]) -> Vec<u8> {
    let mut h = Sha3_256::new();
    h.update(data);
    h.finalize().to_vec()
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let url = std::env::var("GATEWAY_URL")
        .unwrap_or_else(|_| "http://localhost:50051".into());

    // 1. Obter chave pública
    let client = reqwest::Client::new();
    let pk: PubkeyResponse = client
        .get(format!("{}/gateway_pubkey", url))
        .send().await?.json().await?;
    let pk_bytes = hex::decode(&pk.public_key_hex)?;
    let vk = VerifyingKey::from_bytes(&pk_bytes.try_into().unwrap())?;
    println!("[client] Gateway {} | pubkey {}", pk.gateway_id, &pk.public_key_hex[..16]);

    // 2. Invocar Serv paper-reviewer
    let input = br"\documentclass{article}\begin{document}ARKHE OS Kernel\end{document}";
    let req = InvokeRequest {
        input: base64::engine::general_purpose::STANDARD.encode(input),
        time_direction: "+1".into(),
    };
    let env: SignedEnvelope = client
        .post(format!("{}/serv/paper-reviewer/invoke", url))
        .json(&req)
        .send().await?.json().await?;

    // 3. Validar envelope (igual ao kernel fará)
    let in_hash = sha3_256(input);
    assert_eq!(hex::encode(&in_hash), env.input_hash, "input_hash mismatch");
    let out_bytes = base64::engine::general_purpose::STANDARD.decode(&env.output)?;
    let out_hash = sha3_256(&out_bytes);
    assert_eq!(hex::encode(&out_hash), env.output_hash, "output_hash mismatch");

    let phi = (env.phi_score * 10000.0) as u32;
    let mut msg = Vec::new();
    msg.extend(&in_hash);
    msg.extend(&out_hash);
    msg.extend(&phi.to_le_bytes());
    msg.extend(env.timestamp.as_bytes());
    msg.extend(env.gateway_id.as_bytes());

    let sig_bytes = hex::decode(&env.signature)?;
    let sig = Signature::from_slice(&sig_bytes)?;
    vk.verify(&msg, &sig)?;

    println!("✅ Envelope válido! Φ = {:.4}", env.phi_score);
    println!("{}", String::from_utf8_lossy(&out_bytes));
    Ok(())
}
