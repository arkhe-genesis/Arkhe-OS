# arkhe-saas-backend/models.py
"""SQLAlchemy models for multi-tenant PoC SaaS."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import uuid
import numpy as np


# In-memory store (replace with PostgreSQL + SQLAlchemy for production)
_TENANTS: Dict[str, 'Tenant'] = {}
_USERS: Dict[str, 'User'] = {}
_NETWORKS: Dict[str, 'Network'] = {}
_VERTICES: Dict[str, 'Vertex'] = {}
_FORK_VOTES: Dict[str, List['ForkVoteRecord']] = {}


@dataclass
class Tenant:
    id: str
    name: str
    api_key: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True


@dataclass
class User:
    id: str
    tenant_id: str
    email: str
    role: str = "member"  # admin, operator, member
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Network:
    id: str
    tenant_id: str
    name: str
    target_epsilon: List[float] = field(default_factory=lambda: [0.07, 0.07, 0.07])
    sigma: List[float] = field(default_factory=lambda: [0.015, 0.015, 0.015])
    consensus_threshold: float = 0.55
    odysseus_multiplier: float = 0.3
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True


@dataclass
class Vertex:
    id: str
    network_id: str
    did: str  # decentralized identifier
    public_key: str
    epsilon_history: List[List[float]] = field(default_factory=list)
    stake_value: float = 0.0
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ForkVoteRecord:
    id: str
    network_id: str
    fork_id: str
    voter_did: str
    vote_direction: bool
    timestamp: float
    signature: str
    weight: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)


# ─── CRUD helpers ──────────────────────────────────────────────────────────────

def create_tenant(name: str) -> Tenant:
    tenant = Tenant(id=str(uuid.uuid4()), name=name, api_key=str(uuid.uuid4()))
    _TENANTS[tenant.id] = tenant
    return tenant


def get_tenant(tenant_id: str) -> Optional[Tenant]:
    return _TENANTS.get(tenant_id)


def create_network(tenant_id: str, name: str, **kwargs) -> Network:
    network = Network(id=str(uuid.uuid4()), tenant_id=tenant_id, name=name, **kwargs)
    _NETWORKS[network.id] = network
    return network


def get_network(network_id: str) -> Optional[Network]:
    return _NETWORKS.get(network_id)


def list_networks(tenant_id: str) -> List[Network]:
    return [n for n in _NETWORKS.values() if n.tenant_id == tenant_id]


def register_vertex(network_id: str, did: str, public_key: str) -> Vertex:
    vertex = Vertex(id=str(uuid.uuid4()), network_id=network_id, did=did, public_key=public_key)
    _VERTICES[vertex.id] = vertex
    return vertex


def list_vertices(network_id: str) -> List[Vertex]:
    return [v for v in _VERTICES.values() if v.network_id == network_id]


def cast_vote(network_id: str, fork_id: str, voter_did: str, vote_direction: bool,
              timestamp: float, signature: str) -> ForkVoteRecord:
    vote = ForkVoteRecord(
        id=str(uuid.uuid4()), network_id=network_id, fork_id=fork_id,
        voter_did=voter_did, vote_direction=vote_direction,
        timestamp=timestamp, signature=signature
    )
    if fork_id not in _FORK_VOTES:
        _FORK_VOTES[fork_id] = []
    _FORK_VOTES[fork_id].append(vote)
    return vote


def get_votes(fork_id: str) -> List[ForkVoteRecord]:
    return _FORK_VOTES.get(fork_id, [])
