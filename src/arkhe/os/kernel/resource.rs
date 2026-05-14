// src/arkhe/os/kernel/resource.rs
/// Recurso linear: não pode ser clonado, deve ser consumido exatamente uma vez.

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct TemporalAnchor {
    pub id: String,
    pub signature: String,
}

pub struct TemporalChain {}
impl TemporalChain {
    pub fn anchor(_action: &str, id: u64) -> TemporalAnchor {
        TemporalAnchor { id: id.to_string(), signature: "anchor".to_string() }
    }
}

pub struct FdPerms {}
impl FdPerms {
    pub const READ: u32 = 1;
}

pub struct Fd<T> {
    pub id: u64,
    pub resource: T,
    pub permissions: u32,
    pub anchor: Option<TemporalAnchor>,
}

impl<T> Fd<T> {
    /// Consome o recurso e retorna seu conteúdo, ancorando a operação.
    pub fn consume(self) -> (T, TemporalAnchor) {
        let anchor = TemporalChain::anchor("fd_consumed", self.id);
        (self.resource, anchor)
    }
}
