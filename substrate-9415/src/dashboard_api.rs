use axum::{
    extract::Path,
    routing::get,
    Json, Router,
};
use serde_json::json;

use crate::risk_entropy::compute_risk;
use crate::explanation_engine::ExplanationEngine;

pub async fn get_risk(Path(_id): Path<String>) -> Json<serde_json::Value> {
    // Mock history logic
    let mock_history = vec![0.12, 0.15, -0.05, 0.20, -0.10, 0.30];
    let profile = compute_risk(&mock_history);
    Json(json!(profile))
}

pub async fn get_liquidity(Path(_id): Path<String>) -> Json<serde_json::Value> {
    // Mock
    Json(json!({
        "tvl": 10200000.0,
        "concentration": "81% in 3 addresses",
        "proof_root": "4a3f2c"
    }))
}

pub async fn get_audit(Path(_id): Path<String>) -> Json<serde_json::Value> {
    Json(json!({
        "status": "APROVADO",
        "proof": "ipfs://Qm..."
    }))
}

pub async fn get_compliance(Path(_id): Path<String>) -> Json<serde_json::Value> {
    Json(json!({
        "jurisdiction": "Brasil (CVM)",
        "compliant": true,
        "kyc_required": true
    }))
}

pub async fn get_explanation(Path(_id): Path<String>) -> Json<serde_json::Value> {
    let mock_history = vec![0.12, 0.15, -0.05, 0.20, -0.10, 0.30];
    let profile = compute_risk(&mock_history);

    Json(json!({
        "apy_explanation": ExplanationEngine::explain_apy(profile.apy_mean * 100.0),
        "risk_explanation": ExplanationEngine::explain_risk(&profile.risk_level, profile.entropy_30d),
        "liquidity_explanation": ExplanationEngine::explain_liquidity(10200000.0)
    }))
}

pub fn app() -> Router {
    Router::new()
        .route("/pool/:id/risco", get(get_risk))
        .route("/pool/:id/liquidez", get(get_liquidity))
        .route("/pool/:id/contrato", get(get_audit))
        .route("/pool/:id/compliance", get(get_compliance))
        .route("/pool/:id/explicacao", get(get_explanation))
}
