#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
server.py — ArkheMCPServer
Servidor MCP que encapsula o Safe Core da Arkhe (Guardião Atratora, MA-S2, TemporalChain, Φ_C Bus).
Transportes suportados: stdio e http-sse
"""

import sys
import json
import asyncio
import logging
import importlib.util
import os
from typing import Dict, Any, Optional

# Emulação do pacote arkhe na raiz para este contexto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from arkhe.chain.temporal_chain import TemporalChain
from arkhe.chain.inventory import Inventory
from arkhe.security.threat_database import ThreatDatabase, Finding, AttackPath
from arkhe.security.guardian_attractor import GuardianAttractor
from arkhe.orchestrator.fleet_orchestrator import FleetOrchestrator

# Load 9008 substrate dynamically
spec = importlib.util.spec_from_file_location("ma_s2_engine", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "substrates", "9008_ma_s2", "ma_s2_engine.py")))
ma_s2_engine_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ma_s2_engine_module)
MA_S2_Engine = ma_s2_engine_module.MA_S2_Engine

try:
    from .tools import register_tools
    from .resources import register_resources
    from .prompts import register_prompts
except ImportError:
    # Handle before tools are created
    register_tools = lambda server: {}
    register_resources = lambda server: {}
    register_prompts = lambda server: {}

logger = logging.getLogger("ArkheMCPServer")

class ArkheMCPServer:
    """
    Servidor MCP (Model Context Protocol) para o Safe Core.
    """
    def __init__(self, transport: str = "stdio"):
        self.transport = transport
        self.temporal_chain = TemporalChain()
        self.threat_db = ThreatDatabase()
        self.guardian = GuardianAttractor(self.threat_db)
        self.inventory = Inventory(self.temporal_chain)
        self.orchestrator = FleetOrchestrator(self.temporal_chain)
        self.ma_s2_engine = MA_S2_Engine(
            self.temporal_chain, self.guardian, self.inventory, self.orchestrator
        )

        self.tools = register_tools(self)
        self.resources = register_resources(self)
        self.prompts = register_prompts(self)

    async def run_stdio(self):
        """Executa servidor via stdio (para Claude Desktop / Cursor)."""
        logger.info("Iniciando ArkheMCPServer em modo stdio")
        for line in sys.stdin:
            try:
                if not line.strip(): continue
                req = json.loads(line)
                resp = await self.handle_request(req)
                print(json.dumps(resp))
                sys.stdout.flush()
            except Exception as e:
                logger.error(f"Erro processando request: {e}")
                err_resp = {"error": str(e)}
                print(json.dumps(err_resp))
                sys.stdout.flush()

    async def handle_request(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """Processa as requisicoes MCP."""
        method = req.get("method")
        params = req.get("params", {})
        req_id = req.get("id")

        if method == "initialize":
            return {
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": "SafeCore-MCP",
                        "version": "1.0.0"
                    },
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "resources": {"subscribe": True},
                        "prompts": {"listChanged": True}
                    }
                }
            }

        # Tools
        if method == "tools/list":
            return {"id": req_id, "result": {"tools": [t.to_dict() for t in self.tools.values()]}}
        if method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            if tool_name in self.tools:
                result = await self.tools[tool_name].execute(tool_args)
                return {"id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result)}]}}
            else:
                return {"id": req_id, "error": {"code": -32601, "message": "Tool not found"}}

        # Resources
        if method == "resources/list":
            return {"id": req_id, "result": {"resources": [r.to_dict() for r in self.resources.values()]}}
        if method == "resources/read":
            uri = params.get("uri")
            if uri in self.resources:
                content = await self.resources[uri].read()
                return {"id": req_id, "result": {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(content)}]}}
            else:
                return {"id": req_id, "error": {"code": -32602, "message": "Resource not found"}}

        # Prompts
        if method == "prompts/list":
            return {"id": req_id, "result": {"prompts": [p.to_dict() for p in self.prompts.values()]}}
        if method == "prompts/get":
            name = params.get("name")
            args = params.get("arguments", {})
            if name in self.prompts:
                messages = await self.prompts[name].get(args)
                return {"id": req_id, "result": {"description": self.prompts[name].description, "messages": messages}}
            else:
                return {"id": req_id, "error": {"code": -32602, "message": "Prompt not found"}}

        return {"id": req_id, "error": {"code": -32601, "message": "Method not found"}}

if __name__ == "__main__":
    server = ArkheMCPServer()
    try:
        asyncio.run(server.run_stdio())
    except KeyboardInterrupt:
        pass
