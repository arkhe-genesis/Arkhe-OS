// ============================================================================
// ARKHE Ω‑TEMP — Workflow Engine for Multi-Language Pipelines
// ============================================================================
use crate::polyglot_router::{PolyglotRouter, SemanticRequirements};
use std::collections::{HashMap, VecDeque};
use async_trait::async_trait;

/// Representa um pipeline de processamento de código multi-linguagem
#[derive(Clone, Debug)]
pub struct Workflow {
    pub id: String,
    pub name: String,
    pub description: String,
    pub steps: Vec<WorkflowStep>,
    pub inputs: Vec<WorkflowInput>,
    pub outputs: Vec<WorkflowOutput>,
    pub timeout_seconds: u64,
}

#[derive(Clone, Debug)]
pub struct WorkflowInput {
    pub name: String,
    pub description: String,
    pub required: bool,
}

#[derive(Clone, Debug)]
pub struct WorkflowOutput {
    pub name: String,
    pub variable_name: String,
}

#[derive(Clone, Debug)]
pub struct WorkflowStep {
    pub id: String,
    pub name: String,
    pub action: StepAction,
    pub dependencies: Vec<String>, // IDs de steps anteriores
    pub retry_policy: RetryPolicy,
    pub output_mapping: HashMap<String, String>, // Mapeamento de outputs → vars
}

#[derive(Clone, Debug)]
pub enum StepAction {
    Parse { language: Option<String> },
    Transpile { target: String, from: Option<String> },
    Analyze { analysis_type: AnalysisType },
    Validate { validator: String },
    Deploy { target_env: String },
    Custom { plugin_name: String, config: serde_json::Value },
}

#[derive(Clone, Debug)]
pub enum AnalysisType {
    Semantic,
    Security,
    Performance,
    Complexity,
    CrossLanguage,
}

#[derive(Clone, Debug, Default)]
pub struct RetryPolicy {
    pub max_attempts: u32,
    pub backoff_ms: u64,
    pub retryable_errors: Vec<String>,
}

/// Engine que executa workflows com suporte a paralelismo e recuperação de erros
pub struct WorkflowEngine {
    router: PolyglotRouter,
    plugins: HashMap<String, Box<dyn StepExecutor + Send + Sync>>,
    execution_log: Vec<ExecutionError>,
}

#[async_trait]
pub trait StepExecutor: Send + Sync {
    async fn execute(
        &self,
        ctx: &ExecutionContext,
        action: &StepAction,
    ) -> Result<StepResult, ExecutionError>;
}

pub struct ExecutionContext {
    pub workflow_id: String,
    pub variables: HashMap<String, serde_json::Value>,
    pub artifacts: HashMap<String, Vec<u8>>, // Código/ASTs intermediários
    pub metadata: WorkflowMetadata,
}

#[derive(Clone)]
pub struct StepResult {
    pub success: bool,
    pub outputs: HashMap<String, serde_json::Value>,
    pub artifacts: HashMap<String, Vec<u8>>,
    pub metrics: StepMetrics,
}

pub struct WorkflowResult {
    pub workflow_id: String,
    pub success: bool,
    pub outputs: HashMap<String, serde_json::Value>,
    pub artifacts: HashMap<String, Vec<u8>>,
    pub execution_time_ms: u64,
    pub step_results: HashMap<String, StepResult>,
}

impl WorkflowEngine {
    pub fn new(router: PolyglotRouter) -> Self {
        Self {
            router,
            plugins: HashMap::new(),
            execution_log: Vec::new(),
        }
    }

    /// Registrar executor customizado para actions do tipo Custom
    pub fn register_plugin(
        &mut self,
        name: &str,
        executor: Box<dyn StepExecutor + Send + Sync>,
    ) {
        self.plugins.insert(name.into(), executor);
    }

    /// Executar workflow completo
    pub async fn execute_workflow(
        &mut self,
        workflow: &Workflow,
        inputs: HashMap<String, serde_json::Value>,
    ) -> Result<WorkflowResult, ExecutionError> {
        let mut ctx = ExecutionContext {
            workflow_id: workflow.id.clone(),
            variables: inputs,
            artifacts: HashMap::new(),
            metadata: WorkflowMetadata {
                started_at: std::time::SystemTime::now(),
                ..Default::default()
            },
        };

        // Ordenar steps por dependências (topological sort)
        let ordered_steps = self.topological_sort(&workflow.steps)?;

        // Executar steps em ordem, com paralelismo onde possível
        let mut results = HashMap::new();

        for step in ordered_steps {
            // Aguardar dependências
            for dep in &step.dependencies {
                if !results.contains_key(dep) {
                    return Err(ExecutionError::DependencyNotMet(dep.clone()));
                }
            }

            // Executar step
            let result = self.execute_step(&mut ctx, &step).await?;
            results.insert(step.id.clone(), result.clone());

            // Mapear outputs para variáveis do contexto
            for (output_name, var_name) in &step.output_mapping {
                if let Some(value) = result.outputs.get(output_name) {
                    ctx.variables.insert(var_name.clone(), value.clone());
                }
            }

            // Armazenar artifacts
            ctx.artifacts.extend(result.artifacts);
        }

        // Coletar outputs finais do workflow
        let final_outputs = workflow.outputs.iter()
            .filter_map(|out| {
                ctx.variables.get(&out.variable_name)
                    .map(|v| (out.name.clone(), v.clone()))
            })
            .collect();

        Ok(WorkflowResult {
            workflow_id: workflow.id.clone(),
            success: true,
            outputs: final_outputs,
            artifacts: ctx.artifacts,
            execution_time_ms: ctx.metadata.started_at.elapsed()
                .map(|d| d.as_millis() as u64)
                .unwrap_or(0),
            step_results: results,
        })
    }

    async fn execute_step(
        &self,
        ctx: &mut ExecutionContext,
        step: &WorkflowStep,
    ) -> Result<StepResult, ExecutionError> {
        let mut last_error = None;

        for attempt in 1..=step.retry_policy.max_attempts {
            match self.do_execute_step(ctx, &step.action).await {
                Ok(result) => return Ok(result),
                Err(e) => {
                    if step.retry_policy.retryable_errors.iter().any(|err|
                        e.to_string().contains(err)
                    ) && attempt < step.retry_policy.max_attempts {
                        // Backoff exponencial
                        tokio::time::sleep(
                            std::time::Duration::from_millis(
                                step.retry_policy.backoff_ms * (1 << (attempt - 1))
                            )
                        ).await;
                        last_error = Some(e);
                        continue;
                    }
                    return Err(e);
                }
            }
        }

        Err(last_error.unwrap_or(ExecutionError::Unknown("Max retries exceeded".into())))
    }

    async fn do_execute_step(
        &self,
        ctx: &ExecutionContext,
        action: &StepAction,
    ) -> Result<StepResult, ExecutionError> {
        match action {
            StepAction::Parse { language: _ } => {
                let source = ctx.variables.get("source_code")
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| ExecutionError::MissingInput("source_code".into()))?;

                let mut parser = self.router.get_parser();
                let result = parser.parse(source, None)
                    .map_err(|e| ExecutionError::ParseFailed(e))?;

                Ok(StepResult {
                    success: true,
                    outputs: HashMap::from([
                        ("ast_hash".into(), serde_json::Value::String(
                            hex::encode(&result.integrity_proof)
                        )),
                        ("detected_language".into(), serde_json::Value::String(
                            result.detected_language
                        )),
                    ]),
                    artifacts: HashMap::from([
                        ("uast".into(), serde_json::to_vec(&result.uast).unwrap_or_default()),
                    ]),
                    metrics: StepMetrics {
                        duration_ms: 0, // TODO: medir tempo real
                        ..Default::default()
                    },
                })
            }

            StepAction::Transpile { target, from } => {
                let source = ctx.variables.get("source_code")
                    .or_else(|| ctx.variables.get("transpiled_code"))
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| ExecutionError::MissingInput("source_code".into()))?;

                let source_lang = from.as_deref()
                    .or_else(|| ctx.variables.get("detected_language")
                        .and_then(|v| v.as_str()));

                let result = self.router.clone().transpile_with_routing(
                    source,
                    source_lang,
                    target,
                    SemanticRequirements::default(),
                ).await
                .map_err(|e| ExecutionError::TranspileFailed(e.to_string()))?;

                Ok(StepResult {
                    success: true,
                    outputs: HashMap::from([
                        ("target_language".into(), serde_json::Value::String(
                            result.target_language
                        )),
                        ("output_size".into(), serde_json::Value::Number(
                            result.metrics.output_size_bytes.into()
                        )),
                    ]),
                    artifacts: HashMap::from([
                        ("transpiled_code".into(), result.code.into_bytes()),
                    ]),
                    metrics: StepMetrics {
                        nodes_transformed: result.metrics.nodes_visited as u64,
                        ..Default::default()
                    },
                })
            }

            StepAction::Analyze { analysis_type: _ } => {
                // Executar análise semântica
                let source = ctx.variables.get("source_code")
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| ExecutionError::MissingInput("source_code".into()))?;

                let language = ctx.variables.get("detected_language")
                    .and_then(|v| v.as_str())
                    .unwrap_or("unknown");

                let mut parser = self.router.get_parser();
                let report = parser.analyze_cross_language(source, language);

                Ok(StepResult {
                    success: true,
                    outputs: HashMap::from([
                        ("overall_score".into(), serde_json::Value::Number(
                            serde_json::Number::from_f64(report.overall_score)
                                .unwrap_or(serde_json::Number::from(0))
                        )),
                        ("security_score".into(), serde_json::Value::Number(
                            serde_json::Number::from_f64(report.security_score)
                                .unwrap_or(serde_json::Number::from(0))
                        )),
                        ("issues_count".into(), serde_json::Value::Number(
                            0.into()
                        )),
                    ]),
                    artifacts: HashMap::from([
                        ("analysis_report".into(), Vec::new()),
                    ]),
                    metrics: StepMetrics::default(),
                })
            }

            StepAction::Custom { plugin_name, config: _ } => {
                // Executar plugin customizado
                let executor = self.plugins.get(plugin_name)
                    .ok_or_else(|| ExecutionError::PluginNotFound(plugin_name.clone()))?;

                executor.execute(ctx, action).await
            }

            // ... outros tipos de action
            _ => Err(ExecutionError::NotImplemented(format!("{:?}", action))),
        }
    }

    fn topological_sort(
        &self,
        steps: &[WorkflowStep],
    ) -> Result<Vec<WorkflowStep>, ExecutionError> {
        // Implementação de ordenação topológica simples
        // (Kahn's algorithm)
        let mut in_degree = HashMap::new();
        let mut graph = HashMap::new();

        for step in steps {
            in_degree.insert(&step.id, step.dependencies.len());
            for dep in &step.dependencies {
                graph.entry(dep).or_insert_with(Vec::new).push(&step.id);
            }
        }

        let mut queue: VecDeque<_> = steps.iter()
            .filter(|s| in_degree[&s.id] == 0)
            .collect();

        let mut result = Vec::new();

        while let Some(step) = queue.pop_front() {
            result.push(step.clone());

            if let Some(dependents) = graph.get(&step.id) {
                for dep_id in dependents {
                    *in_degree.get_mut(dep_id).unwrap() -= 1;
                    if in_degree[dep_id] == 0 {
                        if let Some(s) = steps.iter().find(|s| s.id == **dep_id) {
                            queue.push_back(s);
                        }
                    }
                }
            }
        }

        if result.len() != steps.len() {
            return Err(ExecutionError::CycleDetected);
        }

        Ok(result)
    }
}

#[derive(Clone, Debug)]
pub struct WorkflowMetadata {
    pub started_at: std::time::SystemTime,
    pub completed_at: Option<std::time::SystemTime>,
    pub total_steps: usize,
    pub successful_steps: usize,
    pub failed_steps: usize,
}

impl Default for WorkflowMetadata {
    fn default() -> Self {
        Self {
            started_at: std::time::SystemTime::now(),
            completed_at: None,
            total_steps: 0,
            successful_steps: 0,
            failed_steps: 0,
        }
    }
}

#[derive(Clone, Debug, Default)]
pub struct StepMetrics {
    pub duration_ms: u64,
    pub memory_used_bytes: u64,
    pub nodes_transformed: u64,
    pub cache_hits: u64,
}

#[derive(Debug, thiserror::Error)]
pub enum ExecutionError {
    #[error("Input ausente: {0}")]
    MissingInput(String),
    #[error("Falha no parse: {0}")]
    ParseFailed(String),
    #[error("Falha na transpilação: {0}")]
    TranspileFailed(String),
    #[error("Plugin não encontrado: {0}")]
    PluginNotFound(String),
    #[error("Dependência não satisfeita: {0}")]
    DependencyNotMet(String),
    #[error("Ciclo detectado nas dependências")]
    CycleDetected,
    #[error("Não implementado: {0}")]
    NotImplemented(String),
    #[error("Erro desconhecido: {0}")]
    Unknown(String),
}
