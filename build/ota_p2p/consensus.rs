// build/ota_p2p/consensus.rs — Consenso federado para OTA P2P em mesh network
use anyhow::{Result, Context, bail};
use ed25519_dalek::{SigningKey, VerifyingKey, Signature, SIGNATURE_LENGTH};
use sha2::{Sha256, Digest};
use std::collections::{HashMap, HashSet};
use std::time::{Duration, Instant};
use tokio::sync::broadcast;

use crate::core::config::P2PConfig;

/// Mensagem de voto para consenso de atualização OTA
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct VoteMessage {
    /// Hash do binário proposto
    pub proposal_hash: String,
    /// Assinatura do nó votante
    pub signature: Vec<u8>,
    /// ID do nó votante
    pub voter_id: String,
    /// Timestamp do voto
    pub timestamp: u64,
    /// Versão proposta
    pub proposed_version: String,
}

/// Gerenciador de consenso OTA P2P
pub struct P2PConsensusManager {
    /// Configuração P2P
    config: P2PConfig,

    /// Chave do nó local para assinar votos
    signing_key: SigningKey,
    verifying_key: VerifyingKey,

    /// Chaves públicas conhecidas de outros nós (via bootstrap ou DHT)
    known_peers: HashMap<String, VerifyingKey>,

    /// Proposta ativa de atualização
    active_proposal: Option<UpdateProposal>,

    /// Votos recebidos para proposta atual
    votes: HashMap<String, VoteMessage>,

    /// Canal para broadcast de votos na mesh
    vote_broadcast: broadcast::Sender<VoteMessage>,

    /// Threshold para commit: 2f+1 de 3f+1 nós
    commit_threshold: usize,
}

#[derive(Debug, Clone)]
pub struct UpdateProposal {
    pub proposal_hash: String,
    pub proposed_version: String,
    pub binary_url: String,
    pub proposer_id: String,
    pub timestamp: u64,
    pub metadata: serde_json::Value,
}

impl P2PConsensusManager {
    /// Criar novo gerenciador de consenso
    pub fn new(config: P2PConfig, signing_key: SigningKey) -> Result<Self> {
        let verifying_key = signing_key.verifying_key();
        let (vote_broadcast, _) = broadcast::channel(100);

        // Threshold BFT: 2f+1 de 3f+1
        let total_nodes = config.estimated_mesh_size;
        let f = (total_nodes - 1) / 3;  // máximo de nós bizantinos tolerados
        let commit_threshold = 2 * f + 1;

        Ok(Self {
            config,
            signing_key,
            verifying_key,
            known_peers: HashMap::new(),
            active_proposal: None,
            votes: HashMap::new(),
            vote_broadcast,
            commit_threshold,
        })
    }

    /// Registrar chave pública de peer conhecido
    pub fn register_peer(&mut self, peer_id: String, public_key: VerifyingKey) {
        self.known_peers.insert(peer_id, public_key);
    }

    /// Propor nova atualização OTA para a mesh
    pub async fn propose_update(
        &mut self,
        proposal: UpdateProposal,
    ) -> Result<String> {
        // Verificar se já há proposta ativa
        if self.active_proposal.is_some() {
            bail!("Proposal already active");
        }

        // Assinar proposta com chave local
        let proposal_bytes = serde_json::to_vec(&proposal)?;
        let proposal_hash = format!("{:x}", Sha256::digest(&proposal_bytes));

        // Criar voto próprio
        let vote = self.create_vote(&proposal_hash, &proposal.proposed_version)?;

        // Ativar proposta localmente
        self.active_proposal = Some(proposal.clone());
        self.votes.clear();
        self.votes.insert(self.config.node_id.clone(), vote.clone());

        // Broadcast voto para mesh
        self.vote_broadcast.send(vote)?;

        Ok(proposal_hash)
    }

    /// Processar voto recebido de peer
    pub fn process_vote(&mut self, vote: VoteMessage) -> Result<bool> {
        // Verificar assinatura do voto
        if !self.verify_vote_signature(&vote)? {
            bail!("Invalid vote signature from {}", vote.voter_id);
        }

        // Verificar timestamp (prevenir replay attacks)
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)?
            .as_secs();
        if vote.timestamp < now - 300 || vote.timestamp > now + 60 {
            bail!("Vote timestamp out of bounds");
        }

        // Verificar se voto é para proposta ativa
        if let Some(prop) = &self.active_proposal {
            if vote.proposal_hash != prop.proposal_hash {
                // Voto para proposta diferente: ignorar ou armazenar para depois
                return Ok(false);
            }
        } else {
            // Sem proposta ativa: armazenar voto para possível proposta futura
            // (em produção: usar cache com TTL)
            return Ok(false);
        }

        // Armazenar voto válido
        self.votes.insert(vote.voter_id.clone(), vote);

        // Verificar se atingiu threshold para commit
        if self.votes.len() >= self.commit_threshold {
            self.commit_proposal()?;
            return Ok(true);
        }

        Ok(false)
    }

    /// Commit da proposta após consenso atingido
    fn commit_proposal(&mut self) -> Result<()> {
        let proposal = self.active_proposal.take()
            .ok_or_else(|| anyhow::anyhow!("No active proposal to commit"))?;

        tracing::info!(
            "✅ Consenso atingido para versão {}: {} votos de {} necessários",
            proposal.proposed_version,
            self.votes.len(),
            self.commit_threshold
        );

        // Em produção: disparar download e instalação da atualização
        // Aqui: apenas log
        Ok(())
    }

    /// Criar voto assinado para proposta
    fn create_vote(&self, proposal_hash: &str, version: &str) -> Result<VoteMessage> {
        use signature::Signer;
        // Mensagem a ser assinada: hash + versão + timestamp
        let message = format!("{}:{}:{}", proposal_hash, version,
            std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)?.as_secs());

        let signature = self.signing_key.sign(message.as_bytes());

        Ok(VoteMessage {
            proposal_hash: proposal_hash.to_string(),
            signature: signature.to_bytes().to_vec(),
            voter_id: self.config.node_id.clone(),
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)?
                .as_secs(),
            proposed_version: version.to_string(),
        })
    }

    /// Verificar assinatura de voto recebido
    fn verify_vote_signature(&self, vote: &VoteMessage) -> Result<bool> {
        // Recuperar chave pública do votante
        let pubkey = self.known_peers.get(&vote.voter_id)
            .ok_or_else(|| anyhow::anyhow!("Unknown voter: {}", vote.voter_id))?;

        // Reconstruir mensagem original
        let message = format!("{}:{}:{}", vote.proposal_hash, vote.proposed_version, vote.timestamp);

        // Verificar assinatura Ed25519
        let signature = Signature::from_bytes(
            vote.signature.as_slice().try_into()
                .map_err(|_| anyhow::anyhow!("Invalid signature length"))?
        );

        Ok(pubkey.verify_strict(message.as_bytes(), &signature).is_ok())
    }

    /// Obter status do consenso atual
    pub fn get_consensus_status(&self) -> ConsensusStatus {
        ConsensusStatus {
            active_proposal: self.active_proposal.clone(),
            votes_received: self.votes.len(),
            commit_threshold: self.commit_threshold,
            consensus_reached: self.votes.len() >= self.commit_threshold,
            known_peers: self.known_peers.len(),
        }
    }

    /// Obter receiver para ouvir votos broadcast
    pub fn vote_receiver(&self) -> broadcast::Receiver<VoteMessage> {
        self.vote_broadcast.subscribe()
    }
}

#[derive(Debug, Clone, serde::Serialize)]
pub struct ConsensusStatus {
    pub active_proposal: Option<UpdateProposal>,
    pub votes_received: usize,
    pub commit_threshold: usize,
    pub consensus_reached: bool,
    pub known_peers: usize,
}
