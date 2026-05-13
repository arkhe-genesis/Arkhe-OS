use crate::temporal::{TemporalBlock, TemporalMetadata, TemporalPayload};

pub trait UnixResource {}
pub trait FdPerms {}

pub struct ZKProof {
    pub scheme: String,
    pub public_inputs: Vec<Vec<u8>>,
    pub proof_bytes: Vec<u8>,
    pub verification_key: Vec<u8>,
}

#[derive(Debug)]
pub enum UnixError {
    Utf8(std::string::FromUtf8Error),
    CommandFailed(i32),
    PermissionDenied(String),
    NotFound(String),
    InvalidFd(i32),
    Interrupted(String),
    SystemError(i32),
}

impl From<std::io::Error> for UnixError {
    fn from(err: std::io::Error) -> Self {
        UnixError::SystemError(err.raw_os_error().unwrap_or(1))
    }
}

/// A linear, typed file descriptor.
///
/// Cannot be copied. Must be explicitly closed or moved.
/// Anchoring is automatic if `anchored` is true and the fd is dropped.
pub struct Fd<T: UnixResource, P: FdPerms> {
    pub _fd: i32,
    pub resource: T,
    pub perms: P,
    pub temporal: Option<TemporalMetadata>,
    pub zk_proof: Option<ZKProof>,
    pub anchored: bool,
}

impl<T: UnixResource, P: FdPerms> Fd<T, P> {
    pub fn close(mut self) -> Result<(), UnixError> {
        if self.anchored && self.temporal.is_some() {
            let meta = self.temporal.as_ref().unwrap();
            if meta.block_id.is_none() {
                self._finalize_anchor()?;
            }
        }
        unsafe { libc::close(self._fd) };
        self._fd = -1;
        Ok(())
    }

    fn _finalize_anchor(&self) -> Result<(), UnixError> {
        Ok(())
    }
    fn _read_for_anchor(&self) -> Result<Vec<u8>, UnixError> {
        Ok(vec![])
    }

    pub fn anchor(&mut self) -> Result<TemporalBlock, UnixError> {
        let content = self._read_for_anchor()?;
        use sha3::Digest;
        let mut hasher = sha3::Sha3_256::new();
        hasher.update(&content);
        let hash = hasher.finalize().to_vec();
        let block = crate::temporal::anchor_content(
            content.clone(),
            TemporalPayload {
                resource_type: "file".into(),
                perms: 0,
                timestamp: 0, // time::nanos()
            },
        )
        .map_err(|_e| UnixError::SystemError(1))?;
        self.temporal = Some(TemporalMetadata {
            anchor_hash: Some(hash),
            timestamp_ns: 0,
            block_id: Some(TemporalBlock {
                number: block.number,
                hash: block.hash.clone(),
            }),
            entropy_score: 0.0,
        });
        self.anchored = true;
        Ok(block)
    }
}

// Prevent cloning – linear type
// impl<T, P> Clone for Fd<T, P> {
//     fn clone(&self) -> Self { panic!("Fd<T> is linear"); }
// }
