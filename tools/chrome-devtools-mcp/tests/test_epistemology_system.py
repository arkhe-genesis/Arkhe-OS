import pytest
import json
from src.cathedral.epistemology.psa import PSA, SemanticGraph, Claim, Edge, DiamondPipeline
from src.cathedral.epistemology.enrichment import FeatureEnricher
from src.cathedral.epistemology.pefm import PEFM

def test_psa_determinism():
    psa = PSA()
    claims = [Claim("Test 1", 0), Claim("Test 2", 1)]
    edges = [Edge(0, 1, "entails")]
    G = SemanticGraph(claims, edges)

    res1 = psa.calculate_score(G)
    res2 = psa.calculate_score(G)

    assert res1["score"] == res2["score"]
    assert res1["hash"] == res2["hash"]

def test_psa_invariants():
    psa = PSA()

    # I6: Epistemic Relevance
    G_gen = SemanticGraph([Claim("A", 0)], [], domain="general")
    G_gov = SemanticGraph([Claim("A", 0)], [], domain="governance")

    res_gen = psa.calculate_score(G_gen)
    res_gov = psa.calculate_score(G_gov)

    assert res_gov["score"] > res_gen["score"] # Due to delta*E

def test_pefm_risk_response():
    psa = PSA()
    pefm = PEFM()
    enricher = FeatureEnricher(psa)

    # Coherent graph
    G_good = SemanticGraph([Claim("A", 0), Claim("B", 1)], [Edge(0, 1, "entails")], domain="general")
    f_good = enricher.enrich("art1", G_good, 123)
    p_good = pefm.predict_failure_probability(f_good)

    # Incoherent graph (contradiction)
    G_bad = SemanticGraph([Claim("A", 0), Claim("B", 1)], [Edge(0, 1, "contradicts")], domain="governance")
    f_bad = enricher.enrich("art2", G_bad, 124)
    p_bad = pefm.predict_failure_probability(f_bad)

    assert p_bad > p_good

def test_psa_hash_canonical():
    psa = PSA()
    c1, c2 = Claim("A", 0), Claim("B", 1)
    e = Edge(0, 1, "entails")

    # Order should not matter for the hash if sorted internally
    G1 = SemanticGraph([c1, c2], [e])
    G2 = SemanticGraph([c2, c1], [e])

    assert psa.generate_hash(G1) == psa.generate_hash(G2)

def test_diamond_pipeline_logic():
    psa = PSA()
    pipeline = DiamondPipeline(psa)

    prompt = "The Arkhe is awake. The Cathedral is coherent."
    res = pipeline.run(prompt, iterations=2)

    assert "best" in res
    assert len(res["all_evaluated"]) == 2
    assert res["best"]["score"] > 0
