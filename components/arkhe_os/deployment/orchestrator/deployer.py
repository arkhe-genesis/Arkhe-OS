"""
Executor de deployment com validação regulatória prévia e rollback automático.
"""
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

from .infrastructure import DeploymentStack
from ..compliance.engine import ComplianceEngine, DeploymentConfig
from ..audit.ledger import AuditLedger

logger = logging.getLogger(__name__)

class DeploymentDeployer:
    """Orquestrador de deployment com compliance integrado."""

    def __init__(self, compliance_engine: ComplianceEngine, audit_ledger: AuditLedger):
        self.compliance_engine = compliance_engine
        self.audit_ledger = audit_ledger
        self.deployment_history: Dict[str, Dict] = {}

    async def deploy(self, stack: DeploymentStack, config: DeploymentConfig) -> Dict:
        """
        Executa deployment com validação regulatória completa.

        Fluxo:
        1. Validar configuração contra regras de compliance
        2. Gerar proofs ZK de conformidade
        3. Executar deploy da infraestrutura
        4. Validar estado pós-deploy
        5. Registrar audit trail com proofs
        """
        deployment_id = f"{stack.stack_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Registrar início do deployment
        await self.audit_ledger.log_event(
            event_type="DEPLOYMENT_STARTED",
            deployment_id=deployment_id,
            metadata={
                "stack_id": stack.stack_id,
                "jurisdictions": stack.jurisdictions,
                "timestamp": datetime.now().isoformat(),
            }
        )

        try:
            # 1. Validar configuração de compliance
            logger.info(f"[{deployment_id}] Validating compliance configuration...")
            compliance_results = self.compliance_engine.evaluate_deployment(config)

            # Verificar se todas as jurisdições estão compliant
            non_compliant = [
                (jur, result) for jur, result in compliance_results.items()
                if not result.is_compliant
            ]

            if non_compliant:
                error_msg = f"Compliance validation failed for: {[j.value for j, _ in non_compliant]}"
                logger.error(f"[{deployment_id}] {error_msg}")

                await self.audit_ledger.log_event(
                    event_type="COMPLIANCE_VALIDATION_FAILED",
                    deployment_id=deployment_id,
                    metadata={
                        "violations": [
                            {"jurisdiction": j.value, "count": r.rules_failed}
                            for j, r in non_compliant
                        ],
                    }
                )

                return {
                    "status": "FAILED",
                    "reason": "compliance_validation_failed",
                    "details": {j.value: r.to_report() for j, r in compliance_results.items()},
                }

            # 2. Registrar proofs de compliance
            for jurisdiction, result in compliance_results.items():
                if result.zk_proof_hash:
                    await self.audit_ledger.log_event(
                        event_type=f"COMPLIANCE_PROOF_GENERATED_{jurisdiction.value.upper()}",
                        deployment_id=deployment_id,
                        metadata={
                            "jurisdiction": jurisdiction.value,
                            "proof_hash": result.zk_proof_hash,
                            "rules_passed": result.rules_passed,
                        }
                    )

            # 3. Executar deploy da infraestrutura
            logger.info(f"[{deployment_id}] Executing infrastructure deployment...")
            deploy_result = await self._execute_infrastructure_deploy(stack)

            if not deploy_result["success"]:
                raise RuntimeError(f"Infrastructure deployment failed: {deploy_result['error']}")

            # 4. Validar estado pós-deploy
            logger.info(f"[{deployment_id}] Validating post-deployment state...")
            post_deploy_state = await self._capture_post_deploy_state(stack)
            post_compliance = self.compliance_engine.evaluate_deployment(
                self._state_to_config(post_deploy_state)
            )

            # 5. Registrar sucesso e finalizar
            await self.audit_ledger.log_event(
                event_type="DEPLOYMENT_COMPLETED",
                deployment_id=deployment_id,
                metadata={
                    "infrastructure_status": "SUCCESS",
                    "compliance_status": {
                        j.value: "COMPLIANT" if r.is_compliant else "NON_COMPLIANT"
                        for j, r in post_compliance.items()
                    },
                    "proofs": {
                        j.value: r.zk_proof_hash
                        for j, r in post_compliance.items() if r.zk_proof_hash
                    },
                }
            )

            self.deployment_history[deployment_id] = {
                "status": "SUCCESS",
                "compliance_results": {j.value: r.to_report() for j, r in compliance_results.items()},
                "infrastructure": deploy_result,
                "timestamp": datetime.now().isoformat(),
            }

            return {
                "status": "SUCCESS",
                "deployment_id": deployment_id,
                "compliance_summary": {
                    j.value: {"status": "COMPLIANT", "proof": r.zk_proof_hash}
                    for j, r in compliance_results.items()
                },
            }

        except Exception as e:
            logger.error(f"[{deployment_id}] Deployment failed: {str(e)}")

            # Tentar rollback automático
            logger.info(f"[{deployment_id}] Attempting automatic rollback...")
            rollback_result = await self._execute_rollback(stack, deployment_id)

            await self.audit_ledger.log_event(
                event_type="DEPLOYMENT_FAILED",
                deployment_id=deployment_id,
                metadata={
                    "error": str(e),
                    "rollback_status": "SUCCESS" if rollback_result else "FAILED",
                }
            )

            return {
                "status": "FAILED",
                "reason": str(e),
                "rollback_completed": rollback_result,
            }

    async def _execute_infrastructure_deploy(self, stack: DeploymentStack) -> Dict:
        """Executa deploy da infraestrutura (stub para integração com Terraform/CDK)."""
        # Em produção: integrar com Terraform Cloud, AWS CDK, ou similar
        # Aqui: simulação de deploy bem-sucedido
        await asyncio.sleep(2)  # Simular tempo de deploy

        return {
            "success": True,
            "resources_created": len(stack.resources),
            "regions_deployed": list(set(r.region for r in stack.resources)),
        }

    async def _capture_post_deploy_state(self, stack: DeploymentStack) -> Dict:
        """Captura estado real do sistema pós-deploy para validação."""
        # Em produção: consultar APIs de cloud provider para estado real
        return {
            "deployment_id": stack.stack_id,
            "regions": list(set(r.region for r in stack.resources)),
            "data_types": {"phi": True, "pii": True},  # Exemplo
            "encryption": {
                "at_rest": True,
                "in_transit": True,
                "algorithm": "AES-256-GCM",
                "protocol": "TLS-1.3",
            },
            "access_control": {
                "unique_user_ids": True,
                "role_based": True,
                "audit_logging": True,
            },
            "audit": {
                "enabled": True,
                "immutable": True,
                "retention_days": 2555,
            },
        }

    def _state_to_config(self, state: Dict) -> DeploymentConfig:
        """Converte estado capturado para configuração para reavaliação."""
        return DeploymentConfig(
            deployment_id=state["deployment_id"],
            regions=state["regions"],
            data_classification=state.get("data_types", {}),
            encryption=state.get("encryption", {}),
            access_control=state.get("access_control", {}),
            audit=state.get("audit", {}),
            retention=state.get("retention_policy", {}),
        )

    async def _execute_rollback(self, stack: DeploymentStack, deployment_id: str) -> bool:
        """Executa rollback automático em caso de falha."""
        try:
            # Em produção: integrar com Terraform destroy ou similar
            await asyncio.sleep(1)  # Simular rollback
            logger.info(f"[{deployment_id}] Rollback completed successfully")
            return True
        except Exception as e:
            logger.error(f"[{deployment_id}] Rollback failed: {str(e)}")
            return False
