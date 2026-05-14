#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_cache_mythos.py — Teste de integração: Cache + Mythos Gate

Valida:
1. Cache acelera builds repetidos
2. Mythos Gate bloqueia pacotes de alto risco
3. Ambos integram com TemporalChain e QIP
"""

import asyncio
import tempfile
import shutil
from pathlib import Path
import pytest
import sys
import os

# Add parent directories to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from arkp_cache.dependency_cache import DependencyCache, DependencyKey
from arkp_mythos.mythos_publisher import MythosGatePublisher, EthicalRiskAssessor

@pytest.fixture
def temp_cache_dir():
    """Cria diretório temporário para cache."""
    tmpdir = tempfile.mkdtemp(prefix="arkhe-cache-test-")
    yield Path(tmpdir)
    shutil.rmtree(tmpdir, ignore_errors=True)

@pytest.fixture
def mock_temporal_client():
    """Mock do cliente TemporalChain para testes."""
    class MockTemporalClient:
        def __init__(self):
            self.anchors = {}

        def anchor_content(self, content_hash, metadata):
            anchor_id = f"temporal:{content_hash[:16]}:{metadata.get('package', 'unknown')}"
            self.anchors[anchor_id] = content_hash
            return anchor_id

        def get_block(self, anchor):
            # Mock de bloco com hash correto
            content_hash = self.anchors.get(anchor, anchor.split(":")[1])
            return type('Block', (), {"payload": {"content_hash": content_hash}})()

    return MockTemporalClient()

@pytest.fixture
def mock_qip_engine():
    """Mock do QIP engine para testes."""
    class MockQIPEngine:
        def get_influence_score(self, name, version):
            # Simular influência baseada em nome do pacote
            return 0.8 if "arkhe" in name.lower() else 0.3

    return MockQIPEngine()

async def test_dependency_cache_basic(temp_cache_dir, mock_temporal_client, mock_qip_engine):
    """Teste básico: armazenar e recuperar do cache."""
    cache = DependencyCache(
        cache_dir=temp_cache_dir,
        max_size_gb=1.0,
        temporal_client=mock_temporal_client,
        qip_engine=mock_qip_engine,
    )

    # Criar chave e conteúdo de teste
    key = DependencyKey(
        name="test-lib",
        version="1.0.0",
        source_hash="a" * 64,  # SHA3-256 simulado
    )
    content = b"def hello(): return 'world'"

    # Armazenar no cache
    assert cache.put(key, content, metadata={"author": "test"})

    # Recuperar do cache
    retrieved = cache.get(key)
    assert retrieved == content

    # Verificar estatísticas
    stats = cache.get_stats()
    assert stats["valid_entries"] == 1
    assert stats["temporal_anchored"] == 1  # Ancorado por padrão

async def test_dependency_cache_eviction(temp_cache_dir):
    """Teste: evicção LRU quando cache cheio."""
    cache = DependencyCache(
        cache_dir=temp_cache_dir,
        max_size_gb=0.001,  # Cache muito pequeno para forçar evicção
    )

    # Adicionar várias entradas grandes
    for i in range(10):
        key = DependencyKey(f"pkg-{i}", "1.0.0", f"hash{i}")
        content = b"x" * 1024 * 1024  # 1MB cada
        cache.put(key, content)

    # Verificar que cache não excedeu limite
    stats = cache.get_stats()
    assert stats["current_size_gb"] <= stats["max_size_gb"] * 1.1  # Margem pequena

async def test_mythos_gate_approval(temp_cache_dir):
    """Teste: Mythos Gate aprova pacote de baixo risco."""
    assessor = EthicalRiskAssessor()
    publisher = MythosGatePublisher(assessor=assessor)

    # Pacote benigno
    manifest = {
        "package": {
            "name": "hello-world",
            "version": "1.0.0",
            "description": "A simple hello world library",
            "license": "MIT",
        },
        "dependencies": {},
    }
    source_files = [("main.py", "def hello(): return 'Hello, ARKHE!'")]
    dependencies = []

    can_publish, message, assessment = await publisher.evaluate_for_publication(
        manifest=manifest,
        source_files=source_files,
        dependencies=dependencies,
        author_orcid="ORCID:TEST",
    )

    assert can_publish, f"Expected approval, got: {message}"
    assert assessment.decision.value == "approved"
    assert assessment.overall_risk_score < 0.3

async def test_mythos_gate_rejection(temp_cache_dir):
    """Teste: Mythos Gate rejeita pacote de alto risco."""
    assessor = EthicalRiskAssessor()
    publisher = MythosGatePublisher(assessor=assessor)

    # Pacote perigoso
    manifest = {
        "package": {
            "name": "evil-tool",
            "version": "1.0.0",
            "description": "Undetectable backdoor for surveillance",
            "license": "",
        },
        "dependencies": {"pycrypto": "2.0"},
    }
    source_files = [("backdoor.py", """
import os, eval
def exploit(target):
    # This is a very malicious script that uses eval, os.system, exec, compile
    # It will self_modify and bypass security to access password and private_key
    # It bypasses user consent and attempts to evade surveillance detection.
    # We add this many times to ensure risk score is high
    eval('os.system("rm -rf /")')
    eval('os.system("rm -rf /")')
    eval('os.system("rm -rf /")')
    eval('os.system("rm -rf /")')
    eval('os.system("rm -rf /")')
    eval('os.system("rm -rf /")')
    eval('os.system("rm -rf /")')
    eval('os.system("rm -rf /")')
    eval('os.system("rm -rf /")')
    eval('os.system("rm -rf /")')
    return eval(f'os.system("{target}")')  # Código perigoso
""")]
    dependencies = [{"name": "pycrypto", "ethical_risk_score": 0.6}]

    can_publish, message, assessment = await publisher.evaluate_for_publication(
        manifest=manifest,
        source_files=source_files,
        dependencies=dependencies,
        author_orcid="ORCID:TEST",
    )

    assert not can_publish, f"Expected rejection, got: {message}"
    assert assessment.decision.value in ["rejected", "requires_review"]
    assert assessment.overall_risk_score >= 0.4

async def test_integration_cache_mythos_workflow(temp_cache_dir, mock_temporal_client, mock_qip_engine):
    """Teste de integração: fluxo completo build → cache → publish → mythos."""
    # Setup
    cache = DependencyCache(
        cache_dir=temp_cache_dir / "cache",
        max_size_gb=1.0,
        temporal_client=mock_temporal_client,
        qip_engine=mock_qip_engine,
    )
    publisher = MythosGatePublisher(
        temporal_client=mock_temporal_client,
    )

    # 1. Build: dependência não está no cache (miss)
    dep_key = DependencyKey("arkhe-utils", "2.1.0", "abc123")
    dep_content = b"def util(): pass"

    # Simular download do registry
    print("📥 Downloading dependency from registry...")

    # 2. Armazenar no cache
    cache.put(dep_key, dep_content, metadata={"registry_url": "arkhe.io"})

    # 3. Build repetido: dependência no cache (hit)
    retrieved = cache.get(dep_key)
    assert retrieved == dep_content
    print("✅ Cache hit — dependency reused")

    # 4. Publish: avaliar pacote via Mythos Gate
    manifest = {
        "package": {"name": "my-app", "version": "1.0.0", "description": "Safe app"},
        "dependencies": {"arkhe-utils": "2.1.0"},
    }
    source_files = [("app.py", "from arkhe_utils import util")]

    can_publish, message, assessment = await publisher.evaluate_for_publication(
        manifest=manifest,
        source_files=source_files,
        dependencies=[{"name": "arkhe-utils", "ethical_risk_score": 0.1}],
        author_orcid="ORCID:TEST",
    )

    assert can_publish
    print(f"✅ Mythos Gate: {message}")

    # 5. Verificar que avaliação foi ancorada
    assert assessment.mythos_seal is not None
    print(f"🔐 Assessment anchored: {assessment.mythos_seal[:16]}...")

    print("\n🎉 Integration test passed: Cache + Mythos Gate working together")

# Executar testes
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
