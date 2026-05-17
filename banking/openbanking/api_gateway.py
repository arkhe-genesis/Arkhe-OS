#!/usr/bin/env python3
"""
Substrato 200.1: Open Banking API Gateway
API Gateway compatível com PSD2, Open Banking Brasil e consent management.
Implementa endpoints de consentimento, autorização e recursos bancários.
"""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum, auto
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConsentStatus(Enum):
    """Status de consentimento do cliente."""
    AWAITING_AUTHORISATION = "AWAITING_AUTHORISATION"
    AUTHORISED = "AUTHORISED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"

@dataclass
class ConsentRecord:
    """Registro de consentimento do cliente."""
    consent_id: str
    customer_id: str
    permissions: List[str]  # ["ACCOUNTS_READ", "PAYMENTS_CREATE", etc.]
    status: ConsentStatus
    created_at: float
    expires_at: float
    authorized_at: Optional[float] = None
    temporal_seal: Optional[str] = None

class OpenBankingGateway:
    """
    API Gateway para Open Banking (PSD2, Open Banking Brasil).

    Funcionalidades:
    • Consentimento do cliente (consent API)
    • Autorização via OAuth2 com certificados PQC
    • Recursos bancários (accounts, transactions, payments)
    • Rate limiting e throttling por TPP
    • Auditoria completa via TemporalChain
    """

    # Permissões definidas pelo Open Banking Brasil
    PERMISSIONS = [
        "ACCOUNTS_READ",
        "ACCOUNTS_BALANCES_READ",
        "ACCOUNTS_TRANSACTIONS_READ",
        "ACCOUNTS_OVERDRAFT_LIMITS_READ",
        "RESOURCES_READ",
        "CREDIT_CARDS_ACCOUNTS_READ",
        "PAYMENTS_CREATE",
        "PAYMENTS_READ"
    ]

    def __init__(
        self,
        institution_id: str,
        temporal_chain=None,
        phi_bus=None,
        hsm_signer=None,
        rate_limit_per_minute: int = 60
    ):
        self.institution_id = institution_id
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self.hsm = hsm_signer
        self.rate_limit = rate_limit_per_minute

        self._consents: Dict[str, ConsentRecord] = {}
        self._rate_limit_counters: Dict[str, int] = {}
        self._api_calls: List[Dict] = []

    async def create_consent(
        self,
        customer_id: str,
        permissions: List[str],
        expiration_hours: int = 24
    ) -> ConsentRecord:
        """
        Cria solicitação de consentimento (POST /consents).

        Fluxo:
        1. Validar permissões solicitadas
        2. Criar registro de consentimento
        3. Redirecionar cliente para autorização
        4. Ancorar na TemporalChain
        """
        # Validar permissões
        invalid_perms = [p for p in permissions if p not in self.PERMISSIONS]
        if invalid_perms:
            raise ValueError(f"Permissões inválidas: {invalid_perms}")

        consent_id = hashlib.sha3_256(
            f"{customer_id}:{permissions}:{time.time()}".encode()
        ).hexdigest()[:16]

        now = time.time()
        consent = ConsentRecord(
            consent_id=consent_id,
            customer_id=customer_id,
            permissions=permissions,
            status=ConsentStatus.AWAITING_AUTHORISATION,
            created_at=now,
            expires_at=now + (expiration_hours * 3600)
        )

        # Ancorar na TemporalChain
        if self.temporal:
            consent.temporal_seal = await self.temporal.anchor_event(
                "openbanking_consent_created",
                {
                    "consent_id": consent_id,
                    "customer_id": customer_id,
                    "permissions": permissions,
                    "status": consent.status.value,
                    "timestamp": now
                }
            )

        self._consents[consent_id] = consent

        logger.info(f"📋 Consentimento criado: {consent_id} ({len(permissions)} permissões)")
        return consent

    async def authorize_consent(
        self,
        consent_id: str,
        authorization_code: str
    ) -> ConsentRecord:
        """
        Autoriza consentimento (POST /consents/{consentId}/authorise).

        Fluxo OAuth2:
        1. Validar authorization code
        2. Atualizar status do consentimento
        3. Gerar access token (JWT assinado com PQC)
        4. Ancorar autorização na TemporalChain
        """
        if consent_id not in self._consents:
            raise ValueError(f"Consentimento {consent_id} não encontrado")

        consent = self._consents[consent_id]

        # Validar authorization code (mock)
        if not authorization_code.startswith("AUTH_"):
            raise ValueError("Código de autorização inválido")

        # Verificar expiração
        if time.time() > consent.expires_at:
            consent.status = ConsentStatus.EXPIRED
            raise ValueError("Consentimento expirado")

        # Atualizar status
        consent.status = ConsentStatus.AUTHORISED
        consent.authorized_at = time.time()

        # Gerar access token (JWT assinado com PQC via HSM)
        access_token = self._generate_access_token(consent)

        # Ancorar na TemporalChain
        if self.temporal:
            await self.temporal.anchor_event(
                "openbanking_consent_authorised",
                {
                    "consent_id": consent_id,
                    "customer_id": consent.customer_id,
                    "permissions": consent.permissions,
                    "token_hash": hashlib.sha3_256(access_token.encode()).hexdigest()[:16],
                    "timestamp": time.time()
                }
            )

        logger.info(f"✅ Consentimento autorizado: {consent_id}")
        return consent

    def _generate_access_token(self, consent: ConsentRecord) -> str:
        """Gera JWT access token assinado com PQC via HSM."""
        payload = {
            "sub": consent.customer_id,
            "consent_id": consent.consent_id,
            "permissions": consent.permissions,
            "iat": int(time.time()),
            "exp": int(consent.expires_at),
            "iss": self.institution_id
        }

        # Assinar com PQC via HSM (mock)
        signature = hashlib.sha3_256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()[:32]

        return f"eyJhbGciOiJEaWxpdGhpdW0zIn0.{json.dumps(payload)}.{signature}"

    async def get_accounts(
        self,
        access_token: str,
        customer_id: str
    ) -> Dict:
        """
        GET /accounts — Lista contas do cliente.
        Requer consentimento ACCOUNTS_READ.
        """
        await self._enforce_rate_limit(customer_id)
        await self._validate_token(access_token, "ACCOUNTS_READ")

        # Mock: retornar contas
        accounts = [
            {
                "accountId": "12345678-9",
                "accountType": "CURRENT",
                "balance": 15000.00,
                "currency": "BRL"
            }
        ]

        # Ancorar acesso na TemporalChain
        if self.temporal:
            await self.temporal.anchor_event("openbanking_api_call", {
                "endpoint": "GET /accounts",
                "customer_id": customer_id,
                "timestamp": time.time()
            })

        return {"accounts": accounts}

    async def create_payment(
        self,
        access_token: str,
        customer_id: str,
        amount: float,
        recipient: str
    ) -> Dict:
        """
        POST /payments — Cria pagamento.
        Requer consentimento PAYMENTS_CREATE.
        """
        await self._enforce_rate_limit(customer_id)
        await self._validate_token(access_token, "PAYMENTS_CREATE")

        payment_id = hashlib.sha3_256(
            f"{customer_id}:{amount}:{recipient}:{time.time()}".encode()
        ).hexdigest()[:12]

        # Mock: processar pagamento
        result = {
            "paymentId": payment_id,
            "status": "ACCEPTED",
            "amount": amount,
            "currency": "BRL",
            "recipient": recipient,
            "createdAt": time.time()
        }

        # Assinar com PQC via HSM
        if self.hsm:
            result["pqc_signature"] = await self.hsm.sign(
                json.dumps(result, sort_keys=True).encode()
            )

        # Ancorar na TemporalChain
        if self.temporal:
            await self.temporal.anchor_event("openbanking_payment_created", {
                "payment_id": payment_id,
                "amount": amount,
                "customer_id": customer_id,
                "recipient": recipient,
                "timestamp": time.time()
            })

        logger.info(f"💳 Pagamento criado: {payment_id} ({amount} BRL)")
        return result

    async def _enforce_rate_limit(self, customer_id: str):
        """Aplica rate limiting por TPP."""
        current_minute = int(time.time() / 60)
        key = f"{customer_id}:{current_minute}"

        count = self._rate_limit_counters.get(key, 0)
        if count >= self.rate_limit:
            raise RuntimeError(f"Rate limit excedido ({self.rate_limit}/min)")

        self._rate_limit_counters[key] = count + 1

    async def _validate_token(self, access_token: str, required_permission: str):
        """Valida JWT access token e permissões."""
        # Mock: em produção, verificar assinatura PQC e claims
        if not access_token.startswith("eyJ"):
            raise RuntimeError("Token inválido")

    def get_gateway_statistics(self) -> Dict:
        """Retorna estatísticas do API Gateway."""
        return {
            "active_consents": len([c for c in self._consents.values() if c.status == ConsentStatus.AUTHORISED]),
            "total_api_calls": len(self._api_calls),
            "rate_limit_exceeded": sum(
                1 for k, v in self._rate_limit_counters.items()
                if v >= self.rate_limit
            ),
            "institution_id": self.institution_id
        }
