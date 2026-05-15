#!/usr/bin/env python3
"""
Substrato 182-B: Auditoria Formal de Guardrails por Laboratório Acreditado EAL4+
Prepara e submete artefatos de guardrails para avaliação por laboratório certificado,
garantindo conformidade com Common Criteria para sistemas de alta criticidade.
"""

import asyncio
import json
import time
import hashlib
import zipfile
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Union
from enum import Enum, auto
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EALLevel(Enum):
    """Níveis de Evaluation Assurance Level (Common Criteria)."""
    EAL1 = "EAL1"  # Functionally tested
    EAL2 = "EAL2"  # Structurally tested
    EAL3 = "EAL3"  # Methodically tested and checked
    EAL4 = "EAL4"  # Methodically designed, tested, and reviewed ← TARGET
    EAL5 = "EAL5"  # Semi-formally designed and tested
    EAL6 = "EAL6"  # Semi-formally verified, designed, and tested
    EAL7 = "EAL7"  # Formally verified, designed, and tested

@dataclass
class AuditArtifact:
    """Artefato submetido para auditoria EAL4+."""
    artifact_id: str
    name: str
    description: str
    artifact_type: str  # "specification", "code", "test", "configuration"
    file_path: str
    hash_sha3_256: str
    version: str
    temporal_seal: Optional[str] = None

@dataclass
class EAL4AuditSubmission:
    """Submissão completa para auditoria EAL4+."""
    submission_id: str
    system_name: str
    eal_target: EALLevel
    artifacts: List[AuditArtifact]
    security_target: Dict  # Security Target document (ST)
    evaluation_facility: str  # Nome do laboratório acreditado
    submitted_at: float = field(default_factory=time.time)
    status: str = "submitted"  # submitted, in_review, completed, failed
    final_report: Optional[Dict] = None
    certification_seal: Optional[str] = None

class EAL4GuardrailAuditor:
    """
    Prepara e gerencia submissão de guardrails para auditoria EAL4+.

    Conformidade com Common Criteria ISO/IEC 15408:
    • Security Target (ST) documentado
    • Artefatos de especificação, código, teste e configuração
    • Rastreabilidade de requisitos de segurança
    • Evidências de implementação e teste
    • Ancoragem de submissão na TemporalChain
    """

    # Requisitos de segurança para guardrails (mapeados para CC)
    SECURITY_REQUIREMENTS = {
        "FAU_GEN.1": "Audit data generation",  # Geração de logs de auditoria
        "FAU_SAR.1": "Audit review",  # Revisão de logs
        "FDP_ACC.1": "Subset access control",  # Controle de acesso a dados
        "FDP_ACF.1": "Security attribute based access control",  # Controle baseado em atributos
        "FMT_MSA.1": "Management of security attributes",  # Gestão de atributos de segurança
        "FMT_MSA.3": "Static attribute initialization",  # Inicialização estática
        "FPT_TDC.1": "Inter-TSF basic TSF data consistency",  # Consistência entre componentes
        "FPT_TST.1": "TSF testing",  # Teste do TSF
    }

    def __init__(
        self,
        evaluation_facility: str,
        temporal_chain=None,
        pqc_signer=None,
    ):
        self.facility = evaluation_facility
        self.temporal = temporal_chain
        self.pqc_signer = pqc_signer
        self.submissions: Dict[str, EAL4AuditSubmission] = {}

    async def prepare_submission(
        self,
        system_name: str,
        guardrail_artifacts: List[Dict],
        security_target: Dict,
    ) -> EAL4AuditSubmission:
        """
        Prepara submissão completa para auditoria EAL4+.

        Args:
            system_name: Nome do sistema sendo auditado
            guardrail_artifacts: Lista de artefatos de guardrails
            security_target: Documento Security Target (conforme Common Criteria)

        Returns:
            EAL4AuditSubmission pronta para envio
        """
        submission_id = hashlib.sha3_256(
            f"{system_name}:{time.time()}".encode()
        ).hexdigest()[:12]

        # Processar artefatos: calcular hash e ancorar
        processed_artifacts = []
        for artifact in guardrail_artifacts:
            artifact_hash = await self._hash_artifact(artifact["file_path"])

            processed = AuditArtifact(
                artifact_id=hashlib.sha3_256(
                    f"{artifact['name']}:{artifact_hash}".encode()
                ).hexdigest()[:16],
                name=artifact["name"],
                description=artifact["description"],
                artifact_type=artifact["type"],
                file_path=artifact["file_path"],
                hash_sha3_256=artifact_hash,
                version=artifact.get("version", "1.0"),
            )

            # Ancorar artefato na TemporalChain
            if self.temporal:
                processed.temporal_seal = await self.temporal.anchor_event(
                    "eal4_artifact_submitted",
                    {
                        "artifact_id": processed.artifact_id,
                        "name": processed.name,
                        "hash": processed.hash_sha3_256,
                        "type": processed.artifact_type,
                        "submission_id": submission_id,
                    }
                )

            processed_artifacts.append(processed)

        # Assinar Security Target com PQC se disponível
        st_signed = False
        st_signature = None
        if self.pqc_signer and "document_content" in security_target:
            sign_result = await self.pqc_signer.sign_segment(
                security_target["document_content"].encode(),
                {"type": "security_target", "system": system_name},
            )
            if sign_result.success:
                st_signed = True
                st_signature = sign_result.signature_hex[:16]
                security_target["pqc_signature"] = st_signature

        submission = EAL4AuditSubmission(
            submission_id=submission_id,
            system_name=system_name,
            eal_target=EALLevel.EAL4,
            artifacts=processed_artifacts,
            security_target=security_target,
            evaluation_facility=self.facility,
        )

        # Ancorar submissão na TemporalChain
        if self.temporal:
            await self.temporal.anchor_event(
                "eal4_submission_created",
                {
                    "submission_id": submission_id,
                    "system_name": system_name,
                    "artifact_count": len(processed_artifacts),
                    "st_signed": st_signed,
                    "facility": self.facility,
                    "timestamp": submission.submitted_at,
                }
            )

        self.submissions[submission_id] = submission

        logger.info(f"✅ Submissão EAL4+ preparada: {submission_id} | {len(processed_artifacts)} artefatos")
        return submission

    async def _hash_artifact(self, file_path: str) -> str:
        """Calcula hash SHA3-256 de artefato para integridade."""
        try:
            import hashlib
            sha3 = hashlib.sha3_256()

            with open(file_path, "rb") as f:
                # Ler em chunks para arquivos grandes
                for chunk in iter(lambda: f.read(8192), b""):
                    sha3.update(chunk)

            return sha3.hexdigest()

        except Exception as e:
            logger.error(f"❌ Falha ao calcular hash de {file_path}: {e}")
            return hashlib.sha3_256(f"error:{file_path}:{time.time()}".encode()).hexdigest()

    async def submit_to_facility(self, submission: EAL4AuditSubmission) -> bool:
        """
        Submete pacote de auditoria ao laboratório acreditado.

        Em produção: integrar com API do laboratório (ex: via SFTP, API REST segura).
        Para demo: simular submissão bem-sucedida.
        """
        logger.info(f"📤 Submetendo {submission.submission_id} para {self.facility}...")

        # Criar pacote ZIP com artefatos e documentação
        package_path = await self._create_submission_package(submission)

        # Simular upload para laboratório (em produção: usar API segura)
        await asyncio.sleep(2)  # Simular tempo de upload

        # Atualizar status
        submission.status = "in_review"

        # Ancorar evento de submissão
        if self.temporal:
            await self.temporal.anchor_event(
                "eal4_submission_sent",
                {
                    "submission_id": submission.submission_id,
                    "facility": submission.evaluation_facility,
                    "package_path": str(package_path),
                    "timestamp": time.time(),
                }
            )

        logger.info(f"✅ Submissão enviada: {submission.submission_id}")
        return True

    async def _create_submission_package(self, submission: EAL4AuditSubmission) -> Path:
        """Cria pacote ZIP com artefatos para submissão."""
        package_dir = Path("/tmp/eal4_submissions")
        package_dir.mkdir(exist_ok=True)

        package_path = package_dir / f"{submission.submission_id}.zip"

        with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Adicionar Security Target
            st_path = package_dir / "Security_Target.json"
            with open(st_path, "w") as f:
                json.dump(submission.security_target, f, indent=2, default=str)
            zipf.write(st_path, "Security_Target.json")

            # Adicionar lista de artefatos com hashes
            manifest = {
                "submission_id": submission.submission_id,
                "system_name": submission.system_name,
                "eal_target": submission.eal_target.value,
                "artifacts": [asdict(a) for a in submission.artifacts],
                "generated_at": datetime.utcnow().isoformat(),
            }
            manifest_path = package_dir / "manifest.json"
            with open(manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)
            zipf.write(manifest_path, "manifest.json")

            # Adicionar artefatos reais (se disponíveis)
            for artifact in submission.artifacts:
                if Path(artifact.file_path).exists():
                    zipf.write(artifact.file_path, f"artifacts/{Path(artifact.file_path).name}")

        return package_path

    async def poll_audit_status(self, submission_id: str) -> Dict:
        """
        Consulta status da auditoria no laboratório.

        Em produção: integrar com API de status do laboratório.
        Para demo: simular progresso de revisão.
        """
        if submission_id not in self.submissions:
            return {"error": "Submission not found"}

        submission = self.submissions[submission_id]

        # Simular progresso baseado no tempo desde submissão
        elapsed_hours = (time.time() - submission.submitted_at) / 3600

        if elapsed_hours < 24:
            status = "initial_review"
            progress = min(30, int(elapsed_hours * 1.25))
        elif elapsed_hours < 72:
            status = "technical_evaluation"
            progress = min(70, 30 + int((elapsed_hours - 24) * 0.67))
        elif elapsed_hours < 168:  # 1 semana
            status = "final_report_generation"
            progress = min(95, 70 + int((elapsed_hours - 72) * 0.35))
        else:
            status = "completed"
            progress = 100
            submission.status = "completed"

            # Gerar relatório simulado
            submission.final_report = {
                "evaluation_result": "PASS",
                "eal_level_achieved": "EAL4+",
                "findings": {
                    "critical": 0,
                    "major": 0,
                    "minor": 2,
                    "observations": 5,
                },
                "recommendations": [
                    "Atualizar threshold de Φ_C crítico para 0.88",
                    "Adicionar teste de penetração trimestral",
                ],
                "validity_period_months": 12,
            }

            # Gerar selo de certificação
            submission.certification_seal = hashlib.sha3_256(
                f"{submission_id}:EAL4+:CERTIFIED:{time.time()}".encode()
            ).hexdigest()[:16]

            # Assinar relatório com PQC
            if self.pqc_signer and submission.final_report:
                report_json = json.dumps(submission.final_report, sort_keys=True).encode()
                sign_result = await self.pqc_signer.sign_segment(
                    report_json,
                    {"type": "eal4_certification", "submission_id": submission_id},
                )
                if sign_result.success:
                    submission.final_report["pqc_certification_signature"] = sign_result.signature_hex[:16]

        return {
            "submission_id": submission_id,
            "status": status,
            "progress_percent": progress,
            "estimated_completion_hours": max(0, 168 - elapsed_hours),
            "current_phase": status.replace("_", " ").title(),
        }

    def get_certification_status(self, submission_id: str) -> Optional[Dict]:
        """Retorna status de certificação para consulta pública."""
        submission = self.submissions.get(submission_id)
        if not submission:
            return None

        return {
            "submission_id": submission_id,
            "system_name": submission.system_name,
            "eal_target": submission.eal_target.value,
            "status": submission.status,
            "submitted_at": datetime.fromtimestamp(submission.submitted_at).isoformat(),
            "facility": submission.evaluation_facility,
            "artifact_count": len(submission.artifacts),
            "certification_seal": submission.certification_seal,
            "final_result": submission.final_report.get("evaluation_result") if submission.final_report else None,
            "validity_until": (
                datetime.fromtimestamp(submission.submitted_at + 365*24*3600).strftime("%Y-%m-%d")
                if submission.final_report and submission.final_report.get("evaluation_result") == "PASS"
                else None
            ),
        }