#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_unified_9013_9014.py — Teste unificado: Multi-No + Agente Autonomo
"""

import asyncio
import time
import pytest
from unittest.mock import MagicMock

from arkp_multi_node.src.multi_node import WheelerMeshNetwork, WheelerMeshNode, NodeStatus, MultiNodeDeployer, SyncPriority
from arkp_synthetic_agent.src.synthetic_reviewer import SyntheticReviewerAgent, AgentOrchestrator, ReviewExperience, AgentState


@pytest.fixture
def mock_qip():
    m = MagicMock()
    m.record_contribution = MagicMock()
    return m


async def test_wheeler_mesh_node_registration():
    """Testa registro de nos na rede mesh."""
    network = WheelerMeshNetwork("seed-01", "10.0.0.1", 8443, "us-east-1")

    node1 = WheelerMeshNode("node-01", "10.0.0.2", 8443, "us-east-1", NodeStatus.ONLINE, time.time(), 0.9, ["review", "sync"])
    node2 = WheelerMeshNode("node-02", "10.0.0.3", 8443, "eu-west-1", NodeStatus.ONLINE, time.time(), 0.85, ["review", "sync", "bridge"])

    assert network.register_node(node1) is True
    assert network.register_node(node2) is True
    assert network.register_node(node1) is False  # Duplicado

    assert len(network.nodes) == 2  # 2 nos registrados
    assert "node-02" in node1.peers
    assert "node-01" in node2.peers


async def test_qhttp_message_creation():
    """Testa criacao e assinatura de mensagem qhttp://."""
    network = WheelerMeshNetwork("seed-01", "10.0.0.1", 8443, "us-east-1")

    msg = network.create_message("node-01", {"type": "test", "data": "hello"}, SyncPriority.HIGH)
    assert msg.message_id is not None
    assert msg.sender == "seed-01"
    assert msg.recipient == "node-01"
    assert msg.signature is not None
    assert len(msg.signature) == 64  # sha3-256 hex
    assert msg in network.messages.values()


async def test_crdt_sync():
    """Testa sincronizacao CRDT entre nos."""
    network = WheelerMeshNetwork("seed-01", "10.0.0.1", 8443, "us-east-1")

    # Registrar nos para permitir broadcast
    node1 = WheelerMeshNode("node-01", "10.0.0.2", 8443, "us-east-1", NodeStatus.ONLINE, time.time(), 0.9, ["review"])
    network.register_node(node1)

    result = await network.sync_crdt("test_key", {"a": {"_version": 1, "value": 100}})
    assert "a" in result
    assert result["a"]["_version"] == 1
    assert "test_key" in network.crdt_state


async def test_merkle_root_computation():
    """Testa computacao de Merkle root."""
    network = WheelerMeshNetwork("seed-01", "10.0.0.1", 8443, "us-east-1")

    empty_root = network.compute_merkle_root([])
    assert len(empty_root) == 64

    data = [{"a": 1}, {"b": 2}]
    root1 = network.compute_merkle_root(data)
    root2 = network.compute_merkle_root(data)
    assert root1 == root2  # Deterministico

    data2 = [{"a": 1}, {"b": 3}]
    root3 = network.compute_merkle_root(data2)
    assert root1 != root3  # Diferente conteudo = diferente root


async def test_gossip_protocol():
    """Testa protocolo gossip."""
    network = WheelerMeshNetwork("seed-01", "10.0.0.1", 8443, "us-east-1")

    # Sem peers online
    result = await network.gossip_protocol()
    assert result["gossiped"] == 0

    # Com peers online
    for i in range(5):
        node = WheelerMeshNode(f"node-{i}", f"10.0.0.{i+2}", 8443, "us-east-1", NodeStatus.ONLINE, time.time(), 0.9, ["review"])
        network.register_node(node)

    result = await network.gossip_protocol()
    assert result["gossiped"] > 0
    assert len(result["targets"]) <= 3  # Fanout limit


async def test_multi_node_deploy():
    """Testa deploy de cluster multi-no."""
    deployer = MultiNodeDeployer()
    result = await deployer.deploy_arkhe_cluster("test-cluster")

    assert result["deployment_id"] == "test-cluster"
    assert result["nodes_deployed"] == 5
    assert result["network_status"]["total_nodes"] == 5
    assert result["network_status"]["online_nodes"] == 5
    assert "sa-east-1" in result["network_status"]["regions"]
    assert "ap-northeast-1" in result["network_status"]["regions"]
    assert result["gossip_round"]["gossiped"] > 0
    assert len(result["merkle_root"]) == 64


async def test_synthetic_agent_analysis(mock_qip):
    """Testa analise automatica de pacote pelo agente."""
    agent = SyntheticReviewerAgent("agent-001", mock_qip, ["healthcare", "ai"])

    manifest = {"package": {"name": "test-ai", "version": "1.0.0"}}
    source_files = [("diagnoser.py", "def diagnose(patient_data): return ml.predict(patient_data)")]
    dependencies = []

    result = await agent.analyze_package(manifest, source_files, dependencies, "healthcare")

    assert "vote" in result
    assert result["vote"] in ["approve", "reject", "request_changes"]
    assert 0.0 <= result["confidence"] <= 1.0
    assert "features" in result
    assert result["features"]["total_files"] == 1
    assert result["domain"] == "healthcare"
    assert result["agent_id"] == "agent-001"


async def test_synthetic_agent_learning(mock_qip):
    """Testa aprendizado por reforco do agente."""
    agent = SyntheticReviewerAgent("agent-002", mock_qip, ["healthcare"])

    # Experiencia correta
    exp_correct = ReviewExperience(
        task_id="task-001", package_name="health-ai", domain="healthcare",
        risk_score=0.5, vote="approve", final_decision="approve",
        was_correct=True, confidence=0.8, rationale="Good package", timestamp=time.time(),
    )
    result = await agent.learn_from_feedback(exp_correct)
    assert result["was_correct"] is True
    assert result["new_confidence"] > 0.7  # Aumentou
    assert result["total_experiences"] == 1

    # Experiencia incorreta
    exp_wrong = ReviewExperience(
        task_id="task-002", package_name="bad-ai", domain="healthcare",
        risk_score=0.8, vote="approve", final_decision="reject",
        was_correct=False, confidence=0.9, rationale="Missed privacy issue", timestamp=time.time(),
    )
    result2 = await agent.learn_from_feedback(exp_wrong)
    assert result2["was_correct"] is False
    assert result2["new_confidence"] < result["new_confidence"]  # Diminuiu
    assert agent.memory.error_patterns["healthcare"] == 1


async def test_synthetic_agent_meta_cognition(mock_qip):
    """Testa meta-cognicao: agente pede revisao humana quando incerto."""
    agent = SyntheticReviewerAgent("agent-003", mock_qip, ["healthcare"])

    # Forcar baixa confianca
    agent._confidence_model["healthcare"] = 0.3

    manifest = {"package": {"name": "uncertain", "version": "1.0.0"}}
    source_files = [("complex.py", "x" * 5000)]  # Codigo grande = risco alto

    result = await agent.analyze_package(manifest, source_files, [], "healthcare")
    assert result["vote"] == "request_changes"  # Meta-cognicao: pedir ajuda


async def test_synthetic_agent_sleep_cycle(mock_qip):
    """Testa ciclo de sono e consolidacao."""
    agent = SyntheticReviewerAgent("agent-004", mock_qip, ["healthcare", "finance"])

    # Popular memoria
    for i in range(60):
        agent.memory.domain_patterns["healthcare"].append({"keyword": f"pattern-{i}", "risk_weight": 0.1, "timestamp": time.time()})

    result = await agent.sleep_cycle(duration_seconds=0.1)

    assert result["consolidated_patterns"] <= 30  # Limitado apos consolidacao
    assert agent.state == AgentState.IDLE


async def test_agent_orchestrator(mock_qip):
    """Testa orquestrador de multiplos agentes."""
    orch = AgentOrchestrator(mock_qip)

    # Criar especialistas
    agent1 = orch.create_agent("health-expert", ["healthcare"])
    agent2 = orch.create_agent("finance-expert", ["finance"])

    assert len(orch.agents) == 2

    # Atribuir tarefa por dominio
    result = await orch.assign_task("task-001", {"package": {"name": "med-ai"}}, [], [], "healthcare")
    assert result["agent_id"] == "health-expert"
    assert result["assignment_confidence"] == 0.7

    # Atribuir tarefa sem especialista (cria generico)
    result2 = await orch.assign_task("task-002", {"package": {"name": "edu-ai"}}, [], [], "education")
    assert "generic" in result2["agent_id"]

    # Status do orquestrador
    status = orch.get_orchestrator_status()
    assert status["total_agents"] == 3
    assert status["active_tasks"] == 2


async def test_full_unified_9013_9014(mock_qip):
    """Teste unificado: Multi-No + Agente Autonomo."""
    # 1. Deploy cluster multi-no
    deployer = MultiNodeDeployer()
    cluster = await deployer.deploy_arkhe_cluster("unified-cluster")
    assert cluster["nodes_deployed"] == 5

    # 2. Criar orquestrador de agentes
    orch = AgentOrchestrator(mock_qip)
    health_agent = orch.create_agent("health-bot", ["healthcare"])
    finance_agent = orch.create_agent("finance-bot", ["finance"])

    # 3. Simular revisao distribuida
    tasks = [
        ("task-h1", "healthcare", [("diagnoser.py", "def diag(p): return ml.predict(p['race'])")]),
        ("task-f1", "finance", [("trader.py", "def trade(amount): return api.buy(amount * 2)")]),
        ("task-h2", "healthcare", [("analyzer.py", "# Safe healthcare code\npass")]),
    ]

    reviews = []
    for task_id, domain, files in tasks:
        assignment = await orch.assign_task(task_id, {"package": {"name": task_id}}, files, [], domain)
        agent = orch.agents[assignment["agent_id"]]
        analysis = await agent.analyze_package({"package": {"name": task_id}}, files, [], domain)
        reviews.append({"task": task_id, "agent": agent.agent_id, "vote": analysis["vote"], "confidence": analysis["confidence"]})

    # 4. Simular feedback e aprendizado
    for review in reviews:
        exp = ReviewExperience(
            task_id=review["task"], package_name=review["task"], domain="healthcare" if "h" in review["task"] else "finance",
            risk_score=0.5, vote=review["vote"], final_decision="approve", was_correct=True,
            confidence=review["confidence"], rationale="Auto-review", timestamp=time.time(),
        )
        agent = orch.agents[review["agent"]]
        await agent.learn_from_feedback(exp)

    # 5. Sync estado via CRDT
    network = deployer.networks["unified-cluster"]
    await network.sync_crdt("agent_reviews", {r["task"]: {"_version": 1, "vote": r["vote"]} for r in reviews})

    # 6. Verificar integridade
    merkle = network.compute_merkle_root(list(network.crdt_state.values()))
    assert len(merkle) == 64

    # 7. Ciclo de sono dos agentes
    for agent in orch.agents.values():
        await agent.sleep_cycle(duration_seconds=0.05)

    print(f"✅ Unified 9013-9014 passed: {cluster['nodes_deployed']} nodes, {len(orch.agents)} agents, {len(reviews)} reviews, merkle={merkle[:16]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])