import logging
from typing import Dict

logger = logging.getLogger(__name__)

class PolyglotOrchestrator:
    def __init__(self, pypi_tool, npm_tool):
        self.pypi_tool = pypi_tool
        self.npm_tool = npm_tool

    async def install_polyglot_project(self, project_path: str, parameters: Dict) -> Dict:
        logger.info(f"🔄 [Polyglot Orch] Iniciando orquestração em {project_path}")

        pypi_res = await self.pypi_tool.pip_install(parameters)
        if pypi_res.get("status") == "error":
            return pypi_res

        npm_res = await self.npm_tool.install_dependencies(parameters)
        if npm_res.get("status") == "error":
             return npm_res

        return {"status": "success", "pypi": pypi_res, "npm": npm_res}
