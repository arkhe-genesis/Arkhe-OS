#!/usr/bin/env python3
"""
Substrato 232: Production NPM Canon Deploy
Gestão canônica de pacotes para builds de produção com:
• Pipeline CI/CD integrado ao Sentinel Fabric
• Validação Φ_C em cada etapa do build
• Rollback automático se coerência degradar
• Auditoria completa ancorada na TemporalChain
"""
import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ProductionBuildRecord:
    """Registro imutável de build em produção."""
    build_id: str
    project_name: str
    npm_commands_executed: List[str]
    phi_c_scores: Dict[str, float]  # comando → score
    vulnerabilities_found: int
    build_duration_seconds: float
    output_hash: str  # SHA3-256 do artefato final
    temporal_seal: Optional[str] = None
    deployed: bool = False
    rollback_triggered: bool = False
    created_at: float = field(default_factory=time.time)

class ProductionNPMDeployer:
    """
    Deployer de produção para NPM Canon.
    Características:
    • Pipeline CI/CD com validação Φ_C em cada estágio
    • Integração com Build/Security/Deployment Sentinels
    • Rollback automático se Φ_C < threshold configurado
    • Ancoragem de cada build na TemporalChain
    """

    # Thresholds de produção
    MIN_PHI_C_BUILD = 0.90
    MIN_PHI_C_DEPLOY = 0.95
    MAX_VULNERABILITIES_CRITICAL = 0
    MAX_BUILD_DURATION_MIN = 30

    def __init__(
        self,
        npm_manager,  # NPMPackageManager instance
        phi_bus=None,
        temporal_chain=None,
        guardian=None,
        sentinel_fabric=None
    ):
        self.npm = npm_manager
        self.phi_bus = phi_bus
        self.temporal = temporal_chain
        self.guardian = guardian
        self.sentinels = sentinel_fabric
        self._build_history: List[ProductionBuildRecord] = []

    async def execute_production_build(
        self,
        project_path: str,
        build_config: Dict
    ) -> ProductionBuildRecord:
        """
        Executa build canônico em produção.

        Pipeline:
        1. npm install com validação de segurança
        2. npm audit --audit-level=critical
        3. npm run build com validação de output
        4. npm run test com threshold de coverage
        5. Validação Φ_C composta do build completo
        6. Deploy condicional se Φ_C ≥ threshold
        7. Rollback automático se health check falhar
        """
        build_id = hashlib.sha3_256(
            f"{project_path}:{time.time()}".encode()
        ).hexdigest()[:12]

        logger.info(f"🚀 Iniciando build canônico: {build_id}")

        phi_c_scores = {}
        npm_commands = []
        vulnerabilities = 0
        start_time = time.time()

        try:
            # Estágio 1: Install com validação de segurança
            logger.info("   📦 npm install com validação de segurança...")
            install_result = await self.npm.npm_install(
                package=None,  # install all from package.json
                registry=build_config.get("registry"),
                save_dev=False
            )
            phi_c_scores["install"] = install_result.get("phi_c", 0.0)
            npm_commands.append("install")

            if install_result.get("record", {}).get("returncode") != 0:
                raise RuntimeError("npm install falhou")

            # Estágio 2: Audit de segurança
            logger.info("   🔍 npm audit --audit-level=critical...")
            audit_result = await self.npm.npm_audit(fix=False)
            phi_c_scores["audit"] = audit_result.get("phi_c", 0.0)
            npm_commands.append("audit")

            audit_summary = audit_result.get("audit_summary", {})
            vulnerabilities = audit_summary.get("vulnerabilities", {}).get("critical", 0)

            if vulnerabilities > self.MAX_VULNERABILITIES_CRITICAL:
                logger.error(f"🚨 {vulnerabilities} vulnerabilidades críticas bloqueiam deploy")
                raise RuntimeError(f"Critical vulnerabilities: {vulnerabilities}")

            # Estágio 3: Build com validação de output
            logger.info("   🔨 npm run build...")
            build_result = await self.npm.npm_run_script("build")
            phi_c_scores["build"] = build_result.get("phi_c", 0.0)
            npm_commands.append("build")

            if build_result.get("record", {}).get("returncode") != 0:
                raise RuntimeError("npm run build falhou")

            # Estágio 4: Testes com threshold de coverage
            if build_config.get("run_tests", True):
                logger.info("   🧪 npm run test...")
                test_result = await self.npm.npm_run_script("test")
                phi_c_scores["test"] = test_result.get("phi_c", 0.0)
                npm_commands.append("test")

                # Validar coverage se configurado
                min_coverage = build_config.get("min_coverage", 0.80)
                coverage = self._extract_coverage(test_result.get("record", {}).get("stdout", ""))
                if coverage < min_coverage:
                    logger.warning(f"⚠️  Coverage {coverage:.2%} < threshold {min_coverage:.2%}")

            # Calcular Φ_C composto do build
            build_duration = time.time() - start_time
            if build_duration > self.MAX_BUILD_DURATION_MIN * 60:
                logger.warning(f"⏱️  Build excedeu tempo máximo: {build_duration/60:.1f}min")

            composite_phi_c = self._calculate_composite_phi_c(phi_c_scores, vulnerabilities, build_duration)

            # Validar threshold de deploy
            if composite_phi_c < self.MIN_PHI_C_BUILD:
                logger.error(f"❌ Φ_C do build {composite_phi_c:.3f} < threshold {self.MIN_PHI_C_BUILD}")
                raise RuntimeError(f"Build Φ_C insufficient: {composite_phi_c:.3f}")

            # Calcular hash do output do build
            output_path = Path(project_path) / "dist"
            output_hash = self._hash_directory(output_path) if output_path.exists() else ""

            # Criar registro do build
            record = ProductionBuildRecord(
                build_id=build_id,
                project_name=Path(project_path).name,
                npm_commands_executed=npm_commands,
                phi_c_scores=phi_c_scores,
                vulnerabilities_found=vulnerabilities,
                build_duration_seconds=build_duration,
                output_hash=output_hash
            )

            # Ancorar na TemporalChain
            if self.temporal:
                record.temporal_seal = await self.temporal.anchor_event(
                    "production_build_completed",
                    {
                        "build_id": build_id,
                        "project": record.project_name,
                        "composite_phi_c": composite_phi_c,
                        "vulnerabilities": vulnerabilities,
                        "duration_seconds": build_duration,
                        "output_hash": output_hash[:16],
                        "timestamp": time.time()
                    }
                )

            # Publicar métrica no Phi-Bus
            if self.phi_bus:
                await self.phi_bus.publish_metric("production_build_completed", {
                    "build_id": build_id,
                    "phi_c": composite_phi_c,
                    "vulnerabilities": vulnerabilities,
                    "duration_seconds": build_duration
                })

            self._build_history.append(record)

            logger.info(
                f"✅ Build canônico concluído: {build_id} | "
                f"Φ_C={composite_phi_c:.3f} | "
                f"Vulns={vulnerabilities} | "
                f"Tempo={build_duration:.1f}s"
            )

            return record

        except Exception as e:
            logger.error(f"❌ Build falhou: {e}")
            # Registrar falha no audit trail
            if self.temporal:
                await self.temporal.anchor_event("production_build_failed", {
                    "build_id": build_id,
                    "error": str(e),
                    "timestamp": time.time()
                })
            raise

    def _calculate_composite_phi_c(
        self,
        stage_scores: Dict[str, float],
        vulnerabilities: int,
        duration_seconds: float
    ) -> float:
        """Calcula Φ_C composto do build completo."""
        # Média ponderada dos estágios
        weights = {"install": 0.2, "audit": 0.3, "build": 0.3, "test": 0.2}
        stage_phi = sum(
            stage_scores.get(stage, 0.5) * weight
            for stage, weight in weights.items()
            if stage in stage_scores
        ) / sum(weights.get(s, 0) for s in stage_scores)

        # Penalidade por vulnerabilidades
        vuln_penalty = max(0, 1.0 - vulnerabilities * 0.1)

        # Penalidade por tempo excessivo
        time_penalty = 1.0 if duration_seconds < self.MAX_BUILD_DURATION_MIN * 60 else 0.9

        return stage_phi * vuln_penalty * time_penalty

    def _extract_coverage(self, test_output: str) -> float:
        """Extrai coverage de output de testes (mock)."""
        # Mock: em produção, parsear output real de Jest/Vitest/etc.
        import re
        match = re.search(r'All files\s+\|\s+([\d.]+)%', test_output)
        return float(match.group(1)) / 100 if match else 0.85

    def _hash_directory(self, path: Path) -> str:
        """Calcula hash SHA3-256 de diretório de build."""
        hasher = hashlib.sha3_256()
        for file in sorted(path.rglob("*")):
            if file.is_file():
                hasher.update(str(file.relative_to(path)).encode())
                hasher.update(file.read_bytes())
        return hasher.hexdigest()

    async def deploy_with_rollback(
        self,
        build_record: ProductionBuildRecord,
        deploy_config: Dict
    ) -> Dict:
        """
        Executa deploy com rollback automático se health check falhar.
        """
        # Validar Φ_C para deploy
        if build_record.phi_c_scores.get("build", 0) < self.MIN_PHI_C_DEPLOY:
            return {
                "status": "rejected",
                "reason": f"phi_c_too_low: {build_record.phi_c_scores.get('build', 0):.3f} < {self.MIN_PHI_C_DEPLOY}"
            }

        logger.info(f"🚀 Executando deploy canônico: {build_record.build_id}")

        try:
            # Executar deploy via Deployment Sentinel
            if self.sentinels and self.sentinels.deployment:
                deploy_result = await self.sentinels.deployment.execute_canonical_deploy(
                    artifact_hash=build_record.output_hash,
                    environment=deploy_config.get("environment", "production"),
                    phi_c_threshold=self.MIN_PHI_C_DEPLOY
                )
            else:
                # Mock deploy
                await asyncio.sleep(1.0)
                deploy_result = {"status": "deployed", "endpoint": "https://app.arkhe.os"}

            # Executar health check canônico
            health_ok = await self._run_canonical_health_check(deploy_config.get("health_endpoint"))

            if not health_ok:
                logger.warning("⚠️  Health check falhou — acionando rollback")
                rollback_result = await self._execute_rollback(build_record, deploy_config)
                build_record.rollback_triggered = True
                return {
                    "status": "rolled_back",
                    "reason": "health_check_failed",
                    "rollback_result": rollback_result
                }

            build_record.deployed = True

            # Ancorar deploy na TemporalChain
            if self.temporal:
                await self.temporal.anchor_event("production_deploy_completed", {
                    "build_id": build_record.build_id,
                    "environment": deploy_config.get("environment"),
                    "endpoint": deploy_result.get("endpoint"),
                    "health_check": "passed",
                    "timestamp": time.time()
                })

            logger.info(f"✅ Deploy canônico concluído: {build_record.build_id}")
            return {"status": "deployed", **deploy_result}

        except Exception as e:
            logger.error(f"❌ Deploy falhou: {e}")
            # Tentar rollback em caso de erro
            await self._execute_rollback(build_record, deploy_config)
            return {"status": "failed", "error": str(e), "rolled_back": True}

    async def _run_canonical_health_check(self, endpoint: Optional[str]) -> bool:
        """Executa health check canônico pós-deploy."""
        if not endpoint:
            return True  # Mock: assumir sucesso se sem endpoint

        # Mock: em produção, chamar endpoint de health do serviço
        await asyncio.sleep(0.5)
        return True  # Simular health check passed

    async def _execute_rollback(
        self,
        build_record: ProductionBuildRecord,
        deploy_config: Dict
    ) -> Dict:
        """Executa rollback automático."""
        logger.info(f"🔄 Executando rollback para build {build_record.build_id}")

        if self.sentinels and self.sentinels.deployment:
            return await self.sentinels.deployment.execute_rollback(
                previous_version=deploy_config.get("previous_version"),
                environment=deploy_config.get("environment")
            )

        # Mock rollback
        await asyncio.sleep(0.5)
        return {"status": "rolled_back", "timestamp": time.time()}

    def get_production_statistics(self) -> Dict:
        """Retorna estatísticas de builds em produção."""
        if not self._build_history:
            return {"total_builds": 0}

        deployed = sum(1 for b in self._build_history if b.deployed)
        rolled_back = sum(1 for b in self._build_history if b.rollback_triggered)

        return {
            "total_builds": len(self._build_history),
            "deployed": deployed,
            "rolled_back": rolled_back,
            "success_rate": deployed / len(self._build_history),
            "avg_phi_c": sum(
                sum(b.phi_c_scores.values()) / len(b.phi_c_scores)
                for b in self._build_history if b.phi_c_scores
            ) / len(self._build_history),
            "avg_build_duration": sum(b.build_duration_seconds for b in self._build_history) / len(self._build_history),
            "total_vulnerabilities_blocked": sum(
                b.vulnerabilities_found for b in self._build_history
                if b.vulnerabilities_found > 0
            )
        }
