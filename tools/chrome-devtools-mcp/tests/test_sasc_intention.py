import pytest
import numpy as np
from src.physics.sasc_em_engine import SASCEMEngine
from src.physics.sasc_intention_resolver import IntentionResolver

def test_intention_resolution():
    engine = SASCEMEngine()
    resolver = IntentionResolver(engine.fascia)
    res = resolver.resolve_gesture([32, 32])
    assert res["lambda2"] > 0
    assert res["status"] in ["COHERENT", "DISSONANT"]
    assert len(res["target"]) == 2
