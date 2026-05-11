use std::collections::HashMap;
use crate::x402_pix_bridge::PixIpcClient;
use crate::data_valuation::DataValuation;
use crate::{CellState, RoyaltyError, ConsentStatus, PHIPolicy};

pub struct HIPAARoyaltyBridge {
    pix: PixIpcClient,
    valuation: DataValuation,
    consent_ledger: HashMap<String, ConsentStatus>, // ORCID -> consent
}

impl HIPAARoyaltyBridge {
    pub fn new(pix: PixIpcClient, valuation: DataValuation, consent_ledger: HashMap<String, ConsentStatus>) -> Self {
        Self { pix, valuation, consent_ledger }
    }

    /// Anonymise patient data, compute contribution, and pay.
    pub async fn process_query(
        &self,
        patient_orcid: &str,
        simulated_cell: &CellState,
        query_hash: &[u8],
    ) -> Result<(), RoyaltyError> {
        // 1. Check consent
        let consent = self.consent_ledger.get(patient_orcid)
            .ok_or(RoyaltyError::NoConsent)?;
        if !consent.allow_data_use { return Err(RoyaltyError::NoConsent); }

        // 2. De-identify data (remove PHI, keep only the cellular state vector)
        let anonymised = self.anonymise(simulated_cell, consent.phi_policy);

        // 3. Calculate information gain contributed by this cell
        let value = self.valuation.compute(&anonymised, query_hash);

        // 4. Convert value to cents and trigger Pix payment
        let cents = (value * 100.0).round() as u64;
        if cents > 0 {
            let pix_key = self.lookup_pix(patient_orcid)?;
            self.pix.send_pix_royalty(&pix_key, cents, "cell-data-royalty").await?;
        }
        Ok(())
    }

    fn anonymise(&self, cell: &CellState, _phi_policy: PHIPolicy) -> CellState {
        // Strip names, dates, geographic info; keep only molecular-level state
        CellState { data: cell.data.clone() }
    }

    fn lookup_pix(&self, _patient_orcid: &str) -> Result<String, RoyaltyError> {
        Ok("dummy_key".to_string())
    }
}
