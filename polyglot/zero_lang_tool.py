#!/usr/bin/env python3
"""
ARKHE OS Substrato ∞: Zero Language Canonical Tool
Registra o compilador Zero como ferramenta canônica,
integrando diagnóstico estruturado, planos de reparo e skills
ao ecossistema Arkhe.
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
    Cada subcomando do CLI Zero é um método registrado como ferramenta.
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

    async def zero_check(self, file_path: str, json_output: bool = True) -> dict:
        """Verifica um programa Zero com diagnóstico estruturado."""
        args = ["check"]
        if json_output:
            args.append("--json")
        args.append(file_path)
        result = await self._run_zero(args)

        if json_output and result["returncode"] == 0:
            try:
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
            except json.JSONDecodeError:
                pass

        return result

    async def zero_fix_plan(self, file_path: str) -> dict:
        """Gera plano de reparo estruturado para um arquivo Zero."""
        result = await self._run_zero(["fix", "--plan", "--json", file_path])
        if result["returncode"] == 0:
            try:
                plan = json.loads(result["stdout"])
                # Integrar com Predictive Auto-Remediation (Substrato 223)
                if self.tool_system:
                    await self.tool_system.invoke_tool("predictive_auto_remediation", {
                        "plan": plan,
                        "source": "zero_compiler",
                        "timestamp": time.time()
                    })
                return plan
            except json.JSONDecodeError:
                pass
        return result

    async def zero_build(self, file_path: str, target: str = "linux-musl-x64",
                         emit: str = "exe", profile: str = "fast") -> dict:
        """Compila um programa Zero para binário nativo."""
        out_dir = self.cwd / ".zero/out"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / Path(file_path).stem

        args = ["build", "--json", f"--emit", emit, f"--target", target,
                f"--profile", profile, file_path, "--out", str(out_file)]
        result = await self._run_zero(args)

        if result["returncode"] == 0:
            try:
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
            except json.JSONDecodeError:
                pass
        return result

    async def zero_skills_get(self) -> dict:
        """Obtém skills versionadas do Zero para alimentar o δ‑mem."""
        result = await self._run_zero(["skills", "get", "zero", "--full"])
        if result["returncode"] == 0:
            # Importar skills para o estado OSAM do δ‑mem
            if self.delta:
                await self.delta.write_experience("zero_skills", {
                    "content_hash": hashlib.sha3_256(
                        result["stdout"].encode()
                    ).hexdigest()[:16],
                    "timestamp": time.time()
                })
        return result

    async def zero_new_project(self, name: str, template: str = "cli") -> dict:
        """Cria um novo projeto Zero."""
        result = await self._run_zero(["new", template, name])
        if result["returncode"] == 0:
            if self.temporal:
                await self.temporal.anchor_event("zero_project_created", {
                    "name": name,
                    "template": template,
                    "timestamp": time.time()
                })
        return result

    def register_all_tools(self, tool_system):
        """Registra todas as operações Zero como ferramentas canônicas."""
        from tool_calling.canonical_tool_system import ToolDefinition

        tools = [
            ToolDefinition(
                tool_id="zero_check",
                name="zero check",
                description="Verify a Zero program with structured diagnostics",
                parameters_schema={"type": "object", "properties": {"file_path": {"type": "string"}}},
                handler=self.zero_check,
                agent_owner="build_sentinel",
                confidence_required=0.85
            ),
            ToolDefinition(
                tool_id="zero_fix_plan",
                name="zero fix --plan",
                description="Generate structured repair plan for a Zero file",
                parameters_schema={"type": "object", "properties": {"file_path": {"type": "string"}}},
                handler=self.zero_fix_plan,
                agent_owner="healing_sentinel",
                confidence_required=0.90
            ),
            ToolDefinition(
                tool_id="zero_build",
                name="zero build",
                description="Compile a Zero program to native binary",
                parameters_schema={"type": "object", "properties": {"file_path": {"type": "string"}}},
                handler=self.zero_build,
                agent_owner="build_sentinel",
                confidence_required=0.90
            ),
            ToolDefinition(
                tool_id="zero_skills_get",
                name="zero skills get",
                description="Get version-matched agent guidance from Zero CLI",
                parameters_schema={"type": "object", "properties": {}},
                handler=self.zero_skills_get,
                agent_owner="training_sentinel",
                confidence_required=0.80
            ),
            ToolDefinition(
                tool_id="zero_new_project",
                name="zero new",
                description="Create a new Zero project",
                parameters_schema={"type": "object", "properties": {"name": {"type": "string"}}},
                handler=self.zero_new_project,
                agent_owner="deployment_sentinel",
                confidence_required=0.85
            ),
        ]
        for tool_def in tools:
            tool_system.register_tool(tool_def)
        return len(tools)
