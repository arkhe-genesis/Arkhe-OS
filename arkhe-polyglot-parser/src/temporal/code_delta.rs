// ============================================================================
// ARKHE P³ — Temporal Code Deltas
// ============================================================================
// Representam mudanças entre versões temporais do código.
// Usados para:
//   - Rastrear evolução do código
//   - Rollback seguro
//   - Merge semântico
//   - Prova de autoria temporal
// ============================================================================

use crate::ast::{UAST, UASTNode, NodeId, AttributeValue};
use crate::semantic::SemanticReport;
use std::collections::HashMap;

/// Representa uma transformação atômica no código
#[derive(Clone, Debug)]
pub enum CodeOperation {
    /// Adicionar nó
    Add {
        node: UASTNode,
        parent: NodeId,
        position: usize, // Posição entre irmãos
    },
    /// Remover nó
    Remove {
        node_id: NodeId,
        removed_node: UASTNode,
        former_parent: NodeId,
    },
    /// Modificar atributo
    ModifyAttribute {
        node_id: NodeId,
        attribute: String,
        old_value: AttributeValue,
        new_value: AttributeValue,
    },
    /// Mover nó
    Move {
        node_id: NodeId,
        from_parent: NodeId,
        from_position: usize,
        to_parent: NodeId,
        to_position: usize,
    },
    /// Modificar tipo (refactoring)
    Retype {
        node_id: NodeId,
        old_kind: String, // Nome do tipo antigo (ou NodeKind)
        new_kind: String,
    },
    /// Merge de dois nós
    Merge {
        base_node_id: NodeId,
        merged_node_id: NodeId,
        result: UASTNode,
    },
    /// Split de um nó em dois
    Split {
        original_node_id: NodeId,
        left: UASTNode,
        right: UASTNode,
    },
}

/// Conjunto de operações que formam uma versão
#[derive(Clone, Debug)]
pub struct CodeVersion {
    pub version_id: u64,
    pub timestamp_ns: u64,
    pub author: Option<Vec<u8>>,
    pub operations: Vec<CodeOperation>,
    pub resulting_uast_hash: Vec<u8>,
    pub semantic_report: SemanticReport,
}

/// Rollback seguro — reverter código a uma versão anterior
pub struct CodeRollback {
    target_version: u64,
    intermediate_operations: Vec<CodeOperation>,
    verification: RollbackVerification,
}

#[derive(Debug, PartialEq)]
pub enum RollbackVerification {
    Verified,
    SemanticDrift(f64), // Score de drift semântico
    ConflictDetected(Vec<String>),
    Unreachable,
}

impl CodeRollback {
    /// Criar plano de rollback
    pub fn plan(
        current_uast: &UAST,
        target_uast: &UAST,
        current_version: u64,
        target_version: u64,
    ) -> Result<Self, RollbackError> {
        if target_version >= current_version {
            return Err(RollbackError::InvalidTargetVersion {
                current: current_version,
                target: target_version,
            });
        }

        // Computar delta reverso
        let delta = Self::compute_reverse_delta(current_uast, target_uast);

        // Verificar viabilidade
        let verification = Self::verify_rollback_safety(target_uast);

        Ok(Self {
            target_version,
            intermediate_operations: delta,
            verification,
        })
    }

    /// Executar rollback
    pub fn execute(self, uast: &mut UAST) -> Result<(), RollbackError> {
        // Verificar verificação de segurança
        if self.verification == RollbackVerification::Unreachable {
            return Err(RollbackError::UnsafeRollback {
                reason: "Target state is unreachable from current state".to_string(),
            });
        }

        // Aplicar operações reversas
        for op in self.intermediate_operations.iter().rev() {
            Self::apply_reverse_operation(uast, op)?;
        }

        Ok(())
    }

    fn compute_reverse_delta(
        current: &UAST,
        target: &UAST,
    ) -> Vec<CodeOperation> {
        let mut operations = Vec::new();

        // Nós que existem no atual mas não no target → foram adicionados → precisam ser removidos
        for (id, node) in &current.nodes {
            if !target.nodes.contains_key(id) {
                operations.push(CodeOperation::Remove {
                    node_id: *id,
                    removed_node: node.clone(),
                    former_parent: NodeId::new(0), // Placeholder
                });
            }
        }

        // Nós que existem no target mas não no atual → foram removidos → precisam ser adicionados
        for (id, node) in &target.nodes {
            if !current.nodes.contains_key(id) {
                operations.push(CodeOperation::Add {
                    node: node.clone(),
                    parent: NodeId::new(0), // Placeholder
                    position: 0,
                });
            }
        }

        // Nós modificados
        for (id, current_node) in &current.nodes {
            if let Some(target_node) = target.nodes.get(id) {
                if current_node != target_node {
                    operations.push(CodeOperation::ModifyAttribute {
                        node_id: *id,
                        attribute: "full".to_string(),
                        old_value: AttributeValue::String("changed".to_string()),
                        new_value: AttributeValue::String("original".to_string()),
                    });
                }
            }
        }

        operations
    }

    fn verify_rollback_safety(target: &UAST) -> RollbackVerification {
        // Verificar integridade do target UAST
        if target.nodes.is_empty() {
            return RollbackVerification::Unreachable;
        }

        // Verificar que o target tem root válida
        if !target.nodes.contains_key(&target.root) {
            return RollbackVerification::Unreachable;
        }

        // Verificar consistência semântica
        let semantic_score = 0.95; // Placeholder — oracle analysis
        if semantic_score < 0.8 {
            return RollbackVerification::SemanticDrift(semantic_score);
        }

        RollbackVerification::Verified
    }

    fn apply_reverse_operation(
        uast: &mut UAST,
        op: &CodeOperation,
    ) -> Result<(), RollbackError> {
        match op {
            CodeOperation::Remove { node_id, removed_node, .. } => {
                uast.nodes.insert(*node_id, removed_node.clone());
                // Recriar edges
            }
            CodeOperation::Add { node_id, .. } => {
                uast.nodes.remove(node_id);
            }
            CodeOperation::ModifyAttribute { node_id, attribute, old_value, .. } => {
                if let Some(node) = uast.nodes.get_mut(node_id) {
                    node.attributes.insert(attribute.clone(), old_value.clone());
                }
            }
            _ => {}
        }
        Ok(())
    }
}

#[derive(Debug, thiserror::Error)]
pub enum RollbackError {
    #[error("Versão alvo {target} é posterior à versão atual {current}")]
    InvalidTargetVersion { current: u64, target: u64 },

    #[error("Rollback inseguro: {reason}")]
    UnsafeRollback { reason: String },

    #[error("Erro semântico: {0}")]
    SemanticError(String),

    #[error("Conflito de merge: {0}")]
    MergeConflict(String),
}

#[derive(Clone, Debug)]
pub struct DeltaNode {
    pub node_id: u64,
    pub kind: String,
    pub signature: String,       // Assinatura textual
    pub location: SourceLocation,
}

#[derive(Clone, Debug)]
pub struct DeltaModification {
    pub node_id: u64,
    pub kind: String,
    pub before: String,
    pub after: String,
    pub impact: ChangeSeverity,
}

#[derive(Clone, Debug)]
pub struct DeltaMove {
    pub node_id: u64,
    pub from: SourceLocation,
    pub to: SourceLocation,
}

#[derive(Clone, Debug)]
pub struct SemanticChange {
    pub description: String,
    pub severity: ChangeSeverity,
    pub affected_nodes: Vec<u64>,
}

#[derive(Clone, Debug)]
pub enum ChangeSeverity {
    Breaking,
    NonBreaking,
    Cosmetic,
}

#[derive(Clone, Debug, Default)]
pub struct DeltaSummary {
    pub additions: usize,
    pub deletions: usize,
    pub modifications: usize,
    pub moves: usize,
    pub semantic_stability: f64,  // 0.0 - 1.0
}

#[derive(Clone, Debug)]
pub struct SourceLocation {
    pub file: String,
    pub line: u32,
    pub column: u32,
}

#[derive(Clone, Debug, Default)]
pub struct CodeDelta {
    pub added_nodes: Vec<DeltaNode>,
    pub removed_nodes: Vec<DeltaNode>,
    pub modified_nodes: Vec<DeltaModification>,
    pub moved_nodes: Vec<DeltaMove>,
    pub semantic_changes: Vec<SemanticChange>,
    pub summary: DeltaSummary,
}
