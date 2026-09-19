//! Persistent-memory boundary for Arkhe agents.
//!
//! This module deliberately exposes a small capability-based contract instead
//! of coupling agent workflows to a particular memory server.  An Octobrain
//! MCP or crate adapter can implement [`PersistentMemory`] without exposing
//! credentials or vendor-specific records to callers.

use std::collections::HashMap;

use thiserror::Error;

/// A durable, attributable insight available to an agent workflow.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Memory {
    pub id: String,
    pub title: String,
    pub content: String,
    pub tags: Vec<String>,
    pub kind: MemoryKind,
}

/// The class of an Arkhe agent memory.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum MemoryKind {
    JulesInsight,
    WorkflowResult,
}

/// Errors surfaced by a persistent-memory provider.
#[derive(Debug, Error, Eq, PartialEq)]
pub enum MemoryError {
    #[error("memory provider failed: {0}")]
    Provider(String),
}

/// Capability required by agent workflows to retain and retrieve context.
///
/// Production implementations may delegate to Octobrain.  The contract keeps
/// memory retrieval deterministic at this layer: providers decide semantic
/// ranking, while callers receive the selected records in provider order.
pub trait PersistentMemory {
    fn remember(&self, query: &str) -> Result<Vec<Memory>, MemoryError>;

    fn memorize(&mut self, memory: Memory) -> Result<(), MemoryError>;
}

/// Minimal in-process provider used by local workflows and tests.
#[derive(Default)]
pub struct InMemoryMemory {
    records: HashMap<String, Memory>,
}

impl PersistentMemory for InMemoryMemory {
    fn remember(&self, query: &str) -> Result<Vec<Memory>, MemoryError> {
        let query = query.to_lowercase();
        let mut matches = self
            .records
            .values()
            .filter(|memory| {
                memory.title.to_lowercase().contains(&query)
                    || memory.content.to_lowercase().contains(&query)
                    || memory
                        .tags
                        .iter()
                        .any(|tag| tag.to_lowercase().contains(&query))
            })
            .cloned()
            .collect::<Vec<_>>();
        matches.sort_by(|left, right| left.id.cmp(&right.id));
        Ok(matches)
    }

    fn memorize(&mut self, memory: Memory) -> Result<(), MemoryError> {
        self.records.insert(memory.id.clone(), memory);
        Ok(())
    }
}
