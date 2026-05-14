import json
import asyncio
from typing import Dict, Any

class MCPResource:
    def __init__(self, uri: str, name: str, description: str, handler):
        self.uri = uri
        self.name = name
        self.description = description
        self.handler = handler

    def to_dict(self):
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description
        }

    async def read(self):
        return await self.handler()

def register_resources(server) -> Dict[str, MCPResource]:
    resources = {}

    async def get_phi_c():
        anchor = await server.temporal_chain.anchor_event("mcp_resource_read", {"uri": "arkhe://metrics/phi_c"})
        return {
            "coherence": 0.95,
            "resonance": 0.88,
            "temporal_anchor": anchor
        }

    async def get_compliance():
        try:
            report = server.ma_s2_engine.generate_compliance_report()
        except Exception as e:
            report = {"error": str(e)}
        anchor = await server.temporal_chain.anchor_event("mcp_resource_read", {"uri": "arkhe://metrics/compliance"})
        return {
            "report": report,
            "temporal_anchor": anchor
        }

    async def get_nodes():
        anchor = await server.temporal_chain.anchor_event("mcp_resource_read", {"uri": "arkhe://state/nodes"})
        return {
            "nodes": [
                {"id": "node-01", "status": "online"},
                {"id": "node-02", "status": "online"}
            ],
            "temporal_anchor": anchor
        }

    async def get_profile():
        anchor = await server.temporal_chain.anchor_event("mcp_resource_read", {"uri": "arkhe://state/profile"})
        return {
            "profile": "omega_shield",
            "active_rules": ["exorcist", "attractor_field"],
            "temporal_anchor": anchor
        }

    resources["arkhe://metrics/phi_c"] = MCPResource(
        uri="arkhe://metrics/phi_c",
        name="Phi_C Metrics",
        description="Coerência Φ_C em tempo real",
        handler=get_phi_c
    )
    resources["arkhe://metrics/compliance"] = MCPResource(
        uri="arkhe://metrics/compliance",
        name="Compliance Metrics",
        description="Métricas de conformidade MA-S2",
        handler=get_compliance
    )
    resources["arkhe://state/nodes"] = MCPResource(
        uri="arkhe://state/nodes",
        name="Mesh Nodes State",
        description="Estado dos nós na malha",
        handler=get_nodes
    )
    resources["arkhe://state/profile"] = MCPResource(
        uri="arkhe://state/profile",
        name="Attractor Profile",
        description="Perfil ativo do campo atratora",
        handler=get_profile
    )

    return resources
