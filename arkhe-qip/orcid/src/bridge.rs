// ============================================================================
// ORCID → Pix Bridge
// ============================================================================
//
// Mapeia identificadores ORCID para endereços de carteira Pix (ou outras
// carteiras digitais), permitindo que recompensas probabilísticas sejam
// enviadas diretamente ao pesquisador.
//
// Fluxo:
//   1. Pesquisador registra mapeamento ORCID → Pix (paga taxa de registro)
//   2. Sistema verifica ORCID via API externa
//   3. Mapeamento é ancorado na TemporalHashChain
//   4. Quando recompensa é calculada, wallet é resolvido automaticamente
// ============================================================================

use std::collections::HashMap;
use std::sync::{Arc, RwLock};

use serde::{Serialize, Deserialize};
use tracing::{info, warn};
use sha3::Digest;

use crate::auth::{OrcidRecord, OrcidAuthError};
use crate::registry::OrcidRegistry;

/// Representa endereço de carteira digital (Pix, etc.)
#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct WalletAddress {
    pub pix_key: String,           // CPF, telefone, email ou chave aleatória
    pub pix_type: PixKeyType,
    pub bank_code: Option<String>, // Código do banco (para Pix)
    pub account_type: Option<String>,
}

/// Tipos de chave Pix
#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum PixKeyType {
    CPF,
    Phone,
    Email,
    Random,
    CNPJ,
    EVMAddress, // Endereço Ethereum/EVM
}

/// Mapeamento entre ORCID e Wallet
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct OrcidPixMapping {
    pub orcid_id: String,
    pub wallet: WalletAddress,
    pub registered_at: u64,
    pub verification_status: VerificationStatus,
    pub proof_hash: String, // Hash da prova de posse (ancorado na chain)
}

/// Status de verificação do mapeamento
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum VerificationStatus {
    Pending,      // Aguardando verificação
    Verified,     // Verificado com sucesso
    Rejected,     // Rejeitado (ORCID inválido, etc.)
    Suspended,    // Suspenso (possível fraude)
}

/// Pedido de saque (cashout)
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CashoutRequest {
    pub orcid_id: String,
    pub wallet: WalletAddress,
    pub amount_cents: u64, // Centavos de BRL
    pub currency: String,
    pub created_at: u64,
}

/// Erros da bridge
#[derive(Debug)]
pub enum BridgeError {
    OrcidNotFound(String),

    WalletAlreadyRegistered,

    VerificationError(String),

    PaymentError(String),

    NetworkError(String),

    InsufficientBalance,

    ConversionError,
}

/// Bridge principal ORCID ↔ Pix
pub struct OrcidPixBridge {
    /// Cache de mapeamentos ORCID → Wallet
    mappings: Arc<RwLock<HashMap<String, OrcidPixMapping>>>,

    /// Taxa de conversão ARKHE → BRL (1 ARKHE = valor_brl centavos)
    conversion_rate: f64,

    /// Taxa de saque (%)
    cashout_fee_percent: f64,

    /// Mínimo para saque (centavos)
    min_cashout_cents: u64,

    /// API do Banco Central para Pix (placeholder)
    pix_api_url: String,
}

impl OrcidPixBridge {
    /// Criar nova bridge
    pub fn new(conversion_rate: f64, cashout_fee_percent: f64) -> Self {
        Self {
            mappings: Arc::new(RwLock::new(HashMap::new())),
            conversion_rate,
            cashout_fee_percent,
            min_cashout_cents: 50, // R$0,50 mínimo
            pix_api_url: "https://api.bcb.gov.br/pix".to_string(),
        }
    }

    /// Registrar mapeamento ORCID → Wallet
    pub fn register_wallet(
        &mut self,
        orcid_record: &OrcidRecord,
        wallet: WalletAddress,
    ) -> Result<OrcidPixMapping, BridgeError> {
        let orcid_id = &orcid_record.orcid_id;

        let mut mappings = self.mappings.write().unwrap();

        if mappings.contains_key(orcid_id) {
            return Err(BridgeError::WalletAlreadyRegistered);
        }

        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        // Gerar proof hash (hash da chave pública + wallet)
        let proof_data = format!("{}{}{}", orcid_id, wallet.pix_key, now);
        let proof_hash = format!("{:x}", sha3::Keccak256::digest(proof_data.as_bytes()));

        let mapping = OrcidPixMapping {
            orcid_id: orcid_id.clone(),
            wallet,
            registered_at: now,
            verification_status: VerificationStatus::Pending,
            proof_hash,
        };

        mappings.insert(orcid_id.clone(), mapping.clone());

        info!(orcid_id = %orcid_id, "Wallet registered for ORCID");

        Ok(mapping)
    }

    /// Verificar e confirmar mapeamento (via webhook PIX ou confirmação externa)
    pub fn verify_mapping(
        &mut self,
        orcid_id: &str,
        verification_token: &str,
    ) -> Result<(), BridgeError> {
        let mut mappings = self.mappings.write().unwrap();

        if let Some(mapping) = mappings.get_mut(orcid_id) {
            // Em produção: verificar token com API do Banco Central
            if verification_token.len() >= 8 {
                mapping.verification_status = VerificationStatus::Verified;
                info!(orcid_id = %orcid_id, "Wallet verified");
                Ok(())
            } else {
                mapping.verification_status = VerificationStatus::Rejected;
                Err(BridgeError::VerificationError(
                    "Invalid verification token".into(),
                ))
            }
        } else {
            Err(BridgeError::OrcidNotFound(orcid_id.into()))
        }
    }

    /// Resolver ORCID → Wallet
    pub fn resolve_pix(&self, orcid_id: &str) -> Option<WalletAddress> {
        let mappings = self.mappings.read().unwrap();
        mappings
            .get(orcid_id)
            .and_then(|m| {
                if m.verification_status == VerificationStatus::Verified {
                    Some(m.wallet.clone())
                } else {
                    None
                }
            })
    }

    /// Calcular valor da recompensa em centavos
    pub fn calculate_reward_cents(
        &self,
        reward_arkhe: f64,     // Valor em ARKHE tokens
        currency: &str,
    ) -> Result<u64, BridgeError> {
        match currency {
            "BRL" => {
                let cents = (reward_arkhe * self.conversion_rate * 100.0).round() as u64;
                if cents < self.min_cashout_cents {
                    Err(BridgeError::InsufficientBalance)
                } else {
                    Ok(cents)
                }
            }
            "ARKHE" => Ok((reward_arkhe * 100.0).round() as u64), // 1 ARKHE = 100 cents
            _ => Err(BridgeError::ConversionError),
        }
    }

    /// Processar saque
    pub async fn process_cashout(
        &self,
        request: CashoutRequest,
    ) -> Result<String, BridgeError> {
        // Verificar mapeamento
        let mappings = self.mappings.read().unwrap();
        let mapping = mappings
            .get(&request.orcid_id)
            .ok_or_else(|| BridgeError::OrcidNotFound(request.orcid_id.clone()))?;

        if mapping.verification_status != VerificationStatus::Verified {
            return Err(BridgeError::VerificationError(
                "Wallet not verified".into(),
            ));
        }

        // Verificar endereço
        if mapping.wallet.pix_key != request.wallet.pix_key {
            return Err(BridgeError::PaymentError(
                "Wallet mismatch".into(),
            ));
        }

        drop(mappings);

        // Calcular taxa
        let fee = (request.amount_cents as f64 * self.cashout_fee_percent / 100.0).round() as u64;
        let net_amount = request.amount_cents - fee;

        // Executar pagamento Pix (placeholder)
        let payment_id = format!(
            "PIX-{}_{}",
            request.orcid_id.replace('-', ""),
            uuid::Uuid::new_v4().simple()
        );

        info!(
            orcid_id = %request.orcid_id,
            amount_cents = request.amount_cents,
            fee_cents = fee,
            net_cents = net_amount,
            payment_id = %payment_id,
            "Cashout processed"
        );

        // Em produção: chamar API do Banco Central ou PSP
        // POST /pix/cobrança com chave e valor

        Ok(payment_id)
    }

    /// Obter saldos por ORCID
    pub fn get_balance(&self, orcid_id: &str) -> f64 {
        // Placeholder — em produção consultar ledger
        0.0
    }

    /// Listar mapeamentos pendentes de verificação
    pub fn list_pending_verifications(&self) -> Vec<OrcidPixMapping> {
        let mappings = self.mappings.read().unwrap();
        mappings
            .values()
            .filter(|m| m.verification_status == VerificationStatus::Pending)
            .cloned()
            .collect()
    }
}

impl std::fmt::Display for BridgeError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self)
    }
}
impl std::error::Error for BridgeError {}
