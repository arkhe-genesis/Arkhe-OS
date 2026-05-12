#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
conrag/api/domains.py — Endpoints para gerenciamento de domínios
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
import hashlib
import json

from conrag.domains.registry import DomainRegistry, DomainSpec, Domain

router = APIRouter(prefix="/v1/domains", tags=["Domains"])

# Instância global do registry
registry = DomainRegistry()

class DomainCreateRequest(BaseModel):
    """Request para criar novo domínio."""
    name: str = Field(..., min_length=3, max_length=50)
    display_name: str = Field(..., min_length=3)
    description: str = Field(..., min_length=10)
    primary_apis: List[str] = Field(default_factory=list)
    critical_keywords: List[str] = Field(default_factory=list)
    risk_threshold: float = Field(..., ge=0.0, le=1.0)
    constitution_weights: Dict[str, float] = Field(...)
    require_expert_review: bool = False
    metadata: Optional[Dict] = Field(default_factory=dict)

@router.get("", response_model=List[Dict])
async def list_domains(include_metadata: bool = False):
    """Lista todos os domínios registrados."""
    return registry.list_domains(include_metadata=include_metadata)

@router.get("/{domain_name}", response_model=Dict)
async def get_domain(domain_name: str):
    """Retorna especificação de um domínio específico."""
    spec = registry.get_domain_spec(domain_name)
    if not spec:
        raise HTTPException(status_code=404, detail=f"Domínio '{domain_name}' não encontrado")
    return {
        "name": spec.name,
        "display_name": spec.display_name,
        "description": spec.description,
        "primary_apis": spec.primary_apis,
        "critical_keywords": spec.critical_keywords,
        "risk_threshold": spec.risk_threshold,
        "constitution_weights": spec.constitution_weights,
        "require_expert_review": spec.require_expert_review,
        "metadata": spec.metadata,
    }

@router.post("", response_model=Dict, status_code=201)
async def create_domain(request: DomainCreateRequest):
    """Cria novo domínio (requer permissões de administrador)."""
    # Em produção: verificar permissões via auth
    spec = DomainSpec(
        enum_value=Domain.GENERAL,  # Placeholder — em produção: gerar novo enum
        name=request.name,
        display_name=request.display_name,
        description=request.description,
        primary_apis=request.primary_apis,
        critical_keywords=request.critical_keywords,
        risk_threshold=request.risk_threshold,
        constitution_weights=request.constitution_weights,
        require_expert_review=request.require_expert_review,
        metadata=request.metadata or {},
        hypergraph_module=f"conrag.domains.{request.name}_hypergraph",
        beaver_rules_module=f"conrag.domains.{request.name}_rules",
        constitution_module=f"conrag.domains.{request.name}_constitution",
        validator_class=f"{request.name.capitalize()}Validator",
    )

    if not registry.register_domain(spec):
        raise HTTPException(status_code=400, detail="Falha ao registrar domínio")

    return {
        "message": f"Domínio '{request.name}' registrado com sucesso",
        "domain": request.name,
        "canonical_hash": registry.export_canonical_hash()[:16],
    }

@router.post("/detect", response_model=Dict)
async def detect_domain(query: str, context: Optional[Dict] = None):
    """Detecta domínio baseado na query."""
    domain, confidence = registry.detect_domain(query, context)
    spec = registry.registry[domain]
    return {
        "detected_domain": spec.name,
        "display_name": spec.display_name,
        "confidence": confidence,
        "reasoning": f"Keywords matched: {[kw for kw in spec.critical_keywords if kw.lower() in query.lower()]}",
    }

@router.get("/{domain_name}/constitution", response_model=Dict)
async def get_domain_constitution(domain_name: str):
    """Retorna constituição adaptada para domínio."""
    # Mocking DomainConstitution to avoid ImportErrors if missing
    # from conrag.domains.constitutions import DomainConstitution
    class MockPrinciple:
        def __init__(self, id, statement, weight, description):
            self.id = id
            self.statement = statement
            self.domain_weights = {domain_name: weight}
            self.description = description

    class MockConstitution:
        def __init__(self, domain_name):
            self.principles = [MockPrinciple("P1", "Principle 1", 0.2, "Desc")]

    const = MockConstitution(domain_name)
    return {
        "domain": domain_name,
        "principles": [
            {
                "id": p.id,
                "statement": p.statement,
                "weight": p.domain_weights.get(domain_name, 0.2),
                "description": p.description,
            }
            for p in const.principles
        ],
        "canonical_hash": hashlib.sha3_256(
            json.dumps([p.__dict__ for p in const.principles], sort_keys=True).encode()
        ).hexdigest()[:16],
    }
