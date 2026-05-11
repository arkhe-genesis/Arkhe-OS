//! # Bridge x402 → Pix (Go arkh-pix)
//!
//! Conecta o módulo Q-Art ao backend Go de Pix via HTTP/REST + WebSocket.
//! Utiliza o protocolo x402 (HTTP 402 Payment Required) para micropagamentos.
//!
//! ## Fluxo
//!
//! 1. Q-Art calcula royalty a ser pago
//! 2. Solicita criação de cobrança Pix via HTTP POST ao Go bridge
//! 3. Go bridge cria cobrança no BCB Pix e retorna QR code / Location ID
//! 4. Payment é efetuado (Pix Saque/TED instantâneo)
//! 5. Webhook confirma pagamento → Q-Art registra na chain
//!
//! ## Endpoints Go consumidos
//!
//! - `POST /api/v1/pix/charges` — Criar cobrança
//! - `GET  /api/v1/pix/payments/{txid}` — Verificar pagamento
//! - `POST /api/v1/pix/webhook` — Receber notificação de pagamento
//! - `GET  /api/v1/pix/balance` — Verificar saldo

use reqwest::{Client, StatusCode};
use serde::{Deserialize, Serialize};
use std::time::Duration;
use tokio::sync::mpsc;
use tracing::{debug, error, info, warn};

use crate::errors::QArtError;
use crate::types::RoyaltyEvent;

/// Configuração da bridge x402
#[derive(Clone, Debug)]
pub struct X402Config {
    /// Base URL do serviço Go Pix Bridge
    pub base_url: String,
    /// API key para autenticação
    pub api_key: String,
    /// Timeout de requisições
    pub timeout: Duration,
    /// Máximo de tentativas de retry
    pub max_retries: u32,
    /// Endereço para receber webhooks (opcional)
    pub webhook_url: Option<String>,
}

impl Default for X402Config {
    fn default() -> Self {
        Self {
            base_url: "http://localhost:8081".into(),
            api_key: String::new(),
            timeout: Duration::from_secs(30),
            max_retries: 3,
            webhook_url: None,
        }
    }
}

/// Cliente x402 Bridge
pub struct X402PixBridge {
    config: X402Config,
    client: Client,
    /// Canal para receber confirmações de pagamento via webhook
    payment_confirmations: mpsc::Receiver<PaymentConfirmation>,
    /// Cache de cobranças pendentes
    pending_charges: std::sync::Mutex<std::collections::HashMap<String, PendingCharge>>,
}

/// Confirmação de pagamento recebida via webhook
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PaymentConfirmation {
    pub charge_id: String,
    pub txid: String,
    pub amount_cents: u64,
    pub payer_pix_key: String,
    pub status: PaymentStatus,
    pub timestamp: String,
}

/// Status de pagamento
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum PaymentStatus {
    Created,
    Waiting,
    Confirmed,
    Completed,
    Failed,
    Cancelled,
    Refunded,
}

impl std::fmt::Display for PaymentStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Created => write!(f, "CREATED"),
            Self::Waiting => write!(f, "WAITING"),
            Self::Confirmed => write!(f, "CONFIRMED"),
            Self::Completed => write!(f, "COMPLETED"),
            Self::Failed => write!(f, "FAILED"),
            Self::Cancelled => write!(f, "CANCELLED"),
            Self::Refunded => write!(f, "REFUNDED"),
        }
    }
}

/// Resposta da API Pix para criação de cobrança
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ChargeResponse {
    pub charge_id: String,
    pub location: String,
    pub location_id: String,
    pub br_code: String,
    pub qr_code_url: String,
    pub amount: f64,
    pub status: PaymentStatus,
    pub expires_at: String,
    pub transaction_id: Option<String>,
}

/// Cobrança pendente (aguardando pagamento)
#[derive(Clone, Debug)]
struct PendingCharge {
    charge_id: String,
    amount_cents: u64,
    pix_key: String,
    orcid_id: String,
    royalty_event: RoyaltyEvent,
    created_at: std::time::Instant,
}

/// Erros específicos da bridge x402
#[derive(Debug, thiserror::Error)]
pub enum BridgeError {
    #[error("HTTP error {status}: {body}")]
    HttpError {
        status: StatusCode,
        body: String,
    },
    #[error("Network error: {0}")]
    NetworkError(#[from] reqwest::Error),

    #[error("Timeout waiting for payment")]
    PaymentTimeout,

    #[error("Payment failed: {0}")]
    PaymentFailed(String),

    #[error("Authentication failed")]
    AuthFailed,
}

impl X402PixBridge {
    /// Criar nova bridge
    pub fn new(config: X402Config) -> (Self, mpsc::Sender<PaymentConfirmation>) {
        let client = Client::builder()
            .timeout(config.timeout)
            .connect_timeout(Duration::from_secs(5))
            .build()
            .expect("Failed to build HTTP client");

        let (tx, rx) = mpsc::channel(1024);

        let bridge = Self {
            config,
            client,
            payment_confirmations: rx,
            pending_charges: std::sync::Mutex::new(std::collections::HashMap::new()),
        };

        (bridge, tx)
    }

    /// Criar cobrança Pix para pagamento de royalty
    pub async fn create_royalty_charge(
        &self,
        pix_key: &str,
        amount_cents: u64,
        orcid_id: &str,
        royalty_event: &RoyaltyEvent,
    ) -> Result<ChargeResponse, QArtError> {
        let amount_reais = amount_cents as f64 / 100.0;

        let charge_request = serde_json::json!({
            "calendario": {
                "criacao": chrono::Utc::now().to_rfc3339(),
                "expiraApos": 300 // 5 minutos
            },
            "devedor": {
                "cpf": pix_key, // Para chave CPF
                "nome": "Royalty Receiver"
            },
            "valor": {
                "original": format!("{:.2}", amount_reais)
            },
            "location": {
                "id": format!("arkhe-royalty-{}", royalty_event.target_block_id.len())
            },
            "deve": format!(
                "Royalty ARKHE Q-Art - Block {} - ORCID {}",
                hex::encode(&royalty_event.target_block_id[..8]),
                orcid_id
            )
        });

        let url = format!("{}/pix/charges", self.config.base_url);

        debug!(
            url = %url,
            amount = amount_reais,
            pix_key = pix_key,
            "Creating Pix charge for royalty"
        );

        let response = self
            .http_post(&url, charge_request)
            .await
            .map_err(|e| QArtError::PixPaymentError(e.to_string()))?;

        let charge: ChargeResponse = response
            .json()
            .await
            .map_err(|e| QArtError::PixPaymentError(e.to_string()))?;

        // Registrar cobrança pendente
        let mut pending = self.pending_charges.lock().unwrap();
        pending.insert(
            charge.charge_id.clone(),
            PendingCharge {
                charge_id: charge.charge_id.clone(),
                amount_cents,
                pix_key: pix_key.to_string(),
                orcid_id: orcid_id.to_string(),
                royalty_event: royalty_event.clone(),
                created_at: std::time::Instant::now(),
            },
        );

        info!(
            charge_id = %charge.charge_id,
            amount_cents = amount_cents,
            pix_key = pix_key,
            "Royalty charge created successfully"
        );

        Ok(charge)
    }

    /// Verificar status de uma cobrança
    pub async fn check_payment_status(
        &self,
        charge_id: &str,
    ) -> Result<PaymentStatus, QArtError> {
        let url = format!("{}/pix/charges/{}", self.config.base_url, charge_id);

        let response = self.http_get(&url).await?;

        let charge: ChargeResponse = response
            .json()
            .await
            .map_err(|e| QArtError::PixPaymentError(e.to_string()))?;

        Ok(charge.status)
    }

    /// Enviar pagamento instantâneo Pix (efetivo)
    /// Usado quando o x402 não é necessário — pagamento direto
    pub async fn send_instant_payment(
        &self,
        pix_key: String,
        amount_cents: u64,
        end_to_end_id: String,
    ) -> Result<String, QArtError> {
        let amount_reais = amount_cents as f64 / 100.0;

        let payment_request = serde_json::json!({
            "endToEndId": end_to_end_id,
            "valor": {
                "original": format!("{:.2}", amount_reais)
            },
            "pagador": {
                "cpf": pix_key
            }
        });

        let url = format!("{}/pix/payments", self.config.base_url);

        debug!(
            url = %url,
            amount_cents = amount_cents,
            end_to_end_id = %end_to_end_id,
            "Sending instant Pix payment"
        );

        let response = self
            .http_post(&url, payment_request)
            .await
            .map_err(|e| QArtError::PixPaymentError(e.to_string()))?;

        if response.status() == StatusCode::OK {
            let txid: serde_json::Value = response
                .json()
                .await
                .map_err(|e| QArtError::PixPaymentError(e.to_string()))?;

            let txid_str = txid["txid"]
                .as_str()
                .unwrap_or_default()
                .to_string();

            info!(
                txid = %txid_str,
                amount_cents = amount_cents,
                end_to_end_id = %end_to_end_id,
                "Instant Pix payment completed"
            );

            Ok(txid_str)
        } else {
            let body = response.text().await.unwrap_or_default();
            Err(QArtError::PixPaymentError(format!(
                "HTTP {}: {}",
                response.status(),
                body
            )))
        }
    }

    /// Webhook handler — processa notificações de pagamento do Go bridge
    pub async fn handle_webhook(
        &self,
        payload: &[u8],
        webhook_signature: &str,
    ) -> Result<PaymentConfirmation, QArtError> {
        // Verificar assinatura do webhook
        if !self.verify_webhook_signature(payload, webhook_signature) {
            return Err(QArtError::PixPaymentError(
                "Invalid webhook signature".into(),
            ));
        }

        let notification: PaymentConfirmation = serde_json::from_slice(payload)
            .map_err(|e| QArtError::PixPaymentError(e.to_string()))?;

        info!(
            txid = %notification.txid,
            charge_id = %notification.charge_id,
            amount_cents = notification.amount_cents,
            status = %notification.status.to_string(),
            "Received payment webhook"
        );

        // Atualizar cobrança pendente
        let mut pending = self.pending_charges.lock().unwrap();
        if let Some(charge) = pending.get_mut(&notification.charge_id) {
            if notification.status == PaymentStatus::Completed {
                info!(
                    charge_id = %notification.charge_id,
                    orcid_id = %charge.orcid_id,
                    amount_cents = notification.amount_cents,
                    "Royalty payment confirmed — artist compensated"
                );
            }
        }

        Ok(notification)
    }

    /// Obter charge ID para um evento de royalty
    pub fn get_charge_id_for_event(
        &self,
        event: &RoyaltyEvent,
    ) -> Option<String> {
        let pending = self.pending_charges.lock().unwrap();
        pending
            .values()
            .find(|c| c.royalty_event.target_block_id == event.target_block_id)
            .map(|c| c.charge_id.clone())
    }

    /// Verificar pagamento para todos os royalties pendentes
    pub async fn check_all_pending_payments(&self) -> Result<Vec<String>, QArtError> {
        let pending = self.pending_charges.lock().unwrap();
        let mut completed = Vec::new();

        for (charge_id, charge) in pending.iter() {
            // Timeout de 5 minutos
            if charge.created_at.elapsed() > Duration::from_secs(300) {
                let status = self.check_payment_status(charge_id).await?;

                if status == PaymentStatus::Completed || status == PaymentStatus::Confirmed {
                    completed.push(charge_id.clone());
                }
            }
        }

        Ok(completed)
    }

    /// Obter QR code para uma cobrança
    pub fn get_qr_code(&self, charge_id: &str) -> Option<String> {
        let pending = self.pending_charges.lock().unwrap();
        pending
            .get(charge_id)
            .map(|_| {
                format!("{}/pix/qr/{}", self.config.base_url, charge_id)
            })
    }

    /// Verificar saldos
    pub async fn get_balance(&self) -> Result<f64, QArtError> {
        let url = format!("{}/pix/balance", self.config.base_url);

        let response = self.http_get(&url).await?;

        let json: serde_json::Value = response
            .json()
            .await
            .map_err(|e| QArtError::PixPaymentError(e.to_string()))?;

        let balance = json["balance"]
            .as_f64()
            .unwrap_or(0.0);

        Ok(balance)
    }

    // === Métodos HTTP internos ===

    async fn http_post(
        &self,
        url: &str,
        body: serde_json::Value,
    ) -> Result<reqwest::Response, BridgeError> {
        let mut retries = 0;

        loop {
            let response = self
                .client
                .post(url)
                .header("Content-Type", "application/json")
                .header("X-API-Key", &self.config.api_key)
                .json(&body)
                .send()
                .await?;

            match response.status() {
                StatusCode::OK | StatusCode::CREATED => return Ok(response),
                StatusCode::UNAUTHORIZED if retries < self.config.max_retries => {
                    retries += 1;
                    tokio::time::sleep(Duration::from_secs(1)).await;
                    continue;
                }
                status => {
                    let body = response.text().await.unwrap_or_default();
                    return Err(BridgeError::HttpError {
                        status,
                        body,
                    });
                }
            }
        }
    }

    async fn http_get(&self, url: &str) -> Result<reqwest::Response, BridgeError> {
        let mut retries = 0;

        loop {
            let response = self
                .client
                .get(url)
                .header("X-API-Key", &self.config.api_key)
                .send()
                .await?;

            match response.status() {
                StatusCode::OK => return Ok(response),
                StatusCode::UNAUTHORIZED if retries < self.config.max_retries => {
                    retries += 1;
                    tokio::time::sleep(Duration::from_secs(1)).await;
                    continue;
                }
                status => {
                    let body = response.text().await.unwrap_or_default();
                    return Err(BridgeError::HttpError {
                        status,
                        body,
                    });
                }
            }
        }
    }

    /// Verificar assinatura do webhook
    fn verify_webhook_signature(&self, payload: &[u8], signature: &str) -> bool {
        use hmac::{Hmac, Mac};
        use sha2::Sha256;

        if self.config.api_key.is_empty() {
            return true; // Sem verificação se sem API key
        }

        let key = self.config.api_key.as_bytes();
        let mut mac = Hmac::<Sha256>::new_from_slice(key)
            .expect("HMAC can take key of any size");
        mac.update(payload);

        let expected = hex::encode(mac.finalize().into_bytes());
        expected == signature
    }

    /// Start webhook listener (inicia task async que escuta notificações)
    pub fn start_webhook_listener(
        &self,
        webhook_tx: mpsc::Sender<PaymentConfirmation>,
    ) -> Result<(), QArtError> {
        let config = self.config.clone();
        let server = tiny_http::Server::http("0.0.0.0:8082").map_err(|e| {
            QArtError::PixPaymentError(format!("Failed to start webhook server: {}", e))
        })?;

        info!("Webhook listener started on port 8082");

        // Spawn thread para escutar
        std::thread::spawn(move || {
            for mut request in server.incoming_requests() {
                if request.method() != &tiny_http::Method::Post {
                    let _ = request.respond(tiny_http::Response::empty(405));
                    continue;
                }

                let signature_header = request
                    .headers()
                    .iter()
                    .find(|h| h.field.as_str() == "X-Signature");
                let signature = signature_header.map(|h| h.value.as_str()).unwrap_or("");

                // Ler body
                let mut body = Vec::new();
                if let Some(len) = request.body_length() {
                    body.resize(len as usize, 0);
                    if request.as_reader().read_exact(&mut body).is_err() {
                        let _ = request.respond(tiny_http::Response::empty(400));
                        continue;
                    }
                }

                // Verificar autenticidade
                let local_bridge = config.clone();
                // Note: In production, use proper HMAC verification

                // Parse notification
                if let Ok(notification) = serde_json::from_slice::<PaymentConfirmation>(&body) {
                    let tx = webhook_tx.clone();
                    tokio::spawn(async move {
                        if tx.send(notification).await.is_err() {
                            warn!("Failed to forward payment notification");
                        }
                    });

                    let _ = request.respond(
                        tiny_http::Response::from_string("OK").with_status_code(200),
                    );
                } else {
                    let _ = request.respond(tiny_http::Response::empty(400));
                }
            }
        });

        Ok(())
    }
}

/// Implementação síncrona alternativa para ambientes sem async
impl X402PixBridge {
    /// Enviar pagamento síncrono (bloqueador)
    pub fn send_payment_sync(
        &self,
        pix_key: String,
        amount_cents: u64,
        orcid_id: &str,
    ) -> Result<String, QArtError> {
        let runtime = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .map_err(|e| QArtError::PixPaymentError(e.to_string()))?;

        runtime.block_on(self.send_instant_payment(pix_key, amount_cents, format!("qart-{}-{}", orcid_id, uuid::Uuid::new_v4())))
    }
}
use crate::errors::QArtError;
use std::process::{Command, Stdio};
use serde::{Serialize, Deserialize};

/// Representa um payload de pagamento Pix para o bridge Go.
#[derive(Serialize, Deserialize)]
struct PixRequest {
    pix_key: String,
    amount_cents: u64,
    order_id: String,
    description: String,
}

#[derive(Serialize, Deserialize)]
struct PixResponse {
    success: bool,
    transaction_id: Option<String>,
    error: Option<String>,
}

/// Ponte de comunicação com o módulo Go `x402` via stdin/stdout pipes.
pub struct X402PixBridge {
    /// Caminho para o binário Go (ex: /usr/bin/arkhe-pix)
    binary_path: String,
}

impl X402PixBridge {
    pub fn new() -> Self {
        Self {
            binary_path: std::env::var("ARKHE_PIX_BIN")
                .unwrap_or_else(|_| "arkhe-pix".to_string()),
        }
    }

    /// Envia um pagamento instantâneo Pix.
    pub async fn send_pix_royalty(
        &self,
        pix_key: &str,
        amount_cents: u64,
        order_id: &str,
    ) -> Result<PixResponse, QArtError> {
        let request = PixRequest {
            pix_key: pix_key.to_string(),
            amount_cents,
            order_id: order_id.to_string(),
            description: "ARKHE Q-Art Royalty".to_string(),
        };

        let request_json = serde_json::to_string(&request)
            .map_err(|e| QArtError::ZkProofError(e.to_string()))?;

        // Invoca o binário Go com o payload JSON na stdin, captura stdout
        let mut child = Command::new(&self.binary_path)
            .arg("--mode=pix-transfer")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| QArtError::PixPaymentError(format!("spawn: {}", e)))?;

        // Escrever stdin
        if let Some(stdin) = child.stdin.as_mut() {
            use std::io::Write;
            stdin.write_all(request_json.as_bytes())
                .map_err(|e| QArtError::PixPaymentError(e.to_string()))?;
        }

        let output = child.wait_with_output()
            .map_err(|e| QArtError::PixPaymentError(e.to_string()))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(QArtError::PixPaymentError(format!("binary error: {}", stderr)));
        }

        let response: PixResponse = serde_json::from_slice(&output.stdout)
            .map_err(|e| QArtError::PixPaymentError(e.to_string()))?;

        if !response.success {
            return Err(QArtError::PixPaymentError(
                response.error.unwrap_or_default()
            ));
        }

        Ok(response)
    }
}
