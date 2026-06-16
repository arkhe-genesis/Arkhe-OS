// use cathedral_agent::orchestrator::String;

pub struct CurriculumTask {
    pub description: String,
}

pub struct CurriculumManager {}

impl CurriculumManager {
    pub fn new() -> Self {
        Self {}
    }

    pub async fn sample_task_for_agent(&self, _agent_id: &String) -> CurriculumTask {
        CurriculumTask { description: "Dummy Task".to_string() }
    }
}
