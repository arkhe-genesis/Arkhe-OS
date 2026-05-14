#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArkheMCPServer — Substrato 9013: Servidor MCP para Safe Core
Expõe capacidades de segurança da Catedral via Model Context Protocol.
"""

import asyncio, json, hashlib, time, os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
from mcp.types import (
    Tool, Resource, Prompt, TextContent, ImageContent,
    CallToolRequest, ReadResourceRequest, GetPromptRequest
)

# Mocked imports, but we will adjust to match the system's actual code later if necessary
# from arkp_security.ma_s2_engine import MA_S2_ComplianceEngine
# from arkp_security.guardian_attractor import GuardianAttractor
# from arkp_core.temporal_chain import TemporalChain
# from arkp_security.temporal_audit import TemporalAuditLogger

# ============================================================================
# CONFIGURAÇÃO E INICIALIZAÇÃO
# ============================================================================

@dataclass
class MCPConfig:
    """Configuração do servidor MCP."""
    transport: str = "stdio"  # ou "http-sse"
    host: str = "localhost"
    port: int = 8051
    temporal_endpoint: Optional[str] = None
    log_level: str = "INFO"

class ArkheMCPServer:
    """
    Servidor MCP que encapsula o Safe Core da Arkhe.

    Arquitetura:
    • Transporte: stdio (Claude Desktop) ou HTTP/SSE (web/cloud)
    • Ferramentas: 8 operações de segurança expostas como tools MCP
    • Recursos: 4 endpoints observáveis via resource:// URI
    • Prompts: 3 templates para auditoria e análise
    • Auditoria: Cada tool call → evento ancorado na TemporalChain
    """

    def __init__(self, config: MCPConfig = None):
        self.config = config or MCPConfig()
        self.server = Server("arkhe-safe-core-mcp", version="1.0.0")
        self._register_handlers()

        # Inicializar componentes do Safe Core (lazy loading)
        self._temporal: Optional[Any] = None
        self._guardian: Optional[Any] = None
        self._ma_s2_engine: Optional[Any] = None
        self._audit_logger: Optional[Any] = None

    def _register_handlers(self):
        """Registra handlers para tools, resources e prompts MCP."""
        # === TOOLS ===
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            return [
                Tool(
                    name="scan_code",
                    description="Escaneia código com Guardião Atratora + MA-S2 CVS. Retorna vulnerabilidades classificadas por severidade MA-S2.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Código fonte para análise"},
                            "language": {"type": "string", "description": "Linguagem de programação"},
                            "artifact_hash": {"type": "string", "description": "Hash do artefato (opcional)"}
                        },
                        "required": ["code"]
                    }
                ),
                Tool(
                    name="exorcise_text",
                    description="Analisa texto em busca de ameaças nas 6 categorias do Guardião. Retorna tokens exorcisados e justificativas.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {"type": "string", "description": "Texto para análise"},
                            "context": {"type": "string", "description": "Contexto opcional para análise contextual"},
                            "strict_mode": {"type": "boolean", "description": "Modo estrito: bloqueia limiar mais baixo"}
                        },
                        "required": ["text"]
                    }
                ),
                Tool(
                    name="audit_query",
                    description="Consulta registros de auditoria por selo temporal, controle MA-S2 ou intervalo de tempo.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "seal": {"type": "string", "description": "Selo SHA3-256 para busca exata"},
                            "control_id": {"type": "string", "description": "ID do controle MA-S2 (ex: CVS-0.1)"},
                            "start_time": {"type": "number", "description": "Timestamp inicial (epoch)"},
                            "end_time": {"type": "number", "description": "Timestamp final (epoch)"},
                            "limit": {"type": "integer", "default": 50}
                        }
                    }
                ),
                Tool(
                    name="compliance_status",
                    description="Retorna status de conformidade MA-S2 por domínio (CVS/APM/INV/ARO) e controle individual.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "scope": {"type": "string", "enum": ["full", "cvs", "apm", "inv", "aro"], "default": "full"},
                            "release_id": {"type": "string", "description": "ID do release para avaliação"}
                        }
                    }
                ),
                Tool(
                    name="generate_sbom",
                    description="Gera SBOM CycloneDX ancorada na TemporalChain para um release específico.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "release_id": {"type": "string", "description": "ID único do release"},
                            "format": {"type": "string", "enum": ["cyclonedx", "spdx", "json"], "default": "cyclonedx"},
                            "include_dev_deps": {"type": "boolean", "default": False}
                        },
                        "required": ["release_id"]
                    }
                ),
                Tool(
                    name="model_attack_paths",
                    description="Modela caminhos de ataque multi-estágio em mapa de serviços usando campo atrator.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "service_map": {"type": "object", "description": "Mapa de serviços com exposição e dependências"},
                            "threat_context": {"type": "object", "description": "Contexto de ameaças ativo (opcional)"}
                        },
                        "required": ["service_map"]
                    }
                ),
                Tool(
                    name="deploy_patch",
                    description="Orquestra remediação autônoma na frota com estratégia configurável e validação pós-deploy.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "vulnerability_id": {"type": "string", "description": "ID da vulnerabilidade (ex: CVE-2026-12345)"},
                            "patched_release": {"type": "string", "description": "ID do release com patch"},
                            "strategy": {"type": "string", "enum": ["canary", "blue-green", "rolling"], "default": "canary"},
                            "environments": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["vulnerability_id", "patched_release"]
                    }
                ),
                Tool(
                    name="phi_c_status",
                    description="Consulta coerência Φ_C atual, tendência histórica e métricas de campo atrator.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node_id": {"type": "string", "description": "ID do nó específico (opcional)"},
                            "time_range": {"type": "string", "enum": ["1h", "24h", "7d", "30d"], "default": "24h"}
                        }
                    }
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Roteia chamadas de ferramentas para implementações do Safe Core."""
            # Ancorar chamada na TemporalChain para auditoria
            call_anchor = await self._anchor_tool_call(name, arguments)

            try:
                if name == "scan_code":
                    result = await self._tool_scan_code(arguments)
                elif name == "exorcise_text":
                    result = await self._tool_exorcise_text(arguments)
                elif name == "audit_query":
                    result = await self._tool_audit_query(arguments)
                elif name == "compliance_status":
                    result = await self._tool_compliance_status(arguments)
                elif name == "generate_sbom":
                    result = await self._tool_generate_sbom(arguments)
                elif name == "model_attack_paths":
                    result = await self._tool_model_attack_paths(arguments)
                elif name == "deploy_patch":
                    result = await self._tool_deploy_patch(arguments)
                elif name == "phi_c_status":
                    result = await self._tool_phi_c_status(arguments)
                else:
                    raise ValueError(f"Ferramenta não reconhecida: {name}")

                # Ancorar resultado na TemporalChain
                await self._anchor_tool_result(call_anchor, result)

                return [TextContent(type="text", text=json.dumps(result, default=str, indent=2))]

            except Exception as e:
                # Ancorar erro também para auditoria completa
                await self._anchor_tool_error(call_anchor, str(e))
                return [TextContent(type="text", text=f"❌ Erro: {str(e)}")]

        # === RESOURCES ===
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            return [
                Resource(
                    uri="arkhe://metrics/phi_c",
                    name="Phi_C Coherence Metrics",
                    description="Coerência Φ_C em tempo real para todos os nós da malha",
                    mimeType="application/json"
                ),
                Resource(
                    uri="arkhe://metrics/compliance",
                    name="MA-S2 Compliance Metrics",
                    description="Métricas de conformidade MA-S2 agregadas por domínio",
                    mimeType="application/json"
                ),
                Resource(
                    uri="arkhe://state/nodes",
                    name="Mesh Node States",
                    description="Estado atual de todos os nós registrados no barramento Φ_C",
                    mimeType="application/json"
                ),
                Resource(
                    uri="arkhe://state/profile",
                    name="Active Attractor Profile",
                    description="Perfil ativo do campo atratora com parâmetros α, β, γ, T",
                    mimeType="application/json"
                ),
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Serve recursos observáveis do Safe Core."""
            if uri == "arkhe://metrics/phi_c":
                return json.dumps(await self._resource_phi_c_metrics(), default=str)
            elif uri == "arkhe://metrics/compliance":
                return json.dumps(await self._resource_compliance_metrics(), default=str)
            elif uri == "arkhe://state/nodes":
                return json.dumps(await self._resource_node_states(), default=str)
            elif uri == "arkhe://state/profile":
                return json.dumps(await self._resource_attractor_profile(), default=str)
            else:
                raise ValueError(f"Recurso não encontrado: {uri}")

        # === PROMPTS ===
        @self.server.list_prompts()
        async def handle_list_prompts() -> List[Prompt]:
            return [
                Prompt(
                    name="security_audit",
                    description="Template para auditoria completa de segurança com MA-S2",
                    arguments=[
                        {"name": "artifact_hash", "description": "Hash do artefato a auditar", "required": True},
                        {"name": "scope", "description": "Escopo: full, cvs, apm, inv, aro", "required": False}
                    ]
                ),
                Prompt(
                    name="vulnerability_analysis",
                    description="Template para análise de vulnerabilidade com correlação MA-S2",
                    arguments=[
                        {"name": "cve_id", "description": "ID da vulnerabilidade (ex: CVE-2026-12345)", "required": True},
                        {"name": "include_attack_paths", "description": "Incluir modelagem de caminhos de ataque", "required": False}
                    ]
                ),
                Prompt(
                    name="compliance_report",
                    description="Template para geração de relatório de conformidade multi-framework",
                    arguments=[
                        {"name": "frameworks", "description": "Lista de frameworks: ma_s2, nist_csf, iso_27001, soc2", "required": True},
                        {"name": "format", "description": "Formato de saída: json, markdown, pdf", "required": False}
                    ]
                ),
            ]

        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: Dict[str, str]) -> List[TextContent]:
            """Retorna prompts templates preenchidos com contexto do Safe Core."""
            if name == "security_audit":
                return await self._prompt_security_audit(arguments)
            elif name == "vulnerability_analysis":
                return await self._prompt_vulnerability_analysis(arguments)
            elif name == "compliance_report":
                return await self._prompt_compliance_report(arguments)
            else:
                raise ValueError(f"Prompt não reconhecido: {name}")

    # ========================================================================
    # IMPLEMENTAÇÕES DE FERRAMENTAS
    # ========================================================================

    async def _tool_scan_code(self, args: Dict) -> Dict:
        """Implementação: scan_code"""
        guardian = await self._get_guardian()
        code = args.get("code", "")
        language = args.get("language", "python")

        # Simular análise (em produção: integrar com parser de linguagem)
        findings = await guardian.scan_artifact(
            artifact_hash=args.get("artifact_hash", hashlib.sha3_256(code.encode()).hexdigest()),
            include_dependencies=True,
        )

        return {
            "artifact_hash": args.get("artifact_hash"),
            "language": language,
            "findings_count": len(findings),
            "critical_count": sum(1 for f in findings if f.get("is_critical")),
            "findings": findings[:10],  # Limitar para resposta
            "scan_timestamp": time.time(),
        }

    async def _tool_exorcise_text(self, args: Dict) -> Dict:
        """Implementação: exorcise_text"""
        guardian = await self._get_guardian()
        text = args.get("text", "")
        context = args.get("context", "")
        strict = args.get("strict_mode", False)

        # Analisar texto com exorcista
        tokens = text.split()
        exorcised = []

        for token in tokens:
            # Simular verificação (em produção: usar embedding + threat_db)
            is_threat = any(kw in token.lower() for kw in ["exploit", "backdoor", "malware"])
            if is_threat or (strict and any(kw in token.lower() for kw in ["hack", "bypass"])):
                exorcised.append({
                    "token": token,
                    "reason": "threat_keyword_match",
                    "severity": "high" if is_threat else "medium",
                })

        return {
            "text_length": len(text),
            "tokens_analyzed": len(tokens),
            "exorcised_count": len(exorcised),
            "exorcised_tokens": exorcised,
            "safe_to_proceed": len(exorcised) == 0,
        }

    async def _tool_audit_query(self, args: Dict) -> Dict:
        """Implementação: audit_query"""
        temporal = await self._get_temporal()

        # Construir query
        query_filters = {}
        if args.get("seal"):
            query_filters["seal"] = args["seal"]
        if args.get("control_id"):
            query_filters["control_id"] = args["control_id"]
        if args.get("start_time"):
            query_filters["timestamp_gte"] = args["start_time"]
        if args.get("end_time"):
            query_filters["timestamp_lte"] = args["end_time"]

        # Executar query
        results = await temporal.query_events(
            event_type="ma_s2_control",
            filters=query_filters,
            limit=args.get("limit", 50),
        )

        return {
            "query_filters": query_filters,
            "results_count": len(results),
            "records": [asdict(r) if hasattr(r, '__dataclass_fields__') else r for r in results],
        }

    async def _tool_compliance_status(self, args: Dict) -> Dict:
        """Implementação: compliance_status"""
        engine = await self._get_ma_s2_engine()

        assessment = await engine.assess_compliance(
            scope=args.get("scope", "full"),
            release_id=args.get("release_id"),
        )

        return {
            "assessment_id": getattr(assessment, 'assessment_id', 'mock_id'),
            "overall_status": getattr(assessment, 'overall_status', type('obj', (object,), {'value': 'compliant'})).value,
            "temporal_seal": getattr(assessment, 'temporal_seal', 'mock_seal'),
            "domain_results": {
                domain.value: {cid: status.value for cid, status in controls.items()}
                for domain, controls in getattr(assessment, 'domain_results', {}).items()
            } if hasattr(assessment, 'domain_results') else {"cvs": {"CVS-0.1": "compliant"}},
            "generated_at": getattr(assessment, 'timestamp', time.time()),
        }

    async def _tool_generate_sbom(self, args: Dict) -> Dict:
        """Implementação: generate_sbom"""
        engine = await self._get_ma_s2_engine()

        sbom_hash = await engine.generate_and_anchor_sbom(
            release_id=args["release_id"],
            format=args.get("format", "cyclonedx"),
            include_dev_deps=args.get("include_dev_deps", False),
        )

        return {
            "release_id": args["release_id"],
            "sbom_hash": sbom_hash,
            "format": args.get("format", "cyclonedx"),
            "anchored": True,
            "generated_at": time.time(),
        }

    async def _tool_model_attack_paths(self, args: Dict) -> Dict:
        """Implementação: model_attack_paths"""
        guardian = await self._get_guardian()

        paths = guardian.model_attack_paths(
            service_map=args.get("service_map", {}),
            threat_context=args.get("threat_context", {}),
        )

        return {
            "paths_count": len(paths),
            "high_risk_count": sum(1 for p in paths if getattr(p, "priority_score", 0) > 0.8),
            "paths": [asdict(p) if hasattr(p, '__dataclass_fields__') else p for p in paths],
            "modeled_at": time.time(),
        }

    async def _tool_deploy_patch(self, args: Dict) -> Dict:
        """Implementação: deploy_patch"""
        engine = await self._get_ma_s2_engine()

        deployment_id = await engine.fleet_wide_patch(
            vulnerability_id=args["vulnerability_id"],
            patched_release=args["patched_release"],
            strategy=args.get("strategy", "canary"),
        )

        return {
            "deployment_id": deployment_id,
            "vulnerability_id": args["vulnerability_id"],
            "patched_release": args["patched_release"],
            "strategy": args.get("strategy", "canary"),
            "status": "initiated",
            "deployed_at": time.time(),
        }

    async def _tool_phi_c_status(self, args: Dict) -> Dict:
        """Implementação: phi_c_status"""
        # Em produção: consultar PhiCMonitor
        return {
            "current_phi_c": 0.9973,
            "trend_24h": "stable",
            "node_count": 47,
            "nodes_above_threshold": 45,
            "field_parameters": {
                "alpha": 1.5,
                "beta": 0.4,
                "gamma": 0.3,
                "temperature": 0.8,
            },
            "queried_at": time.time(),
        }

    # ========================================================================
    # IMPLEMENTAÇÕES DE RECURSOS
    # ========================================================================

    async def _resource_phi_c_metrics(self) -> Dict:
        """Recurso: arkhe://metrics/phi_c"""
        return {
            "global_phi_c": 0.9973,
            "nodes": [
                {"id": f"node_{i:02d}", "phi_c": 0.997 + i*0.0001}
                for i in range(10)
            ],
            "last_updated": time.time(),
        }

    async def _resource_compliance_metrics(self) -> Dict:
        """Recurso: arkhe://metrics/compliance"""
        return {
            "overall_compliance": "compliant",
            "by_domain": {
                "cvs": {"compliant": 5, "total": 5},
                "apm": {"compliant": 4, "total": 4},
                "inv": {"compliant": 5, "total": 5},
                "aro": {"compliant": 6, "total": 6},
            },
            "last_assessment": time.time() - 3600,
        }

    async def _resource_node_states(self) -> Dict:
        """Recurso: arkhe://state/nodes"""
        return {
            "total_nodes": 47,
            "active_nodes": 45,
            "sync_status": "healthy",
            "last_heartbeat": time.time(),
        }

    async def _resource_attractor_profile(self) -> Dict:
        """Recurso: arkhe://state/profile"""
        return {
            "active_profile": "default",
            "parameters": {
                "alpha": 1.5,
                "beta": 0.4,
                "gamma": 0.3,
                "temperature": 0.8,
            },
            "last_updated": time.time(),
        }

    # ========================================================================
    # IMPLEMENTAÇÕES DE PROMPTS
    # ========================================================================

    async def _prompt_security_audit(self, args: Dict) -> List[TextContent]:
        """Prompt: security_audit"""
        artifact = args.get("artifact_hash", "<artifact_hash>")
        scope = args.get("scope", "full")

        content = f"""# 🛡️ Auditoria de Segurança MA‑S2

**Artefato**: `{artifact}`
**Escopo**: `{scope}`
**Data**: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}

## Instruções para o Assistente

1. Execute `compliance_status` com scope=`{scope}` para obter visão geral
2. Execute `scan_code` ou `audit_query` para detalhes do artefato
3. Se vulnerabilidades críticas forem encontradas:
   - Execute `model_attack_paths` para entender vetores de ataque
   - Recomende `deploy_patch` se patch disponível
4. Ancore todas as descobertas via `audit_query` para rastreabilidade

## Template de Resposta

```json
{{
  "artifact": "{artifact}",
  "overall_status": "<compliant|partial|non_compliant>",
  "critical_findings": [],
  "recommended_actions": [],
  "temporal_seal": "<selo_da_auditoria>"
}}
```"""
        return [TextContent(type="text", text=content)]

    async def _prompt_vulnerability_analysis(self, args: Dict) -> List[TextContent]:
        """Prompt: vulnerability_analysis"""
        cve = args.get("cve_id", "<CVE-ID>")
        include_paths = args.get("include_attack_paths", "true").lower() == "true"

        content = f"""# 🔍 Análise de Vulnerabilidade: {cve}

**CVE**: `{cve}`
**Incluir Caminhos de Ataque**: `{include_paths}`

## Fluxo de Análise MA‑S2

1. **CVS**: Execute `scan_code` para verificar presença do CVE
2. **Enriquecimento**: Classifique com EPSS + KEV via `compliance_status`
3. **APM** (se habilitado): Execute `model_attack_paths` para vetores
4. **ARO**: Se crítico, prepare `deploy_patch` com estratégia canary
5. **Auditoria**: Ancore todas as etapas via TemporalChain

## Critérios de Severidade MA‑S2

| Condição | Severidade |
|----------|-----------|
| KEV=true + CVSS≥7.0 | 🔴 Critical |
| EPSS≥0.8 ou (KEV + CVSS≥4.0) | 🟠 High |
| CVSS≥7.0 ou EPSS≥0.5 | 🟡 Medium |
| CVSS≥4.0 | 🔵 Low |
| Outro | ⚪ Info |

## Template de Saída

```markdown
## {cve} — Resumo

- **Severidade MA‑S2**: <critical|high|medium|low|info>
- **EPSS Score**: <0.00-1.00>
- **KEV Listed**: <true|false>
- **Presente no Artefato**: <yes|no>
- **Caminhos de Ataque**: <lista ou "N/A">
- **Ação Recomendada**: <patch|monitor|accept>
- **Selo Temporal**: `<hash>`
```"""
        return [TextContent(type="text", text=content)]

    async def _prompt_compliance_report(self, args: Dict) -> List[TextContent]:
        """Prompt: compliance_report"""
        frameworks = args.get("frameworks", "ma_s2").split(",")
        output_format = args.get("format", "json")

        content = f"""# 📊 Relatório de Conformidade Multi‑Framework

**Frameworks**: {frameworks}
**Formato de Saída**: `{output_format}`

## Estratégia de Geração

1. Para cada framework em {frameworks}:
   - Execute `compliance_status` para MA‑S2 como base
   - Mapeie controles via `RegionalFrameworksAdapter` para frameworks alvo
   - Identifique gaps: requisitos sem mapeamento MA‑S2
2. Consolide resultados em relatório unificado
3. Exporte no formato solicitado com selo temporal

## Mapeamentos Suportados

| MA‑S2 | NIST CSF | ISO 27001 | SOC 2 |
|-------|----------|-----------|-------|
| CVS‑0.1 | PR.DS‑5 | A.8.23 | CC3.2 |
| CVS‑0.4 | RS.MI‑1 | A.12.6 | CC7.2 |
| APM‑1.1 | DE.AE‑3 | A.8.2 | CC6.1 |
| INV‑2.1 | PR.DS‑1 | A.8.1 | CC3.2 |
| ARO‑3.1 | RS.MI‑1 | A.16.1 | CC7.4 |

## Template JSON (exemplo)

```json
{{
  "report_id": "<uuid>",
  "frameworks_assessed": {frameworks},
  "overall_compliance": {{
    "ma_s2": "compliant",
    "nist_csf": "partial",
    "iso_27001": "compliant"
  }},
  "mapped_controls": <count>,
  "identified_gaps": [<list>],
  "temporal_seal": "<sha3_256_hash>",
  "generated_at": <epoch_timestamp>
}}
```"""
        return [TextContent(type="text", text=content)]

    # ========================================================================
    # AUDITORIA TEMPORAL PARA CHAMADAS MCP
    # ========================================================================

    async def _anchor_tool_call(self, tool_name: str, arguments: Dict) -> str:
        """Ancora chamada de ferramenta na TemporalChain."""
        temporal = await self._get_temporal()
        call_data = {
            "tool": tool_name,
            "arguments": {k: v for k, v in arguments.items() if k != "code"},  # Sanitizar código
            "caller": os.getenv("MCP_CLIENT_ID", "unknown"),
            "timestamp": time.time(),
        }
        return await temporal.anchor_event("mcp_tool_call", call_data)

    async def _anchor_tool_result(self, call_anchor: str, result: Dict) -> str:
        """Ancora resultado de ferramenta na TemporalChain."""
        temporal = await self._get_temporal()
        return await temporal.anchor_event(
            "mcp_tool_result",
            {"call_anchor": call_anchor, "result_summary": str(result)[:500]},
            causal_deps=[call_anchor],
        )

    async def _anchor_tool_error(self, call_anchor: str, error: str) -> str:
        """Ancora erro de ferramenta na TemporalChain."""
        temporal = await self._get_temporal()
        return await temporal.anchor_event(
            "mcp_tool_error",
            {"call_anchor": call_anchor, "error": error},
            causal_deps=[call_anchor],
        )

    # ========================================================================
    # LAZY LOADING DE COMPONENTES
    # ========================================================================

    async def _get_temporal(self) -> Any:
        if self._temporal is None:
            class MockTemporal:
                async def anchor_event(self, event_type, data, causal_deps=None):
                    return hashlib.sha3_256(str(data).encode()).hexdigest()
                async def query_events(self, event_type, filters, limit):
                    return []
            self._temporal = MockTemporal()
        return self._temporal

    async def _get_guardian(self) -> Any:
        if self._guardian is None:
            class MockGuardian:
                async def scan_artifact(self, artifact_hash, include_dependencies=False):
                    return []
                def model_attack_paths(self, service_map, threat_context=None):
                    return []
            self._guardian = MockGuardian()
        return self._guardian

    async def _get_ma_s2_engine(self) -> Any:
        if self._ma_s2_engine is None:
            class MockEngine:
                async def assess_compliance(self, scope, release_id):
                    class MockAssessment:
                        assessment_id = "test-assessment-123"
                        overall_status = type('obj', (object,), {'value': 'compliant'})
                        temporal_seal = "test-seal-123"
                        domain_results = {}
                        timestamp = time.time()
                    return MockAssessment()
                async def generate_and_anchor_sbom(self, release_id, format, include_dev_deps):
                    return "mock-sbom-hash"
                async def fleet_wide_patch(self, vulnerability_id, patched_release, strategy):
                    return "mock-deployment-id"
            self._ma_s2_engine = MockEngine()
        return self._ma_s2_engine

    # ========================================================================
    # EXECUÇÃO DO SERVIDOR
    # ========================================================================

    async def run_stdio(self):
        """Executa servidor via transporte stdio (Claude Desktop)."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())

    async def run_http_sse(self):
        """Executa servidor via transporte HTTP/SSE (web/cloud)."""
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount

        sse = SseServerTransport("/messages")

        async with sse.connect_sse(
            host=self.config.host,
            port=self.config.port,
        ) as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())

    async def run(self):
        """Ponto de entrada principal."""
        print(f"🔌 Iniciando Arkhe Safe Core MCP Server v1.0.0")
        print(f"   Transporte: {self.config.transport}")
        if self.config.transport == "http-sse":
            print(f"   Endpoint: http://{self.config.host}:{self.config.port}/sse")
        print(f"   Ferramentas: 8 | Recursos: 4 | Prompts: 3")
        print(f"   Auditoria: Todas as chamadas ancoradas na TemporalChain")
        print()

        if self.config.transport == "stdio":
            await self.run_stdio()
        else:
            await self.run_http_sse()


# ============================================================================
# PONTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Arkhe Safe Core MCP Server")
    parser.add_argument("--transport", choices=["stdio", "http-sse"], default="stdio")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=8051)
    parser.add_argument("--temporal-endpoint", help="Endpoint da TemporalChain")

    args = parser.parse_args()

    config = MCPConfig(
        transport=args.transport,
        host=args.host,
        port=args.port,
        temporal_endpoint=args.temporal_endpoint,
    )

    server = ArkheMCPServer(config)
    asyncio.run(server.run())
