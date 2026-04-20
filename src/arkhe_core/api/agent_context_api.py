from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from enum import Enum
import uuid
from datetime import datetime
import os
import sys

# Add arkhe_core to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ontology.sparql_client import OntologyClient

app = FastAPI(title="Agent Context API", version="1.2.0")

class TaskType(str, Enum):
    QEC_EXECUTION = "QEC_EXECUTION"
    MAGIC_DISTILLATION = "MAGIC_DISTILLATION"
    INFERENCE_ROUTING = "INFERENCE_ROUTING"

class ComplexityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class TaskAssignedEvent(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    task_type: TaskType
    complexity: ComplexityLevel
    required_tokens: int
    quantum_preference: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ExecutionPlan(BaseModel):
    plan_id: str
    tasks: List[dict]
    required_seals: List[str]
    fallback_strategy: Literal["ABORT", "DEGRADE", "RETRY"]
    estimated_risk: float

def get_ontology_client():
    return OntologyClient()

@app.post("/v1/tasks", response_model=ExecutionPlan, status_code=201)
async def submit_task(event: TaskAssignedEvent, ont: OntologyClient = Depends(get_ontology_client)):
    # Validação ontológica em tempo de execução
    if not ont.validate_agent_task(event.agent_id, event.task_type):
        raise HTTPException(status_code=403, detail="Agent not authorized for this task type")

    seals = ont.get_required_seals(event.task_id)

    # Lógica de orquestração
    profile = "MEDIUM_GPU"
    risk = 0.05
    if event.complexity == ComplexityLevel.HIGH:
        profile = "LARGE_GPU"
        risk = 0.15

    return ExecutionPlan(
        plan_id=str(uuid.uuid4()),
        tasks=[{"task_id": event.task_id, "profile": profile}],
        required_seals=seals or ["TEMPORAL"],
        fallback_strategy="DEGRADE",
        estimated_risk=risk
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
