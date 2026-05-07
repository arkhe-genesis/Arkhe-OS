"""
Regras de compliance para HIPAA (Health Insurance Portability and Accountability Act).
Baseado em 45 CFR Part 160 e Part 164 (Security Rule, Privacy Rule).
"""
from .base_rule import ComplianceRule, Jurisdiction, ComplianceLevel
from typing import Dict

def _contains_phi(state: Dict) -> bool:
    """Verifica se o sistema processa Protected Health Information (PHI)."""
    return state.get("data_types", {}).get("phi", False)

def _encryption_at_rest(state: Dict) -> bool:
    """Requisito: PHI deve ser criptografado em repouso (45 CFR 164.312(a)(2)(iv))."""
    encryption = state.get("encryption", {})
    return encryption.get("at_rest", False) and encryption.get("algorithm") in [
        "AES-256-GCM", "ChaCha20-Poly1305", "FHE_CKKS"
    ]

def _encryption_in_transit(state: Dict) -> bool:
    """Requisito: PHI deve ser criptografado em trânsito (45 CFR 164.312(e)(1))."""
    encryption = state.get("encryption", {})
    return encryption.get("in_transit", False) and encryption.get("protocol") in [
        "TLS-1.3", "qhttp_pqc", "mrc_encrypted"
    ]

def _access_controls(state: Dict) -> bool:
    """Requisito: Controles de acesso únicos para cada usuário (45 CFR 164.312(a)(1))."""
    access = state.get("access_control", {})
    return (
        access.get("unique_user_ids", False) and
        access.get("role_based", False) and
        access.get("audit_logging", False)
    )

def _audit_controls(state: Dict) -> bool:
    """Requisito: Registrar e examinar atividade em sistemas com PHI (45 CFR 164.312(b))."""
    audit = state.get("audit", {})
    return (
        audit.get("enabled", False) and
        audit.get("immutable", False) and
        audit.get("retention_days", 0) >= 2555  # 7 anos mínimo
    )

def _data_integrity(state: Dict) -> bool:
    """Requisito: Proteger PHI de alteração ou destruição não autorizada (45 CFR 164.312(c)(1))."""
    integrity = state.get("integrity", {})
    return integrity.get("checksums", False) and integrity.get("versioning", False)

def _transmission_security(state: Dict) -> bool:
    """Requisito: Implementar medidas de segurança para transmissão eletrônica de PHI."""
    security = state.get("transmission_security", {})
    return security.get("integrity_controls", False)

# Regras HIPAA compiladas
HIPAA_RULES = [
    ComplianceRule(
        rule_id="HIPAA-164.312(a)(2)(iv)",
        jurisdiction=Jurisdiction.HIPAA_US,
        name="Encryption at Rest for PHI",
        description="PHI must be encrypted when stored",
        condition=_contains_phi,
        requirement=_encryption_at_rest,
        severity=ComplianceLevel.CRITICAL,
        remediation="Enable AES-256-GCM or FHE encryption for data at rest",
        references=["45 CFR 164.312(a)(2)(iv)", "NIST SP 800-111"],
    ),
    ComplianceRule(
        rule_id="HIPAA-164.312(e)(1)",
        jurisdiction=Jurisdiction.HIPAA_US,
        name="Encryption in Transit for PHI",
        description="PHI must be encrypted during transmission",
        condition=_contains_phi,
        requirement=_encryption_in_transit,
        severity=ComplianceLevel.CRITICAL,
        remediation="Enable TLS 1.3 or qhttp:// with post-quantum signatures",
        references=["45 CFR 164.312(e)(1)", "NIST SP 800-52 Rev. 2"],
    ),
    ComplianceRule(
        rule_id="HIPAA-164.312(a)(1)",
        jurisdiction=Jurisdiction.HIPAA_US,
        name="Unique User Identification",
        description="Assign unique identifiers to track user activity",
        condition=lambda s: True,  # Sempre aplicável
        requirement=_access_controls,
        severity=ComplianceLevel.HIGH,
        remediation="Implement RBAC with unique user IDs and audit logging",
        references=["45 CFR 164.312(a)(1)"],
    ),
    ComplianceRule(
        rule_id="HIPAA-164.312(b)",
        jurisdiction=Jurisdiction.HIPAA_US,
        name="Audit Controls",
        description="Record and examine activity in systems containing PHI",
        condition=lambda s: True,
        requirement=_audit_controls,
        severity=ComplianceLevel.HIGH,
        remediation="Enable immutable audit logging with 7-year retention",
        references=["45 CFR 164.312(b)", "45 CFR 164.308(a)(1)(ii)(D)"],
    ),
    ComplianceRule(
        rule_id="HIPAA-164.312(c)(1)",
        jurisdiction=Jurisdiction.HIPAA_US,
        name="Data Integrity Controls",
        description="Protect PHI from improper alteration or destruction",
        condition=_contains_phi,
        requirement=_data_integrity,
        severity=ComplianceLevel.MEDIUM,
        remediation="Enable checksums, versioning, and write-once storage",
        references=["45 CFR 164.312(c)(1)"],
    ),
]
