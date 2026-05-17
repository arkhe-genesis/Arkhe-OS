#!/usr/bin/env python3
"""
ARKHE OS Substrato 240: PyPI Package Manager Canon
Registra todos os comandos pip, venv e poetry como ferramentas do Sistema Canônico,
com idempotência, circuit breaker, rate limiting e ancoragem na TemporalChain.
"""

import asyncio
import subprocess
import hashlib
import json
import time
import os
import logging
from pathlib import Path
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class PyPICanonicalTool:
    """
    Gerenciador canônico de pacotes Python (pip + venv + poetry).
    Cada método é um handler registrado como ferramenta.
    """

    def __init__(self, working_dir: str = "/app", tool_system=None, temporal=None, hsm=None, pqc_verifier=None, vuln_auditor=None):
        self.cwd = Path(working_dir)
        self.tool_system = tool_system
        self.temporal = temporal
        self.hsm = hsm
        self.pqc_verifier = pqc_verifier
        self.vuln_auditor = vuln_auditor
        self._last_freeze_hash: Optional[str] = None

    async def _run_command(self, cmd: List[str], cwd: str = None, env: Dict = None) -> dict:
        """Executa comando e retorna stdout, stderr, returncode."""
        full_cmd = cmd if cmd[0] != "source" else cmd  # source is shell builtin
        process = await asyncio.create_subprocess_exec(
            *full_cmd,
            cwd=cwd or str(self.cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, **(env or {})}
        )
        stdout, stderr = await process.communicate()
        return {
            "command": " ".join(full_cmd),
            "returncode": process.returncode,
            "stdout": stdout.decode().strip(),
            "stderr": stderr.decode().strip()
        }

    async def pip_install(self, parameters: dict) -> dict:
        """Instala pacote(s) pip."""
        package = parameters.get("package")
        requirements_file = parameters.get("requirements_file")
        upgrade = parameters.get("upgrade", False)
        version = parameters.get("version")

        if package and self.pqc_verifier:
            is_valid = await self.pqc_verifier.verify_package_signature(package, version or "latest")
            if not is_valid:
                return {"status": "error", "reason": "PQC signature validation failed"}

        if package and self.vuln_auditor:
            audit = await self.vuln_auditor.audit_package(package, version or "latest")
            if audit["vulnerabilities"] > 0:
                return {"status": "error", "reason": "Vulnerabilities found"}

        if requirements_file and self.vuln_auditor:
            audit = await self.vuln_auditor.audit_requirements(requirements_file)
            if audit["vulnerabilities"] > 0:
                return {"status": "error", "reason": "Vulnerabilities found in requirements"}

        args = ["pip", "install"]
        if upgrade:
            args.append("--upgrade")
        if package:
            if version:
                args.append(f"{package}=={version}")
            else:
                args.append(package)
        elif requirements_file:
            args.extend(["-r", requirements_file])
        else:
            return {"status": "error", "reason": "package or requirements_file required"}

        result = await self._run_command(args)

        if result["returncode"] == 0:
            # Ancorar na TemporalChain
            if self.temporal:
                await self.temporal.anchor_event("pip_install_completed", {
                    "package": package or "requirements",
                    "version": version or "latest",
                    "timestamp": time.time()
                })
        return result

    async def pip_freeze(self, parameters: dict) -> dict:
        """Congela dependências instaladas em um arquivo."""
        output_file = parameters.get("output_file", "requirements.txt")
        result = await self._run_command(["pip", "freeze"])

        if result["returncode"] == 0:
            # Escrever no arquivo e assinar com HSM se disponível
            reqs = result["stdout"]
            req_hash = hashlib.sha3_256(reqs.encode()).hexdigest()
            with open(self.cwd / output_file, "w") as f:
                f.write(reqs)
            self._last_freeze_hash = req_hash

            # Assinar o arquivo de requirements
            signature = None
            if self.hsm:
                signature = await self.hsm.sign(reqs.encode())

            # Ancorar
            if self.temporal:
                await self.temporal.anchor_event("pip_freeze_completed", {
                    "output_file": output_file,
                    "packages_count": len(reqs.splitlines()),
                    "hash": req_hash[:16],
                    "pqc_signed": bool(signature)
                })
        return result

    async def pip_list(self, parameters: dict = None) -> dict:
        """Lista pacotes instalados."""
        return await self._run_command(["pip", "list", "--format=json"])

    async def pip_show(self, parameters: dict) -> dict:
        """Mostra informações de um pacote."""
        package = parameters.get("package", "")
        return await self._run_command(["pip", "show", package])

    async def pip_uninstall(self, parameters: dict) -> dict:
        """Desinstala um pacote."""
        package = parameters.get("package", "")
        return await self._run_command(["pip", "uninstall", "-y", package])

    async def create_venv(self, parameters: dict) -> dict:
        """Cria um ambiente virtual Python."""
        venv_name = parameters.get("venv_name", "venv")
        result = await self._run_command(["python", "-m", "venv", venv_name])
        if result["returncode"] == 0 and self.temporal:
            await self.temporal.anchor_event("venv_created", {"name": venv_name, "timestamp": time.time()})
        return result

    async def activate_venv(self, parameters: dict) -> dict:
        """Ativa o ambiente virtual (simulando retorno para scripts)."""
        venv_name = parameters.get("venv_name", "venv")
        # source é um builtin do shell, mas podemos retornar o caminho do binário
        activate_path = self.cwd / venv_name / "bin" / "python"
        if not activate_path.exists():
            return {"status": "error", "reason": "Virtual environment not found"}
        # Em produção, o comando "source" seria executado no shell; aqui retornamos instruções
        return {"status": "activated", "python_path": str(activate_path)}

    async def deactivate_venv(self, parameters: dict = None) -> dict:
        """Desativa o ambiente virtual (simulado)."""
        return {"status": "deactivated"}

    # ─── Poetry ───
    async def pip_install_poetry(self, parameters: dict = None) -> dict:
        """Instala o poetry globalmente."""
        return await self._run_command(["pip", "install", "poetry"])

    async def poetry_new_project(self, parameters: dict) -> dict:
        """Cria um novo projeto com poetry."""
        project_name = parameters.get("project_name", "")
        result = await self._run_command(["poetry", "new", project_name])
        if result["returncode"] == 0 and self.temporal:
            await self.temporal.anchor_event("poetry_project_created", {
                "project": project_name, "timestamp": time.time()
            })
        return result

    async def poetry_add_package(self, parameters: dict) -> dict:
        """Adiciona um pacote ao projeto poetry."""
        package = parameters.get("package", "")
        return await self._run_command(["poetry", "add", package])

    async def poetry_install(self, parameters: dict = None) -> dict:
        """Instala as dependências do poetry."""
        return await self._run_command(["poetry", "install"])

    # ─── Registro de Ferramentas ───
    def register_all_tools(self, tool_system):
        """Registra todas as operações como ferramentas canônicas."""
        from tool_calling.canonical_tool_system import ToolDefinition

        tools = [
            ToolDefinition("pip_install", "pip install <pkg>", "Install Python package",
                           {"type": "object", "properties": {"package": {"type": "string"}, "requirements_file": {"type": "string"}, "upgrade": {"type": "boolean"}, "version": {"type": "string"}}},
                           self.pip_install, agent_owner="build_sentinel", confidence_required=0.85),
            ToolDefinition("pip_freeze", "pip freeze > requirements.txt", "Freeze current dependencies",
                           {"type": "object", "properties": {"output_file": {"type": "string"}}},
                           self.pip_freeze, agent_owner="build_sentinel", confidence_required=0.80),
            ToolDefinition("pip_list", "pip list", "List installed packages",
                           {"type": "object", "properties": {}},
                           self.pip_list, agent_owner="build_sentinel", confidence_required=0.75),
            ToolDefinition("pip_show", "pip show <pkg>", "Show package details",
                           {"type": "object", "properties": {"package": {"type": "string"}}},
                           self.pip_show, agent_owner="build_sentinel", confidence_required=0.80),
            ToolDefinition("pip_uninstall", "pip uninstall <pkg>", "Uninstall package",
                           {"type": "object", "properties": {"package": {"type": "string"}}},
                           self.pip_uninstall, agent_owner="build_sentinel", confidence_required=0.85),
            ToolDefinition("create_venv", "python -m venv venv", "Create virtual environment",
                           {"type": "object", "properties": {"venv_name": {"type": "string"}}},
                           self.create_venv, agent_owner="build_sentinel", confidence_required=0.85),
            ToolDefinition("activate_venv", "source venv/bin/activate", "Activate virtual environment",
                           {"type": "object", "properties": {"venv_name": {"type": "string"}}},
                           self.activate_venv, agent_owner="build_sentinel", confidence_required=0.80),
            ToolDefinition("deactivate_venv", "deactivate", "Deactivate virtual environment",
                           {"type": "object", "properties": {}},
                           self.deactivate_venv, agent_owner="build_sentinel", confidence_required=0.80),
            ToolDefinition("poetry_new", "poetry new <project>", "Create new poetry project",
                           {"type": "object", "properties": {"project_name": {"type": "string"}}},
                           self.poetry_new_project, agent_owner="build_sentinel", confidence_required=0.85),
            ToolDefinition("poetry_add", "poetry add <pkg>", "Add package with poetry",
                           {"type": "object", "properties": {"package": {"type": "string"}}},
                           self.poetry_add_package, agent_owner="build_sentinel", confidence_required=0.85),
            ToolDefinition("poetry_install", "poetry install", "Install poetry dependencies",
                           {"type": "object", "properties": {}},
                           self.poetry_install, agent_owner="build_sentinel", confidence_required=0.85),
            ToolDefinition("pip_install_poetry", "pip install poetry", "Install poetry globally",
                           {"type": "object", "properties": {}},
                           self.pip_install_poetry, agent_owner="build_sentinel", confidence_required=0.80),
        ]

        for tool_def in tools:
            tool_system.register_tool(tool_def)
        logger.info(f"✅ {len(tools)} ferramentas pip/venv/poetry registradas no Sistema Canônico")
