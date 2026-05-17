#!/usr/bin/env python3
"""
ARKHE OS Substratum 210: MoonPay Canonical Integration Tool
Canon: INF.OMEGA.NABLA.210.MOONPAY.1.0
Selo Canônico: integrado ao Substratum 210 (The Project 2.0)

Integra a REST API da MoonPay (https://dev.moonpay.com) como um sistema
de pagamentos canônico da Catedral. Cada endpoint é uma ferramenta registrada
no CanonicalToolCallingSystem, com assinatura PQC, ancoragem TemporalChain,
circuit breaker e rate limiting.

Autenticação: API Key via header Authorization (server-side) ou Bearer token (client-side).
Base URL: https://api.moonpay.com (produção) / https://api.moonpay.dev (sandbox).
"""

import asyncio
import hashlib
import hmac
import json
import time
import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import aiohttp
from tool_calling.canonical_tool_system import ToolDefinition, ToolCallRequest

# ═══════════════════════════════════════════════════════════════
# CONFIGURAÇÕES E TIPOS CANÔNICOS
# ═══════════════════════════════════════════════════════════════

class MoonPayEnvironment(Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"

@dataclass
class MoonPayConfig:
    """Configuração canônica para integração MoonPay."""
    api_key: str                          # sk_test_... ou sk_live_...
    webhook_key: Optional[str] = None     # chave secreta para verificação de webhooks
    environment: MoonPayEnvironment = MoonPayEnvironment.SANDBOX
    rate_limit_per_sec: float = 25.0      # abaixo do limite oficial de 30 req/s
    max_retries: int = 3
    circuit_breaker_threshold: int = 5

@dataclass
class MoonPayApiResponse:
    """Resposta canônica da API MoonPay."""
    endpoint: str
    status_code: int
    data: Optional[Dict] = None
    error: Optional[str] = None
    request_id: Optional[str] = None
    temporal_seal: Optional[str] = None
    latency_ms: float = 0.0

# ═══════════════════════════════════════════════════════════════
# CLIENTE CANÔNICO MOONPAY
# ═══════════════════════════════════════════════════════════════

class MoonPayCanonicalTool:
    """
    Cliente canônico da MoonPay API.
    Cada operação é registrada como ferramenta no CanonicalToolCallingSystem.
    """

    BASE_URLS = {
        MoonPayEnvironment.PRODUCTION: "https://api.moonpay.com",
        MoonPayEnvironment.SANDBOX:    "https://api.moonpay.dev",
    }
    PLATFORM_PATH = "/platform/v1"

    def __init__(self, config: MoonPayConfig, tool_system=None,
                 temporal_chain=None, phi_bus=None, hsm_signer=None):
        self.config = config
        self.base_url = self.BASE_URLS[config.environment]
        self.tool_system = tool_system
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self.hsm = hsm_signer
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limit_window: List[float] = []
        self._failure_count = 0
        self._circuit_open = False

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _check_rate_limit(self) -> bool:
        now = time.time()
        self._rate_limit_window = [t for t in self._rate_limit_window if now - t < 1.0]
        if len(self._rate_limit_window) >= self.config.rate_limit_per_sec:
            return False
        self._rate_limit_window.append(now)
        return True

    async def _request(self, method: str, path: str, body: Optional[Dict] = None,
                       use_access_token: Optional[str] = None) -> MoonPayApiResponse:
        """Executa requisição HTTP autenticada à API MoonPay."""
        if self._circuit_open:
            return MoonPayApiResponse(endpoint=path, status_code=503,
                                       error="Circuit breaker open")

        if not await self._check_rate_limit():
            return MoonPayApiResponse(endpoint=path, status_code=429,
                                       error="Rate limit exceeded")

        url = f"{self.base_url}{self.PLATFORM_PATH}{path}"
        headers = {"Content-Type": "application/json"}
        if use_access_token:
            headers["Authorization"] = f"Bearer {use_access_token}"
        else:
            headers["Authorization"] = f"Api-Key {self.config.api_key}"

        session = await self._get_session()
        start = time.time()
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                async with session.request(method, url, json=body, headers=headers,
                                           timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    latency = (time.time() - start) * 1000
                    request_id = resp.headers.get("X-Request-Id")
                    data = await resp.json() if resp.status < 400 else None
                    error = await resp.text() if resp.status >= 400 else None
                    self._failure_count = 0
                    result = MoonPayApiResponse(endpoint=path, status_code=resp.status,
                                                 data=data, error=error,
                                                 request_id=request_id, latency_ms=latency)
                    if self.temporal:
                        result.temporal_seal = await self._anchor_event(path, resp.status)
                    return result
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = str(e)
                self._failure_count += 1
                if self._failure_count >= self.config.circuit_breaker_threshold:
                    self._circuit_open = True
                await asyncio.sleep(2 ** attempt)
        return MoonPayApiResponse(endpoint=path, status_code=0, error=last_error)

    async def _anchor_event(self, endpoint: str, status_code: int) -> str:
        if not self.temporal:
            return ""
        payload = {"endpoint": endpoint, "status": status_code, "timestamp": time.time()}
        seal = await self.temporal.anchor_event("moonpay_api_call", payload)
        return seal.get("seal", "") if isinstance(seal, dict) else str(seal)

    # ─── ENDPOINTS CANÔNICOS ──────────────────────────────

    async def create_session(self, external_customer_id: str, device_ip: str, email: Optional[str] = None, phone_number: Optional[str] = None) -> MoonPayApiResponse:
        """Cria um session token para inicializar uma conexão."""
        body = {"externalCustomerId": external_customer_id, "deviceIp": device_ip}
        if email:           body["email"] = email
        if phone_number:    body["phoneNumber"] = phone_number
        return await self._request("POST", "/sessions", body)

    async def get_transaction(self, transaction_id: str) -> MoonPayApiResponse:
        """Obtém detalhes de uma transação por ID."""
        return await self._request("GET", f"/transactions/{transaction_id}")

    async def list_transactions(self, cursor: Optional[str] = None, from_date: Optional[str] = None, to_date: Optional[str] = None) -> MoonPayApiResponse:
        """Lista transações do usuário conectado com paginação."""
        params = {}
        if cursor:    params["cursor"] = cursor
        if from_date: params["fromDate"] = from_date
        if to_date:   params["toDate"] = to_date
        qs = f"?{urlencode(params)}" if params else ""
        return await self._request("GET", f"/transactions{qs}")

    async def get_quote(self, source: str, destination: str, source_amount: str, wallet_address: str, payment_method: str, access_token: str) -> MoonPayApiResponse:
        """Obtém uma cotação executável para compra de cripto."""
        body = {"source": source, "destination": destination,
                "sourceAmount": source_amount, "walletAddress": wallet_address,
                "paymentMethod": payment_method}
        return await self._request("POST", "/quotes", body, use_access_token=access_token)

    async def list_payment_methods(self, access_token: str) -> MoonPayApiResponse:
        """Lista métodos de pagamento disponíveis para o cliente."""
        return await self._request("GET", "/payment-methods",
                                    use_access_token=access_token)

    async def delete_payment_method(self, payment_method_id: str, access_token: str) -> MoonPayApiResponse:
        """Remove um método de pagamento armazenado."""
        payment_method_id = parameters.get("payment_method_id", "")
        return await self._request("DELETE", f"/payment-methods/{payment_method_id}",
                                    use_access_token=access_token)

    # ─── WEBHOOK VERIFICATION ──────────────────────────────

    def verify_webhook_signature(self, payload: bytes,
                                 signature_header: str) -> bool:
        """Verifica assinatura de webhook MoonPay (Moonpay-Signature-V2)."""
        if not self.config.webhook_key:
            return False
        computed = hmac.new(self.config.webhook_key.encode(), payload,
                            hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, signature_header)

    # ─── REGISTRO DE FERRAMENTAS ──────────────────────────

    def register_all_tools(self, tool_system) -> int:
        """Registra todos os endpoints MoonPay como ferramentas canônicas."""
        tools = [
            ToolDefinition(tool_id="moonpay_create_session", name="MoonPay: Create Session Token",
                           description="Create session token",
                           handler=self.create_session, agent_owner="payment_sentinel",
                           confidence_required=0.95, parameters_schema={"type": "object", "properties": {"external_customer_id": {"type": "string"}, "device_ip": {"type": "string"}, "email": {"type": "string"}, "phone_number": {"type": "string"}}}),
            ToolDefinition(tool_id="moonpay_get_transaction", name="MoonPay: Get Transaction",
                           description="Get transaction by id",
                           handler=self.get_transaction, agent_owner="payment_sentinel",
                           confidence_required=0.90, parameters_schema={"type": "object", "properties": {"transaction_id": {"type": "string"}}}),
            ToolDefinition(tool_id="moonpay_list_transactions", name="MoonPay: List Transactions",
                           description="List transactions",
                           handler=self.list_transactions, agent_owner="payment_sentinel",
                           confidence_required=0.85, parameters_schema={"type": "object", "properties": {"cursor": {"type": "string"}, "from_date": {"type": "string"}, "to_date": {"type": "string"}}}),
            ToolDefinition(tool_id="moonpay_get_quote", name="MoonPay: Get Executable Quote",
                           description="Get executable quote",
                           handler=self.get_quote, agent_owner="payment_sentinel",
                           confidence_required=0.95, parameters_schema={"type": "object", "properties": {"source": {"type": "string"}, "destination": {"type": "string"}, "source_amount": {"type": "string"}, "wallet_address": {"type": "string"}, "payment_method": {"type": "string"}, "access_token": {"type": "string"}}}),
            ToolDefinition(tool_id="moonpay_list_payment_methods", name="MoonPay: List Payment Methods",
                           description="List payment methods",
                           handler=self.list_payment_methods, agent_owner="payment_sentinel",
                           confidence_required=0.90, parameters_schema={"type": "object", "properties": {"access_token": {"type": "string"}}}),
            ToolDefinition(tool_id="moonpay_delete_payment_method", name="MoonPay: Delete Payment Method",
                           description="Delete payment method",
                           handler=self.delete_payment_method, agent_owner="payment_sentinel",
                           confidence_required=0.95, parameters_schema={"type": "object", "properties": {"payment_method_id": {"type": "string"}, "access_token": {"type": "string"}}}),
        ]
        for t in tools:
            tool_system.register_tool(t)
        return len(tools)
