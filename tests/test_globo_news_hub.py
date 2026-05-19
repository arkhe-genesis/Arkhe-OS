import pytest
import time
import sys
import os
import importlib.util

# Dynamically import due to python syntax rules regarding modules starting with numbers
spec = importlib.util.spec_from_file_location('globo_news_hub', 'src/25_external_validation/252_globo_news_hub/globo_news_hub.py')
globo_news_hub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(globo_news_hub)
GloboNewsHub = globo_news_hub.GloboNewsHub

def test_submit_valid_article():
    hub = GloboNewsHub()
    sources = [
        {"name": "Source1", "hash": "h1", "timestamp": time.time()},
        {"name": "Source2", "hash": "h2", "timestamp": time.time()},
        {"name": "Source3", "hash": "h3", "timestamp": time.time()}
    ]
    article = hub.submit_article("Reporter", "Title", "Body text here", sources, "politics", "arc1")
    assert article["constitutional"] is True
    assert article["phi_c"] == 0.9999
    assert len(hub.temporal_chain) == 1
    assert hub.get_novela_arc("arc1") == [article]

def test_missing_hash_violation():
    hub = GloboNewsHub()
    sources = [{"name": "Source1", "timestamp": time.time()}]
    with pytest.raises(ValueError, match="P1 Violation"):
         hub.submit_article("Reporter", "Title", "Body", sources, "politics")

def test_violations():
    hub = GloboNewsHub()
    sources = [
        {"name": "Source1", "hash": "h1", "timestamp": time.time()}
    ]
    # Body contains P8, P9, and P10 violations
    body = "Todo mundo sabe que isso comprova que há uma democracia relativa. A realidade é uma ilusão, mas observe os fatos."
    article = hub.submit_article("Reporter", "Title", body, sources, "politics")
    assert article["violations"]["p8"] == 3 # 'todo mundo sabe', 'comprova que', 'prova que' (in comprova que)
    assert article["violations"]["p9"] == 1 # 'democracia relativa'
    assert article["violations"]["p10"] == 1 # 'a realidade é uma ilusão...'
    # Base = 1/3 (0.333)
    # Penalty = 0.2*3 + 0.15*1 + 0.1*1 = 0.6 + 0.15 + 0.1 = 0.85
    # phi_c = max(0, 0.333 - 0.85) = 0.0
    assert article["phi_c"] == 0.0
    assert article["constitutional"] is False

def test_broadcast():
    hub = GloboNewsHub()
    sources = [{"name": "Source1", "hash": "h1", "timestamp": time.time()}]
    article = hub.submit_article("Reporter", "Title", "Body", sources, "politics")
    # Shouldn't raise error
    hub.broadcast_international(article["id"], ["pt", "en"])

def test_broadcast_invalid_article():
    hub = GloboNewsHub()
    with pytest.raises(ValueError, match="Artigo não encontrado"):
        hub.broadcast_international("invalid_id")
