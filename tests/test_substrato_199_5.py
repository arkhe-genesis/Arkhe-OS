import pytest
import asyncio
import numpy as np
from collections import deque

from refinements.security_production_refinements import EpsilonValidator
from refinements.regulatory_compliance_refinements import RegulatoryFramework, RegulatoryTemplateGenerator
from refinements.llm_ops_production_refinements import SemanticCache
from refinements.zero_day_detection_refinements import ShapExplainer
from refinements.autonomous_orchestration_refinements import ConsensusPolicyEngine, SentinelAgent
from refinements.global_federation_refinements import CrossBorderPrivacy
from refinements.observability_refinements import DistributedTracing

class MockModel:
    async def embed(self, text):
        return np.array([1.0, 0.0]) # Dummy embedding

@pytest.mark.asyncio
async def test_epsilon_validator():
    val, reason, sug = EpsilonValidator.validate(1.0, 0.9, 5)
    assert not val
    assert sug >= 2.0

@pytest.mark.asyncio
async def test_regulatory_templates():
    tpl = RegulatoryTemplateGenerator.generate_template(RegulatoryFramework.LGPD, "breach")
    assert tpl["framework"] == "lgpd"
    assert "encarregado" in tpl["content"]

@pytest.mark.asyncio
async def test_semantic_cache():
    cache = SemanticCache(embedding_model=MockModel())
    await cache.store("test", {"resp": "ok"})
    hit = await cache.lookup("test")
    assert hit is not None
    assert hit["resp"] == "ok"

@pytest.mark.asyncio
async def test_shap_explainer():
    shap = ShapExplainer()
    res = await shap.explain_alert(np.array([1, 2]), ["A", "B"])
    assert "explanation" in res
    assert len(res["contributions"]) == 2

@pytest.mark.asyncio
async def test_consensus_engine():
    engine = ConsensusPolicyEngine()
    engine.register_agent(SentinelAgent("a", "role", 1.0))
    engine.register_agent(SentinelAgent("b", "role", 1.0))
    # Unanimous but weighted phi
    assert engine.reach_decision({}, {"a": True, "b": True})

@pytest.mark.asyncio
async def test_cross_border_privacy():
    eps = CrossBorderPrivacy.adjust_for_jurisdiction(4.0, ["BR_LGPD", "EU_GDPR"])
    assert eps <= 4.0

@pytest.mark.asyncio
async def test_tracing():
    trace = DistributedTracing()
    span = trace.start_span("req1", "op1")
    trace.end_span(span)
    assert "duration_ms" in trace.traces[span]
