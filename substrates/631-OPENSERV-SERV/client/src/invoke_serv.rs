// src/invoke_serv.rs
use ed25519_dalek::{Verifier, VerifyingKey, Signature};
use sha3::{Sha3_256, Digest};
use base64::Engine as _;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
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

/// Realiza uma invocação HTTP ao gateway e valida o envelope assinado.
/// Retorna (output, phi_score) ou erro.
pub async fn invoke_serv(
    gateway_url: &str,
    gateway_pubkey_hex: &str,
    serv_id: &str,
    input_data: &[u8],
    time_direction: &str,
) -> Result<(Vec<u8>, f64), Box<dyn std::error::Error>> {
    let client = reqwest::Client::new();

    // 1. Instanciar chave pública pinada do gateway
    let pk_bytes = hex::decode(gateway_pubkey_hex)?;
    let pk_array: [u8; 32] = pk_bytes.try_into().map_err(|_| "Invalid gateway pubkey length")?;
    let vk = VerifyingKey::from_bytes(&pk_array)?;

    // 2. Preparar requisição
    let req = InvokeRequest {
        input: base64::engine::general_purpose::STANDARD.encode(input_data),
        time_direction: time_direction.to_string(),
    };

    // 3. Enviar ao gateway
    let envelope: SignedEnvelope = client
        .post(format!("{}/serv/{}/invoke", gateway_url, serv_id))
        .json(&req)
        .send().await?.json().await?;

    // 4. Validar envelope (hashes + assinatura)
    let in_hash = sha3_256(input_data);
    if hex::encode(&in_hash) != envelope.input_hash {
        return Err("input_hash mismatch".into());
    }

    let out_bytes = base64::engine::general_purpose::STANDARD.decode(&envelope.output)?;
    let out_hash = sha3_256(&out_bytes);
    if hex::encode(&out_hash) != envelope.output_hash {
        return Err("output_hash mismatch".into());
    }

    let phi_int = (envelope.phi_score * 10000.0) as u32;
    let mut msg = Vec::new();
    msg.extend_from_slice(&in_hash);
    msg.extend_from_slice(&out_hash);
    msg.extend_from_slice(&phi_int.to_le_bytes());
    msg.extend_from_slice(envelope.timestamp.as_bytes());
    msg.extend_from_slice(envelope.gateway_id.as_bytes());

    let sig_bytes = hex::decode(&envelope.signature)?;
    let signature = Signature::from_slice(&sig_bytes)?;
    vk.verify(&msg, &signature)?;

    Ok((out_bytes, envelope.phi_score))
}
