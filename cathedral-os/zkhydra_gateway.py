#!/usr/bin/env python3
"""
Cathedral ARKHE v17.2 - zkHydra Gateway
Orquestra análise de segurança de circuitos ZK (Circom) usando o framework zkHydra.
"""

import argparse
import asyncio
import json
import logging
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger("cathedral.zkhydra")
logging.basicConfig(level=logging.INFO)

class ZkHydraResult:
    """Estrutura para resultados de análise do zkHydra."""
    def __init__(self, tool_name: str, raw_output: dict):
        self.tool_name = tool_name
        self.has_findings = raw_output.get("findings", []) != []
        self.findings = raw_output.get("findings", [])

class ZkHydraGateway:
    """
    Gateway para o framework zkHydra.
    Executa análises de segurança sobre circuitos Circom e retorna resultados estruturados.
    """

    def __init__(self, work_dir: str = "./zkhydra_work"):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

    async def analyze_circuit(
        self,
        circuit_path: str,
        tools: List[str] = None,
        timeout: int = 600
    ) -> Dict[str, ZkHydraResult]:
        """
        Executa o zkHydra (modo analyze) sobre um arquivo .circom.

        Args:
            circuit_path: Caminho para o arquivo .circom.
            tools: Lista de ferramentas a usar (ex: ["circomspect", "circom_civer"]).
            timeout: Tempo limite em segundos.

        Returns:
            Dicionário mapeando nome da ferramenta para ZkHydraResult.
        """
        if tools is None or tools == ["all"]:
            tools = ["circomspect", "circom_civer", "picus"]

        output_dir = self.work_dir / "output"
        output_dir.mkdir(exist_ok=True)

        cmd = [
            "docker", "run", "--rm",
            "-v", "{}:/zkhydra/input".format(Path(circuit_path).parent.absolute()),
            "-v", "{}:/zkhydra/output".format(output_dir.absolute()),
            "ghcr.io/zksecurity/zkhydra:latest",
            "uv", "run", "python", "-m", "zkhydra.main", "analyze",
            "--input", "/zkhydra/input/{}".format(Path(circuit_path).name),
            "--tools", ",".join(tools),
            "--timeout", str(timeout),
            "--output", "/zkhydra/output"
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError("zkHydra falhou (RC={}): {}".format(proc.returncode, stderr.decode()))

            results = {}
            for tool in tools:
                result_file = output_dir / tool / "results.json"
                if result_file.exists():
                    with open(result_file, "r") as f:
                        raw = json.load(f)
                        results[tool] = ZkHydraResult(tool, raw)
                else:
                    logger.warning("Resultado da ferramenta {} não encontrado em {}".format(tool, result_file))
            return results

        except Exception as e:
            logger.error("Erro ao executar zkHydra: {}".format(e))
            return {}

    async def evaluate_vulnerability(self, bug_config_path: str, tools: List[str] = None) -> Dict:
        """
        Executa o modo 'evaluate' do zkHydra, comparando resultados com vulnerabilidades conhecidas (zkbugs).
        Útil para benchmarking e validação de novas ferramentas.
        """
        if tools is None or tools == ["all"]:
            tools = ["circomspect", "circom_civer", "picus", "zkfuzz"]

        output_dir = self.work_dir / "evaluate_output"
        output_dir.mkdir(exist_ok=True)

        cmd = [
            "docker", "run", "--rm",
            "-v", "{}:/zkhydra/bug".format(Path(bug_config_path).parent.absolute()),
            "-v", "{}:/zkhydra/output".format(output_dir.absolute()),
            "ghcr.io/zksecurity/zkhydra:latest",
            "uv", "run", "python", "-m", "zkhydra.main", "evaluate",
            "--input", "/zkhydra/bug/{}".format(Path(bug_config_path).name),
            "--tools", ",".join(tools),
            "--output", "/zkhydra/output"
        ]

        try:
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError("zkHydra evaluate falhou: {}".format(stderr.decode()))

            eval_file = output_dir / "evaluation.json"
            if eval_file.exists():
                with open(eval_file, "r") as f:
                    return json.load(f)
            else:
                logger.warning("Arquivo evaluation.json não encontrado")
                return {}
        except Exception as e:
            logger.error("Erro no evaluate: {}".format(e))
            return {}

async def process_zkhydra_results(results: Dict[str, ZkHydraResult]) -> None:
    for tool, res in results.items():
        if res.has_findings:
            logger.warning("[{}] Vulnerabilidades detectadas: {}".format(tool, res.findings))
            await send_alert(
                title="Vulnerabilidade em circuito ZK ({})".format(tool),
                message=json.dumps(res.findings, indent=2),
                severity="high"
            )
        else:
            logger.info("[{}] Nenhuma vulnerabilidade encontrada.".format(tool))

async def send_alert(title: str, message: str, severity: str):
    logger.info("Alert - {}: {}".format(title, message))

def main():
    parser = argparse.ArgumentParser(description="Cathedral ARKHE zkHydra Gateway")
    subparsers = parser.add_subparsers(dest="command")

    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("--circuit", required=True, help="Caminho para o circuito .circom")
    analyze_parser.add_argument("--tools", default="all", help="Ferramentas separadas por virgula ou 'all'")
    analyze_parser.add_argument("--fail-on-finding", action="store_true", help="Falha se encontrar vulnerabilidades")
    analyze_parser.add_argument("--output", help="Arquivo de saida para o relatorio JSON")

    args = parser.parse_args()

    if args.command == "analyze":
        tools = args.tools.split(",") if args.tools != "all" else None
        gateway = ZkHydraGateway()

        results = asyncio.run(gateway.analyze_circuit(args.circuit, tools=tools))

        asyncio.run(process_zkhydra_results(results))

        report = {}
        has_vulnerabilities = False
        for tool, res in results.items():
            report[tool] = {"has_findings": res.has_findings, "findings": res.findings}
            if res.has_findings:
                has_vulnerabilities = True

        if args.output:
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2)

        if args.fail_on_finding and has_vulnerabilities:
            logger.error("Falha: vulnerabilidades encontradas!")
            sys.exit(1)

if __name__ == "__main__":
    main()
