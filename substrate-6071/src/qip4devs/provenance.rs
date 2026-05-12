use std::path::Path;
use sha2::{Digest, Sha256};
use syn::Item;

pub struct FunctionFingerprint {
    pub hash: [u8; 32],
}

impl FunctionFingerprint {
    pub fn new(hash: &[u8; 32]) -> Self {
        Self { hash: *hash }
    }
}

pub fn fingerprint_crate(crate_path: &Path) -> Vec<FunctionFingerprint> {
    let content = std::fs::read_to_string(crate_path).unwrap_or_default();
    if let Ok(ast) = syn::parse_file(&content) {
        ast.items.iter()
            .filter_map(|item| {
                if let Item::Fn(f) = item {
                    let s = quote::quote!(#f).to_string();
                    let hash: [u8; 32] = Sha256::digest(s.as_bytes()).into();
                    Some(FunctionFingerprint::new(&hash))
                } else {
                    None
                }
            })
            .collect()
    } else {
        vec![]
    }
}
