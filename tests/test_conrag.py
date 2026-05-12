import pytest
from conrag.domains.registry import DomainRegistry, Domain
from conrag.domains.education_hypergraph import EducationHypergraph
from conrag.domains.journalism_rules import JournalismBEAVERRules
from conrag.core.cross_domain import CrossDomainReasoner
from conrag.galactic.consensus import GalacticDomainConsensus
from fastapi import APIRouter

def test_registry():
    r = DomainRegistry()
    assert len(r.list_domains()) >= 10

def test_education_hypergraph():
    eh = EducationHypergraph()
    assert len(eh.query('blooms_taxonomy')) > 0

def test_journalism_rules():
    jr = JournalismBEAVERRules()
    assert not jr._check_misinformation('pizzagate', {})[0]

def test_cross_domain_reasoner():
    r = CrossDomainReasoner(DomainRegistry())
    inf = r.infer_cross_domain('ethics', ['programming', 'philosophy'])
    assert inf is not None
    assert inf.confidence > 0

def test_galactic_consensus():
    gc = GalacticDomainConsensus(None, None)
    gc.register_stellar_node('n1', 'b1', 1.0, 'direct')
    assert 'n1' in gc.stellar_nodes
