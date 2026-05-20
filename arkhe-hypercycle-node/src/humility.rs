use crate::invariants::GHOST;
use sha3::{Sha3_256, Digest};

#[derive(Debug, Clone, PartialEq)]
pub enum HumilityVerdict {
    Acceptable { score: f64 },
    Rejected { score: f64, reason: String },
}

pub struct EpistemicHumilityEngine;

impl EpistemicHumilityEngine {
    pub fn evaluate(complexity: f64, task_type: &str,
                    has_attestation: bool) -> HumilityVerdict {
        let base = match task_type {
            "code_execution" | "ai_inference" => GHOST * 1.1,
            "unverified_claim" | "speculative" => GHOST * 0.7,
            _ => GHOST,
        };

        let attestation_bonus = if has_attestation { 0.05 } else { 0.0 };
        let complexity_factor = (complexity * 0.3).min(0.2);
        let score = (base + attestation_bonus + complexity_factor).min(0.99);

        if score >= GHOST {
            HumilityVerdict::Acceptable { score }
        } else {
            HumilityVerdict::Rejected {
                score,
                reason: format!(
                    "Humility {:.4} < Ghost {:.4}: task lacks epistemic humility",
                    score, GHOST
                ),
            }
        }
    }

    pub fn compute_attestation(task_id: &str, node_id: &str,
                               result_hash: &str, humility: f64) -> String {
        let input = format!("{}:{}:{}:{:.4}", task_id, node_id, result_hash, humility);
        hex::encode(Sha3_256::digest(input.as_bytes()))
    }
}