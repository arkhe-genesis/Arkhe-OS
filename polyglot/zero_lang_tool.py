#!/usr/bin/env python3
"""
ARKHE OS Substrato ∞: Zero Language Canonical Tool
Canon: ∞.Ω.∇+++.∞.zero
Integra o compilador Zero como ferramenta canônica,
ancorando diagnóstico, reparo e skills ao ecossistema Arkhe.
"""

import asyncio
import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional

class ZeroLangTool:
    """
    Ferramenta canônica para o compilador Zero.
    Cada subcomando é registrado como ToolDefinition no sistema Arkhe.
    """

    def __init__(self, zero_bin: str = "zero", working_dir: str = "/app",
                 tool_system=None, temporal=None, delta_mem=None):
        self.zero_bin = zero_bin
        self.cwd = Path(working_dir)
        self.tool_system = tool_system
        self.temporal = temporal
        self.delta = delta_mem

    async def _run_zero(self, args: list) -> dict:
        """Executa comando zero e retorna stdout, stderr, returncode."""
        cmd = [self.zero_bin] + args
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self.cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return {
            "command": " ".join(cmd),
            "returncode": process.returncode,
            "stdout": stdout.decode().strip(),
            "stderr": stderr.decode().strip()
        }

    async def zero_check(self, parameters: dict) -> dict:
        """Verifica um programa Zero com diagnóstico estruturado (BEAVer-compatible)."""
        file_path = parameters.get("file_path")
        json_output = parameters.get("json_output", True)
        args = ["check"]
        if json_output:
            args.append("--json")
        args.append(file_path)
        result = await self._run_zero(args)

        if json_output and result["returncode"] == 0:
            diagnostics = json.loads(result["stdout"])
            # Ancorar diagnóstico na TemporalChain
            if self.temporal:
                await self.temporal.anchor_event("zero_check_completed", {
                    "file": file_path,
                    "ok": diagnostics.get("ok", False),
                    "diagnostic_count": len(diagnostics.get("diagnostics", [])),
                    "timestamp": time.time()
                })
            # Registrar no δ‑mem para contexto de compilação
            if self.delta:
                await self.delta.write_experience("zero_build", {
                    "file": file_path,
                    "ok": diagnostics.get("ok", False),
                    "timestamp": time.time()
                })
            return diagnostics

        return result

    async def zero_fix_plan(self, parameters: dict) -> dict:
        """Gera plano de reparo estruturado para Auto-Remediation."""
        file_path = parameters.get("file_path")
        result = await self._run_zero(["fix", "--plan", "--json", file_path])
        if result["returncode"] == 0:
            plan = json.loads(result["stdout"])
            # Integrar com Predictive Auto-Remediation (Substrato 223)
            if self.tool_system:
                from tool_calling.canonical_tool_system import ToolCallRequest
                import uuid
                await self.tool_system.invoke_tool(ToolCallRequest(
                    call_id=str(uuid.uuid4()),
                    tool_id="predictive_auto_remediation",
                    parameters={
                        "plan": plan,
                        "source": "zero_compiler",
                        "timestamp": time.time()
                    }
                ))
            return plan
        return result

    async def zero_build(self, parameters: dict) -> dict:
        """Compila um programa Zero para binário nativo."""
        file_path = parameters.get("file_path")
        target = parameters.get("target", "linux-musl-x64")
        emit = parameters.get("emit", "exe")
        profile = parameters.get("profile", "fast")

        out_dir = self.cwd / ".zero/out"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / Path(file_path).stem

        args = ["build", "--json", f"--emit", emit, f"--target", target,
                f"--profile", profile, file_path, "--out", str(out_file)]
        result = await self._run_zero(args)

        if result["returncode"] == 0:
            build_info = json.loads(result["stdout"])
            # Ancorar build na TemporalChain
            if self.temporal:
                await self.temporal.anchor_event("zero_build_completed", {
                    "file": file_path,
                    "target": target,
                    "profile": profile,
                    "output": str(out_file),
                    "size_bytes": build_info.get("sizeBreakdown", {}).get("total", 0),
                    "timestamp": time.time()
                })
            return build_info
        return result

    async def zero_skills_get(self, parameters: dict) -> dict:
        """Obtém skills versionadas do Zero para alimentar o δ‑mem Oracle."""
        result = await self._run_zero(["skills", "get", "zero", "--full"])
        if result["returncode"] == 0:
            if self.delta:
                await self.delta.write_experience("zero_skills", {
                    "content_hash": hashlib.sha3_256(
                        result["stdout"].encode()
                    ).hexdigest()[:16],
                    "timestamp": time.time()
                })
        return result

    def register_all_tools(self, tool_system):
        """Registra todas as operações Zero como ferramentas canônicas."""
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
        from tool_calling.canonical_tool_system import ToolDefinition

        tools = [
            ToolDefinition("zero_check", "zero check",
                          "Verify a Zero program with structured diagnostics",
                          {"type": "object", "properties": {"file_path": {"type": "string"}, "json_output": {"type": "boolean"}}},
                          self.zero_check, agent_owner="build_sentinel",
                          confidence_required=0.85),
            ToolDefinition("zero_fix_plan", "zero fix --plan",
                          "Generate structured repair plan for a Zero file",
                          {"type": "object", "properties": {"file_path": {"type": "string"}}},
                          self.zero_fix_plan, agent_owner="healing_sentinel",
                          confidence_required=0.90),
            ToolDefinition("zero_build", "zero build",
                          "Compile a Zero program to native binary",
                          {"type": "object", "properties": {"file_path": {"type": "string"}, "target": {"type": "string"}, "emit": {"type": "string"}, "profile": {"type": "string"}}},
                          self.zero_build, agent_owner="build_sentinel",
                          confidence_required=0.90),
            ToolDefinition("zero_skills_get", "zero skills get",
                          "Get version-matched agent guidance from Zero CLI",
                          {"type": "object", "properties": {}},
                          self.zero_skills_get, agent_owner="training_sentinel",
                          confidence_required=0.80),
        ]
        for tool_def in tools:
            tool_system.register_tool(tool_def)
        return len(tools)
