# =========================================================
# Servidor MCP - Model Context Protocol
# Substrato 230
# =========================================================
import json, hashlib, time
from typing import Dict, Any, Callable

class MCPServer:
    """Servidor MCP base com registro dinamico de ferramentas."""

    def __init__(self, name: str):
        self.name = name
        self.tools: Dict[str, Callable] = {}
        self.request_count = 0
        self.start_time = time.time()

    def register_tool(self, name: str, func: Callable, description: str = ""):
        self.tools[name] = {
            "function": func,
            "description": description,
            "call_count": 0
        }

    def handle_request(self, method: str, params: Dict) -> Dict:
        self.request_count += 1
        request_id = params.get("id", self.request_count)

        if method == "tool/list":
            return {
                "jsonrpc": "2.0",
                "result": {"tools": [
                    {"name": name, "description": info["description"]}
                    for name, info in self.tools.items()
                ]},
                "id": request_id
            }

        elif method == "tool/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name not in self.tools:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"},
                    "id": request_id
                }

            try:
                self.tools[tool_name]["call_count"] += 1
                result = self.tools[tool_name]["function"](arguments)
                return {
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": request_id
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": str(e)},
                    "id": request_id
                }

        return {
            "jsonrpc": "2.0",
            "error": {"code": -32600, "message": f"Unknown method '{method}'"},
            "id": request_id
        }

    def get_stats(self) -> dict:
        uptime = time.time() - self.start_time
        return {
            "server_name": self.name,
            "uptime_seconds": uptime,
            "total_requests": self.request_count,
            "tools_registered": len(self.tools),
            "tool_stats": {
                name: {"calls": info["call_count"]}
                for name, info in self.tools.items()
            }
        }
