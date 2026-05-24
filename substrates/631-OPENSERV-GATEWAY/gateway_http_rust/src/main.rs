use actix_web::{web, App, HttpServer, HttpResponse};
use ed25519_dalek::{SigningKey, VerifyingKey, Signer};
use sha3::{Sha3_256, Digest};
use base64::Engine as _;
use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use chrono::Utc;

const GATEWAY_ID: &str = "openserv-gateway-01";

struct AppState {
    signing_key: SigningKey,
}

#[derive(Deserialize)]
struct InvokeRequest {
    input: String,        // base64
    #[serde(default = "default_time_direction")]
    time_direction: String,
}

fn default_time_direction() -> String { "+1".to_string() }

#[derive(Serialize)]
struct SignedEnvelope {
    input_hash: String,
    output_hash: String,
    output: String,
    phi_score: f64,
    timestamp: String,
    gateway_id: String,
    signature: String,
}

#[derive(Serialize)]
struct PubkeyResponse {
    gateway_id: String,
    public_key_hex: String,
}

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
    let timestamp = Utc::now().to_rfc3339();
    let input_hash = sha3_256(input_data);
    let output_hash = sha3_256(output_data);

    // Mensagem canônica
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

fn mock_reviewer_serv(input_data: &[u8]) -> (Vec<u8>, f64) {
    let text = String::from_utf8_lossy(input_data);
    let critique = format!(
        "## Reviewer Report (AAAI Style)\n\n\
         **Originality**: The submission shows adequate novelty.\n\
         **Clarity**: The text of {} characters requires minor revision.\n\
         **Significance**: Potentially impactful.\n\n\
         **Recommendation**: Accept with minor revisions (score: 6/10)\n",
        text.len()
    );
    (critique.into_bytes(), 0.72)
}

async fn invoke_serv(
    path: web::Path<String>,
    body: web::Json<InvokeRequest>,
    state: web::Data<Mutex<AppState>>,
) -> HttpResponse {
    let serv_id = path.into_inner();

    let input_data = match base64::engine::general_purpose::STANDARD.decode(&body.input) {
        Ok(d) => d,
        Err(_) => return HttpResponse::BadRequest().json(serde_json::json!({"error": "Invalid base64"})),
    };

    let (output_data, phi_score) = match serv_id.as_str() {
        "paper-reviewer" => mock_reviewer_serv(&input_data),
        _ => return HttpResponse::NotFound().json(serde_json::json!({"error": "Unknown serv"})),
    };

    let (output_data, phi_score) = if body.time_direction == "-1" {
        let mut reversed = output_data.clone();
        reversed.reverse();
        (reversed, 1.0 - phi_score)
    } else {
        (output_data, phi_score)
    };

    let state = state.lock().unwrap();
    let envelope = build_signed_envelope(&input_data, &output_data, phi_score, &state.signing_key);

    HttpResponse::Ok().json(envelope)
}

async fn get_pubkey(state: web::Data<Mutex<AppState>>) -> HttpResponse {
    let state = state.lock().unwrap();
    let verifying_key: VerifyingKey = (&state.signing_key).into();
    HttpResponse::Ok().json(PubkeyResponse {
        gateway_id: GATEWAY_ID.to_string(),
        public_key_hex: hex::encode(verifying_key.as_bytes()),
    })
}

async fn health() -> HttpResponse {
    HttpResponse::Ok().json(serde_json::json!({"status": "ok", "gateway_id": GATEWAY_ID}))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    let signing_key = SigningKey::generate(&mut rand::thread_rng());
    let verifying_key: VerifyingKey = (&signing_key).into();
    println!("[631] OpenServ Gateway starting...");
    println!("[631] Gateway ID: {}", GATEWAY_ID);
    println!("[631] Public key: {}", hex::encode(verifying_key.as_bytes()));

    let state = web::Data::new(Mutex::new(AppState { signing_key }));

    HttpServer::new(move || {
        App::new()
            .app_data(state.clone())
            .route("/health", web::get().to(health))
            .route("/gateway_pubkey", web::get().to(get_pubkey))
            .route("/serv/{serv_id}/invoke", web::post().to(invoke_serv))
    })
    .bind("0.0.0.0:50051")?
    .run()
    .await
}
