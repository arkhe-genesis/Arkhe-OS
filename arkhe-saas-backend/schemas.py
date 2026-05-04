# arkhe-saas-backend/schemas.py
"""Pydantic schemas for API validation."""
from typing import List, Optional
from pydantic import BaseModel, Field


class RegisterVertexRequest(BaseModel):
    network_id: str
    did: str
    public_key: str
    epsilon_history: Optional[List[List[float]]] = Field(
        default_factory=lambda: [[0.07, 0.07, 0.07] for _ in range(10)]
    )


class VertexResponse(BaseModel):
    id: str
    network_id: str
    did: str
    stake_value: float
    registered_at: float


class CastVoteRequest(BaseModel):
    fork_id: str
    voter_did: str
    vote_direction: bool
    timestamp: float
    signature: str


class VoteResponse(BaseModel):
    id: str
    fork_id: str
    voter_did: str
    weight: float


class EvaluateMergeRequest(BaseModel):
    fork_id: str
    odysseus_insight_ratio: float = 1.0


class EvaluateMergeResponse(BaseModel):
    fork_id: str
    accept: bool
    consensus_score: float
    total_votes: int
    for_weight: float
    against_weight: float


class NetworkCreateRequest(BaseModel):
    name: str
    target_epsilon: Optional[List[float]] = Field(default_factory=lambda: [0.07, 0.07, 0.07])
    sigma: Optional[List[float]] = Field(default_factory=lambda: [0.015, 0.015, 0.015])
    consensus_threshold: float = 0.55
    odysseus_multiplier: float = 0.3


class NetworkResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    target_epsilon: List[float]
    sigma: List[float]
    consensus_threshold: float
    odysseus_multiplier: float
    created_at: float


class TenantCreateRequest(BaseModel):
    name: str


class TenantResponse(BaseModel):
    id: str
    name: str
    api_key: str
    created_at: float
