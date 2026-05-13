
use ed25519_dalek::{Signer, Verifier, Signature, SigningKey, VerifyingKey};
use serde::{Deserialize, Serialize};

pub struct OrcidIdentity {
    pub orcid: String,
    pub signing_key: SigningKey,
}

impl OrcidIdentity {
    pub fn generate(orcid: &str) -> Self {
        let mut csprng = rand::rngs::OsRng;
        let signing_key = SigningKey::generate(&mut csprng);
        Self { orcid: orcid.into(), signing_key }
    }

    pub fn verifying_key(&self) -> VerifyingKey {
        self.signing_key.verifying_key()
    }

    pub fn sign(&self, payload: &[u8]) -> Vec<u8> {
        self.signing_key.sign(payload).to_bytes().to_vec()
    }
}

pub fn verify(payload: &[u8], signature: &[u8], verifying_key: &VerifyingKey) -> bool {
    if let Ok(sig_bytes) = signature.try_into() {
        let sig = Signature::from_bytes(sig_bytes);
        verifying_key.verify(payload, &sig).is_ok()
    } else {
        false
    }
}
