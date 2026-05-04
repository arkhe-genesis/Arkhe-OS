# arkhe-saas-backend/routers/coherence.py
"""Coherence network API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException

from schemas import (
    CastVoteRequest,
    EvaluateMergeRequest,
    EvaluateMergeResponse,
    NetworkCreateRequest,
    NetworkResponse,
    RegisterVertexRequest,
    VertexResponse,
    VoteResponse,
)
from models import (
    cast_vote as db_cast_vote,
    create_network,
    get_network,
    list_networks,
    list_vertices,
    register_vertex as db_register_vertex,
)
from services.consensus_service import consensus_service

router = APIRouter(prefix="/coherence", tags=["Coherence"])


@router.post("/networks", response_model=NetworkResponse)
def create_coherence_network(tenant_id: str, body: NetworkCreateRequest):
    """Create a new coherence network for a tenant."""
    network = create_network(
        tenant_id=tenant_id,
        name=body.name,
        target_epsilon=body.target_epsilon,
        sigma=body.sigma,
        consensus_threshold=body.consensus_threshold,
        odysseus_multiplier=body.odysseus_multiplier,
    )
    return NetworkResponse(
        id=network.id,
        tenant_id=network.tenant_id,
        name=network.name,
        target_epsilon=network.target_epsilon,
        sigma=network.sigma,
        consensus_threshold=network.consensus_threshold,
        odysseus_multiplier=network.odysseus_multiplier,
        created_at=network.created_at.timestamp(),
    )


@router.get("/networks", response_model=List[NetworkResponse])
def list_coherence_networks(tenant_id: str):
    """List all coherence networks for a tenant."""
    networks = list_networks(tenant_id)
    return [
        NetworkResponse(
            id=n.id,
            tenant_id=n.tenant_id,
            name=n.name,
            target_epsilon=n.target_epsilon,
            sigma=n.sigma,
            consensus_threshold=n.consensus_threshold,
            odysseus_multiplier=n.odysseus_multiplier,
            created_at=n.created_at.timestamp(),
        )
        for n in networks
    ]


@router.get("/networks/{network_id}", response_model=NetworkResponse)
def get_coherence_network(network_id: str):
    """Get a specific coherence network."""
    network = get_network(network_id)
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")
    return NetworkResponse(
        id=network.id,
        tenant_id=network.tenant_id,
        name=network.name,
        target_epsilon=network.target_epsilon,
        sigma=network.sigma,
        consensus_threshold=network.consensus_threshold,
        odysseus_multiplier=network.odysseus_multiplier,
        created_at=network.created_at.timestamp(),
    )


@router.post("/register-vertex", response_model=VertexResponse)
def register_vertex_endpoint(body: RegisterVertexRequest):
    """Register a new vertex in a coherence network."""
    network = get_network(body.network_id)
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")

    stake_value = consensus_service.register_vertex(
        network_id=body.network_id,
        vertex_did=body.did,
        epsilon_history=body.epsilon_history or [[0.07, 0.07, 0.07] for _ in range(10)],
        target_epsilon=network.target_epsilon,
        sigma=network.sigma,
        threshold=network.consensus_threshold,
        odys_mult=network.odysseus_multiplier,
    )

    vertex = db_register_vertex(
        network_id=body.network_id,
        did=body.did,
        public_key=body.public_key,
    )

    return VertexResponse(
        id=vertex.id,
        network_id=vertex.network_id,
        did=vertex.did,
        stake_value=stake_value,
        registered_at=vertex.registered_at.timestamp(),
    )


@router.get("/vertices/{network_id}", response_model=List[VertexResponse])
def list_network_vertices(network_id: str):
    """List all vertices in a coherence network."""
    vertices = list_vertices(network_id)
    return [
        VertexResponse(
            id=v.id,
            network_id=v.network_id,
            did=v.did,
            stake_value=v.stake_value,
            registered_at=v.registered_at.timestamp(),
        )
        for v in vertices
    ]


@router.post("/cast-vote", response_model=VoteResponse)
def cast_vote_endpoint(tenant_id: str, body: CastVoteRequest):
    """Cast a vote for/against a fork merge."""
    networks = list_networks(tenant_id)
    if not networks:
        raise HTTPException(status_code=404, detail="No networks found for tenant")

    network = networks[0]

    weight = consensus_service.cast_vote(
        network_id=network.id,
        fork_id=body.fork_id,
        voter_did=body.voter_did,
        vote_direction=body.vote_direction,
        timestamp=body.timestamp,
        signature=body.signature,
        epsilon_fork=network.target_epsilon,
        threshold=network.consensus_threshold,
        odys_mult=network.odysseus_multiplier,
    )

    vote = db_cast_vote(
        network_id=network.id,
        fork_id=body.fork_id,
        voter_did=body.voter_did,
        vote_direction=body.vote_direction,
        timestamp=body.timestamp,
        signature=body.signature,
    )

    return VoteResponse(
        id=vote.id,
        fork_id=vote.fork_id,
        voter_did=vote.voter_did,
        weight=weight,
    )


@router.post("/evaluate-merge", response_model=EvaluateMergeResponse)
def evaluate_merge_endpoint(tenant_id: str, body: EvaluateMergeRequest):
    """Evaluate consensus for a fork merge."""
    networks = list_networks(tenant_id)
    if not networks:
        raise HTTPException(status_code=404, detail="No networks found for tenant")

    network = networks[0]

    accept, score, for_w, against_w, total = consensus_service.evaluate_merge(
        network_id=network.id,
        fork_id=body.fork_id,
        odysseus_insight_ratio=body.odysseus_insight_ratio,
        threshold=network.consensus_threshold,
        odys_mult=network.odysseus_multiplier,
    )

    return EvaluateMergeResponse(
        fork_id=body.fork_id,
        accept=accept,
        consensus_score=score,
        total_votes=total,
        for_weight=for_w,
        against_weight=against_w,
    )
