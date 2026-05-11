# data_portability.py — Motor de portabilidade de dados interoperável

import asyncio
import json
import hashlib
import time
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass, asdict
from enum import Enum
from audit_logger import AuditLogger, AuditRecord, DecisionType

class ExportFormat(Enum):
    JSON_LD = "json-ld"
    CSV = "csv"
    PDF = "pdf"

@dataclass
class ExportPackage:
    export_id: str
    citizen_id: str
    format: ExportFormat
    content: str
    timestamp: float
    signature: str

class DataPortabilityEngine:
    """
    Motor que permite ao cidadão exportar sua história decisória.
    """

    def __init__(self, audit_logger: AuditLogger):
        self.audit = audit_logger

    async def request_export(self, citizen_id: str, format: ExportFormat) -> ExportPackage:
        """Coleta dados do cidadão e gera um pacote de exportação."""

        # 1. Filtra decisões do cidadão no ledger
        # No nosso mock, o AuditLogger não tem index por citizen_id,
        # então filtramos no contexto.
        all_records = self.audit.ledger.values()
        citizen_records = [
            r for r in all_records
            if r.context.get("citizen_id") == citizen_id
        ]

        # 2. Transforma para o formato solicitado (Simulado)
        if format == ExportFormat.JSON_LD:
            data = {
                "@context": "https://schema.cathedral.ark/v1",
                "type": "DecisionHistory",
                "citizen_id": citizen_id,
                "decisions": [r.to_dict() for r in citizen_records]
            }
            content = json.dumps(data, indent=2)
        elif format == ExportFormat.CSV:
            headers = "decision_id,type,timestamp,outcome\n"
            rows = [f"{r.decision_id},{r.decision_type.name},{r.timestamp},SUCCESS" for r in citizen_records]
            content = headers + "\n".join(rows)
        else: # PDF
            content = f"RELATÓRIO DE PORTABILIDADE - CIDADÃO {citizen_id}\n"
            content += "="*40 + "\n"
            for r in citizen_records:
                content += f"[{r.timestamp}] {r.decision_type.name}: {r.decision_id}\n"

        # 3. Gera hash e assinatura
        export_id = f"exp_{int(time.time())}_{hashlib.md5(citizen_id.encode()).hexdigest()[:6]}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        signature = f"sig_cathedral_{content_hash[:16]}"

        package = ExportPackage(
            export_id=export_id,
            citizen_id=citizen_id,
            format=format,
            content=content,
            timestamp=time.time(),
            signature=signature
        )

        # 4. Registra evento de portabilidade
        await self.audit.log_decision(
            DecisionType.DATA_PROCESSING,
            context={"citizen_id": citizen_id, "export_id": export_id, "format": format.name},
            explainability={"reason": "Portabilidade de dados solicitada e concluída"},
            compliance_tags=["LGPD_art18", "GDPR_art20", "FS-55"],
            expected_impact={"benefit": 1.0, "risk": 0.0}
        )

        return package
