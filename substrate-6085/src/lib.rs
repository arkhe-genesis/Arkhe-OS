// ============================================================================
// ARKHE Ω‑TEMP v6.1.0 — Substrato 6085: Quantum Compliance (QC)
// ============================================================================
//
// ═══════════════════════════════════════════════════════════════════════════
//  REGULATORY SUPERPOSITION — PROVING QUANTUM LAWFULNESS
// ═══════════════════════════════════════════════════════════════════════════
//
// Quantum‑Compliance (QC) guarantees that every quantum circuit executed
// inside the ARKHE multiverse respects international regulations:
//   - Wassenaar Arrangement qubit/gate thresholds
//   - NIST post‑quantum cryptographic standards
//   - Data privacy (HIPAA/GDPR) for quantum machine learning inputs
//   - Quantum fairness & bias constraints
//   - Export‑controlled quantum hardware usage (ion‑trap, superconducting)
//
// Each compliance check is distilled into a ZK‑proof that can be verified
// without revealing the circuit itself. All proofs are anchored on the
// TemporalChain.
//
// Example:
//   use arkhe_quantum_compliance::{
//       QuantumExportProver, FairnessProver, QuantumAuditTrail,
//   };
//
//   let export_proof = QuantumExportProver::prove(&circuit, &export_limits)?;
//   let fairness_proof = FairnessProver::prove(&qml_model, &fairness_config)?;
//   QuantumAuditTrail::anchor(&export_proof, &fairness_proof)?;
// ============================================================================

#![allow(clippy::too_many_arguments)]

pub mod export_control;
pub mod nist_pq_validator;
pub mod quantum_audit;
pub mod quantum_data_privacy;
pub mod quantum_fairness;
pub mod wassenaar_circuit;

pub use export_control::{ExportLimits, QuantumExportProver, WassenaarCircuitProof};
pub use nist_pq_validator::NISTPQValidator;
pub use quantum_audit::QuantumAuditTrail;
pub use quantum_data_privacy::{DataPrivacyProver, QMLPrivacyProof};
pub use quantum_fairness::{FairnessConfig, FairnessProof, FairnessProver};
