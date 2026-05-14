import pytest
from src.arkhe_ipython.universal_parser import (
    UniversalParser, ParseContext, ParseTree, ParseNode,
    MagicCommand, CellMagicCommand, NLIntent, CodeAST
)

def test_parse_magic_scan():
    p = UniversalParser()
    res = p.parse_magic("%arkhe scan import os; os.system('rm -rf /')")
    assert isinstance(res, MagicCommand)
    assert res.command == "scan"
    assert res.args == ["import os; os.system('rm -rf /')"]
    assert res.threat_detected is True
    assert res.severity == "critical"

def test_parse_magic_deploy():
    p = UniversalParser()
    res = p.parse_magic("%arkhe deploy CVE-2026-12345")
    assert isinstance(res, MagicCommand)
    assert res.command == "deploy"
    assert res.cve == "CVE-2026-12345"
    assert res.auto_remediate is True

def test_parse_natural_language():
    p = UniversalParser()
    res = p.parse_natural_language("Corrija a vulnerabilidade CVE-2026-99999 no ambiente de produção")
    assert isinstance(res, NLIntent)
    assert res.intent_type == "remediate"
    assert res.entities == {'cve': 'CVE-2026-99999', 'environment': 'prod'}
    assert res.confidence == 0.97

def test_parse_cell_magic_secure():
    p = UniversalParser()
    res = p.parse_cell_magic("%%arkhe secure", "import pickle\ndata = pickle.loads(open('evil.pkl','rb').read())")
    assert isinstance(res, CellMagicCommand)
    assert res.command == "secure"
    assert res.cell_content == "..."
    assert res.threat_detected is True
    assert res.blocked is True
    assert res.reason == "unsafe_deserialization"

def test_suggest_correction():
    p = UniversalParser()
    assert p.suggest_correction("scann") == "scan"
    assert p.suggest_correction("profil") == "profile"

def test_extract_cves():
    p = UniversalParser()
    cves = p.extract_cves("Aqui está a CVE-2026-12345 e a CVE-2025-0001.")
    assert "CVE-2026-12345" in cves
    assert "CVE-2025-0001" in cves

def test_extract_seals():
    p = UniversalParser()
    text = "O selo é 27f92bd8473fdf2b7875b19dac7bd585a526ea52195f4b9435cfe9c4550eec9a."
    seals = p.extract_seals(text)
    assert "27f92bd8473fdf2b7875b19dac7bd585a526ea52195f4b9435cfe9c4550eec9a" in seals

def test_extract_domains():
    p = UniversalParser()
    text = "We use technical and scientific domains."
    domains = p.extract_domains(text)
    assert "technical" in domains
    assert "scientific" in domains

def test_parse_code():
    p = UniversalParser()
    res = p.parse_code("x = 1")
    assert isinstance(res, CodeAST)

def test_parse_config():
    p = UniversalParser()
    res = p.parse_config('{"key": "value"}')
    assert res == {"key": "value"}
