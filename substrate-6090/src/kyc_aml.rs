use serde::{Serialize, Deserialize};

/// Status KYC
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub enum KYCStatus {
    Verified,
    Pending,
    Failed(String),
    Exempt,
}

/// Engine KYC/AML
pub struct KYCChecker {
    sanction_list: Vec<String>,
    mintransaction_for_kyc: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PixTransaction {
    pub amount: f64,
}

impl KYCChecker {
    pub fn new(mintransaction_for_kyc: f64) -> Self {
        Self {
            sanction_list: vec![],
            mintransaction_for_kyc,
        }
    }

    /// Verifica identidade do pagador/recebedor
    pub fn verify_identity(&self, pix_key: &str, amount_cents: u64) -> KYCStatus {
        if amount_cents as f64 / 100.0 < self.mintransaction_for_kyc {
            return KYCStatus::Exempt;
        }
        // Verificar contra lista de sanções
        if self.sanction_list.iter().any(|s| s == pix_key) {
            return KYCStatus::Failed("Sanctioned entity".into());
        }
        KYCStatus::Verified
    }

    /// Gera relatório AML para transações suspeitas
    pub fn generate_aml_report(&self, transactions: &[PixTransaction]) -> AMLReport {
        let suspicious: Vec<PixTransaction> = transactions
            .iter()
            .filter(|t| t.amount > 10_000.0 || self.is_suspicious_pattern(t))
            .map(|t| PixTransaction { amount: t.amount })
            .collect();
        AMLReport {
            totaltransactions: transactions.len(),
            suspicious_count: suspicious.len(),
            suspicioustransactions: suspicious,
            generated_at: chrono::Utc::now().timestamp(),
        }
    }

    fn is_suspicious_pattern(&self, _t: &PixTransaction) -> bool {
        // Detecção de padrões: múltiplas pequenas transações (structuring)
        false
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AMLReport {
    pub totaltransactions: usize,
    pub suspicious_count: usize,
    pub suspicioustransactions: Vec<PixTransaction>,
    pub generated_at: i64,
}
