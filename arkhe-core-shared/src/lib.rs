// lib.rs — Canon: ∞.Ω.∇+++.246.multiplatform_core
// Shared canonical core for Arkhe-Core multiplatform SDK
// Compiled to: Android (.aar via JNI), iOS (.xcframework via C interop)

use sha3::{Sha3_256, Digest};
use serde::{Serialize, Deserialize};
use std::collections::HashMap;

// ── Canonical Types ──

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ConstitutionalPrinciple {
    P1Verification,
    P2Redundancy,
    P3SovereignGap,
    P4CrossPlatform,
    P5CanonicalLearning,
    P6AuditableTransparency,
    P7EnergyResource,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PhiCResult {
    pub component: String,
    pub phi_c_score: f32,
    pub timestamp: u64,
    pub temporal_anchor: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConstitutionalVerification {
    pub passed: bool,
    pub violated_principle: Option<ConstitutionalPrinciple>,
    pub message: Option<String>,
}

// ── Φ_C Orchestration (Platform-Agnostic) ──

pub fn calculate_phi_c(component_metrics: &HashMap<String, f32>) -> f32 {
    // Canonical Φ_C calculation algorithm (same on Android/iOS)
    // Weighted average with constitutional penalties

    let mut weighted_sum = 0.0f32;
    let mut total_weight = 0.0f32;

    // Default weights by metric type
    let weights: HashMap<&str, f32> = [
        ("coherence", 0.4),
        ("consistency", 0.3),
        ("auditability", 0.2),
        ("energy_efficiency", 0.1),
    ].iter().cloned().collect();

    for (metric, &value) in component_metrics {
        if let Some(&weight) = weights.get(metric.as_str()) {
            weighted_sum += value * weight;
            total_weight += weight;
        }
    }

    if total_weight > 0.0 {
        let mut phi_c = weighted_sum / total_weight;

        // P3: Enforce Sovereign Gap (Φ_C < 1.0)
        phi_c = phi_c.min(0.9999);

        // P7: Energy penalty if efficiency < threshold
        if let Some(&efficiency) = component_metrics.get("energy_efficiency") {
            if efficiency < 0.7 {
                phi_c *= 0.95; // 5% penalty
            }
        }

        phi_c
    } else {
        0.85 // Default minimum operational Φ_C
    }
}

// ── Constitutional Guardrails (Shared Logic) ──

pub fn verify_constitutional_compliance(
    operation: &str,
    principles: &[ConstitutionalPrinciple],
    context: &HashMap<String, String>
) -> ConstitutionalVerification {

    // P1: Formal specification check
    if principles.contains(&ConstitutionalPrinciple::P1Verification) {
        if !context.contains_key("formal_spec_hash") {
            return ConstitutionalVerification {
                passed: false,
                violated_principle: Some(ConstitutionalPrinciple::P1Verification),
                message: Some(format!("Operation '{}' lacks formal specification", operation)),
            };
        }
    }

    // P3: Sovereign Gap enforcement
    if principles.contains(&ConstitutionalPrinciple::P3SovereignGap) {
        if let Some(phi_c_str) = context.get("current_phi_c") {
            if let Ok(phi_c) = phi_c_str.parse::<f32>() {
                if phi_c >= 1.0 {
                    return ConstitutionalVerification {
                        passed: false,
                        violated_principle: Some(ConstitutionalPrinciple::P3SovereignGap),
                        message: Some(format!("Φ_C = {} violates Sovereign Gap (must be < 1.0)", phi_c)),
                    };
                }
            }
        }
    }

    // P7: Energy budget check
    if principles.contains(&ConstitutionalPrinciple::P7EnergyResource) {
        if let Some(energy_str) = context.get("energy_budget_remaining") {
            if let Ok(remaining) = energy_str.parse::<f32>() {
                if remaining < 0.1 {
                    return ConstitutionalVerification {
                        passed: false,
                        violated_principle: Some(ConstitutionalPrinciple::P7EnergyResource),
                        message: Some("Energy budget exhausted".to_string()),
                    };
                }
            }
        }
    }

    ConstitutionalVerification {
        passed: true,
        violated_principle: None,
        message: None,
    }
}

// ── TemporalChain Anchoring (Canonical Protocol) ──

pub fn generate_canonical_seal(event_type: &str, payload: &HashMap<String, String>) -> String {
    // Canonical SHA3-256 seal generation (identical on all platforms)
    let mut hasher = Sha3_256::new();

    // Sort keys for deterministic hashing
    let mut sorted_payload: Vec<_> = payload.iter().collect();
    sorted_payload.sort_by_key(|(k, _)| *k);

    for (key, value) in sorted_payload {
        hasher.update(format!("{}:{}|", key, value).as_bytes());
    }
    hasher.update(format!("event_type:{}|", event_type).as_bytes());

    let result = hasher.finalize();
    hex::encode(result)
}

// ── FFI Bindings for Platform Integration ──

#[no_mangle]
pub extern "C" fn arkhe_calculate_phi_c_json(
    metrics_json: *const i8
) -> *mut i8 {
    // C FFI binding for iOS/Android interop
    use std::ffi::{CString, CStr};
    use std::os::raw::c_char;

    let metrics_str = unsafe { CStr::from_ptr(metrics_json).to_string_lossy().into_owned() };

    let metrics: HashMap<String, f32> = serde_json::from_str(&metrics_str).unwrap_or_default();
    let result = calculate_phi_c(&metrics);

    let result_json = serde_json::json!({ "phi_c": result });
    let c_str = CString::new(result_json.to_string()).unwrap();
    c_str.into_raw()
}

#[no_mangle]
pub extern "C" fn arkhe_generate_seal(
    event_type: *const i8,
    payload_json: *const i8
) -> *mut i8 {
    use std::ffi::{CString, CStr};

    let event = unsafe { CStr::from_ptr(event_type).to_string_lossy().into_owned() };
    let payload_str = unsafe { CStr::from_ptr(payload_json).to_string_lossy().into_owned() };
    let payload: HashMap<String, String> = serde_json::from_str(&payload_str).unwrap_or_default();

    let seal = generate_canonical_seal(&event, &payload);
    let c_str = CString::new(seal).unwrap();
    c_str.into_raw()
}