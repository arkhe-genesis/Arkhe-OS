use std::collections::HashMap;
use crate::usage_token::UsageToken;
use substrate_6070::shannon_entropy;

pub type VendorId = String;

pub fn distribute_monthly_fee(
    user_payment: f64,
    tokens: Vec<UsageToken>,
) -> HashMap<VendorId, f64> {
    let mut total_entropy = 0.0;
    for t in &tokens {
        total_entropy += shannon_entropy(&t.feature_hash);
    }

    let mut payouts = HashMap::new();

    if total_entropy == 0.0 {
        return payouts;
    }

    for token in tokens {
        let weight = shannon_entropy(&token.feature_hash) / total_entropy;
        *payouts.entry(token.vendor_id).or_insert(0.0) += user_payment * weight * 0.85; // 15% cathedral fee
    }
    payouts
}
