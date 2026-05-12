// ============================================================================
// ARKHE P³ — Temporal Code Graph
// ============================================================================
// Grafo temporal que rastreia a evolução do código ao longo do tempo.
// Cada nó do grafo é uma versão do código, e as arestas representam
// transformações (commits, merges, refatorações).
//
// Integração com a cadeia temporal ARKHE:
// cada "commit" do código gera um bloco temporal com o hash do UAST.
// ============================================================================

use std::collections::{HashMap, BTreeMap, HashSet};
use crate::temporal::code_delta::{CodeDelta, DeltaSummary, DeltaNode, DeltaModification, ChangeSeverity, SourceLocation};

/// Grafo temporal de código — versionamento semântico
pub struct TemporalCodeGraph {
    versions: BTreeMap<u64, VersionNode>,
    edges: Vec<TemporalEdge>,
    current_version: u64,
}

/// Nó de versão no grafo temporal
#[derive(Clone, Debug)]
pub struct VersionNode {
    pub version_id: u64,
    pub timestamp_ns: u64,
    pub author: Option<Vec<u8>>,
    pub uast_hash: Vec<u8>,       // SHA3-256 do UAST
    pub source_hash: Vec<u8>,     // SHA3-256 do código fonte
    pub language: String,
    pub semantic_score: f64,
    pub parent_versions: Vec<u64>, // Para merges
    pub metadata: VersionMetadata,
}

#[derive(Clone, Debug)]
pub struct VersionMetadata {
    pub commit_message: Option<String>,
    pub branch: Option<String>,
    pub tags: Vec<String>,
    pub test_coverage: Option<f64>,
    pub build_status: BuildStatus,
    pub vulnerabilities: Vec<VulnerabilityRef>,
}

#[derive(Clone, Debug, PartialEq)]
pub enum BuildStatus {
    Unknown,
    Passing,
    Failing,
    Broken,
}

#[derive(Clone, Debug)]
pub struct VulnerabilityRef {
    pub id: String,           // CVE ou ID interno
    pub severity: Severity,
    pub description: String,
    pub introduced_in: u64,   // Versão de introdução
    pub fixed_in: Option<u64>,// Versão de correção (None se ainda aberta)
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum Severity {
    Critical = 0,
    High = 1,
    Medium = 2,
    Low = 3,
}

/// Aresta temporal — representa a transformação entre versões
#[derive(Clone, Debug)]
pub struct TemporalEdge {
    pub from: u64,
    pub to: u64,
    pub edge_type: TemporalEdgeType,
    pub delta: CodeDelta,
}

#[derive(Clone, Debug)]
pub enum TemporalEdgeType {
    Linear,     // Commit simples (A → B)
    Branch,     // Criação de branch (A → B, A → C)
    Merge,      // Merge de branches (B → D, C → D)
    Revert,     // Revert (B → A)
    CherryPick, // Cherry-pick de commit
    Squash,     // Squash de múltiplos commits
    Rewrite,    // Rewrite (rebase, amend)
}

impl TemporalCodeGraph {
    /// Cria novo grafo temporal vazio
    pub fn new() -> Self {
        Self {
            versions: BTreeMap::new(),
            edges: Vec::new(),
            current_version: 0,
        }
    }

    /// Registra nova versão do código
    pub fn record_version(
        &mut self,
        uast: &crate::ast::UAST,
        language: &str,
        author: Option<Vec<u8>>,
        metadata: VersionMetadata,
    ) -> u64 {
        let version_id = self.current_version + 1;

        let version_node = VersionNode {
            version_id,
            timestamp_ns: self.current_nanos(),
            author,
            uast_hash: uast.compute_hash(),
            source_hash: uast.compute_hash(), // Na prática, hash do source
            language: language.to_string(),
            semantic_score: 1.0, // Computado pelo oracle
            parent_versions: Vec::new(),
            metadata,
        };

        // Computar delta em relação à versão anterior
        if let Some((&prev_id, prev_node)) = self.versions.iter().next_back() {
            let delta = self.compute_delta_between(&prev_node.uast_hash, &uast.compute_hash());
            let edge = TemporalEdge {
                from: prev_id,
                to: version_id,
                edge_type: TemporalEdgeType::Linear,
                delta,
            };
            self.edges.push(edge);
        }

        self.versions.insert(version_id, version_node);
        self.current_version = version_id;

        version_id
    }

    /// Computa delta temporal entre duas versões
    pub fn compute_delta(&self, old_uast: &crate::ast::UAST, new_uast: &crate::ast::UAST)
        -> Option<CodeDelta>
    {
        let mut delta = CodeDelta::default();

        let old_ids: HashSet<_> = old_uast.nodes.keys().collect();
        let new_ids: HashSet<_> = new_uast.nodes.keys().collect();

        // Nós adicionados
        for id in new_ids.difference(&old_ids) {
            if let Some(node) = new_uast.nodes.get(id) {
                delta.added_nodes.push(DeltaNode {
                    node_id: id.to_u64(),
                    kind: format!("{:?}", node.kind),
                    signature: self.node_signature(node, new_uast),
                    location: SourceLocation {
                        file: new_uast.source_info.filename.clone().unwrap_or_default(),
                        line: node.source_range.start_line,
                        column: node.source_range.start_column,
                    },
                });
            }
        }

        // Nós removidos
        for id in old_ids.difference(&new_ids) {
            if let Some(node) = old_uast.nodes.get(id) {
                delta.removed_nodes.push(DeltaNode {
                    node_id: id.to_u64(),
                    kind: format!("{:?}", node.kind),
                    signature: self.node_signature(node, old_uast),
                    location: SourceLocation {
                        file: old_uast.source_info.filename.clone().unwrap_or_default(),
                        line: node.source_range.start_line,
                        column: node.source_range.start_column,
                    },
                });
            }
        }

        // Nós modificados
        for id in old_ids.intersection(&new_ids) {
            let old_node = old_uast.nodes.get(id).unwrap();
            let new_node = new_uast.nodes.get(id).unwrap();

            if old_node != new_node {
                delta.modified_nodes.push(DeltaModification {
                    node_id: id.to_u64(),
                    kind: format!("{:?}", new_node.kind),
                    before: self.node_signature(old_node, old_uast),
                    after: self.node_signature(new_node, new_uast),
                    impact: self.assess_impact(old_node, new_node),
                });
            }
        }

        // Calcular estabilidade semântica
        let total_nodes = old_uast.nodes.len().max(new_uast.nodes.len()) as f64;
        let unchanged = total_nodes - delta.modified_nodes.len() as f64
            - delta.removed_nodes.len() as f64;
        delta.summary.semantic_stability = (unchanged / total_nodes.max(1.0))
            .clamp(0.0, 1.0);

        delta.summary.additions = delta.added_nodes.len();
        delta.summary.deletions = delta.removed_nodes.len();
        delta.summary.modifications = delta.modified_nodes.len();

        Some(delta)
    }

    /// Computa delta temporal (por hash)
    fn compute_delta_between(&self, old_hash: &[u8], new_hash: &[u8]) -> CodeDelta {
        if old_hash == new_hash {
            return CodeDelta::default();
        }

        // Placeholder: em produção, computar delta real a partir dos UASTs
        CodeDelta {
            summary: DeltaSummary {
                semantic_stability: 0.8, // Placeholder
                ..Default::default()
            },
            ..Default::default()
        }
    }

    /// Assinala impacto de uma modificação
    fn assess_impact(
        &self,
        old_node: &crate::ast::UASTNode,
        new_node: &crate::ast::UASTNode,
    ) -> ChangeSeverity {
        // Breaking: mudança de tipo, remoção de campo, mudança de assinatura
        if old_node.kind != new_node.kind {
            return ChangeSeverity::Breaking;
        }

        // Non-breaking: mudança de nome, corpo, etc.
        if old_node != new_node {
            return ChangeSeverity::NonBreaking;
        }

        ChangeSeverity::Cosmetic
    }

    /// Gera assinatura textual de um nó
    fn node_signature(
        &self,
        node: &crate::ast::UASTNode,
        uast: &crate::ast::UAST,
    ) -> String {
        match &node.kind {
            crate::ast::NodeKind::DeclFunction => {
                let name = node.attributes.get("name")
                    .and_then(|v| match v { crate::ast::AttributeValue::String(s) => Some(s), _ => None })
                    .map(|s| s.as_str())
                    .unwrap_or("fn");
                let params: Vec<_> = node.children.iter()
                    .filter_map(|c| uast.nodes.get(c))
                    .filter(|c| matches!(c.kind, crate::ast::NodeKind::DeclVariable))
                    .map(|c| {
                        c.attributes.get("name")
                            .and_then(|v| match v { crate::ast::AttributeValue::String(s) => Some(s.clone()), _ => None })
                            .unwrap_or_default()
                    })
                    .collect();
                format!("{}({})", name, params.join(", "))
            }
            crate::ast::NodeKind::DeclVariable => {
                format!("var {}", node.attributes.get("name")
                    .and_then(|v| match v { crate::ast::AttributeValue::String(s) => Some(s.as_str()), _ => None })
                    .unwrap_or("x"))
            }
            _ => format!("{:?}", node.kind),
        }
    }

    fn current_nanos(&self) -> u64 {
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_nanos() as u64)
            .unwrap_or(0)
    }

    pub fn record_parse(&mut self, uast: &crate::ast::UAST, language: &str) {
        self.record_version(uast, language, None, VersionMetadata {
             commit_message: None,
             branch: None,
             tags: Vec::new(),
             test_coverage: None,
             build_status: BuildStatus::Unknown,
             vulnerabilities: Vec::new()
        });
    }

    pub fn compute_temporal_delta(&self, old_version: &str, new_version: &str) -> Option<CodeDelta> {
         None
    }

    /// Reconstruir UAST de uma versão anterior
    pub fn reconstruct_uast(
        &self,
        version_id: u64,
        uast_store: &HashMap<u64, crate::ast::UAST>,
    ) -> Option<crate::ast::UAST> {
        uast_store.get(&version_id)
            .cloned()
            .or_else(|| {
                // Reconstruir a partir do delta
                // let version = self.versions.get(&version_id)?;
                // ... reconstruir a partir do parent + delta
                None // Placeholder
            })
    }

    /// Consultar histórico de mudanças em um nó
    pub fn query_node_history(
        &self,
        node_id: u64,
    ) -> Vec<(u64, crate::ast::NodeKind, ChangeSeverity)> {
        let mut history = Vec::new();

        for (version_id, version) in &self.versions {
            // Verificar se o nó existia nesta versão
            // (Em produção: buscar no store de UASTs)
            history.push((*version_id, crate::ast::NodeKind::ExprIdentifier, ChangeSeverity::Cosmetic));
            // Placeholder
        }

        history
    }
}
