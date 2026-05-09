from rdflib.plugins.sparql.parser import parseQuery
from typing import Any, List, Optional
import re

FORBIDDEN_OPERATORS = ['DESCRIBE', 'CONSTRUCT']
FORBIDDEN_URIS = ["http://arkhe.ai/ontology/2026#", "http://www.w3.org/2002/07/owl#"]

class SecurityException(Exception):
    pass

def sanitize_sparql_query(sparql_string: str, trusted_source: bool = False) -> str:
    """
    Intercepts and modifies the SPARQL query before sending it to Fuseki.

    Args:
        sparql_string: The query string to validate.
        trusted_source: If True, bypasses URI-based schema mining protections.
                       Operators like DESCRIBE/CONSTRUCT are still blocked for safety.
    """
    try:
        # Normalize whitespace for consistent matching
        normalized_query = " ".join(sparql_string.split())
        upper_query = normalized_query.upper()

        # 1. Block forbidden operators (DESCRIBE, CONSTRUCT)
        # These are blocked even for trusted sources to enforce the no-dump policy.
        for op in FORBIDDEN_OPERATORS:
            if re.search(rf'\b{op}\b', upper_query):
                raise SecurityException(f"{op} queries are disabled.")

        # 2. Block restricted URIs for untrusted sources
        # This prevents schema mining via SELECT or ASK by users.
        if not trusted_source:
            for uri in FORBIDDEN_URIS:
                if uri in sparql_string:
                    raise SecurityException("Query targets restricted schema namespace.")

        # 3. Block potentially dangerous patterns via AST
        try:
            parsed = parseQuery(sparql_string)
            if hasattr(parsed, 'algebra'):
                if parsed.algebra.name in ['DescribeQuery', 'ConstructQuery']:
                    raise SecurityException("Forbidden query type detected by AST.")
        except SecurityException:
            raise
        except Exception:
            # If parsing fails, we already have string-based protections
            pass

        return sparql_string

    except SecurityException:
        raise
    except Exception as e:
        # Fail-Safe
        raise SecurityException(f"Query validation failed. Contact administrator.")

def sanitize_shacl_report(shacl_report_violations: List[dict]) -> List[dict]:
    """
    Intercepts the SHACL validation report and removes schema metadata.
    """
    if shacl_report_violations:
        # Return a generic error message instead of detailed violations
        # to prevent T-Box leakage via validation reports.
        return [{"message": "Data violates schema constraints."}]
    return []
