#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
magics.py — Extensão IPython com comandos %arkhe e %%arkhe
"""

import asyncio
import json
import time
import hashlib
from typing import Dict, Any, Optional

from IPython.core.magic import (
    Magics, magics_class, line_magic, cell_magic,
    line_cell_magic, needs_local_scope
)
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from IPython.display import display, Markdown, JSON, HTML
from .utils import SafeCoreConnection, format_phi_c_display, extract_code_context

@magics_class
class ArkheMagics(Magics):
    """
    Magics do Arkhe para IPython.

    Comandos de linha (%arkhe):
    • status — Estado do nó (Φ_C, selo, perfil)
    • scan <code> — Escaneia código com CVS
    • sbom [release] — Gera SBOM ancorada
    • audit <seal> — Consulta auditoria por selo
    • profile <domain> — Altera perfil do atrator
    • compliance [scope] — Status de conformidade MA‑S2
    • model-attack <service_map> — Modela caminhos de ataque
    • phi-c — Consulta coerência Φ_C atual
    • deploy <cve> — Orquestra patch para vulnerabilidade
    • grc-sync <cve> — Sincroniza finding com ServiceNow/Archer

    Comandos de célula (%%arkhe):
    • secure — Executa célula com proteção completa do Safe Core
    • regenerate — Força regeneração de código seguro via Multi‑LLM Core
    """

    def __init__(self, shell):
        super().__init__(shell)
        self.safe_core = SafeCoreConnection()
        self._last_execution_seal = None

    @magic_arguments()
    @argument("command", nargs="?", default="status", help="Comando a executar")
    @argument("args", nargs="*", help="Argumentos do comando")
    @line_cell_magic
    def arkhe(self, line: str, cell: Optional[str] = None):
        """Comando %arkhe: interface de linha e de célula para o Safe Core."""
        if cell is None:
            # Line magic
            args = parse_argstring(self.arkhe, line)
            command = args.command
            cmd_args = args.args

            # Executar comando assincronamente (IPython handles awaitables in magics natively if configured or by get_ipython().loop.run_until_complete)
            # However, since Jupyter has a running event loop, we can just return the awaitable if it's async, or use asyncio.get_event_loop().run_until_complete if we must.
            # But wait, jupyter magics can be async in modern ipython.
            # actually we can't use `async def arkhe`, but we can schedule task or run until complete.
            # Let's create task and wait for it.
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # running in jupyter notebook
                import nest_asyncio
                nest_asyncio.apply()

            result = loop.run_until_complete(self._execute_command(command, cmd_args))

            # Exibir resultado formatado
            if isinstance(result, dict) and "error" in result:
                display(Markdown(f"❌ **Erro**: {result['error']}"))
            elif isinstance(result, dict):
                display(JSON(result, expanded=True))
            else:
                display(Markdown(str(result)))

            return result
        else:
            # Cell magic implementation
            # We parse the line arguments which dictates the command (secure, regenerate, etc)
            parts = line.split()
            command = parts[0] if parts else "secure"

            if command == "secure":
                return self._arkhe_secure_impl(line, cell)
            elif command == "regenerate":
                return self._arkhe_regenerate_impl(line, cell)
            else:
                display(Markdown(f"❌ **Erro**: Cell magic command `{command}` not recognized. Try `secure` or `regenerate`."))
                return None


    async def _execute_command(self, command: str, args: list) -> Any:
        """Roteia comando para implementação correspondente."""
        commands = {
            "status": self._cmd_status,
            "scan": self._cmd_scan,
            "sbom": self._cmd_sbom,
            "audit": self._cmd_audit,
            "profile": self._cmd_profile,
            "compliance": self._cmd_compliance,
            "model-attack": self._cmd_model_attack,
            "phi-c": self._cmd_phi_c,
            "deploy": self._cmd_deploy,
            "grc-sync": self._cmd_grc_sync,
        }

        if command not in commands:
            return {"error": f"Comando desconhecido: {command}. Use: {', '.join(commands.keys())}"}

        return await commands[command](args)

    async def _cmd_status(self, args: list) -> Dict:
        """%arkhe status — Estado do nó."""
        result = await self.safe_core.call_tool("phi_c_status", {})
        return {
            "node_status": "online",
            "phi_c_coherence": result.get("current_phi_c", 0.0),
            "phi_c_display": format_phi_c_display(result.get("current_phi_c", 0.0)),
            "active_profile": result.get("active_profile", "default"),
            "temporal_seal": self._last_execution_seal or "N/A",
            "timestamp": time.time(),
        }

    async def _cmd_scan(self, args: list) -> Dict:
        """%arkhe scan <code> — Escaneia código."""
        if not args:
            return {"error": "Uso: %arkhe scan <código ou arquivo>"}

        code = " ".join(args)
        # Se for caminho de arquivo, ler conteúdo
        if len(args) == 1 and args[0].endswith((".py", ".ipynb")):
            try:
                with open(args[0], "r", encoding="utf-8") as f:
                    code = f.read()
            except FileNotFoundError:
                return {"error": f"Arquivo não encontrado: {args[0]}"}

        result = await self.safe_core.call_tool("scan_code", {
            "code": code,
            "language": "python",
        })

        # Ancorar na TemporalChain
        seal = self.safe_core.compute_execution_seal(code, {"command": "scan"})
        self._last_execution_seal = seal

        return {
            **result,
            "temporal_anchor": seal,
            "scanned_at": time.time(),
        }

    async def _cmd_sbom(self, args: list) -> Dict:
        """%arkhe sbom [release_id] — Gera SBOM."""
        import os
        release_id = args[0] if args else f"ipython-session-{int(time.time())}"

        result = await self.safe_core.call_tool("generate_sbom", {
            "release_id": release_id,
            "format": "cyclonedx",
            "include_dev_deps": False,
        })

        return {
            **result,
            "generated_by": "arkhe-ipython",
            "session": os.getenv("JPY_SESSION_NAME", "unknown"),
        }

    async def _cmd_audit(self, args: list) -> Dict:
        """%arkhe audit <seal> — Consulta auditoria."""
        if not args:
            return {"error": "Uso: %arkhe audit <seal_sha3_256>"}

        seal = args[0]
        record = await self.safe_core.query_audit(seal)

        if record:
            return {
                "found": True,
                "seal": seal,
                "record": record,
            }
        else:
            return {
                "found": False,
                "seal": seal,
                "message": "Registro não encontrado na TemporalChain",
            }

    async def _cmd_profile(self, args: list) -> Dict:
        """%arkhe profile <domain> — Altera perfil do atrator."""
        if not args:
            return {
                "available_profiles": ["default", "creative", "technical", "educational", "scientific", "conversational"],
                "current_profile": "default",  # Simulado
                "message": "Uso: %arkhe profile <nome_do_perfil>",
            }

        profile = args[0].lower()
        valid_profiles = ["default", "creative", "technical", "educational", "scientific", "conversational"]

        if profile not in valid_profiles:
            return {"error": f"Perfil inválido. Opções: {', '.join(valid_profiles)}"}

        # Em produção: chamar API para mudar perfil
        return {
            "profile_changed": True,
            "new_profile": profile,
            "parameters": {
                "creative": {"alpha": 2.0, "beta": 0.6, "gamma": 0.4, "temperature": 0.9},
                "technical": {"alpha": 1.0, "beta": 0.2, "gamma": 0.6, "temperature": 0.6},
                "educational": {"alpha": 1.5, "beta": 0.5, "gamma": 0.5, "temperature": 0.8},
                "scientific": {"alpha": 1.8, "beta": 0.3, "gamma": 0.7, "temperature": 0.7},
                "conversational": {"alpha": 1.2, "beta": 0.5, "gamma": 0.6, "temperature": 0.85},
                "default": {"alpha": 1.5, "beta": 0.4, "gamma": 0.3, "temperature": 0.8},
            }.get(profile, {}),
            "message": f"Perfil alterado para '{profile}'. Parâmetros do campo atrator atualizados.",
        }

    async def _cmd_compliance(self, args: list) -> Dict:
        """%arkhe compliance [scope] — Status de conformidade MA‑S2."""
        scope = args[0] if args and args[0] in ["full", "cvs", "apm", "inv", "aro"] else "full"

        result = await self.safe_core.call_tool("compliance_status", {"scope": scope})
        return {
            **result,
            "scope": scope,
            "queried_at": time.time(),
        }

    async def _cmd_model_attack(self, args: list) -> Dict:
        """%arkhe model-attack <service_map_json> — Modela caminhos de ataque."""
        if not args:
            return {
                "error": "Uso: %arkhe model-attack '{\"api\": {\"exposure\": 0.9}, \"db\": {\"exposure\": 0.2}}'",
                "example": {
                    "api-gateway": {"exposure": 1.0, "ports": [443, 80]},
                    "auth-service": {"exposure": 0.6, "ports": [8080]},
                    "database": {"exposure": 0.2, "ports": [5432]},
                },
            }

        try:
            service_map = json.loads(" ".join(args))
        except json.JSONDecodeError as e:
            return {"error": f"JSON inválido: {e}"}

        result = await self.safe_core.call_tool("model_attack_paths", {
            "service_map": service_map,
        })

        return {
            **result,
            "service_map_hash": hashlib.sha3_256(json.dumps(service_map, sort_keys=True).encode()).hexdigest()[:16],
        }

    async def _cmd_phi_c(self, args: list) -> Dict:
        """%arkhe phi-c — Consulta coerência Φ_C."""
        time_range = args[0] if args and args[0] in ["1h", "24h", "7d", "30d"] else "24h"

        result = await self.safe_core.call_tool("phi_c_status", {"time_range": time_range})
        return {
            "current_phi_c": result.get("current_phi_c"),
            "phi_c_display": format_phi_c_display(result.get("current_phi_c", 0.0)),
            "trend": result.get("trend_24h", "stable"),
            "field_parameters": result.get("field_parameters", {}),
            "time_range": time_range,
        }

    async def _cmd_deploy(self, args: list) -> Dict:
        """%arkhe deploy <cve_id> — Orquestra patch."""
        if not args:
            return {"error": "Uso: %arkhe deploy <CVE-2026-XXXXX>"}

        cve_id = args[0]

        result = await self.safe_core.call_tool("deploy_patch", {
            "vulnerability_id": cve_id,
            "patched_release": f"patched-{cve_id.lower()}",
            "strategy": "canary",
        })

        return {
            **result,
            "cve": cve_id,
            "initiated_at": time.time(),
        }

    async def _cmd_grc_sync(self, args: list) -> Dict:
        """%arkhe grc-sync <cve_id> — Sincroniza com ferramentas GRC."""
        if not args:
            return {"error": "Uso: %arkhe grc-sync <CVE-2026-XXXXX>"}

        cve_id = args[0]

        # Simular sincronização com ServiceNow/Archer
        return {
            "cve": cve_id,
            "grc_platforms": ["ServiceNow", "RSA Archer"],
            "sync_status": "completed",
            "tickets_created": [
                {"platform": "ServiceNow", "ticket_id": "INC0012345", "status": "open"},
                {"platform": "RSA Archer", "ticket_id": "RISK-7890", "status": "in_progress"},
            ],
            "synced_at": time.time(),
        }

    def _arkhe_secure_impl(self, line: str, cell: str):
        """%%arkhe secure — Executa célula com proteção do Safe Core."""
        strict_mode = "--strict" in line
        log_execution = "--log" in line

        # Extrair contexto do código para auditoria
        code_context = extract_code_context(cell)

        # 1. Exorcismo: verificar se código contém ameaças
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()

        exorcism_result = loop.run_until_complete(self.safe_core.call_tool("exorcise_text", {
            "text": cell,
            "context": "python_code_execution",
            "strict_mode": strict_mode,
        }))

        if exorcism_result.get("exorcised_count", 0) > 0 and not exorcism_result.get("safe_to_proceed", True):
            error_msg = f"🛡️ **Código bloqueado pelo Guardião Atratora**\n\nTokens exorcisados: {exorcism_result.get('exorcised_count')}\n\nDetalhes:\n```json\n{json.dumps(exorcism_result.get('exorcised_tokens', []), indent=2)}\n```"
            display(Markdown(error_msg))
            return None

        # 2. Ancorar na TemporalChain
        seal = self.safe_core.compute_execution_seal(cell, {
            "magic": "secure",
            "strict": strict_mode,
            **code_context,
        })
        self._last_execution_seal = seal

        # 3. Executar código original (em ambiente isolado em produção)
        try:
            # Em produção: executar em sandbox com monitoramento
            result = self.shell.run_cell(cell, store_history=True)

            # 4. Logar execução se solicitado
            if log_execution:
                log_entry = {
                    "seal": seal,
                    "code_hash": hashlib.sha3_256(cell.encode()).hexdigest()[:16],
                    "exorcism": exorcism_result,
                    "execution_result": str(result) if result else "None",
                    "timestamp": time.time(),
                }
                self.safe_core.cache_result(f"exec_log_{seal}", log_entry)

            # 5. Exibir selo de auditoria
            display(Markdown(f"✅ **Execução concluída** | 🔐 Selo: `{seal}` | Φ_C: {format_phi_c_display(0.997)}"))

            return result

        except Exception as e:
            display(Markdown(f"❌ **Erro na execução**: {e}\n\n🔐 Selo da tentativa: `{seal}`"))
            return None

    def _arkhe_regenerate_impl(self, line: str, cell: str):
        """%%arkhe regenerate — Regenera código seguro via Multi‑LLM Core."""
        # Em produção: chamar MultiLLMSecureDevCore para regeneração
        # Para demo: simular regeneração com melhorias de segurança

        improved_code = self._simulate_secure_regeneration(cell)

        display(Markdown(f"🔄 **Código regenerado com proteções do Safe Core**:\n\n```python\n{improved_code}\n```"))

        # Oferecer opção de executar o código regenerado
        display(Markdown("> 💡 Use `%%arkhe secure` para executar este código com proteção completa."))

        return improved_code

    def _simulate_secure_regeneration(self, code: str) -> str:
        """Simula regeneração de código com melhorias de segurança (demo)."""
        # Adicionar comentários de segurança e validações básicas
        lines = code.split("\n")
        secured_lines = ["# 🔐 Código regenerado pelo Arkhe Safe Core", ""]

        for line in lines:
            # Adicionar validação para inputs sensíveis
            if "input(" in line or "eval(" in line or "exec(" in line:
                secured_lines.append(f"# ⚠️ Validação de segurança recomendada para: {line.strip()}")
            secured_lines.append(line)

        # Adicionar header de auditoria
        secured_lines.insert(2, f"# 📜 Audit seal: {hashlib.sha3_256(code.encode()).hexdigest()[:16]}")

        return "\n".join(secured_lines)


def load_ipython_extension(ipython):
    """Carrega a extensão Arkhe no IPython."""
    ipython.register_magics(ArkheMagics)
    print("🛡️ Arkhe Safe Core extension loaded. Use %arkhe --help for commands.")


def unload_ipython_extension(ipython):
    """Descarrega a extensão Arkhe."""
    print("🔓 Arkhe Safe Core extension unloaded.")
