#!/usr/bin/env python3
"""
Basic MCP server example
"""
import asyncio
from agi.system32.mcp.server import ARKHEMCPServer, MCPServerConfig

async def main():
    config = MCPServerConfig(transport="stdio")
    server = ARKHEMCPServer(config)
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
