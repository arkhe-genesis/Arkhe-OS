#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hsm_cert_rotation.py — Substrato 9028: Sistema de Rotação Automática de Certificados HSM
Renova certificados de código sem downtime, com validação cruzada e rollback automático.
"""

import asyncio
import json
import time
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
import logging
import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# TIPOS E CONSTANTES
# ============================================================================

class RotationStatus(Enum):
    """Status do processo de rotação."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class CertificateInfo:
    """Informações de um certificado de código."""
    thumbprint: str
    subject: str
    issuer: str
    valid_from: datetime
    valid_to: datetime
    key_label: str
    hsm_provider: str
    usage: str  # "code_signing", "timestamp", etc.

    @property
    def days_until_expiry(self) -> int:
        """Dias restantes até expiração."""
        delta = self.valid_to - datetime.utcnow()
        return delta.days

    @property
    def is_expiring_soon(self) -> bool:
        """Verifica se certificado está próximo da expiração."""
        return self.days_until_expiry <= 60  # Alertar com 60 dias de antecedência

@dataclass
class RotationPlan:
    """Plano de rotação de certificado."""
    rotation_id: str
    old_cert: CertificateInfo
    new_cert: Optional[CertificateInfo]
    status: RotationStatus
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    validation_results: Dict = field(default_factory=dict)
    rollback_available: bool = True
    error_message: Optional[str] = None

# ============================================================================
# GERENCIADOR DE ROTAÇÃO
# ============================================================================

class HSMCertificateRotator:
    """Gerencia rotação automática de certificados HSM com zero downtime."""

    def __init__(self, hsm_config: Dict, catalog_paths: List[str]):
        self.hsm_config = hsm_config
        self.catalog_paths = [Path(p) for p in catalog_paths]
        self.active_rotations: Dict[str, RotationPlan] = {}
        self.notification_webhook = hsm_config.get("notification_webhook")

    async def check_certificates(self) -> List[CertificateInfo]:
        """Verifica status de todos os certificados configurados."""
        certs = []

        # Em produção: consultar HSM via PKCS#11 para listar certificados
        # Para demo: simular certificados
        simulated_certs = [
            {
                "thumbprint": "A1B2C3D4E5F6...",
                "subject": "CN=ARKHE Observatory Code Signing, O=ARKHE Observatory",
                "issuer": "CN=ARKHE Root CA, O=ARKHE Observatory",
                "valid_from": datetime(2026, 1, 1),
                "valid_to": datetime(2027, 1, 1),
                "key_label": "arkhe-cathedral-production",
                "hsm_provider": "thales",
                "usage": "code_signing",
            }
        ]

        for cert_data in simulated_certs:
            cert = CertificateInfo(**cert_data)
            certs.append(cert)

            # Alertar se expirando em breve
            if cert.is_expiring_soon:
                logger.warning(f"⚠️  Certificate expiring soon: {cert.subject} ({cert.days_until_expiry} days)")
                await self._send_notification(
                    "certificate_expiring_soon",
                    {"subject": cert.subject, "days_remaining": cert.days_until_expiry}
                )

        return certs

    async def initiate_rotation(self, cert_thumbprint: str,
                             new_key_label: Optional[str] = None) -> RotationPlan:
        """Inicia processo de rotação para um certificado."""
        rotation_id = hashlib.sha3_256(f"{cert_thumbprint}:{time.time()}".encode()).hexdigest()[:16]

        # Obter certificado atual
        certs = await self.check_certificates()
        old_cert = next((c for c in certs if c.thumbprint == cert_thumbprint), None)

        if not old_cert:
            raise ValueError(f"Certificate not found: {cert_thumbprint}")

        # Criar plano de rotação
        plan = RotationPlan(
            rotation_id=rotation_id,
            old_cert=old_cert,
            new_cert=None,
            status=RotationStatus.IN_PROGRESS,
            started_at=time.time(),
        )

        self.active_rotations[rotation_id] = plan
        logger.info(f"🔄 Starting rotation {rotation_id} for {old_cert.subject}")

        # Executar rotação em background
        asyncio.create_task(self._execute_rotation(plan, new_key_label))

        return plan

    async def _execute_rotation(self, plan: RotationPlan, new_key_label: Optional[str]):
        """Executa processo completo de rotação."""
        try:
            # 1. Gerar novo par de chaves no HSM
            logger.info(f"   1/5 Generating new key pair in HSM...")
            new_key_label = new_key_label or f"{plan.old_cert.key_label}-v2"
            new_cert = await self._generate_new_certificate(plan.old_cert, new_key_label)
            plan.new_cert = new_cert

            # 2. Assinar binários com novo certificado (sem remover o antigo)
            logger.info(f"   2/5 Signing binaries with new certificate...")
            signed_successfully = await self._dual_sign_binaries(plan.old_cert, new_cert)
            if not signed_successfully:
                raise RuntimeError("Failed to sign binaries with new certificate")

            # 3. Atualizar catálogo com ambos os certificados (período de transição)
            logger.info(f"   3/5 Updating catalog with dual certificates...")
            await self._update_catalog_dual_cert(plan.old_cert, new_cert)

            # 4. Validar integridade pós-rotação
            logger.info(f"   4/5 Validating post-rotation integrity...")
            validation = await self._validate_rotation(plan)
            plan.validation_results = validation

            if not validation["passed"]:
                raise RuntimeError(f"Validation failed: {validation['errors']}")

            # 5. Remover certificado antigo após período de graça
            logger.info(f"   5/5 Scheduling old certificate removal (30-day grace period)...")
            # Em produção: agendar remoção via scheduler
            plan.status = RotationStatus.COMPLETED
            plan.completed_at = time.time()

            logger.info(f"✅ Rotation {plan.rotation_id} completed successfully")
            await self._send_notification("rotation_completed", {"rotation_id": plan.rotation_id})

        except Exception as e:
            logger.error(f"❌ Rotation {plan.rotation_id} failed: {e}")
            plan.status = RotationStatus.FAILED
            plan.error_message = str(e)

            # Tentar rollback automático se disponível
            if plan.rollback_available:
                logger.info(f"🔄 Attempting automatic rollback...")
                rollback_success = await self._rollback_rotation(plan)
                if rollback_success:
                    plan.status = RotationStatus.ROLLED_BACK
                    await self._send_notification("rotation_rolled_back", {"rotation_id": plan.rotation_id})
                else:
                    logger.error(f"❌ Rollback failed — manual intervention required")

            await self._send_notification("rotation_failed", {
                "rotation_id": plan.rotation_id,
                "error": str(e)
            })

    async def _generate_new_certificate(self, old_cert: CertificateInfo,
                                       new_key_label: str) -> CertificateInfo:
        """Gera novo certificado no HSM baseado no antigo."""
        # Em produção: usar API do HSM para gerar CSR e obter certificado da CA
        # Para demo: simular novo certificado

        new_valid_to = datetime.utcnow() + timedelta(days=365)  # 1 ano de validade

        return CertificateInfo(
            thumbprint=hashlib.sha3_256(f"{new_key_label}:{time.time()}".encode()).hexdigest()[:20],
            subject=old_cert.subject,
            issuer=old_cert.issuer,
            valid_from=datetime.utcnow(),
            valid_to=new_valid_to,
            key_label=new_key_label,
            hsm_provider=old_cert.hsm_provider,
            usage=old_cert.usage,
        )

    async def _dual_sign_binaries(self, old_cert: CertificateInfo,
                                 new_cert: CertificateInfo) -> bool:
        """Assina binários com ambos os certificados para transição suave."""
        # Em produção: iterar sobre todos os binários catalogados e aplicar assinatura dupla
        # signtool suporta múltiplas assinaturas via /as (append signature)

        binaries = ["catedral.sys"]  # Lista real viria do catálogo

        for binary in binaries:
            # Primeira assinatura (nova)
            cmd_new = [
                "signtool", "sign", "/as",  # /as = append signature
                "/fd", "SHA3_256",
                "/tr", "http://timestamp.digicert.com",
                "/td", "SHA3_256",
                "/csp", self.hsm_config.get("csp_name"),
                "/kc", new_cert.key_label,
                binary,
            ]

            result = subprocess.run(cmd_new, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"❌ Failed to sign {binary} with new cert: {result.stderr}")
                return False

        logger.info(f"✅ Binaries dual-signed successfully")
        return True

    async def _update_catalog_dual_cert(self, old_cert: CertificateInfo,
                                       new_cert: CertificateInfo) -> bool:
        """Atualiza catálogo para aceitar ambos os certificados."""
        # Em produção: modificar catálogo .cat para incluir ambos os thumbprints
        # e atualizar políticas de validação

        for catalog_path in self.catalog_paths:
            if not catalog_path.exists():
                continue

            # Backup do catálogo original
            backup_path = catalog_path.with_suffix(".cat.bak")
            subprocess.run(["copy", str(catalog_path), str(backup_path)], shell=True)

            # Em produção: editar XML do catálogo para adicionar novo certificado
            # e configurar política de validação "accept either"
            logger.info(f"📋 Updated catalog for dual-cert validation: {catalog_path}")

        return True

    async def _validate_rotation(self, plan: RotationPlan) -> Dict:
        """Valida integridade pós-rotação."""
        results = {
            "passed": True,
            "checks": {},
            "errors": [],
        }

        # 1. Verificar assinatura de binários com novo certificado
        for binary in ["catedral.sys"]:
            cmd = ["signtool", "verify", "/pa", "/v", binary]
            result = subprocess.run(cmd, capture_output=True, text=True)
            results["checks"][f"{binary}_signature"] = {
                "passed": result.returncode == 0,
                "output": result.stdout[:200] if result.stdout else None,
            }
            if result.returncode != 0:
                results["passed"] = False
                results["errors"].append(f"Signature validation failed for {binary}")

        # 2. Verificar coerência Φ_C pós-rotação
        # Em produção: consultar Φ_C bus real
        phi_c = 0.9973  # Simulado
        results["checks"]["phi_c_stability"] = {
            "passed": phi_c >= 0.99,
            "value": phi_c,
        }
        if phi_c < 0.99:
            results["passed"] = False
            results["errors"].append(f"Φ_C dropped to {phi_c} post-rotation")

        # 3. Verificar catálogo atualizado
        for catalog_path in self.catalog_paths:
            if catalog_path.exists():
                cmd = ["Test-FileCatalog", "-Path", str(catalog_path.parent),
                      "-CatalogFilePath", str(catalog_path)]
                # Em produção: executar via PowerShell
                results["checks"][f"catalog_{catalog_path.name}"] = {
                    "passed": True,  # Simulado
                }

        return results

    async def _rollback_rotation(self, plan: RotationPlan) -> bool:
        """Reverte rotação em caso de falha."""
        try:
            # 1. Restaurar catálogo do backup
            for catalog_path in self.catalog_paths:
                backup_path = catalog_path.with_suffix(".cat.bak")
                if backup_path.exists():
                    subprocess.run(["copy", str(backup_path), str(catalog_path)], shell=True)
                    logger.info(f"🔄 Restored catalog from backup: {catalog_path}")

            # 2. Re-assinar binários com certificado antigo (se necessário)
            # (Geralmente não necessário se assinatura dupla foi usada)

            # 3. Remover novo certificado do HSM (opcional, manter para próxima tentativa)

            logger.info(f"✅ Rollback completed for rotation {plan.rotation_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            return False

    async def _send_notification(self, event_type: str, data: Dict):
        """Envia notificação via webhook configurado."""
        if not self.notification_webhook:
            return

        payload = {
            "event": event_type,
            "timestamp": time.time(),
            "data": data,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.notification_webhook, json=payload, timeout=10) as resp:
                    if resp.status == 200:
                        logger.info(f"📧 Notification sent: {event_type}")
                    else:
                        logger.warning(f"⚠️  Notification failed: {resp.status}")
        except Exception as e:
            logger.error(f"❌ Failed to send notification: {e}")

    async def auto_rotation_scheduler(self, check_interval_hours: int = 24):
        """Scheduler para verificação automática e rotação proativa."""
        logger.info(f"🕐 Starting auto-rotation scheduler (check every {check_interval_hours}h)")

        while True:
            try:
                certs = await self.check_certificates()

                for cert in certs:
                    if cert.is_expiring_soon and cert.days_until_expiry <= 30:
                        logger.info(f"🔄 Auto-initiating rotation for expiring cert: {cert.subject}")
                        await self.initiate_rotation(cert.thumbprint)

                await asyncio.sleep(check_interval_hours * 3600)

            except Exception as e:
                logger.error(f"❌ Error in auto-rotation scheduler: {e}")
                await asyncio.sleep(3600)  # Retry after 1 hour on error

# ============================================================================
# CLI E ENTRY POINT
# ============================================================================

async def main():
    import argparse

    parser = argparse.ArgumentParser(description="HSM Certificate Rotation Manager")
    parser.add_argument("--check", action="store_true", help="Check certificate status")
    parser.add_argument("--rotate", help="Initiate rotation for certificate thumbprint")
    parser.add_argument("--status", help="Check status of rotation by ID")
    parser.add_argument("--config", required=True, help="Path to HSM config JSON")
    parser.add_argument("--catalog", action="append", help="Catalog paths to update (repeatable)")
    parser.add_argument("--auto", action="store_true", help="Enable auto-rotation scheduler")

    args = parser.parse_args()

    # Carregar configuração HSM
    with open(args.config) as f:
        hsm_config = json.load(f)

    rotator = HSMCertificateRotator(hsm_config, args.catalog or [])

    if args.check:
        certs = await rotator.check_certificates()
        print(f"\n📋 Certificate Status:")
        for cert in certs:
            status = "⚠️  EXPIRING SOON" if cert.is_expiring_soon else "✅ Valid"
            print(f"   {status} | {cert.subject}")
            print(f"      Expires: {cert.valid_to.strftime('%Y-%m-%d')} ({cert.days_until_expiry} days)")
            print(f"      Key: {cert.key_label} @ {cert.hsm_provider}")
            print()

    elif args.rotate:
        plan = await rotator.initiate_rotation(args.rotate)
        print(f"🔄 Rotation initiated: {plan.rotation_id}")
        print(f"   Old cert: {plan.old_cert.subject}")
        print(f"   Status: {plan.status.value}")

    elif args.status:
        plan = rotator.active_rotations.get(args.status)
        if plan:
            print(f"📊 Rotation Status: {plan.rotation_id}")
            print(f"   Status: {plan.status.value}")
            print(f"   Started: {datetime.fromtimestamp(plan.started_at) if plan.started_at else 'N/A'}")
            print(f"   Validation: {plan.validation_results}")
            if plan.error_message:
                print(f"   Error: {plan.error_message}")
        else:
            print(f"❌ Rotation not found: {args.status}")

    elif args.auto:
        print("🕐 Starting auto-rotation scheduler...")
        await rotator.auto_rotation_scheduler()

    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
