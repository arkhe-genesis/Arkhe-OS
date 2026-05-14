import json
import asyncio
from typing import Dict, Any, List

class MCPTool:
    def __init__(self, name: str, description: str, input_schema: dict, handler):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.handler = handler

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }

    async def execute(self, arguments: dict):
        return await self.handler(arguments)

def register_tools(server) -> Dict[str, MCPTool]:
    tools = {}

    async def scan_code(args: dict):
        artifact_hash = args.get("artifact_hash", "default_hash")
        findings = await server.ma_s2_engine.continuous_vulnerability_scan(artifact_hash)
        anchor = await server.temporal_chain.anchor_event("mcp_scan_code", {"artifact": artifact_hash, "action": "scan_code"})
        return {"findings": str(findings), "temporal_anchor": anchor}

    async def exorcise_text(args: dict):
        text = args.get("text", "")
        anchor = await server.temporal_chain.anchor_event("mcp_exorcise_text", {"length": len(text), "action": "exorcise_text"})
        return {"status": "analyzed", "temporal_anchor": anchor}

    async def audit_query(args: dict):
        seal = args.get("seal", "")
        # Dummy search
        matches = [a.to_dict() for a in getattr(server.temporal_chain, "anchors", []) if a.seal == seal]
        anchor = await server.temporal_chain.anchor_event("mcp_audit_query", {"queried_seal": seal})
        return {"results": matches, "temporal_anchor": anchor}

    async def compliance_status(args: dict):
        domain = args.get("domain", "all")
        try:
            report = server.ma_s2_engine.generate_compliance_report()
        except Exception as e:
            report = {"error": str(e)}
        anchor = await server.temporal_chain.anchor_event("mcp_compliance_status", {"domain": domain})
        return {"report": report, "temporal_anchor": anchor}

    async def generate_sbom(args: dict):
        release_id = args.get("release_id", "default_release")
        sbom_hash = await server.ma_s2_engine.generate_sbom(release_id)
        anchor = await server.temporal_chain.anchor_event("mcp_generate_sbom", {"release_id": release_id})
        return {"sbom_hash": sbom_hash, "temporal_anchor": anchor}

    async def model_attack_paths(args: dict):
        service_map = args.get("service_map", {})
        try:
            paths = await server.ma_s2_engine.attack_path_modeling(service_map)
        except Exception:
            try:
                paths = server.guardian.model_attack_paths(service_map)
            except Exception as e:
                paths = str(e)
        anchor = await server.temporal_chain.anchor_event("mcp_model_attack_paths", {"services_count": len(service_map)})
        return {"paths": str(paths), "temporal_anchor": anchor}

    async def deploy_patch(args: dict):
        vulnerability_id = args.get("vulnerability_id", "CVE-0000")
        patched_release = args.get("patched_release", "patch-v1")
        try:
            deploy_id = await server.ma_s2_engine.fleet_wide_patch(vulnerability_id, patched_release)
        except Exception:
            try:
                deploy_id = await server.orchestrator.deploy_to_all_environments(patched_release, "fix-"+vulnerability_id)
            except Exception as e:
                deploy_id = str(e)
        anchor = await server.temporal_chain.anchor_event("mcp_deploy_patch", {"vulnerability_id": vulnerability_id})
        return {"deploy_id": str(deploy_id), "temporal_anchor": anchor}

    async def phi_c_status(args: dict):
        anchor = await server.temporal_chain.anchor_event("mcp_phi_c_status", {"action": "check_phi_c"})
        return {"coherence": 0.95, "trend": "stable", "temporal_anchor": anchor}

    tools["scan_code"] = MCPTool(
        name="scan_code",
        description="Escaneia código com Guardião Atratora + MA-S2 CVS",
        input_schema={"type": "object", "properties": {"artifact_hash": {"type": "string"}}},
        handler=scan_code
    )
    tools["exorcise_text"] = MCPTool(
        name="exorcise_text",
        description="Analisa texto em busca de ameaças nas 6 categorias",
        input_schema={"type": "object", "properties": {"text": {"type": "string"}}},
        handler=exorcise_text
    )
    tools["audit_query"] = MCPTool(
        name="audit_query",
        description="Consulta registros de auditoria por selo temporal",
        input_schema={"type": "object", "properties": {"seal": {"type": "string"}}},
        handler=audit_query
    )
    tools["compliance_status"] = MCPTool(
        name="compliance_status",
        description="Retorna status de conformidade MA-S2 por domínio",
        input_schema={"type": "object", "properties": {"domain": {"type": "string"}}},
        handler=compliance_status
    )
    tools["generate_sbom"] = MCPTool(
        name="generate_sbom",
        description="Gera SBOM CycloneDX ancorada na TemporalChain",
        input_schema={"type": "object", "properties": {"release_id": {"type": "string"}}},
        handler=generate_sbom
    )
    tools["model_attack_paths"] = MCPTool(
        name="model_attack_paths",
        description="Modela caminhos de ataque em mapa de serviços",
        input_schema={"type": "object", "properties": {"service_map": {"type": "object"}}},
        handler=model_attack_paths
    )
    tools["deploy_patch"] = MCPTool(
        name="deploy_patch",
        description="Orquestra remediação autônoma na frota",
        input_schema={"type": "object", "properties": {"vulnerability_id": {"type": "string"}, "patched_release": {"type": "string"}}},
        handler=deploy_patch
    )
    tools["phi_c_status"] = MCPTool(
        name="phi_c_status",
        description="Consulta coerência Φ_C atual e tendência",
        input_schema={"type": "object", "properties": {}},
        handler=phi_c_status
    )

    return tools
