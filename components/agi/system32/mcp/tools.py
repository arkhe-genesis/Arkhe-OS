#!/usr/bin/env python3
"""
mcp/tools.py — Tool Registry for ARKHE OS MCP
Registers and executes tools with Φ_C-based access control.
"""
import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union
import json

@dataclass
class ToolDefinition:
    """Definition of an MCP tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[[Dict], Awaitable["ToolInvocationResult"]]
    min_coherence: float = 0.0  # Minimum Φ_C required to invoke
    max_invocations_per_minute: Optional[int] = None  # Rate limiting

@dataclass
class ToolInvocationResult:
    """Result of a tool invocation."""
    success: bool
    output: Any
    execution_time_ms: float
    error: Optional[str] = None
    attestation: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "output": self.output,
            "execution_time_ms": self.execution_time_ms,
            "error": self.error,
            "attestation": self.attestation
        }

class ToolRegistry:
    """Registry for MCP tools with coherence-based access control."""

    def __init__(self, coherence_threshold: float = 0.7):
        self.tools: Dict[str, ToolDefinition] = {}
        self.coherence_threshold = coherence_threshold
        self.invocation_counts: Dict[str, List[float]] = {}  # tool_name -> [timestamps]

    def register_tool(self,
                     name: str,
                     description: str,
                     input_schema: Dict[str, Any],
                     handler: Callable[[Dict], Awaitable[ToolInvocationResult]],
                     min_coherence: float = 0.0,
                     max_invocations_per_minute: Optional[int] = None):
        """Register a new tool."""
        self.tools[name] = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler,
            min_coherence=min_coherence,
            max_invocations_per_minute=max_invocations_per_minute
        )

    def list_tools(self) -> List[ToolDefinition]:
        """List all registered tools."""
        return list(self.tools.values())

    async def invoke_tool(self,
                         tool_name: str,
                         arguments: Dict[str, Any],
                         current_coherence: Optional[float] = None) -> ToolInvocationResult:
        """Invoke a tool with coherence and rate limiting checks."""
        if tool_name not in self.tools:
            return ToolInvocationResult(
                success=False,
                output=None,
                execution_time_ms=0,
                error=f"Tool not found: {tool_name}"
            )

        tool = self.tools[tool_name]

        # Check coherence threshold
        if current_coherence is not None and current_coherence < tool.min_coherence:
            return ToolInvocationResult(
                success=False,
                output=None,
                execution_time_ms=0,
                error=f"Coherence {current_coherence:.3f} below tool threshold {tool.min_coherence}"
            )

        # Check rate limit
        if tool.max_invocations_per_minute:
            if not self._check_rate_limit(tool_name, tool.max_invocations_per_minute):
                return ToolInvocationResult(
                    success=False,
                    output=None,
                    execution_time_ms=0,
                    error="Rate limit exceeded"
                )

        # Execute tool with timing
        start_time = time.time()
        try:
            result = await tool.handler(arguments)
            execution_time = (time.time() - start_time) * 1000
            result.execution_time_ms = execution_time
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ToolInvocationResult(
                success=False,
                output=None,
                execution_time_ms=execution_time,
                error=str(e)
            )

    def _check_rate_limit(self, tool_name: str, max_per_minute: int) -> bool:
        """Check if tool invocation is within rate limit."""
        now = time.time()
        window_start = now - 60

        # Clean old invocations
        if tool_name in self.invocation_counts:
            self.invocation_counts[tool_name] = [
                ts for ts in self.invocation_counts[tool_name]
                if ts > window_start
            ]
        else:
            self.invocation_counts[tool_name] = []

        # Check limit
        if len(self.invocation_counts[tool_name]) >= max_per_minute:
            return False

        # Record this invocation
        self.invocation_counts[tool_name].append(now)
        return True
