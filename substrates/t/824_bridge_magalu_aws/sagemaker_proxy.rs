// src/bin/sagemaker_proxy.rs
// Proxy Criptografado SageMaker — Substrato 824.2
// Arquiteto: ORCID 0009-0005-2697-4668 | Data: 2026-05-25
//
// Pipeline seguro de offload de treinamento ML para AWS SageMaker
// com residência efêmera, criptografia AES-256-GCM, e attestation.

use std::collections::HashMap;
use std::time::{Duration, Instant};
use tokio::time::timeout;
use serde::{Deserialize, Serialize};
use reqwest::{Client, StatusCode};
use aws_sdk_s3::{Client as S3Client, primitives::ByteStream};
use aws_sdk_sagemaker::{Client as SmClient, types::TrainingInputMode};
use aws_sdk_kms::{Client as KmsClient};
use ring::aead::{Aes256Gcm, Nonce, UnboundKey, AES_256_GCM};
use ring::rand::SecureRandom;
use tracing::{info, warn, error};

/// Configuração do proxy de offload.
#[derive(Clone, Debug, Deserialize)]
pub struct ProxyConfig {
    pub magalu_kms_key_id: String,
    pub aws_role_arn: String,
    pub ephemeral_bucket: String,
    pub output_bucket: String,
    pub max_residence_secs: u64,
    pub magalu_object_storage_endpoint: String,
    pub mtls_cert_path: String,
    pub mtls_key_path: String,
    pub mtls_ca_path: String,
    pub attestation_enclave_pcr0: String,
    pub aws_nitro_root_ca_path: String,
}

/// Requisição de treinamento recebida do cluster Magalu.
#[derive(Debug, Deserialize)]
pub struct TrainRequest {
    pub training_data_uri: String,        // s3://arkhe-ml-input/... (Magalu OS)
    pub algorithm: String,                // xgboost, linear-learner, etc.
    pub instance_type: String,            // ml.m5.xlarge
    pub hyperparameters: HashMap<String, String>,
    pub max_data_lifetime_hours: Option<u64>,
}

/// Resposta canônica do proxy.
#[derive(Debug, Serialize)]
pub struct TrainResponse {
    pub job_name: String,
    pub status: String,
    pub model_uri_magalu: String,
    pub residence_time_secs: u64,
    pub seal_sha3: String,
}

/// Proxy criptografado com residência efêmera.
pub struct SageMakerProxy {
    config: ProxyConfig,
    http: Client,
    s3: S3Client,
    sm: SmClient,
    kms: KmsClient,
    rng: ring::rand::SystemRandom,
}

impl SageMakerProxy {
    pub async fn new(config: ProxyConfig) -> anyhow::Result<Self> {
        let aws_config = aws_config::load_from_env().await;
        Ok(Self {
            config: config.clone(),
            http: Client::builder()
                .timeout(Duration::from_secs(30))
                .build()?,
            s3: S3Client::new(&aws_config),
            sm: SmClient::new(&aws_config),
            kms: KmsClient::new(&aws_config),
            rng: ring::rand::SystemRandom::new(),
        })
    }

    /// Executa o pipeline completo de treinamento seguro.
    pub async fn run_training(&self, req: TrainRequest) -> anyhow::Result<TrainResponse> {
        let start = Instant::now();
        let job_name = format!("arkhe-824-{}-{}", req.algorithm, uuid::Uuid::new_v4());

        info!("[824.2] Iniciando offload seguro: job={}", job_name);

        // 1. Gerar chave de sessão efêmera (32 bytes para AES-256)
        let mut session_key = [0u8; 32];
        self.rng.fill(&mut session_key)
            .map_err(|e| anyhow::anyhow!("RNG failure: {:?}", e))?;

        // 2. Baixar dados criptografados do Magalu Object Storage
        let encrypted_data = self.fetch_from_magalu(&req.training_data_uri).await?;

        // 3. Re-criptografar com chave de sessão para envelope S3
        let (encrypted_blob, nonce) = self.aes_gcm_encrypt(&encrypted_data, &session_key)?;

        // 4. Upload para S3 efêmero na AWS (lifecycle: delete after N hours)
        let s3_input_key = format!("ephemeral/{}/train.enc", job_name);
        self.upload_ephemeral(&s3_input_key, &encrypted_blob).await?;

        // 5. Invocar SageMaker CreateTrainingJob
        let sm_job = self.create_training_job(&job_name, &s3_input_key, &req).await?;

        // 6. Polling até conclusão (com timeout de residência)
        let max_wait = Duration::from_secs(self.config.max_residence_secs);
        let completed = self.poll_job_completion(&job_name, max_wait).await?;
        if !completed {
            self.purge_ephemeral(&job_name).await?;
            anyhow::bail!("Job {} excedeu tempo de residência efêmera", job_name);
        }

        // 7. Baixar modelo criptografado do S3 de saída
        let s3_output_key = format!("ephemeral/{}/output/model.tar.gz.enc", job_name);
        let encrypted_model = self.download_ephemeral(&s3_output_key).await?;

        // 8. Descriptografar modelo localmente com chave de sessão
        let model_plain = self.aes_gcm_decrypt(&encrypted_model, &session_key, &nonce)?;

        // 9. Salvar modelo no Magalu Object Storage (origem canônica)
        let model_uri = format!("{}/models/{}/model.tar.gz", self.config.magalu_object_storage_endpoint, job_name);
        self.upload_to_magalu(&model_uri, &model_plain).await?;

        // 10. Purga total: deletar S3 efêmero, revogar chave de sessão (drop)
        self.purge_ephemeral(&job_name).await?;
        drop(session_key); // chave de sessão descartada da memória

        let residence = start.elapsed().as_secs();
        let seal = self.compute_seal(&job_name, &model_uri, residence);

        info!("[824.2] Offload concluído: job={} | residence={}s | seal={:.16}...", job_name, residence, seal);

        Ok(TrainResponse {
            job_name,
            status: "COMPLETED".into(),
            model_uri_magalu: model_uri,
            residence_time_secs: residence,
            seal_sha3: seal,
        })
    }

    // --- Métodos privados de criptografia ---

    fn aes_gcm_encrypt(&self, plaintext: &[u8], key: &[u8; 32]) -> anyhow::Result<(Vec<u8>, [u8; 12])> {
        let unbound = UnboundKey::new(&AES_256_GCM, key)
            .map_err(|_| anyhow::anyhow!("invalid AES-256 key"))?;
        let mut nonce_bytes = [0u8; 12];
        self.rng.fill(&mut nonce_bytes)
            .map_err(|e| anyhow::anyhow!("nonce RNG: {:?}", e))?;
        let nonce = Nonce::assume_unique_for_key(nonce_bytes);
        let sealing_key = ring::aead::LessSafeKey::new(unbound);

        let mut in_out = plaintext.to_vec();
        sealing_key.seal_in_place_append_tag(nonce, ring::aead::Aad::empty(), &mut in_out)
            .map_err(|_| anyhow::anyhow!("encryption failed"))?;

        let mut final_ciphertext = nonce_bytes.to_vec();
        final_ciphertext.extend_from_slice(&in_out);

        Ok((final_ciphertext, nonce_bytes))
    }

    fn aes_gcm_decrypt(&self, ciphertext: &[u8], key: &[u8; 32], _nonce: &[u8; 12]) -> anyhow::Result<Vec<u8>> {
        if ciphertext.len() < 12 {
            anyhow::bail!("ciphertext too short");
        }
        let (nonce_bytes, actual_ciphertext) = ciphertext.split_at(12);
        let mut nonce_arr = [0u8; 12];
        nonce_arr.copy_from_slice(nonce_bytes);

        let unbound = UnboundKey::new(&AES_256_GCM, key)
            .map_err(|_| anyhow::anyhow!("invalid AES-256 key"))?;
        let opening_key = ring::aead::LessSafeKey::new(unbound);
        let nonce_val = Nonce::assume_unique_for_key(nonce_arr);

        let mut in_out = actual_ciphertext.to_vec();
        let decrypted_slice = opening_key.open_in_place(nonce_val, ring::aead::Aad::empty(), &mut in_out)
            .map_err(|_| anyhow::anyhow!("decryption failed"))?;

        Ok(decrypted_slice.to_vec())
    }

    // --- Métodos privados de storage ---

    async fn fetch_from_magalu(&self, uri: &str) -> anyhow::Result<Vec<u8>> {
        info!("[824.2] Fetching from Magalu OS: {}", uri);
        // TODO: implementar cliente S3-compatível Magalu Cloud
        Ok(vec![0u8; 1024]) // stub
    }

    async fn upload_ephemeral(&self, key: &str, data: &[u8]) -> anyhow::Result<()> {
        self.s3.put_object()
            .bucket(&self.config.ephemeral_bucket)
            .key(key)
            .body(ByteStream::from(data.to_vec()))
            .send()
            .await?;
        info!("[824.2] Uploaded ephemeral: s3://{}/{}", self.config.ephemeral_bucket, key);
        Ok(())
    }

    async fn download_ephemeral(&self, key: &str) -> anyhow::Result<Vec<u8>> {
        let resp = self.s3.get_object()
            .bucket(&self.config.ephemeral_bucket)
            .key(key)
            .send()
            .await?;
        let data = resp.body.collect().await?.into_bytes();
        Ok(data.to_vec())
    }

    async fn purge_ephemeral(&self, job_name: &str) -> anyhow::Result<()> {
        let prefix = format!("ephemeral/{}/", job_name);
        info!("[824.2] Purging ephemeral data: s3://{}/{}", self.config.ephemeral_bucket, prefix);
        // Listar e deletar objetos com prefixo
        let list = self.s3.list_objects_v2()
            .bucket(&self.config.ephemeral_bucket)
            .prefix(&prefix)
            .send()
            .await?;
        for obj in list.contents() {
            if let Some(key) = obj.key() {
                self.s3.delete_object()
                    .bucket(&self.config.ephemeral_bucket)
                    .key(key)
                    .send()
                    .await?;
            }
        }
        info!("[824.2] Purge complete for job {}", job_name);
        Ok(())
    }

    async fn upload_to_magalu(&self, uri: &str, data: &[u8]) -> anyhow::Result<()> {
        info!("[824.2] Uploading model to Magalu canonical origin: {}", uri);
        // TODO: implementar upload S3-compatível Magalu
        Ok(())
    }

    // --- Métodos SageMaker ---

    async fn create_training_job(&self, job_name: &str, s3_input: &str, req: &TrainRequest) -> anyhow::Result<String> {
        // Simplificado: em produção, montar CreateTrainingJob completo
        info!("[824.2] Creating SageMaker training job: {}", job_name);
        Ok(job_name.into())
    }

    async fn poll_job_completion(&self, job_name: &str, max_wait: Duration) -> anyhow::Result<bool> {
        let deadline = Instant::now() + max_wait;
        while Instant::now() < deadline {
            let resp = self.sm.describe_training_job()
                .training_job_name(job_name)
                .send()
                .await;

            if let Ok(job_status) = resp {
                if let Some(status) = job_status.training_job_status {
                    if status == aws_sdk_sagemaker::types::TrainingJobStatus::Completed {
                        return Ok(true);
                    } else if status == aws_sdk_sagemaker::types::TrainingJobStatus::Failed ||
                              status == aws_sdk_sagemaker::types::TrainingJobStatus::Stopped {
                        return Ok(false);
                    }
                }
            }

            tokio::time::sleep(Duration::from_secs(60)).await;
        }
        Ok(false) // stub: timeout
    }

    // --- Utilitários ---

    pub fn verify_attestation(&self, token: &str) -> anyhow::Result<()> {
        info!("[824.2] Verifying Nitro Enclave Attestation Token: {}...", &token[..10.min(token.len())]);

        if token.is_empty() {
            anyhow::bail!("Attestation token is empty");
        }

        if self.config.attestation_enclave_pcr0.is_empty() {
            anyhow::bail!("PCR0 configuration is missing; insecure fallback rejected");
        }

        let decoded = base64::decode(token)
            .map_err(|e| anyhow::anyhow!("Base64 decode failed: {:?}", e))?;

        // COSE_Sign1 structure: [protected_header, unprotected_header, payload, signature]
        let cose_sign1: (Vec<u8>, serde_cbor::Value, Vec<u8>, Vec<u8>) = serde_cbor::from_slice(&decoded)
            .map_err(|e| anyhow::anyhow!("CBOR parsing failed: {:?}", e))?;

        let (protected, _unprotected, payload, signature) = cose_sign1;

        // Parse the embedded AttestationDocument
        let doc_value: serde_cbor::Value = serde_cbor::from_slice(&payload)
            .map_err(|e| anyhow::anyhow!("Payload is not valid CBOR: {:?}", e))?;

        let pcrs = match &doc_value {
            serde_cbor::Value::Map(m) => {
                let pcr_key = serde_cbor::Value::Text("pcrs".to_string());
                match m.get(&pcr_key) {
                    Some(serde_cbor::Value::Map(pcr_map)) => pcr_map,
                    _ => anyhow::bail!("pcrs not found or invalid type in document"),
                }
            },
            _ => anyhow::bail!("Attestation document is not a map"),
        };

        let pcr0_val = pcrs.get(&serde_cbor::Value::Integer(0))
            .ok_or_else(|| anyhow::anyhow!("PCR0 missing from document"))?;

        let pcr0_bytes = match pcr0_val {
            serde_cbor::Value::Bytes(b) => b,
            _ => anyhow::bail!("PCR0 is not bytes"),
        };

        let mut pcr0_hex = String::with_capacity(pcr0_bytes.len() * 2);
        for b in pcr0_bytes {
            pcr0_hex.push_str(&std::format!("{:02x}", b));
        }

        if self.config.attestation_enclave_pcr0 != pcr0_hex {
            anyhow::bail!("PCR0 mismatch: expected {}, got {}", self.config.attestation_enclave_pcr0, pcr0_hex);
        }

        // Extract leaf certificate and cabundle
        let cert_val = match &doc_value {
            serde_cbor::Value::Map(m) => m.get(&serde_cbor::Value::Text("certificate".to_string()))
                .ok_or_else(|| anyhow::anyhow!("certificate missing from document"))?,
            _ => anyhow::bail!("Invalid document"),
        };

        let cert_bytes = match cert_val {
            serde_cbor::Value::Bytes(b) => b,
            _ => anyhow::bail!("Certificate is not bytes"),
        };

        let cabundle_val = match &doc_value {
            serde_cbor::Value::Map(m) => m.get(&serde_cbor::Value::Text("cabundle".to_string()))
                .ok_or_else(|| anyhow::anyhow!("cabundle missing from document"))?,
            _ => anyhow::bail!("Invalid document"),
        };

        let cabundle_array = match cabundle_val {
            serde_cbor::Value::Array(arr) => arr,
            _ => anyhow::bail!("cabundle is not an array"),
        };

        // 1. Authenticate the leaf certificate against the AWS Nitro Enclaves Root CA
        // Carrega o Root CA confiável
        let root_ca_file = std::fs::File::open(&self.config.aws_nitro_root_ca_path)
            .map_err(|e| anyhow::anyhow!("Failed to open AWS Nitro Root CA: {}", e))?;
        let mut root_ca_reader = std::io::BufReader::new(root_ca_file);
        let root_ca_certs = rustls_pemfile::certs(&mut root_ca_reader)
            .map_err(|e| anyhow::anyhow!("Failed to parse AWS Nitro Root CA: {}", e))?;

        if root_ca_certs.is_empty() {
            anyhow::bail!("AWS Nitro Root CA is empty");
        }

        let mut intermediates = Vec::new();
        for item in cabundle_array {
            if let serde_cbor::Value::Bytes(b) = item {
                intermediates.push(b.clone());
            }
        }

        let parsed_leaf = x509_parser::parse_x509_certificate(cert_bytes.as_slice())
            .map_err(|e| anyhow::anyhow!("Failed to parse leaf certificate: {:?}", e))?.1;

        // Implement cryptographic chain verification using ring.
        // We verify that parsed_leaf is signed by an intermediate or root,
        // and any intermediate is signed by the trusted AWS Nitro Root CA.

        let mut current_cert = parsed_leaf.clone();
        let mut is_trusted = false;

        // Limitar profundidade da cadeia para evitar loops infinitos
        for _ in 0..10 {
            // Check if current_cert is directly signed by any trusted Root CA
            let mut signed_by_root = false;
            for root_der in &root_ca_certs {
                if let Ok((_, root_cert)) = x509_parser::parse_x509_certificate(root_der) {
                    if current_cert.issuer() == root_cert.subject() {
                        let issuer_pub_key = root_cert.public_key().subject_public_key.as_ref();
                        let unparsed_key = ring::signature::UnparsedPublicKey::new(
                            &ring::signature::RSA_PKCS1_2048_8192_SHA256, // AWS Root is usually RSA
                            issuer_pub_key
                        );
                        if unparsed_key.verify(current_cert.tbs_certificate.as_ref(), current_cert.signature_value.as_ref()).is_ok() {
                            signed_by_root = true;
                            break;
                        }
                        // Fallback para ECDSA caso a AWS mude o Root
                        let unparsed_key_ecdsa = ring::signature::UnparsedPublicKey::new(
                            &ring::signature::ECDSA_P384_SHA384_ASN1,
                            issuer_pub_key
                        );
                        if unparsed_key_ecdsa.verify(current_cert.tbs_certificate.as_ref(), current_cert.signature_value.as_ref()).is_ok() {
                            signed_by_root = true;
                            break;
                        }
                    }
                }
            }

            if signed_by_root {
                is_trusted = true;
                break;
            }

            // Check if signed by an intermediate
            let mut signed_by_intermediate = false;
            let mut next_cert = None;
            for inter_der in &intermediates {
                if let Ok((_, inter_cert)) = x509_parser::parse_x509_certificate(inter_der) {
                    if current_cert.issuer() == inter_cert.subject() {
                        let issuer_pub_key = inter_cert.public_key().subject_public_key.as_ref();
                        // Intermediates for Nitro are typically ECDSA P-384
                        let unparsed_key = ring::signature::UnparsedPublicKey::new(
                            &ring::signature::ECDSA_P384_SHA384_ASN1,
                            issuer_pub_key
                        );
                        if unparsed_key.verify(current_cert.tbs_certificate.as_ref(), current_cert.signature_value.as_ref()).is_ok() {
                            signed_by_intermediate = true;
                            next_cert = Some(inter_cert);
                            break;
                        }
                        // Fallback RSA
                        let unparsed_key_rsa = ring::signature::UnparsedPublicKey::new(
                            &ring::signature::RSA_PKCS1_2048_8192_SHA256,
                            issuer_pub_key
                        );
                        if unparsed_key_rsa.verify(current_cert.tbs_certificate.as_ref(), current_cert.signature_value.as_ref()).is_ok() {
                            signed_by_intermediate = true;
                            next_cert = Some(inter_cert);
                            break;
                        }
                    }
                }
            }

            if signed_by_intermediate {
                current_cert = next_cert.unwrap();
            } else {
                break; // No signer found, chain is broken
            }
        }

        if !is_trusted {
            anyhow::bail!("Leaf certificate failed cryptographic validation against AWS Root CA");
        }

        let pub_key_bytes = parsed_leaf.public_key().subject_public_key.as_ref();

        // 2. For COSE_Sign1 signature verification, construct the Sig_structure
        // Sig_structure = ["Signature1", protected_header, empty_bstr, payload]
        let sig_structure = (
            "Signature1",
            serde_bytes::ByteBuf::from(protected),
            serde_bytes::ByteBuf::from(Vec::new()),
            serde_bytes::ByteBuf::from(payload),
        );
        let sig_data = serde_cbor::to_vec(&sig_structure)
            .map_err(|e| anyhow::anyhow!("Failed to serialize Sig_structure: {:?}", e))?;

        // Enclaves use ECDSA P-384 with SHA-384
        // Convert COSE_Sign1 IEEE P1363 signature back to Ring Fixed format for verification
        let public_key = ring::signature::UnparsedPublicKey::new(
            &ring::signature::ECDSA_P384_SHA384_FIXED,
            pub_key_bytes
        );

        public_key.verify(&sig_data, &signature)
            .map_err(|_| anyhow::anyhow!("Attestation signature verification failed against AWS Nitro PKI leaf certificate"))?;

        info!("[824.2] Attestation verified successfully (PCR0: {})", pcr0_hex);
        Ok(())
    }

    fn compute_seal(&self, job_name: &str, model_uri: &str, residence: u64) -> String {
        use sha3::{Sha3_256, Digest};
        let mut hasher = Sha3_256::new();
        hasher.update(job_name.as_bytes());
        hasher.update(model_uri.as_bytes());
        hasher.update(&residence.to_le_bytes());
        format!("{:x}", hasher.finalize())
    }
}

// --- Servidor HTTP (axum) ---

use axum::{routing::post, Json, Router, extract::State, http::HeaderMap};
use std::sync::Arc;

async fn handle_train(
    State(proxy): State<Arc<SageMakerProxy>>,
    headers: HeaderMap,
    Json(req): Json<TrainRequest>,
) -> Result<Json<TrainResponse>, StatusCode> {
    // Verificar Attestation
    let token = headers.get("x-arkhe-attestation")
        .and_then(|h| h.to_str().ok())
        .unwrap_or("");

    if let Err(e) = proxy.verify_attestation(token) {
        error!("[824.2] Attestation failed: {}", e);
        return Err(StatusCode::UNAUTHORIZED);
    }

    match proxy.run_training(req).await {
        Ok(resp) => Ok(Json(resp)),
        Err(e) => {
            error!("[824.2] Training offload failed: {}", e);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();

    let config = ProxyConfig {
        magalu_kms_key_id: std::env::var("MAGALU_KMS_KEY_ID").unwrap_or_default(),
        aws_role_arn: std::env::var("AWS_ROLE_ARN").unwrap_or_default(),
        ephemeral_bucket: std::env::var("AWS_EPHEMERAL_BUCKET").unwrap_or_default(),
        output_bucket: std::env::var("AWS_OUTPUT_BUCKET").unwrap_or_default(),
        max_residence_secs: std::env::var("MAX_RESIDENCE_SECS")
            .unwrap_or_else(|_| "3600".into())
            .parse()?,
        magalu_object_storage_endpoint: std::env::var("MAGALU_OS_ENDPOINT")
            .unwrap_or_else(|_| "https://object-storage.magalu.cloud".into()),
        mtls_cert_path: std::env::var("MTLS_CERT_PATH").unwrap_or_else(|_| "/etc/arkhe/mtls/cert.pem".into()),
        mtls_key_path: std::env::var("MTLS_KEY_PATH").unwrap_or_else(|_| "/etc/arkhe/mtls/key.pem".into()),
        mtls_ca_path: std::env::var("MTLS_CA_PATH").unwrap_or_else(|_| "/etc/arkhe/mtls/ca.pem".into()),
        attestation_enclave_pcr0: std::env::var("ATTESTATION_PCR0").unwrap_or_default(),
        aws_nitro_root_ca_path: std::env::var("AWS_NITRO_ROOT_CA_PATH").unwrap_or_else(|_| "/etc/arkhe/aws-nitro-root-ca.pem".into()),
    };

    let proxy = Arc::new(SageMakerProxy::new(config).await?);

    let app = Router::new()
        .route("/v1/sagemaker/train", post(handle_train))
        .with_state(proxy);

    info!("[824.2] Configuring mTLS with cert: {}, key: {}, ca: {}", config.mtls_cert_path, config.mtls_key_path, config.mtls_ca_path);

    let mut root_cert_store = rustls::RootCertStore::empty();
    let ca_file = std::fs::File::open(&config.mtls_ca_path)?;
    let mut ca_reader = std::io::BufReader::new(ca_file);
    let ca_certs = rustls_pemfile::certs(&mut ca_reader)?;
    for ca in ca_certs {
        root_cert_store.add(&rustls::Certificate(ca.to_vec()))?;
    }

    let client_auth = rustls::server::AllowAnyAuthenticatedClient::new(root_cert_store);

    let cert_file = std::fs::File::open(&config.mtls_cert_path)?;
    let mut cert_reader = std::io::BufReader::new(cert_file);
    let cert_chain = rustls_pemfile::certs(&mut cert_reader)?
        .into_iter()
        .map(|c| rustls::Certificate(c.to_vec()))
        .collect();

    let key_file = std::fs::File::open(&config.mtls_key_path)?;
    let mut key_reader = std::io::BufReader::new(key_file);
    let keys = rustls_pemfile::pkcs8_private_keys(&mut key_reader)?;
    let key = rustls::PrivateKey(keys.into_iter().next().ok_or_else(|| anyhow::anyhow!("No valid PKCS8 key"))?.to_vec());

    let server_config = rustls::ServerConfig::builder()
        .with_safe_defaults()
        .with_client_cert_verifier(client_auth)
        .with_single_cert(cert_chain, key)?;

    let rustls_config = axum_server::tls_rustls::RustlsConfig::from_config(std::sync::Arc::new(server_config));
    let addr = std::net::SocketAddr::from(([0, 0, 0, 0], 8242));

    info!("[824.2] SageMaker Proxy listening on 0.0.0.0:8242 with STRICT mTLS");
    axum_server::bind_rustls(addr, rustls_config)
        .serve(app.into_make_service())
        .await?;

    Ok(())
}
