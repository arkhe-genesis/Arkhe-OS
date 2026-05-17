#!/usr/bin/env python3
"""
ARKHE OS Substrato 232: NPM Package Manager Canon
Orquestração da gestão canônica de pacotes Node.js em produção.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add root directory to path to allow importing from tools and tool_calling
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.npm_package_manager import NPMPackageManager
from tool_calling.canonical_tool_system import CanonicalToolCallingSystem, ToolCallRequest

# Mock dependencies for isolated testing
class MockTemporalChain:
    async def anchor_event(self, event_type, data):
        return "mocked_seal_abc123"

class MockPhiBus:
    async def publish_metric(self, metric_name, data):
        pass

class MockMetaAudit:
    async def record_cycle(self, **kwargs):
        pass

class MockGuardian:
    async def validate_operation(self, kwargs):
        return True, "Mock Guardian Approved"

    async def validate_external_url(self, url):
        return True, "Mock URL Approved"

async def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-8s | %(message)s')
    logger = logging.getLogger("Substrato232")
    logger.info("🚀 Iniciando Substrato 232: NPM Package Canon")

    # 1. Inicializar dependências canônicas
    temporal = MockTemporalChain()
    phi_bus = MockPhiBus()
    meta_audit = MockMetaAudit()
    guardian = MockGuardian()

    # 2. Inicializar sistema de ferramentas
    tool_system = CanonicalToolCallingSystem(
        temporal=temporal,
        phi_bus=phi_bus
    )

    # 3. Inicializar NPM Manager
    work_dir = Path("./mock_app_dir")
    work_dir.mkdir(exist_ok=True)

    npm_manager = NPMPackageManager(
        working_dir=str(work_dir),
        tool_system=tool_system,
        temporal_chain=temporal,
        phi_bus=phi_bus,
        meta_audit=meta_audit,
        guardian=guardian
    )

    # 4. Registrar ferramentas
    npm_manager.register_all_tools(tool_system)

    # 5. Simular algumas chamadas
    logger.info("--- Testando NPM Init ---")
    req_init = ToolCallRequest(
        call_id="call_init_1",
        tool_id="npm_init",
        parameters={"scope": "@arkhe"},
        context_phi_c=0.95
    )
    res_init = await tool_system.invoke_tool(req_init)
    logger.info(f"Init Result: {res_init.status}")

    logger.info("--- Testando NPM Install ---")
    req_install = ToolCallRequest(
        call_id="call_install_1",
        tool_id="npm_install",
        parameters={"package": "lodash"},
        context_phi_c=0.90
    )
    res_install = await tool_system.invoke_tool(req_install)
    logger.info(f"Install Result: {res_install.status}")

    # Exibir estatísticas
    stats = npm_manager.get_operational_statistics()
    logger.info(f"📊 Estatísticas Finais: {stats}")
    logger.info("✅ Substrato 232 executado com sucesso.")

if __name__ == "__main__":
    asyncio.run(main())
