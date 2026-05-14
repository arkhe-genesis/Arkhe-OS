#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ma_s2_github_action.py — Integração MA‑S2 para GitHub Actions
Executa verificações de conformidade como step nativo do pipeline.
"""

import os, sys, json, asyncio
from pathlib import Path
from typing import Dict, Optional

from arkhe.security.ma_s2_engine import MA_S2_ComplianceEngine, MA_S2_Domain, ComplianceStatus
from arkhe.core.temporal_chain import TemporalChain
from arkhe.security.guardian_attractor import GuardianAttractor
from arkhe.inventory.sbom_manager import SBOMManager
from arkhe.orchestrator.fleet_orchestrator import FleetOrchestrator

class MA_S2_GitHubAction:
    """
    Wrapper para execução de verificações MA‑S2 em GitHub Actions.
    Compatível com inputs, outputs e environment variables do Actions.
    """

    def __init__(self):
        self.github_env = self._parse_github_env()
        self.temporal = TemporalChain(endpoint=os.getenv('TEMPORAL_CHAIN_ENDPOINT'))
        self.guardian = GuardianAttractor()
        self.sbom_manager = SBOMManager(temporal_chain=self.temporal)
        self.orchestrator = FleetOrchestrator(temporal_chain=self.temporal)
        self.engine = MA_S2_ComplianceEngine(
            temporal_chain=self.temporal,
            guardian=self.guardian,
            sbom_manager=self.sbom_manager,
            orchestrator=self.orchestrator,
        )

    def _parse_github_env(self) -> Dict:
        """Parse environment variables do GitHub Actions."""
        return {
            'repository': os.getenv('GITHUB_REPOSITORY', ''),
            'sha': os.getenv('GITHUB_SHA', ''),
            'ref': os.getenv('GITHUB_REF', ''),
            'event_name': os.getenv('GITHUB_EVENT_NAME', ''),
            'workspace': os.getenv('GITHUB_WORKSPACE', '.'),
            'artifact_path': os.getenv('INPUT_ARTIFACT_PATH', '.'),
            'scope': os.getenv('INPUT_SCOPE', 'full'),
        }

    async def run(self) -> int:
        """Executa verificações MA‑S2 e retorna código de saída."""
        print(f"🛡️ Iniciando verificação MA‑S2 para {self.github_env['repository']}@{self.github_env['sha'][:8]}")

        try:
            # 1. Gerar SBOM se não existir
            sbom_path = Path(self.github_env['workspace']) / 'sbom.json'
            if not sbom_path.exists():
                print("📦 Gerando SBOM CycloneDX...")
                sbom_hash = await self.engine.generate_and_anchor_sbom(
                    release_id=self.github_env['sha'],
                    format='cyclonedx',
                )
                print(f"   ✓ SBOM ancorada: {sbom_hash[:16]}...")

            # 2. Escaneamento de vulnerabilidades (CVS)
            print("🔍 Executando escaneamento contínuo (CVS)...")
            findings = await self.engine.continuous_vulnerability_scan(
                artifact_hash=self.github_env['sha'],
                include_dependencies=True,
            )
            critical_count = sum(1 for f in findings if f.get('is_critical'))
            print(f"   ✓ {len(findings)} findings ({critical_count} críticos)")

            # 3. Modelagem de caminhos de ataque (APM)
            print("🗺️ Modelando caminhos de ataque (APM)...")
            service_map = self._load_service_map()
            paths = await self.engine.attack_path_modeling(
                service_map=service_map,
                threat_context=self._load_threat_context(),
            )
            high_risk = [p for p in paths if p.get('priority_score', 0) > 0.8]
            print(f"   ✓ {len(paths)} caminhos modelados ({len(high_risk)} de alto risco)")

            # 4. Avaliação de conformidade completa
            print("📊 Avaliando conformidade MA‑S2...")
            assessment = await self.engine.assess_compliance(
                scope=self.github_env['scope'],
                release_id=self.github_env['sha'],
            )

            # 5. Gerar outputs para Actions
            self._set_github_outputs(assessment)

            # 6. Relatório em Markdown
            report_md = self.engine.generate_compliance_report(assessment, format='markdown')
            report_path = Path(self.github_env['workspace']) / 'MA_S2_Compliance_Report.md'
            report_path.write_text(report_md)
            print(f"📄 Relatório gerado: {report_path}")

            # 7. Decisão de sucesso/falha
            if assessment.overall_status == ComplianceStatus.COMPLIANT:
                print("✅ Conformidade MA‑S2: COMPLIANT")
                return 0
            else:
                print(f"❌ Conformidade MA‑S2: {assessment.overall_status.value.upper()}")
                # Logar detalhes dos controles não conformes
                for domain, controls in assessment.domain_results.items():
                    non_compliant = [cid for cid, status in controls.items() if status != ComplianceStatus.COMPLIANT]
                    if non_compliant:
                        print(f"   • {domain.value}: controles não conformes: {non_compliant}")
                return 1

        except Exception as e:
            print(f"❌ Erro na verificação MA‑S2: {e}")
            # Definir output de erro para Actions
            with open(os.getenv('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
                f.write(f"error={str(e)}\n")
            return 2

    def _load_service_map(self) -> Dict:
        """Carrega mapa de serviços do repositório."""
        path = Path(self.github_env['workspace']) / 'config' / 'services.yaml'
        if path.exists():
            import yaml
            return yaml.safe_load(path.read_text())
        # Fallback: mapa mínimo baseado em estrutura do repositório
        return {
            "api": {"criticality": 0.9, "exposure": 1.0},
            "auth": {"criticality": 0.95, "exposure": 0.8},
            "data": {"criticality": 0.85, "exposure": 0.3},
        }

    def _load_threat_context(self) -> Dict:
        """Carrega contexto de ameaças (simulado)."""
        return {
            "active_threats": ["APT29", "Lazarus"],
            "industry": os.getenv('INPUT_INDUSTRY', 'technology'),
            "region": os.getenv('INPUT_REGION', 'global'),
        }

    def _set_github_outputs(self, assessment):
        """Define outputs para GitHub Actions."""
        outputs = {
            'overall_status': assessment.overall_status.value,
            'temporal_seal': assessment.temporal_seal,
            'assessment_id': assessment.assessment_id,
            'domains_json': json.dumps({
                d.value: {cid: s.value for cid, s in controls.items()}
                for d, controls in assessment.domain_results.items()
            }),
        }
        # Escrever em $GITHUB_OUTPUT
        output_file = os.getenv('GITHUB_OUTPUT')
        if output_file:
            with open(output_file, 'a') as f:
                for key, value in outputs.items():
                    f.write(f"{key}={value}\n")

if __name__ == "__main__":
    action = MA_S2_GitHubAction()
    exit_code = asyncio.run(action.run())
    sys.exit(exit_code)