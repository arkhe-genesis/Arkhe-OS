import pytest
import re
from arkhe_core.security.sparql_guard import sanitize_sparql_query, sanitize_shacl_report, SecurityException
from arkhe_core.ontology.sparql_client import OntologyClient

def test_sparql_guard_blocks_describe():
    query = "DESCRIBE <http://arkhe.ai/ontology/2026#CompromisedAgent>"
    with pytest.raises(SecurityException) as excinfo:
        sanitize_sparql_query(query)
    assert "DESCRIBE" in str(excinfo.value)

def test_sparql_guard_blocks_construct():
    query = "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"
    with pytest.raises(SecurityException) as excinfo:
        sanitize_sparql_query(query)
    assert "CONSTRUCT" in str(excinfo.value)

def test_sparql_guard_blocks_restricted_uris_in_select_untrusted():
    # Untrusted: Restricted URI in a SELECT query (Schema Mining V1)
    query = "SELECT ?prop WHERE { ?s ?prop ?o . FILTER(STRSTARTS(STR(?prop), \"http://arkhe.ai/ontology/2026#\")) }"
    with pytest.raises(SecurityException) as excinfo:
        sanitize_sparql_query(query, trusted_source=False)
    assert "restricted schema namespace" in str(excinfo.value)

def test_sparql_guard_allows_restricted_uris_in_select_trusted():
    # Trusted: Internal query should work
    query = "PREFIX arkhe: <http://arkhe.ai/ontology/2026#> SELECT ?s WHERE { ?s a arkhe:Agent }"
    try:
        sanitize_sparql_query(query, trusted_source=True)
    except SecurityException:
        pytest.fail("Trusted query failed unexpectedly")

def test_sparql_guard_blocks_operators_even_when_trusted():
    query = "DESCRIBE <http://arkhe.ai/ontology/2026#Agent>"
    with pytest.raises(SecurityException):
        sanitize_sparql_query(query, trusted_source=True)

def test_shacl_report_sanitization():
    raw_violations = [
        {
            "focusNode": "ex:Ataque",
            "resultMessage": "Less than 1 values on arkhe:protectedBy -> arkhe:Seal",
            "resultPath": "arkhe:protectedBy",
            "value": [],
            "constraintComponent": {
                "sh:nodeKind": "sh:IRI",
                "sh:pattern": "http://arkhe.ai/ontology/2026#Seal.*"
            }
        }
    ]
    sanitized = sanitize_shacl_report(raw_violations)
    assert len(sanitized) == 1
    assert sanitized[0]["message"] == "Data violates schema constraints."

def test_ontology_client_integration():
    client = OntologyClient()
    # This should now PASS because OntologyClient uses trusted_source=True
    try:
        client.validate_agent_task("Agent1", "Task1")
    except SecurityException:
        pytest.fail("OntologyClient internal query was blocked")

def test_ontology_client_blocks_injected_operator():
    client = OntologyClient()
    # Even if client is trusted, it shouldn't allow DESCRIBE (in case of injection)
    bad_task_id = "Task1 } DESCRIBE ?s #"
    with pytest.raises(SecurityException):
        client.get_required_seals(bad_task_id)
