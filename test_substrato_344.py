import math
import sys
import os
sys.path.insert(0, os.path.abspath('substrates/300-399_foundations'))
import importlib
substrato_344 = importlib.import_module("substrato_344.substrato_344_time_weaver")

def test_invariants():
    validator = substrato_344.ArkheInvariantsValidator()
    assert not validator.validate(0.469624)
    assert validator.validate(0.6)
    assert not validator.validate(1.0)
    assert validator.validate(math.sqrt(3)/3)
    assert validator.validate(0.9999)

def test_time_weaver_v1():
    weaver = substrato_344.TimeWeaverV1(substrato_344.gates_7)
    res = weaver.process(substrato_344.payloads_7)
    assert isinstance(res, float)
    assert res > 0

def test_time_weaver_v2():
    weaver = substrato_344.TimeWeaverV2(substrato_344.gates_7)
    res = weaver.process(substrato_344.payloads_7)
    assert isinstance(res, float)
    assert res > 0

def test_time_weaver_v3():
    weaver = substrato_344.TimeWeaverV3(substrato_344.gates_7)
    res = weaver.process(substrato_344.payloads_7)
    assert isinstance(res, float)
    assert res > 0

def test_time_weaver_v4():
    weaver = substrato_344.TimeWeaverV4(substrato_344.gates_7)
    res = weaver.process(substrato_344.payloads_7)
    assert isinstance(res, float)
    assert res > 0
