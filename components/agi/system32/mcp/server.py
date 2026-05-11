#!/usr/bin/env python3
"""
mcp/server.py — ARKHE OS MCP Server (Substrate 327)
Implements the Model Context Protocol with LFIR/Φ_C integration.
"""
import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict, field

from .context import LFIRContextManager
from .tools import ToolRegistry, ToolInvocationResult
from .resources import ResourceManager
from .prompts import PromptTemplateEngine
from .transport import TransportBackend, StdioTransport, SSETransport
from .attestation import AttestationLayer

logger = logging.getLogger(__name__)

@dataclass
class MCPServerConfig:
    """Configuration for ARKHE OS MCP Server."""
    server_name: str = "arkhe-agi-mcp"
    server_version: str = "1.0.0"
    coherence_threshold: float = 0.7  # Minimum Φ_C for tool invocation
    enable_attestation: bool = True
    enable_anonymous_transport: bool = True
    context_retention_hours: int = 24
    max_context_size: int = 10000  # Max nodes in LFIR context graph
    transport: str = "stdio"  # stdio, sse, websocket
    tor_proxy: Optional[str] = None  # SOCKS5 proxy for anonymous transport

class ARKHEMCPServer:
    """MCP Server with native ARKHE OS integration."""

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.context_manager = LFIRContextManager(
            max_size=config.max_context_size,
            retention_hours=config.context_retention_hours
        )
        self.tool_registry = ToolRegistry(coherence_threshold=config.coherence_threshold)
        self.resource_manager = ResourceManager()
        self.prompt_engine = PromptTemplateEngine()
        self.attestation = AttestationLayer() if config.enable_attestation else None
        self.transport: Optional[TransportBackend] = None
        self.session_id = str(uuid.uuid4())
        self._running = False

    async def initialize(self):
        """Initialize server components and transport."""
        logger.info(f"🧠 Initializing ARKHE MCP Server v{self.config.server_version}")

        # Setup transport backend
        if self.config.transport == "stdio":
            self.transport = StdioTransport(self._handle_message)
        elif self.config.transport == "sse":
            self.transport = SSETransport(self._handle_message, port=8080)
        else:
            raise ValueError(f"Unsupported transport: {self.config.transport}")

        # Register built-in tools from ARKHE substrates
        await self._register_builtin_tools()

        # Load resource providers from config
        await self.resource_manager.load_providers(
            Path(__file__).parent / "config" / "resources.yaml"
        )

        self._running = True
        logger.info("✅ ARKHE MCP Server ready")

    async def _register_builtin_tools(self):
        """Register ARKHE OS substrates as MCP tools."""
        # Coherence Kernel tool
        self.tool_registry.register_tool(
            name="evaluate_coherence",
            description="Evaluate coherence score Φ_C for a given LFIR graph or intent",
            input_schema={
                "type": "object",
                "properties": {
                    "graph": {"type": "object", "description": "LFIR graph JSON"},
                    "intent": {"type": "string", "description": "Natural language intent"}
                },
                "required": []
            },
            handler=self._tool_evaluate_coherence
        )

        # RCP Channel tool
        self.tool_registry.register_tool(
            name="transmit_retrocausal",
            description="Transmit data via Retrocausal Channel Protocol v2.0",
            input_schema={
                "type": "object",
                "properties": {
                    "payload": {"type": "string", "description": "Data to transmit"},
                    "target_temporal_offset": {"type": "number", "description": "Δt for retrocausal influence"}
                },
                "required": ["payload"]
            },
            handler=self._tool_transmit_rcp
        )

        # Federation discovery tool
        self.tool_registry.register_tool(
            name="discover_peers",
            description="Discover ARKHE OS federation peers via DHT",
            input_schema={
                "type": "object",
                "properties": {
                    "min_coherence": {"type": "number", "default": 0.7},
                    "max_results": {"type": "integer", "default": 10}
                }
            },
            handler=self._tool_discover_peers
        )

        # LFIR graph query tool
        self.tool_registry.register_tool(
            name="query_lfir_graph",
            description="Query the local LFIR knowledge graph",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language or SPARQL-like query"},
                    "max_depth": {"type": "integer", "default": 3}
                },
                "required": ["query"]
            },
            handler=self._tool_query_lfir
        )

    async def _handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming MCP protocol messages."""
        method = message.get("method")
        params = message.get("params", {})
        request_id = message.get("id")

        try:
            if method == "initialize":
                return await self._handle_initialize(params, request_id)
            elif method == "tools/list":
                return await self._handle_tools_list(request_id)
            elif method == "tools/call":
                return await self._handle_tool_call(params, request_id)
            elif method == "resources/list":
                return await self._handle_resources_list(request_id)
            elif method == "resources/read":
                return await self._handle_resource_read(params, request_id)
            elif method == "prompts/list":
                return await self._handle_prompts_list(request_id)
            elif method == "prompts/get":
                return await self._handle_prompt_get(params, request_id)
            elif method == "contexts/create":
                return await self._handle_context_create(params, request_id)
            elif method == "contexts/update":
                return await self._handle_context_update(params, request_id)
            elif method == "shutdown":
                await self.shutdown()
                return {"id": request_id, "result": {"status": "shutdown"}}
            else:
                return {
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }

        except Exception as e:
            logger.error(f"Error handling {method}: {e}", exc_info=True)
            return {
                "id": request_id,
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
            }

    async def _handle_initialize(self, params: Dict, request_id: Any) -> Dict:
        """Handle MCP initialize request."""
        client_info = params.get("clientInfo", {})
        logger.info(f"Client connected: {client_info.get('name')} v{client_info.get('version')}")

        return {
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": self.config.server_name,
                    "version": self.config.server_version
                },
                "capabilities": {
                    "tools": {},
                    "resources": {"subscribe": True},
                    "prompts": {},
                    "contexts": {"retention": self.config.context_retention_hours}
                }
            }
        }

    async def _handle_tools_list(self, request_id: Any) -> Dict:
        """List available tools."""
        tools = []
        for tool in self.tool_registry.list_tools():
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            })
        return {"id": request_id, "result": {"tools": tools}}

    async def _handle_tool_call(self, params: Dict, request_id: Any) -> Dict:
        """Execute a tool call with coherence gating."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        # Check coherence threshold before invocation
        current_coherence = await self.context_manager.get_current_coherence()
        if current_coherence < self.config.coherence_threshold:
            return {
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": f"Coherence {current_coherence:.3f} below threshold {self.config.coherence_threshold}"
                }
            }

        # Execute tool
        result = await self.tool_registry.invoke_tool(tool_name, arguments)

        # Attest result if enabled
        if self.config.enable_attestation and self.attestation:
            result.attestation = await self.attestation.sign_result(
                tool_name=tool_name,
                arguments=arguments,
                output=result.output,
                coherence=current_coherence
            )

        return {
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result.output)}],
                "metadata": {
                    "coherence": current_coherence,
                    "execution_time_ms": result.execution_time_ms,
                    "attestation": result.attestation
                }
            }
        }

    async def _handle_resources_list(self, request_id: Any) -> Dict:
        """List available resources."""
        resources = []
        for provider in self.resource_manager.list_providers():
            for resource in provider.list_resources():
                resources.append({
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description,
                    "mimeType": resource.mime_type
                })
        return {"id": request_id, "result": {"resources": resources}}

    async def _handle_resource_read(self, params: Dict, request_id: Any) -> Dict:
        """Read a resource by URI."""
        uri = params.get("uri")
        if not uri:
            return {"id": request_id, "error": {"code": -32602, "message": "Missing uri parameter"}}

        content = await self.resource_manager.read_resource(uri)
        return {
            "id": request_id,
            "result": {
                "contents": [{
                    "uri": uri,
                    "mimeType": content.mime_type,
                    "text": content.text,
                    "blob": content.blob
                }]
            }
        }

    async def _handle_context_create(self, params: Dict, request_id: Any) -> Dict:
        """Create a new LFIR-backed context."""
        context_id = await self.context_manager.create_context(
            initial_graph=params.get("graph"),
            metadata=params.get("metadata", {})
        )
        return {
            "id": request_id,
            "result": {"contextId": context_id}
        }

    async def _handle_context_update(self, params: Dict, request_id: Any) -> Dict:
        """Update an existing context with new nodes/edges."""
        context_id = params.get("contextId")
        updates = params.get("updates", {})

        coherence_delta = await self.context_manager.update_context(
            context_id=context_id,
            additions=updates.get("add", []),
            removals=updates.get("remove", [])
        )

        return {
            "id": request_id,
            "result": {
                "contextId": context_id,
                "coherence_delta": coherence_delta,
                "current_coherence": await self.context_manager.get_context_coherence(context_id)
            }
        }

    async def _tool_evaluate_coherence(self, arguments: Dict) -> ToolInvocationResult:
        """Tool handler: evaluate_coherence."""
        from agi.system32.coherence.kernel import CoherenceKernel

        kernel = CoherenceKernel()

        if "graph" in arguments:
            coherence = kernel.evaluate_graph(arguments["graph"])
        elif "intent" in arguments:
            coherence = kernel.evaluate_intent(arguments["intent"])
        else:
            coherence = kernel.get_current_coherence()

        return ToolInvocationResult(
            success=True,
            output={"coherence_score": coherence, "timestamp": asyncio.get_event_loop().time()},
            execution_time_ms=0
        )

    async def _tool_transmit_rcp(self, arguments: Dict) -> ToolInvocationResult:
        """Tool handler: transmit_retrocausal."""
        from agi.system32.runtime.quantum.rcp_v2_engine import RetrocausalChannel8Bit

        channel = RetrocausalChannel8Bit()
        payload = arguments.get("payload", "")
        temporal_offset = arguments.get("target_temporal_offset", 0)

        # Encode payload for transmission
        encoded = channel.encode_payload(payload)
        fidelity = channel.transmit_byte(encoded, n_shots=20)[1]

        return ToolInvocationResult(
            success=True,
            output={
                "transmitted": True,
                "payload_hash": channel.hash_payload(payload),
                "fidelity": fidelity,
                "temporal_offset": temporal_offset
            },
            execution_time_ms=0
        )

    async def _tool_discover_peers(self, arguments: Dict) -> ToolInvocationResult:
        """Tool handler: discover_peers via DHT."""
        # Simulated DHT query - in production: use Substrate 321
        min_coh = arguments.get("min_coherence", 0.7)
        max_results = arguments.get("max_results", 10)

        # Return mock peers with coherence metadata
        peers = [
            {
                "onion_address": f"arkhe-peer-{i:03d}.onion",
                "coherence_score": 0.7 + (i * 0.03),
                "uptime_hours": 100 + i * 24,
                "capabilities": ["rcp_v2", "omni_core", "federation"]
            }
            for i in range(min(5, max_results))
            if 0.7 + (i * 0.03) >= min_coh
        ]

        return ToolInvocationResult(
            success=True,
            output={"peers": peers, "query_time_ms": 45},
            execution_time_ms=45
        )

    async def _tool_query_lfir(self, arguments: Dict) -> ToolInvocationResult:
        """Tool handler: query_lfir_graph."""
        query = arguments.get("query", "")
        max_depth = arguments.get("max_depth", 3)

        # Execute query against local LFIR graph
        # (simplified - in production: use full graph engine)
        results = {
            "query": query,
            "matches": [
                {"node_id": f"N{i:04d}", "type": "intent", "coherence": 0.8 + (i * 0.02)}
                for i in range(min(5, max_depth * 2))
            ],
            "total_matches": 5,
            "execution_time_ms": 12
        }

        return ToolInvocationResult(
            success=True,
            output=results,
            execution_time_ms=12
        )

    async def run(self):
        """Run the MCP server main loop."""
        await self.initialize()
        await self.transport.run()

    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("🛑 Shutting down ARKHE MCP Server...")
        self._running = False
        if self.transport:
            await self.transport.close()
        await self.context_manager.cleanup()
        logger.info("✅ Shutdown complete")
