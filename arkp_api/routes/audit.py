from fastapi import APIRouter, Depends, HTTPException, Query
from arkp_security.temporal_audit import TemporalAuditLogger
from arkp_auth.auth import verify_token
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

class AuditQueryParams(BaseModel):
    limit: int = 50
    offset: int = 0
    domain: str | None = None
    blocked_only: bool = False
    min_severity: float = 0.0

class IPFSMock:
    @staticmethod
    def store_audit_record(record_dict):
        """Mock de armazenamento descentralizado IPFS/Arweave para imutabilidade a longo prazo."""
        return "ipfs://mock_hash_" + str(hash(str(record_dict)))

@router.get("/records")
async def get_audit_records(
    params: AuditQueryParams = Depends(),
    user = Depends(verify_token),
):
    """Retorna registros de auditoria com paginação e filtros."""
    # Query ao ledger temporal com cache Redis
    results = await TemporalAuditLogger.query(
        filter=params,
        limit=params.limit,
        offset=params.offset,
        mask_pii=True,  # Máscara automática de tokens sensíveis
    )
    return {"total": results.total, "records": results.items}

@router.get("/record/{seal}")
async def get_record_by_seal(seal: str, user = Depends(verify_token)):
    """Consulta registro específico via selo criptográfico."""
    record = await TemporalAuditLogger.get_by_seal(seal)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    record_dict = getattr(record, "to_redacted_dict", lambda: {"mock": "data"})()
    ipfs_hash = IPFSMock.store_audit_record(record_dict)

    return {"record": record_dict, "ipfs_hash": ipfs_hash}
