use ed25519_dalek::{VerifyingKey, Signature, Verifier};
use sha3::{Sha3_256, Digest};
use base64::Engine as _;
use serde::{Deserialize, Serialize};
use std::error::Error;

// ═══════════════════════════════════════════════════════════════════════════════
// Signed Result Envelope (identical to gateway's structure)
// ═══════════════════════════════════════════════════════════════════════════════

#[derive(Debug, Serialize, Deserialize, Clone)]
struct SignedEnvelope {
    input_hash: String,
    output_hash: String,
    output: String,        // base64
    phi_score: f64,
    timestamp: String,
    gateway_id: String,
    signature: String,     // hex
}

#[derive(Debug, Serialize, Deserialize)]
struct InvokeRequest {
    input: String,         // base64
    time_direction: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct PubkeyResponse {
    gateway_id: String,
    public_key_hex: String,
}

// ═══════════════════════════════════════════════════════════════════════════════
// Core: invoke_serv
// ═══════════════════════════════════════════════════════════════════════════════

fn sha3_256(data: &[u8]) -> Vec<u8> {
    let mut hasher = Sha3_256::new();
    hasher.update(data);
    hasher.finalize().to_vec()
}

struct ServClient {
    gateway_url: String,
    verifying_key: VerifyingKey,
}

impl ServClient {
    /// Creates a new client by fetching the gateway's public key.
    async fn new(gateway_url: &str) -> Result<Self, Box<dyn Error>> {
        let client = reqwest::Client::new();
        let resp: PubkeyResponse = client
            .get(format!("{}/gateway_pubkey", gateway_url))
            .send()
            .await?
            .json()
            .await?;

        let pubkey_bytes = hex::decode(&resp.public_key_hex)?;
        let verifying_key = VerifyingKey::from_bytes(
            &pubkey_bytes.try_into().map_err(|_| "invalid pubkey length")?
        )?;

        Ok(ServClient {
            gateway_url: gateway_url.to_string(),
            verifying_key,
        })
    }

    /// Invokes a Serv and returns the validated output with phi_score.
    async fn invoke_serv(
        &self,
        serv_id: &str,
        input_data: &[u8],
        time_direction: &str,
    ) -> Result<(Vec<u8>, f64), Box<dyn Error>> {
        let client = reqwest::Client::new();
        let input_b64 = base64::engine::general_purpose::STANDARD.encode(input_data);

        let request = InvokeRequest {
            input: input_b64,
            time_direction: time_direction.to_string(),
        };

        let envelope: SignedEnvelope = client
            .post(format!("{}/serv/{}/invoke", self.gateway_url, serv_id))
            .json(&request)
            .send()
            .await?
            .json()
            .await?;

        // Validate the receipt
        self.validate_envelope(input_data, &envelope)?;

        // Decode output
        let output = base64::engine::general_purpose::STANDARD.decode(&envelope.output)?;

        Ok((output, envelope.phi_score))
    }

    /// Validates a Signed Result Envelope:
    /// - input_hash matches local computation
    /// - output_hash matches decoded output
    /// - Ed25519 signature is valid
    fn validate_envelope(&self, input_data: &[u8], envelope: &SignedEnvelope) -> Result<(), Box<dyn Error>> {
        // 1. Verify input_hash
        let computed_input_hash = sha3_256(input_data);
        let envelope_input_hash = hex::decode(&envelope.input_hash)?;
        if computed_input_hash.as_slice() != envelope_input_hash.as_slice() {
            return Err("input_hash mismatch".into());
        }

        // 2. Decode output and verify output_hash
        let output_data = base64::engine::general_purpose::STANDARD.decode(&envelope.output)?;
        let computed_output_hash = sha3_256(&output_data);
        let envelope_output_hash = hex::decode(&envelope.output_hash)?;
        if computed_output_hash.as_slice() != envelope_output_hash.as_slice() {
            return Err("output_hash mismatch".into());
        }

        // 3. Verify signature
        let phi_int = (envelope.phi_score * 10000.0) as u32;
        let mut message = Vec::new();
        message.extend_from_slice(&computed_input_hash);
        message.extend_from_slice(&computed_output_hash);
        message.extend_from_slice(&phi_int.to_le_bytes());
        message.extend_from_slice(envelope.timestamp.as_bytes());
        message.extend_from_slice(envelope.gateway_id.as_bytes());

        let signature_bytes = hex::decode(&envelope.signature)?;
        let signature = Signature::from_slice(&signature_bytes)?;
        self.verifying_key.verify(&message, &signature)?;

        Ok(())
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Testes
// ═══════════════════════════════════════════════════════════════════════════════

#[cfg(test)]
mod tests {
    use super::*;
    use ed25519_dalek::{SigningKey, Signer};
    use sha3::Digest;

    fn sha3_256(data: &[u8]) -> Vec<u8> {
        let mut hasher = Sha3_256::new();
        hasher.update(data);
        hasher.finalize().to_vec()
    }

    fn create_test_envelope(signing_key: &SigningKey, input: &[u8], output: &[u8], phi: f64) -> SignedEnvelope {
        let input_hash = sha3_256(input);
        let output_hash = sha3_256(output);
        let phi_int = (phi * 10000.0) as u32;
        let timestamp = "2026-05-28T19:00:00Z";
        let gateway_id = "test-gateway";

        let mut message = Vec::new();
        message.extend_from_slice(&input_hash);
        message.extend_from_slice(&output_hash);
        message.extend_from_slice(&phi_int.to_le_bytes());
        message.extend_from_slice(timestamp.as_bytes());
        message.extend_from_slice(gateway_id.as_bytes());

        let signature = signing_key.sign(&message);

        SignedEnvelope {
            input_hash: hex::encode(&input_hash),
            output_hash: hex::encode(&output_hash),
            output: base64::engine::general_purpose::STANDARD.encode(output),
            phi_score: phi,
            timestamp: timestamp.to_string(),
            gateway_id: gateway_id.to_string(),
            signature: hex::encode(signature.to_bytes()),
        }
    }

    #[test]
    fn test_valid_envelope() {
        let signing_key = SigningKey::generate(&mut rand::thread_rng());
        let verifying_key: VerifyingKey = (&signing_key).into();

        let input = b"Este e o paper original em LaTeX...";
        let output = b"## Reviewer Report\nClarity: needs improvement.";
        let phi = 0.72;

        let envelope = create_test_envelope(&signing_key, input, output, phi);

        let client = ServClient {
            gateway_url: "http://localhost:50051".to_string(),
            verifying_key,
        };

        assert!(client.validate_envelope(input, &envelope).is_ok());
    }

    #[test]
    fn test_tampered_input_hash_rejected() {
        let signing_key = SigningKey::generate(&mut rand::thread_rng());
        let verifying_key: VerifyingKey = (&signing_key).into();

        let input = b"Original paper content";
        let output = b"Review output";
        let mut envelope = create_test_envelope(&signing_key, input, output, 0.5);

        // Tamper: change input_hash to something else
        envelope.input_hash = hex::encode(sha3_256(b"tampered input"));

        let client = ServClient {
            gateway_url: "http://localhost:50051".to_string(),
            verifying_key,
        };

        assert!(client.validate_envelope(input, &envelope).is_err());
    }

    #[test]
    fn test_wrong_signature_rejected() {
        let signing_key = SigningKey::generate(&mut rand::thread_rng());
        let wrong_key = SigningKey::generate(&mut rand::thread_rng());
        let verifying_key: VerifyingKey = (&signing_key).into();

        let input = b"Paper content";
        let output = b"Review";
        let mut envelope = create_test_envelope(&wrong_key, input, output, 0.5);

        let client = ServClient {
            gateway_url: "http://localhost:50051".to_string(),
            verifying_key,
        };

        assert!(client.validate_envelope(input, &envelope).is_err());
    }

    #[test]
    fn test_tampered_output_hash_rejected() {
        let signing_key = SigningKey::generate(&mut rand::thread_rng());
        let verifying_key: VerifyingKey = (&signing_key).into();

        let input = b"Original";
        let output = b"Original output";
        let mut envelope = create_test_envelope(&signing_key, input, output, 0.5);

        // Tamper output but not output_hash (or vice versa)
        envelope.output = base64::engine::general_purpose::STANDARD.encode(b"Tampered output");

        let client = ServClient {
            gateway_url: "http://localhost:50051".to_string(),
            verifying_key,
        };

        assert!(client.validate_envelope(input, &envelope).is_err());
    }

    #[test]
    fn test_phi_score_affects_signature() {
        let signing_key = SigningKey::generate(&mut rand::thread_rng());
        let verifying_key: VerifyingKey = (&signing_key).into();

        let input = b"Test";
        let output = b"Output";

        let envelope1 = create_test_envelope(&signing_key, input, output, 0.5);
        let envelope2 = create_test_envelope(&signing_key, input, output, 0.6);

        // Signatures should be different because phi_score differs
        assert_ne!(envelope1.signature, envelope2.signature);

        let client = ServClient {
            gateway_url: "http://localhost:50051".to_string(),
            verifying_key,
        };

        // But both should validate with their own phi_score
        assert!(client.validate_envelope(input, &envelope1).is_ok());
        assert!(client.validate_envelope(input, &envelope2).is_ok());

        // Changing phi_score in envelope without re-signing should fail
        let mut tampered = envelope1.clone();
        tampered.phi_score = 0.6;
        assert!(client.validate_envelope(input, &tampered).is_err());
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Main — exemplo de uso
// ═══════════════════════════════════════════════════════════════════════════════

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    println!("[631] ARKHE Serv Client — invoke_serv example");

    let gateway_url = std::env::var("GATEWAY_URL")
        .unwrap_or_else(|_| "http://localhost:50051".to_string());

    let client = ServClient::new(&gateway_url).await?;
    println!("[631] Connected to gateway at {}", gateway_url);

    let latex_input = br#"\documentclass{article}
\begin{document}
\section{Introduction}
This paper presents a novel approach to artificial consciousness.
Our method combines tokenic evolution with plasma entropy harvesting.
\end{document}"#;

    match client.invoke_serv("paper-reviewer", latex_input, "+1").await {
        Ok((critique, phi_score)) => {
            println!("\n[631] ✅ Serv invocation successful!");
            println!("[631] Phi Score: {:.4}", phi_score);
            println!("[631] Critique:\n{}", String::from_utf8_lossy(&critique));
        }
        Err(e) => {
            eprintln!("[631] ❌ Serv invocation failed: {}", e);
        }
    }

    Ok(())
}
