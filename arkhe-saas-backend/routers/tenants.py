# arkhe-saas-backend/routers/tenants.py
"""Multi-tenant management endpoints."""
from fastapi import APIRouter

from schemas import TenantCreateRequest, TenantResponse
from models import create_tenant, get_tenant

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.post("", response_model=TenantResponse)
def create_tenant_endpoint(body: TenantCreateRequest):
    """Create a new tenant organization."""
    tenant = create_tenant(name=body.name)
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        api_key=tenant.api_key,
        created_at=tenant.created_at.timestamp(),
    )


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant_endpoint(tenant_id: str):
    """Get tenant details."""
    tenant = get_tenant(tenant_id)
    if not tenant:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Tenant not found")
    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        api_key=tenant.api_key,
        created_at=tenant.created_at.timestamp(),
    )
