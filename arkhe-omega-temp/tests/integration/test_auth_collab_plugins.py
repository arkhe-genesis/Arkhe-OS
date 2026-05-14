#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_auth_collab_plugins.py — Teste de integração: Auth + Collaborative Review + Ethical Plugins
"""

import asyncio
import tempfile
import shutil
import sys
import os
from pathlib import Path
import pytest

# Adjust Python path to load local modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from arkp_auth.src.reviewer_auth import (
    IdentityVerifier, ReviewerAuthManager, ReviewerIdentity, AuthProvider
)
from arkp_review.src.collaborative_review import (
    ConsensusReviewEngine, CollaborativeReviewWorkflow, ReviewVote, ConsensusStrategy, PublicationDecision
)
from arkp_ethical_plugins.src.plugin_system import (
    DomainRuleRegistry, EthicalDomain, HealthcareEthicalPlugin, MythosGateWithPlugins
)
from arkp_ethical_plugins.src.mythos_publisher import EthicalRiskAssessor

@pytest.fixture
def temp_plugin_dir():
    """Cria diretório temporário para plugins."""
    tmpdir = tempfile.mkdtemp(prefix="arkhe-plugins-")
    yield Path(tmpdir)
    shutil.rmtree(tmpdir, ignore_errors=True)

@pytest.fixture
def mock_qip_engine():
    """Mock do QIP engine para testes."""
    class MockQIP:
        def get_reputation_score(self, reviewer_id):
            # Simular reputação baseada no ID
            return 0.9 if "senior" in reviewer_id else 0.75
    return MockQIP()

@pytest.fixture
def mock_temporal_client():
    """Mock do cliente TemporalChain."""
    class MockTemporal:
        def record_event(self, event_type, data):
            pass  # Simular logging
        def anchor_content(self, content_hash, metadata):
            return f"temporal:{content_hash[:16]}"
    return MockTemporal()

@pytest.fixture
def mock_ledger():
    """Mock do AuditLedger."""
    class MockLedger:
        def __init__(self):
            self.records = []
        def record(self, event_type, data):
            self.records.append((event_type, data))
    return MockLedger()

async def test_reviewer_auth_orcid(mock_qip_engine, mock_temporal_client):
    """Testa autenticação de revisor via ORCID."""
    verifier = IdentityVerifier(
        client_id="test-client",
        client_secret="test-secret",
        redirect_uri="https://test/callback"
    )
    auth_manager = ReviewerAuthManager(
        verifier=verifier,
        jwt_secret="test-jwt-secret",
        qip_engine=mock_qip_engine,
        temporal_client=mock_temporal_client,
    )

    # Simular token ORCID válido (em produção: token real)
    orcid_token = "mock-orcid-token-123"
    session = auth_manager.login_with_orcid(orcid_token, ip_address="192.168.1.1")

    assert session is not None
    assert session.reviewer_id is not None
    assert session.access_token is not None

    # Validar token
    identity = auth_manager.validate_access_token(session.access_token)
    assert identity is not None
    assert identity.auth_provider == AuthProvider.ORCID

async def test_collaborative_review_consensus(mock_qip_engine, mock_ledger):
    """Testa consenso em revisão colaborativa."""
    engine = ConsensusReviewEngine(
        qip_engine=mock_qip_engine,
        ledger=mock_ledger,
    )

    # Criar tarefa de revisão de risco médio
    task = engine.create_review_task(
        package_name="health-ai-diagnosis",
        package_version="1.0.0",
        author_orcid="ORCID:AUTHOR",
        risk_score=0.55,  # Medium risk
        risk_breakdown={"privacy_violation": 0.4, "algorithmic_bias": 0.3},
        conrag_report={"overall": 0.72},
        source_files=[("diagnoser.py", "def diagnose(patient_data): ...")],
        dependencies=[],
        assigned_reviewers=["reviewer-1", "reviewer-2", "reviewer-3"],
        deadline_hours=48.0,
    )

    # Simular votos de 3 revisores
    votes = [
        ("reviewer-1", ReviewVote.APPROVE, "Approved with minor suggestions", [], 0.9),
        ("reviewer-2", ReviewVote.APPROVE, "Good implementation", [], 0.85),
        ("reviewer-3", ReviewVote.REQUEST_CHANGES, "Needs bias mitigation", ["Add fairness checks"], 0.7),
    ]

    for reviewer_id, vote, rationale, changes, confidence in votes:
        result = await engine.submit_vote(
            task_id=task.task_id,
            reviewer_id=reviewer_id,
            vote=vote,
            rationale=rationale,
            suggested_changes=changes,
            confidence=confidence,
        )
        assert result["success"]

    # Verificar que consenso foi alcançado (maioria aprova)
    status = engine.get_task_status(task.task_id)
    assert status["status"] == "consensus_reached"
    assert status["final_decision"] == PublicationDecision.APPROVED.value
    assert status["consensus_score"] >= 0.66  # Supermajority

async def test_ethical_plugin_healthcare(temp_plugin_dir):
    """Testa plugin de regras éticas para saúde."""
    registry = DomainRuleRegistry(plugin_dir=temp_plugin_dir)

    # Registrar plugin de saúde (simulado via código inline)
    # Em produção: carregaria de arquivo .py
    registry._loaded_plugins["healthcare-hipaa-v1"] = HealthcareEthicalPlugin()
    registry._plugin_metadata["healthcare-hipaa-v1"] = type('obj', (object,), {
        "plugin_id": "healthcare-hipaa-v1",
        "domain": EthicalDomain.HEALTHCARE,
        "version": "1.2.0",
        "author": "ARKHE Health Ethics Board",
        "description": "HIPAA compliance rules",
        "checksum": "mock-checksum",
        "required_permissions": [],
        "compatible_versions": ["5.0.0"],
    })()
    registry._domain_plugins[EthicalDomain.HEALTHCARE] = ["healthcare-hipaa-v1"]

    # Avaliar pacote de saúde
    manifest = {
        "package": {
            "name": "patient-diagnoser",
            "version": "1.0.0",
            "description": "AI diagnostic tool",
            "license": "MIT",
        },
        "dependencies": {},
    }
    source_files = [
        ("diagnoser.py", """
def diagnose(patient_data):
    # Uses patient_id without encryption
    result = ml_model.predict(patient_data['race'], patient_data['symptoms'])
    print(f"Diagnosis: {result}")  # Logs PHI!
    return result
""")
    ]

    risks = registry.evaluate_package(
        manifest=manifest,
        source_files=source_files,
        dependencies=[],
        domain=EthicalDomain.HEALTHCARE,
    )

    # Verificar que riscos de privacidade foram detectados
    assert "privacy_violation" in risks
    assert risks["privacy_violation"] >= 0.5  # PHI sem criptografia + logging

    # Verificar recomendações
    recommendations = registry.get_recommendations(EthicalDomain.HEALTHCARE, risks)
    assert any("criptografia" in rec.lower() or "encrypt" in rec.lower() for rec in recommendations)

async def test_mythos_with_domain_plugins(mock_ledger):
    """Testa Mythos Gate integrado com plugins de domínio."""
    base_assessor = EthicalRiskAssessor()
    registry = DomainRuleRegistry(plugin_dir=Path("/tmp"))
    # Registrar plugin de saúde (simulado)
    registry._loaded_plugins["healthcare-hipaa-v1"] = HealthcareEthicalPlugin()
    registry._plugin_metadata["healthcare-hipaa-v1"] = type('obj', (object,), {
        "plugin_id": "healthcare-hipaa-v1", "domain": EthicalDomain.HEALTHCARE,
        "version": "1.0.0", "author": "test", "description": "test",
        "checksum": "mock", "required_permissions": [], "compatible_versions": ["5.0.0"],
    })()
    registry._domain_plugins[EthicalDomain.HEALTHCARE] = ["healthcare-hipaa-v1"]

    mythos = MythosGateWithPlugins(base_assessor, registry)

    # Avaliar pacote de saúde com dados sensíveis
    manifest = {
        "package": {"name": "health-ai", "version": "1.0.0",
                    "description": "AI for healthcare", "license": "MIT"},
        "dependencies": {},
    }
    source_files = [("ai.py", "def diagnose(phi_data): return ml.predict(phi_data['race'])")]

    assessment = mythos.assess_package_with_domain_rules(
        manifest=manifest,
        source_files=source_files,
        dependencies=[],
        domain=EthicalDomain.HEALTHCARE,
    )

    # Verificar que risco de domínio aumentou score geral
    assert assessment.overall_risk_score >= 0.4  # Risco de viés + privacidade
    assert assessment.decision in [PublicationDecision.REQUIRES_REVIEW, PublicationDecision.REJECTED]
    assert any("fairness" in rec.lower() or "bias" in rec.lower()
               for rec in assessment.recommendations)

async def test_full_workflow_auth_collab_plugins(
    mock_qip_engine, mock_temporal_client, mock_ledger, temp_plugin_dir
):
    """Teste completo: auth → collaborative review → domain plugins."""
    # 1. Setup auth
    verifier = IdentityVerifier("client", "secret", "https://test/callback")
    auth_manager = ReviewerAuthManager(verifier, "jwt-secret", mock_temporal_client, mock_qip_engine)

    # 2. Setup collaborative review
    consensus_engine = ConsensusReviewEngine(mock_qip_engine, mock_temporal_client, mock_ledger)
    workflow = CollaborativeReviewWorkflow(consensus_engine)

    # 3. Setup ethical plugins
    registry = DomainRuleRegistry(plugin_dir=temp_plugin_dir)
    registry._loaded_plugins["healthcare-hipaa-v1"] = HealthcareEthicalPlugin()
    registry._plugin_metadata["healthcare-hipaa-v1"] = type('obj', (object,), {
        "plugin_id": "healthcare-hipaa-v1", "domain": EthicalDomain.HEALTHCARE,
        "version": "1.0.0", "author": "test", "description": "test",
        "checksum": "mock", "required_permissions": [], "compatible_versions": ["5.0.0"],
    })()
    registry._domain_plugins[EthicalDomain.HEALTHCARE] = ["healthcare-hipaa-v1"]

    mythos = MythosGateWithPlugins(EthicalRiskAssessor(), registry)

    # 4. Simular login de 3 revisores
    reviewers = []
    for i in range(3):
        session = auth_manager.login_with_orcid(f"mock-token-{i}")
        assert session
        reviewers.append(session.reviewer_id)

    # 5. Iniciar revisão colaborativa para pacote de saúde
    available_reviewers = [
        {"reviewer_id": rid, "expertise": ["healthcare", "ai"], "reputation": 0.9, "active_tasks": 1}
        for rid in reviewers
    ]

    task = await workflow.initiate_collaborative_review(
        package_name="patient-ai",
        package_version="1.0.0",
        author_orcid="ORCID:AUTHOR",
        risk_score=0.55,
        risk_breakdown={"privacy_violation": 0.4, "algorithmic_bias": 0.3},
        conrag_report={"overall": 0.72},
        source_files=[("ai.py", "def diagnose(phi): return ml.predict(phi['race'])")],
        dependencies=[],
        available_reviewers=available_reviewers,
    )

    # 6. Revisores submetem votos
    votes = [
        (reviewers[0], ReviewVote.APPROVE, "Approved", [], 0.9),
        (reviewers[1], ReviewVote.REQUEST_CHANGES, "Needs privacy fixes", ["Add encryption"], 0.8),
        (reviewers[2], ReviewVote.APPROVE, "Good work", [], 0.85),
    ]

    for reviewer_id, vote, rationale, changes, confidence in votes:
        result = await consensus_engine.submit_vote(
            task_id=task.task_id,
            reviewer_id=reviewer_id,
            vote=vote,
            rationale=rationale,
            suggested_changes=changes,
            confidence=confidence,
        )
        assert result["success"]

    # 7. Processar decisão final
    decision_result = await workflow.process_collaborative_decision(task)
    assert decision_result["decision"] in [PublicationDecision.APPROVED.value, PublicationDecision.REQUIRES_REVIEW.value]
    assert "audit_seal" in decision_result

    # 8. Verificar auditoria no ledger
    assert len(mock_ledger.records) >= 2  # Criação da tarefa + consenso

    print(f"✅ Full workflow passed: decision={decision_result['decision']}, seal={decision_result['audit_seal'][:16]}")

# ============================================================================
# EXECUÇÃO DOS TESTES
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
