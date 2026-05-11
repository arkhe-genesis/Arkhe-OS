from pydantic import BaseModel, Field
from typing import Dict, Optional

class CoherenceMetrics(BaseModel):
    global_phi: float = Field(..., description="Global coherence score")
    substrate_phis: Dict[int, float] = Field(..., description="Coherence score by substrate")
    timestamp: float = Field(..., description="Timestamp of the metrics")
    validation_count: int = Field(..., description="Number of validations")
    avg_validation_phi: float = Field(..., description="Average validation coherence")
    std_validation_phi: float = Field(..., description="Standard deviation of validation coherence")

class ValidationRequest(BaseModel):
    experiment_type: str = Field(..., description="Type of validation experiment")
    material: str = Field(..., description="Material used")
    data_hash: str = Field(..., description="Hash of the raw data")
    cves: list[str] = Field(..., description="List of relevant CVEs")
    meta: Dict[str, str] = Field(default_factory=dict, description="Additional metadata")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API Version")
    global_phi_c: Optional[float] = Field(None, description="Global coherence score")
    substrates: Dict[str, Dict[str, str]] = Field(default_factory=dict, description="Substrates status")
    mrc_status: Dict[str, str] = Field(default_factory=dict, description="MRC Status")
