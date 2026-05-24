use axum::{
    extract::Path,
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use ed25519_dalek::{Signer, SigningKey, VerifyingKey};
use serde::{Deserialize, Serialize};
use sha3::{Digest, Sha3_256};
use std::sync::Arc;
use tokio::sync::Mutex;
use base64::Engine;

const GATEWAY_ID: &str = "openserv-gateway-01";

// ═══════════════════════════════════════════════════════════════════════════════
// Models
// ═══════════════════════════════════════════════════════════════════════════════

#[derive(Debug, Deserialize)]
struct InvokeRequest {
    input: String,        // base64
    #[serde(default = "default_time_direction")]
    time_direction: String,
}

fn default_time_direction() -> String { "+1".to_string() }

#[derive(Debug, Serialize)]
struct SignedEnvelope {
    input_hash: String,
    output_hash: String,
    output: String,
    phi_score: f64,
    timestamp: String,
    gateway_id: String,
    signature: String,
}

#[derive(Debug, Serialize)]
struct PubkeyResponse {
    gateway_id: String,
    public_key_hex: String,
}

#[derive(Debug, Serialize)]
struct HealthResponse {
    status: String,
    gateway_id: String,
}

struct AppState {
    signing_key: SigningKey,
}

// ═══════════════════════════════════════════════════════════════════════════════
// Core Logic
// ═══════════════════════════════════════════════════════════════════════════════

fn sha3_256(data: &[u8]) -> Vec<u8> {
    let mut hasher = Sha3_256::new();
    hasher.update(data);
    hasher.finalize().to_vec()
}

fn build_signed_envelope(
    input_data: &[u8],
    output_data: &[u8],
    phi_score: f64,
    signing_key: &SigningKey,
) -> SignedEnvelope {
    let timestamp = chrono::Utc::now().to_rfc3339();
    let input_hash = sha3_256(input_data);
    let output_hash = sha3_256(output_data);

    let phi_int = (phi_score * 10000.0) as u32;
    let mut message = Vec::new();
    message.extend_from_slice(&input_hash);
    message.extend_from_slice(&output_hash);
    message.extend_from_slice(&phi_int.to_le_bytes());
    message.extend_from_slice(timestamp.as_bytes());
    message.extend_from_slice(GATEWAY_ID.as_bytes());

    let signature = signing_key.sign(&message);

    SignedEnvelope {
        input_hash: hex::encode(&input_hash),
        output_hash: hex::encode(&output_hash),
        output: base64::engine::general_purpose::STANDARD.encode(output_data),
        phi_score,
        timestamp,
        gateway_id: GATEWAY_ID.to_string(),
        signature: hex::encode(signature.to_bytes()),
    }
}

fn mock_reviewer(input_data: &[u8]) -> (Vec<u8>, f64) {
    let text = String::from_utf8_lossy(input_data);
    let critique = format!(
        "## Reviewer Report (AAAI Style)\n\n\
         **Originality**: Adequate novelty.\n\
         **Clarity**: The text of {} chars needs minor revision.\n\
         **Recommendation**: Accept with minor revisions (6/10)\n",
        text.len()
    );
    (critique.into_bytes(), 0.72)
}

// ═══════════════════════════════════════════════════════════════════════════════
// Handlers
// ═══════════════════════════════════════════════════════════════════════════════

async fn health() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "ok".to_string(),
        gateway_id: GATEWAY_ID.to_string(),
    })
}

async fn get_pubkey(state: Arc<Mutex<AppState>>) -> Json<PubkeyResponse> {
    let state = state.lock().await;
    let verifying: VerifyingKey = (&state.signing_key).into();
    Json(PubkeyResponse {
        gateway_id: GATEWAY_ID.to_string(),
        public_key_hex: hex::encode(verifying.as_bytes()),
    })
}

async fn invoke_serv(
    Path(serv_id): Path<String>,
    state: Arc<Mutex<AppState>>,
    Json(req): Json<InvokeRequest>,
) -> Result<Json<SignedEnvelope>, StatusCode> {
    let input_data = base64::engine::general_purpose::STANDARD
        .decode(&req.input)
        .map_err(|_| StatusCode::BAD_REQUEST)?;

    let (output_data, phi_score) = match serv_id.as_str() {
        "paper-reviewer" => mock_reviewer(&input_data),
        _ => return Err(StatusCode::NOT_FOUND),
    };

    let (output_data, phi_score) = if req.time_direction == "-1" {
        let mut rev = output_data.clone();
        rev.reverse();
        (rev, 1.0 - phi_score)
    } else {
        (output_data, phi_score)
    };

    let state = state.lock().await;
    let envelope = build_signed_envelope(&input_data, &output_data, phi_score, &state.signing_key);
    Ok(Json(envelope))
}

// ═══════════════════════════════════════════════════════════════════════════════
// Main
// ═══════════════════════════════════════════════════════════════════════════════

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut csprng = rand::thread_rng();
    let signing_key = SigningKey::generate(&mut csprng);
    let verifying: VerifyingKey = (&signing_key).into();
    println!("[631] Axum Gateway starting on :50051");
    println!("[631] Public key: {}", hex::encode(verifying.as_bytes()));

    let state = Arc::new(Mutex::new(AppState { signing_key }));

    let app = Router::new()
        .route("/health", get(health))
        .route("/gateway_pubkey", get({
            let state = Arc::clone(&state);
            move || get_pubkey(state)
        }))
        .route("/serv/{serv_id}/invoke", post({
            let state = Arc::clone(&state);
            move |path, req| invoke_serv(path, state, req)
        }))
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:50051").await?;
    axum::serve(listener, app).await?;
    Ok(())
}
