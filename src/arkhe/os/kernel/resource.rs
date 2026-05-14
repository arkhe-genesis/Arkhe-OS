pub struct FdPerms;
pub struct TemporalAnchor;
pub struct TemporalChain;
impl TemporalChain {
    pub fn anchor(name: &str, id: u64) -> TemporalAnchor { TemporalAnchor }
}
// src/arkhe/os/kernel/resource.rs
/// Recurso linear: não pode ser clonado, deve ser consumido exatamente uma vez.
pub struct Fd<T> {
    id: u64,
    resource: T,
    permissions: FdPerms,
    anchor: Option<TemporalAnchor>,
}

impl<T> Fd<T> {
    /// Consome o recurso e retorna seu conteúdo, ancorando a operação.
    pub fn consume(self) -> (T, TemporalAnchor) {
        let anchor = TemporalChain::anchor("fd_consumed", self.id);
        (self.resource, anchor)
    }
}
