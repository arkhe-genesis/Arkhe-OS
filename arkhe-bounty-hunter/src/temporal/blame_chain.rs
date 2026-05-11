pub struct BlameChain {}
impl BlameChain {
    pub fn new(repo_path: &std::path::Path) -> Result<Self, ()> { Ok(Self {}) }
    pub fn get_blame_info(&self, file_path: &std::path::Path, line: u32, pattern_matched: &str) -> Option<crate::TemporalVulnInfo> { None }
    pub fn get_changed_files(&self, since_commit: Option<&str>) -> Result<Vec<String>, ()> { Ok(vec![]) }
}
