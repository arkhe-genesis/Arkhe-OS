import pytest
import numpy as np
from src.physics.sasc_nanobot_engine import NanoBotSwarm, DNAOrigamiCompiler

def test_dna_compiler():
    compiler = DNAOrigamiCompiler()
    res = compiler.compile_structure("CAGE")
    assert res["sequence"].startswith("ATGC")
    assert res["stability_score"] > 0.9

def test_nanobot_swarm_triggers():
    swarm = NanoBotSwarm(count=100)
    # Endogenous trigger: acidic pH
    activated = swarm.check_endogenous_triggers(local_ph=6.0, presence_markers=[])
    assert activated == 100
    assert swarm.status()["active"] == 100

    # Exogenous trigger: NIR light
    swarm.apply_exogenous_trigger("NIR", intensity=0.9)
    assert swarm.status()["deployed"] == 100

def test_nanobot_status():
    swarm = NanoBotSwarm(count=10)
    status = swarm.status()
    assert status["total_bots"] == 10
    assert status["latent"] == 10
