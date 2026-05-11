#[cfg(feature = "federated-riscv-enclaves")]
pub mod riscv_federated_enclaves {
    #[path = "../../build/riscv_federated_enclaves/federated_attestation.rs"]
    pub mod federated_attestation;
}

#[cfg(feature = "zk-async-consensus")]
pub mod zk_honeybadger {
    #[path = "../../build/zk_honeybadger/zk_honeybadger.rs"]
    pub mod zk_honeybadger;
}
