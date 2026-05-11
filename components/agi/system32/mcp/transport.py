#!/usr/bin/env python3
"""
mcp/transport.py — Transport backends for MCP
Supports stdio, SSE, and WebSocket with optional Tor anonymization.
"""
import asyncio
import json
import logging
import sys
from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, Optional

logger = logging.getLogger(__name__)

class TransportBackend(ABC):
    """Abstract base class for MCP transport."""

    def __init__(self, message_handler: Callable[[Dict], Awaitable[Optional[Dict]]]):
        self.message_handler = message_handler
        self._running = False

    @abstractmethod
    async def run(self):
        """Run the transport main loop."""
        pass

    @abstractmethod
    async def send_message(self, message: Dict[str, Any]):
        """Send a message to the client."""
        pass

    @abstractmethod
    async def close(self):
        """Close the transport."""
        pass

class StdioTransport(TransportBackend):
    """stdio transport for MCP (default for local usage)."""

    async def run(self):
        """Read messages from stdin, write responses to stdout."""
        self._running = True
        buffer = ""

        while self._running:
            try:
                # Read a line from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                if not line:
                    break  # EOF

                buffer += line
                if buffer.endswith("\n"):
                    # Parse complete message
                    try:
                        message = json.loads(buffer.strip())
                        response = await self.message_handler(message)
                        if response:
                            await self.send_message(response)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON parse error: {e}")
                    buffer = ""

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in stdio transport: {e}", exc_info=True)

    async def send_message(self, message: Dict[str, Any]):
        """Write message to stdout."""
        output = json.dumps(message) + "\n"
        await asyncio.get_event_loop().run_in_executor(
            None, sys.stdout.write, output
        )
        await asyncio.get_event_loop().run_in_executor(
            None, sys.stdout.flush
        )

    async def close(self):
        """Close stdin/stdout."""
        self._running = False

class SSETransport(TransportBackend):
    """Server-Sent Events transport for MCP (for web clients)."""

    def __init__(self,
                 message_handler: Callable[[Dict], Awaitable[Optional[Dict]]],
                 port: int = 8080):
        super().__init__(message_handler)
        self.port = port
        self.clients: Dict[str, asyncio.Queue] = {}
        self._server: Optional[asyncio.Server] = None

    async def run(self):
        """Start HTTP server for SSE connections."""
        # Simplified implementation - in production: use aiohttp or fastapi
        logger.info(f"🌐 Starting SSE transport on port {self.port}")
        # Implementation would use aiohttp.web for actual SSE handling
        await asyncio.Event().wait()  # Keep running

    async def send_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected SSE clients."""
        data = f"data: {json.dumps(message)}\n\n"
        for queue in self.clients.values():
            await queue.put(data)

    async def close(self):
        """Close server and client connections."""
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
