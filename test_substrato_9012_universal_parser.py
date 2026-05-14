import pytest
import sys
import os
import ast

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'substrates', '9012_arkhe_ipython')))

from arkhe_ipython.universal_parser import UniversalParser, ParseContext

def test_magic_line_with_code():
    parser = UniversalParser()
    tree = parser.parse("%arkhe scan import os; os.system('ls')")
    assert not tree.errors
    assert tree.root.node_type == 'magic_command'
    assert tree.root.confidence == 1.0

def test_natural_language():
    parser = UniversalParser()
    tree = parser.parse("Corrija a vulnerabilidade CVE-2026-99999 em produção")
    # Because there isn't LLM yet, it will fallback to free_text with extracted entities
    assert tree.root.node_type == 'free_text'
    assert 'CVE-2026-99999' in tree.root.metadata['extracted_entities']['cves']

def test_python_code_with_risk():
    parser = UniversalParser()
    code = "import pickle\ndata = pickle.loads(open('evil.pkl','rb').read())"
    tree = parser.parse(code)
    assert tree.root.node_type == 'code_ast'
    assert 'unsafe_deserialization' in tree.root.metadata['risks']

def test_typo_correction():
    parser = UniversalParser()
    tree = parser.parse("%arkhe profil technical")
    assert tree.errors
    assert tree.root.node_type == 'error'
    assert 'profil' in tree.errors[0]

def test_structured_service_map():
    parser = UniversalParser()
    tree = parser.parse('{"api": {"exposure": 0.9}, "db": {"exposure": 0.2}}')
    assert tree.root.node_type == 'structured_data'
    assert tree.root.value == {"api": {"exposure": 0.9}, "db": {"exposure": 0.2}}
