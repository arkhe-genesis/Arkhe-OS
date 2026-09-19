//! Jules workflow orchestration.
//!
//! The transport is injected through [`JulesApi`].  This keeps the public
//! workflow independent of an unstable third-party HTTP surface and ensures
//! API keys remain in a transport implementation, never in workflow state.

use async_trait::async_trait;
use thiserror::Error;

use crate::memory::{Memory, MemoryError, MemoryKind, PersistentMemory};

/// Input used to create a cloud coding-agent session.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CreateSessionRequest {
    pub title: String,
    pub prompt: String,
    pub repository: String,
    pub starting_branch: String,
}

/// A discrete event reported by a Jules session.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Activity {
    pub id: String,
    pub kind: String,
    pub description: String,
}

/// Current state and activities of a Jules session.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Session {
    pub id: String,
    pub state: SessionState,
    pub activities: Vec<Activity>,
}

/// Terminal and in-progress session states understood by the workflow.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum SessionState {
    Pending,
    Running,
    Completed,
    Failed,
    Unknown(String),
}

impl SessionState {
    pub fn is_terminal(&self) -> bool {
        matches!(self, Self::Completed | Self::Failed)
    }
}

/// Error returned by the Jules API transport.
#[derive(Debug, Error, Eq, PartialEq)]
pub enum JulesApiError {
    #[error("Jules API request failed: {0}")]
    Request(String),
}

/// A narrow Jules API transport boundary.
#[async_trait]
pub trait JulesApi: Send + Sync {
    async fn create_session(&self, request: CreateSessionRequest)
        -> Result<Session, JulesApiError>;

    async fn get_session(&self, session_id: &str) -> Result<Session, JulesApiError>;
}

/// Errors from the agent workflow, including the stage that failed.
#[derive(Debug, Error)]
pub enum JulesAgentError {
    #[error(transparent)]
    Api(#[from] JulesApiError),
    #[error(transparent)]
    Memory(#[from] MemoryError),
}

/// Coordinates historical context with an asynchronous Jules session.
pub struct JulesAgent<M, J> {
    memory: M,
    api: J,
}

impl<M, J> JulesAgent<M, J>
where
    M: PersistentMemory,
    J: JulesApi,
{
    pub fn new(memory: M, api: J) -> Self {
        Self { memory, api }
    }

    /// Creates a Jules session with relevant durable context prepended.
    pub async fn start_session(
        &mut self,
        task: &str,
        repository: &str,
        starting_branch: &str,
    ) -> Result<Session, JulesAgentError> {
        let memories = self.memory.remember(task)?;
        let prompt = enrich_prompt(task, &memories);
        let session = self
            .api
            .create_session(CreateSessionRequest {
                title: format!("Arkhe: {task}"),
                prompt,
                repository: repository.to_owned(),
                starting_branch: starting_branch.to_owned(),
            })
            .await?;

        self.record_session_event(&session, "session started", MemoryKind::JulesInsight)?;
        Ok(session)
    }

    /// Fetches a session and records its terminal state exactly once per call.
    pub async fn refresh_session(&mut self, session_id: &str) -> Result<Session, JulesAgentError> {
        let session = self.api.get_session(session_id).await?;
        if session.state.is_terminal() {
            self.record_session_event(
                &session,
                "session reached terminal state",
                MemoryKind::WorkflowResult,
            )?;
        }
        Ok(session)
    }

    pub fn into_parts(self) -> (M, J) {
        (self.memory, self.api)
    }

    fn record_session_event(
        &mut self,
        session: &Session,
        event: &str,
        kind: MemoryKind,
    ) -> Result<(), JulesAgentError> {
        self.memory.memorize(Memory {
            id: format!("jules:{}:{event}", session.id),
            title: format!("Jules session {}", session.id),
            content: format!("{event}: {:?}", session.state),
            tags: vec!["jules".into(), "session".into()],
            kind,
        })?;
        Ok(())
    }
}

fn enrich_prompt(task: &str, memories: &[Memory]) -> String {
    if memories.is_empty() {
        return task.to_owned();
    }

    let context = memories
        .iter()
        .map(|memory| format!("- {}: {}", memory.title, memory.content))
        .collect::<Vec<_>>()
        .join("\n");
    format!("Historical context:\n{context}\n\nTask:\n{task}")
}

#[cfg(test)]
mod tests {
    use std::sync::{Arc, Mutex};

    use super::*;
    use crate::memory::InMemoryMemory;

    #[derive(Clone)]
    struct FakeJulesApi {
        requests: Arc<Mutex<Vec<CreateSessionRequest>>>,
        fetched: Session,
    }

    #[async_trait]
    impl JulesApi for FakeJulesApi {
        async fn create_session(
            &self,
            request: CreateSessionRequest,
        ) -> Result<Session, JulesApiError> {
            self.requests
                .lock()
                .expect("request mutex poisoned")
                .push(request);
            Ok(Session {
                id: "session-1".into(),
                state: SessionState::Running,
                activities: vec![],
            })
        }

        async fn get_session(&self, _session_id: &str) -> Result<Session, JulesApiError> {
            Ok(self.fetched.clone())
        }
    }

    fn session(state: SessionState) -> Session {
        Session {
            id: "session-1".into(),
            state,
            activities: vec![],
        }
    }

    #[tokio::test]
    async fn starts_a_session_with_matching_persistent_context() {
        let mut memory = InMemoryMemory::default();
        memory
            .memorize(Memory {
                id: "decision-1".into(),
                title: "Repository architecture".into(),
                content: "Use the maintained Rust workspace.".into(),
                tags: vec!["architecture".into()],
                kind: MemoryKind::JulesInsight,
            })
            .unwrap();
        let requests = Arc::new(Mutex::new(Vec::new()));
        let api = FakeJulesApi {
            requests: requests.clone(),
            fetched: session(SessionState::Running),
        };
        let mut agent = JulesAgent::new(memory, api);

        agent
            .start_session("architecture", "org/repo", "main")
            .await
            .unwrap();

        let request = requests.lock().unwrap().pop().unwrap();
        assert!(request.prompt.contains("Historical context:"));
        assert!(request
            .prompt
            .contains("Use the maintained Rust workspace."));
        assert_eq!(request.repository, "org/repo");
    }

    #[tokio::test]
    async fn records_only_terminal_session_results() {
        let requests = Arc::new(Mutex::new(Vec::new()));
        let api = FakeJulesApi {
            requests,
            fetched: session(SessionState::Completed),
        };
        let mut agent = JulesAgent::new(InMemoryMemory::default(), api);

        agent.refresh_session("session-1").await.unwrap();
        let (memory, _) = agent.into_parts();

        let result = memory.remember("terminal").unwrap();
        assert_eq!(result.len(), 1);
        assert_eq!(result[0].kind, MemoryKind::WorkflowResult);
    }

    #[test]
    fn recognises_terminal_states() {
        assert!(SessionState::Completed.is_terminal());
        assert!(SessionState::Failed.is_terminal());
        assert!(!SessionState::Running.is_terminal());
    }
}
