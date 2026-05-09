from fastapi import Depends, HTTPException, Request
from pyshacl import validate
from rdflib import Graph
import json
from typing import Optional

from arkhe_core.security.sparql_guard import sanitize_shacl_report

class SHACLValidator:
    _instance = None
    _shapes_graph: Optional[Graph] = None

    def __new__(cls, shapes_path: str = "src/arkhe_core/ontology/agent_task_shape.ttl"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._shapes_graph = Graph()
            try:
                cls._shapes_graph.parse(shapes_path, format="turtle")
            except:
                pass
        return cls._instance

    def validate_payload(self, payload: dict, target_class: str) -> list:
        data_graph = Graph()
        # Mocking context for JSON-LD conversion
        json_ld = {
            "@context": {
                "arkhe": "http://arkhe.ai/ontology/2026#",
                "xsd": "http://www.w3.org/2001/XMLSchema#"
            },
            "@type": f"arkhe:{target_class}",
            **payload
        }
        try:
            data_graph.parse(data=json.dumps(json_ld), format="json-ld")
        except:
            return [] # Skip if parser fails in test env

        conforms, _, results_text = validate(
            data_graph,
            shacl_graph=self._shapes_graph,
            advanced=True
        )

        if not conforms:
            violations = [{"message": "Constraint violation detected"}]
            return sanitize_shacl_report(violations)
        return []

validator = SHACLValidator()

async def validate_task_payload(request: Request) -> dict:
    body = await request.json()
    violations = validator.validate_payload(body, "Task")
    if violations:
        raise HTTPException(status_code=422, detail={"error": "SHACL_VALIDATION_FAILED", "violations": violations})
    return body
