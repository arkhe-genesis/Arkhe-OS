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