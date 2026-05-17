#!/usr/bin/env python3
"""
ARKHE OS Substrato 232: NPM Package Manager Canon
Registra todos os comandos npm como ferramentas do Sistema Canônico,
com idempotência, circuit breaker e ancoragem na TemporalChain.
"""

import asyncio
import subprocess
import hashlib
import json
import time
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class NPMPackageManager:
    """
    Gerenciador canônico de pacotes Node.js.
    Cada método é um handler registrado como ferramenta.
    """

    def __init__(self, working_dir: str = "/app", tool_system=None, temporal=None):
        self.cwd = Path(working_dir)
        self.tool_system = tool_system
        self.temporal = temporal
        self._last_audit_hash: Optional[str] = None

    async def _run_npm(self, args: list, cwd: str = None) -> dict:
        """Executa comando npm e retorna stdout, stderr, returncode."""
        cmd = ["npm"] + args
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd or str(self.cwd),
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

    async def npm_init(self, scope: str = "@arkhe") -> dict:
        """Inicializa um novo package.json com escopo canônico."""
        result = await self._run_npm(["init", "-y", f"--scope={scope}"])
        # Ancorar na TemporalChain
        if self.temporal and result["returncode"] == 0:
            await self.temporal.anchor_event("npm_init", {"scope": scope, "timestamp": time.time()})
        return result

    async def npm_install(self, package: str = "", save_dev: bool = False) -> dict:
        """Instala um pacote (ou todos do package.json)."""
        args = ["install"]
        if save_dev:
            args.append("--save-dev")
        if package:
            args.append(package)
        result = await self._run_npm(args)
        if self.temporal and result["returncode"] == 0:
            await self.temporal.anchor_event("npm_install", {"package": package, "save_dev": save_dev, "timestamp": time.time()})
        return result

    async def npm_run_script(self, script: str) -> dict:
        """Executa um script definido no package.json (start, build, test)."""
        result = await self._run_npm(["run", script])
        if self.temporal and result["returncode"] == 0:
            await self.temporal.anchor_event("npm_run", {"script": script, "timestamp": time.time()})
        return result

    async def npm_update(self, package: str = None) -> dict:
        """Atualiza pacotes para a versão mais recente permitida."""
        args = ["update"]
        if package:
            args.append(package)
        result = await self._run_npm(args)
        return result

    async def npm_outdated(self) -> dict:
        """Lista pacotes desatualizados."""
        result = await self._run_npm(["outdated", "--json"])
        return result

    async def npm_audit(self, fix: bool = False) -> dict:
        """Executa auditoria de segurança (npm audit)."""
        args = ["audit", "--json"]
        if fix:
            args.append("fix")
        result = await self._run_npm(args)
        if fix and result["returncode"] == 0:
            # Ancorar correção
            if self.temporal:
                await self.temporal.anchor_event("npm_audit_fix", {"timestamp": time.time()})
        return result

    async def npm_list(self) -> dict:
        """Lista todos os pacotes instalados."""
        result = await self._run_npm(["list", "--depth=0", "--json"])
        return result

    async def npm_cache_clean(self) -> dict:
        """Limpa o cache do npm."""
        result = await self._run_npm(["cache", "clean", "--force"])
        return result

    async def npx_create_next_app(self, app_name: str) -> dict:
        """Cria uma aplicação Next.js via npx create-next-app."""
        # Alternativa: usar subprocess.run para npx
        process = await asyncio.create_subprocess_exec(
            "npx", "create-next-app", app_name, "--use-npm",
            cwd=str(self.cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        result = {
            "command": f"npx create-next-app {app_name}",
            "returncode": process.returncode,
            "stdout": stdout.decode().strip(),
            "stderr": stderr.decode().strip()
        }
        if self.temporal and result["returncode"] == 0:
            await self.temporal.anchor_event("next_app_created", {"app_name": app_name, "timestamp": time.time()})
        return result

    def register_all_tools(self, tool_system):
        """Registra todas as operações como ferramentas canônicas."""
        from tool_calling.canonical_tool_system import ToolDefinition

        tools = [
            ToolDefinition("npm_init", "npm init", "Initialize a new Node.js project", {"type": "object"}, self.npm_init, agent_owner="build_sentinel"),
            ToolDefinition("npm_install", "npm install", "Install Node.js packages", {"type": "object"}, self.npm_install, agent_owner="build_sentinel"),
            ToolDefinition("npm_run_script", "npm run <script>", "Run an npm script (start, build, test)", {"type": "object"}, self.npm_run_script, agent_owner="build_sentinel"),
            ToolDefinition("npm_update", "npm update", "Update Node.js packages", {"type": "object"}, self.npm_update, agent_owner="build_sentinel"),
            ToolDefinition("npm_outdated", "npm outdated", "Check for outdated packages", {"type": "object"}, self.npm_outdated, agent_owner="build_sentinel"),
            ToolDefinition("npm_audit", "npm audit", "Audit project dependencies for vulnerabilities", {"type": "object"}, self.npm_audit, agent_owner="security_sentinel"),
            ToolDefinition("npm_audit_fix", "npm audit fix", "Fix audit vulnerabilities", {"type": "object"}, self.npm_audit, agent_owner="security_sentinel"),
            ToolDefinition("npm_list", "npm list", "List installed packages", {"type": "object"}, self.npm_list, agent_owner="build_sentinel"),
            ToolDefinition("npm_cache_clean", "npm cache clean", "Clear npm cache", {"type": "object"}, self.npm_cache_clean, agent_owner="build_sentinel"),
            ToolDefinition("npx_create_next_app", "npx create-next-app", "Create a Next.js application", {"type": "object"}, self.npx_create_next_app, agent_owner="deployment_sentinel", confidence_required=0.95),
        ]

        for tool_def in tools:
            tool_system.register_tool(tool_def)
        logger.info(f"✅ {len(tools)} ferramentas npm registradas no Sistema Canônico")
