pub struct CodeContributionBlock {
    pub developer_orcid: String,
    pub commit_hash: [u8; 32],
    pub repository: String,
    pub function_fingerprints: Vec<[u8; 32]>,
    pub timestamp: u64,
}
