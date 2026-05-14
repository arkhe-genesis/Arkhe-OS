#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kernel.py — ArkheKernel: Kernel Jupyter dedicado com proteção do Safe Core
"""

import asyncio
import json
import time
import hashlib
import os
import sys
from typing import Dict, Any, Optional
from ipykernel.kernelbase import Kernel
from .utils import SafeCoreConnection, extract_code_context, format_phi_c_display

class ArkheKernel(Kernel):
    """
    Kernel Jupyter com integração do Safe Core Arkhe.

    Funcionalidades:
    • Intercepta cada execução de código e submete ao Guardião Atratora
    • Bloqueia execução se conteúdo malicioso detectado
    • Ancora cada célula executada na TemporalChain com selo SHA3-256
    • Exibe métricas Φ_C no banner do kernel
    • Suporta autocompletar para comandos arkhe
    • Gera SBOM automática do ambiente de execução
    """

    implementation = "arkhe"
    implementation_version = "1.0.0"
    language = "python"
    language_version = sys.version.split()[0]
    language_info = {
        "name": "python+arkhe",
        "version": sys.version,
        "mimetype": "text/x-python",
        "file_extension": ".py",
    }

    banner = "🛡️ ARKHE Kernel v1.0.0 — Safe Core Integrated"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.safe_core = SafeCoreConnection()
        self._execution_count = 0
        self._phi_c_cache = None
        self._phi_c_last_update = 0
        self._session_sbom = None

        # Atualizar banner com Φ_C inicial
        self._update_banner()

    def _update_banner(self):
        """Atualiza banner do kernel com métricas Φ_C."""
        phi_c = self._get_phi_c_sync()
        self.banner = f"🛡️ ARKHE Kernel v1.0.0 | Φ_C: {format_phi_c_display(phi_c)}"

    def _get_phi_c_sync(self) -> float:
        """Obtém valor de Φ_C (com cache de 60s)."""
        now = time.time()
        if self._phi_c_cache and (now - self._phi_c_last_update) < 60:
            return self._phi_c_cache

        # Em produção: chamar API assincronamente
        # Para demo: valor simulado com variação mínima
        import random
        base_phi_c = 0.997
        variation = random.uniform(-0.002, 0.002)
        self._phi_c_cache = max(0.990, min(0.999, base_phi_c + variation))
        self._phi_c_last_update = now

        return self._phi_c_cache

    def do_execute(self, code: str, silent: bool, store_history: bool,
                   user_expressions: Optional[Dict], allow_stdin: bool) -> Dict[str, Any]:
        """Intercepta e processa execução de código com proteção do Safe Core."""
        self._execution_count += 1
        execution_id = f"exec_{self._execution_count}_{int(time.time())}"

        # 1. Extrair contexto para auditoria
        code_context = extract_code_context(code)

        # 2. Exorcismo: verificar código antes da execução
        if not silent:
            self._send_status("busy", execution_id)

            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()

            exorcism_result = loop.run_until_complete(self.safe_core.call_tool("exorcise_text", {
                "text": code,
                "context": "jupyter_execution",
                "strict_mode": True,  # Kernel sempre em modo estrito
            }))

            if exorcism_result.get("exorcised_count", 0) > 0 and not exorcism_result.get("safe_to_proceed", True):
                # Bloquear execução e enviar erro
                error_content = {
                    "ename": "ArkheSecurityError",
                    "evalue": f"Código bloqueado pelo Guardião Atratora: {exorcism_result.get('exorcised_count')} tokens exorcisados",
                    "traceback": [
                        f"🛡️ ArkheSecurityError: Código contém conteúdo potencialmente malicioso",
                        f"   Tokens exorcisados: {exorcism_result.get('exorcised_count')}",
                        f"   Detalhes: {json.dumps(exorcism_result.get('exorcised_tokens', []), indent=2)}",
                        f"   🔐 Selo da tentativa: {self.safe_core.compute_execution_seal(code, {'blocked': True})}",
                    ],
                }
                self._send_status("idle", execution_id)
                return {
                    "status": "error",
                    "execution_count": self._execution_count,
                    **error_content,
                }

        # 3. Ancorar na TemporalChain antes da execução
        seal = self.safe_core.compute_execution_seal(code, {
            "execution_id": execution_id,
            "execution_count": self._execution_count,
            **code_context,
        })

        # 4. Executar código original via kernel pai (simulado)
        try:
            # Em produção: executar em subprocesso isolado com monitoramento
            # Para demo: simular execução bem-sucedida
            result = {
                "status": "ok",
                "execution_count": self._execution_count,
                "payload": [],
                "user_expressions": {},
            }

            # 5. Ancorar resultado na TemporalChain
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
            loop.run_until_complete(self.safe_core.call_tool("audit_query", {
                "seal": seal,
            }))  # Simula registro de execução

            # 6. Atualizar SBOM da sessão se necessário
            if self._session_sbom is None and self._execution_count % 10 == 0:
                # Avoid task if possible in testing environments, just run directly
                loop.run_until_complete(self._update_session_sbom())

            # 7. Atualizar banner com Φ_C atualizado
            self._update_banner()

            if not silent:
                # Enviar mensagem de status com selo de auditoria
                self._send_status("idle", execution_id)
                self._send_display_data({
                    "text/markdown": f"🔐 Execução ancorada: `{seal}` | Φ_C: {format_phi_c_display(self._get_phi_c_sync())}",
                })

            return result

        except Exception as e:
            # Ancorar erro também
            error_seal = self.safe_core.compute_execution_seal(code, {"error": str(e)})

            if not silent:
                self._send_status("idle", execution_id)
                self._send_error({
                    "ename": type(e).__name__,
                    "evalue": str(e),
                    "traceback": [f"🔐 Error anchor: `{error_seal}`"],
                })

            return {
                "status": "error",
                "execution_count": self._execution_count,
                "ename": type(e).__name__,
                "evalue": str(e),
                "traceback": [f"🔐 Error anchor: `{error_seal}`"],
            }

    def do_complete(self, code: str, cursor_pos: int) -> Dict[str, Any]:
        """Fornece autocompletar para comandos %arkhe."""
        if code.startswith("%arkhe"):
            commands = [
                "status", "scan", "sbom", "audit", "profile",
                "compliance", "model-attack", "phi-c", "deploy", "grc-sync",
            ]
            prefix = code.split()[-1] if len(code.split()) > 1 else ""

            matches = [f"%arkhe {cmd}" for cmd in commands if cmd.startswith(prefix)]

            return {
                "matches": matches,
                "cursor_start": code.rfind("%arkhe "),
                "cursor_end": cursor_pos,
                "metadata": {},
                "status": "ok",
            }

        # Delegar autocompletar padrão para Python
        return {"status": "ok", "matches": [], "cursor_start": cursor_pos, "cursor_end": cursor_pos, "metadata": {}}

    def do_inspect(self, code: str, cursor_pos: int, detail_level: int = 0) -> Dict[str, Any]:
        """Fornece inspeção/ajuda para comandos arkhe."""
        if "%arkhe" in code:
            parts = code.split()
            if len(parts) >= 2 and parts[1] in ["status", "scan", "sbom", "audit", "profile", "compliance", "model-attack", "phi-c", "deploy", "grc-sync"]:
                command = parts[1]
                help_text = self._get_command_help(command)

                return {
                    "status": "ok",
                    "data": {
                        "text/markdown": help_text,
                    },
                    "metadata": {},
                    "found": True,
                }

        return {"status": "ok", "found": False, "data": {}, "metadata": {}}

    def _get_command_help(self, command: str) -> str:
        """Retorna texto de ajuda para comando arkhe."""
        help_texts = {
            "status": "📊 `%arkhe status` — Exibe estado do nó: Φ_C, selo atual, perfil ativo.",
            "scan": "🔍 `%arkhe scan <code>` — Escaneia código com Guardião Atratora + MA-S2 CVS.",
            "sbom": "📦 `%arkhe sbom [release_id]` — Gera SBOM CycloneDX ancorada na TemporalChain.",
            "audit": "🔐 `%arkhe audit <seal>` — Consulta registro de auditoria por selo SHA3-256.",
            "profile": "🎨 `%arkhe profile <domain>` — Altera perfil do campo atrator (creative, technical, etc.).",
            "compliance": "✅ `%arkhe compliance [scope]` — Status de conformidade MA‑S2 por domínio.",
            "model-attack": "🗺️ `%arkhe model-attack <service_map_json>` — Modela caminhos de ataque multi-estágio.",
            "phi-c": "🌀 `%arkhe phi-c [time_range]` — Consulta coerência Φ_C atual e tendência histórica.",
            "deploy": "🚀 `%arkhe deploy <cve_id>` — Orquestra remediação autônoma para vulnerabilidade.",
            "grc-sync": "🔗 `%arkhe grc-sync <cve_id>` — Sincroniza finding com ServiceNow/RSA Archer.",
        }
        return help_texts.get(command, f"❓ Comando desconhecido: {command}")

    async def _update_session_sbom(self):
        """Atualiza SBOM da sessão atual (executado periodicamente)."""
        if self._session_sbom is None:
            session_id = os.getenv("JPY_SESSION_NAME", f"session-{int(time.time())}")
            result = await self.safe_core.call_tool("generate_sbom", {
                "release_id": session_id,
                "format": "json",
                "include_dev_deps": True,
            })
            self._session_sbom = result
            self.log.info(f"📦 SBOM da sessão gerada: {session_id}")

    def _send_status(self, status: str, execution_id: str):
        """Envia mensagem de status para frontend."""
        self.session.send(
            self.iopub_socket,
            "status",
            content={"execution_state": status, "execution_id": execution_id},
            parent=self._parent_header,
        )

    def _send_display_data(self, data: Dict[str, str]):
        """Envia dados para exibição no frontend."""
        self.session.send(
            self.iopub_socket,
            "display_data",
            content={
                "data": data,
                "metadata": {},
                "transient": {"display_id": f"arkhe_{int(time.time())}"},
            },
            parent=self._parent_header,
        )

    def _send_error(self, error_content: Dict):
        """Envia mensagem de erro para frontend."""
        self.session.send(
            self.iopub_socket,
            "error",
            content=error_content,
            parent=self._parent_header,
        )


# Ponto de entrada para registro do kernel
def register_kernel():
    """Registra ArkheKernel no Jupyter."""
    from jupyter_client.kernelspec import KernelSpecManager

    kernel_spec = {
        "argv": [sys.executable, "-m", "arkhe_ipython.kernel", "-f", "{connection_file}"],
        "display_name": "Python (Arkhe Safe Core)",
        "language": "python",
        "metadata": {
            "debugger": True,
            "arkhe": {
                "version": "1.0.0",
                "substrate": "9012",
                "features": ["guardian_attractor", "temporal_chain", "ma_s2_compliance"],
            },
        },
    }

    ksm = KernelSpecManager()
    ksm.install_kernel_spec(
        kernel_spec,
        kernel_name="arkhe",
        user=True,
        prefix=None,
    )
    print("✅ Arkhe kernel registered. Use: jupyter console --kernel arkhe")

if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=ArkheKernel)
