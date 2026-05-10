use std::collections::HashMap;
use serde::{Serialize, Deserialize};
use sha3::{Digest, Sha3_256};

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct UAST {
    pub root: NodeId,
    pub nodes: HashMap<NodeId, UASTNode>,
    pub metadata: UASTMetadata,
    pub source_info: SourceInfo,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct UASTMetadata {
    pub language: String,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct SourceInfo {
    pub filename: Option<String>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct NodeId(pub u64);

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct UASTNode {
    pub id: NodeId,
    pub kind: NodeKind,
    pub children: Vec<NodeId>,
    pub attributes: HashMap<String, AttributeValue>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub enum NodeKind {
    Program, DeclFunction, DeclVariable, ExprCall, ExprBinary, ExprLiteral, ExprIdentifier, StmtIf, ExprReturn,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub enum AttributeValue {
    String(String), Integer(i64), Boolean(bool), Float(f64), None
}

impl UAST {
    pub fn new(language: &str) -> Self {
        Self {
            root: NodeId(0),
            nodes: HashMap::new(),
            metadata: UASTMetadata { language: language.to_string() },
            source_info: SourceInfo { filename: None },
        }
    }

    pub fn node_count(&self) -> usize {
        self.nodes.len()
    }

    pub fn compute_hash(&self) -> Vec<u8> {
        let serialized = serde_json::to_vec(&self.nodes).unwrap_or_default();
        Sha3_256::digest(&serialized).to_vec()
    }
}

pub struct TypeRef {
    pub name: String,
}
