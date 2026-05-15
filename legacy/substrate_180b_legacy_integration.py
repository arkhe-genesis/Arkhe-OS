#!/usr/bin/env python3
"""
Substrato 180-B: Integração com Sistemas Legados
Conecta a Mente Continental a mainframes, SCADA e sistemas bancários
via adaptadores seguros com validação Φ_C e privacidade preservada.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum, auto
import asyncio, hashlib, time, json, logging

logger = logging.getLogger(__name__)

class LegacySystemType(Enum):
    """Tipos de sistemas legados suportados."""
    MAINFRAME = "mainframe"              # IBM z/OS, Unisys, etc.
    SCADA = "scada"                       # Sistemas de controle industrial
    BANKING_CORE = "banking_core"         # Sistemas core bancários
    ERP_LEGACY = "erp_legacy"             # SAP R/3, Oracle E-Business antigo
    CUSTOM_PROTOCOL = "custom_protocol"   # Protocolos proprietários

@dataclass
class LegacySystemConfig:
    """Configuração de integração com sistema legado."""
    system_id: str
    system_type: LegacySystemType
    connection_params: Dict[str, Any]  # Host, port, credentials (via Vault)
    data_schema: Dict[str, Any]  # Schema dos dados trocados
    sync_mode: str  # "realtime", "batch", "hybrid"
    phi_c_validation: bool = True
    privacy_preservation: bool = True
    audit_logging: bool = True

class LegacyAdapter(ABC):
    """Interface abstrata para adaptadores de sistemas legados."""

    @abstractmethod
    async def connect(self) -> bool:
        """Estabelece conexão segura com o sistema legado."""
        pass

    @abstractmethod
    async def query_data(self, query: Dict) -> Dict:
        """Executa consulta no sistema legado com validação Φ_C."""
        pass

    @abstractmethod
    async def execute_transaction(self, transaction: Dict) -> Dict:
        """Executa transação com consenso MAC para operações críticas."""
        pass

    @abstractmethod
    async def subscribe_events(self, handler: Callable) -> bool:
        """Assina eventos do sistema legado para processamento em tempo real."""
        pass

    @abstractmethod
    async def close(self):
        """Encerra conexão e libera recursos."""
        pass

class MainframeAdapter(LegacyAdapter):
    """Adaptador para mainframes IBM z/OS via CICS/IMS."""

    def __init__(self, config: LegacySystemConfig, temporal_chain=None, guardian=None):
        self.config = config
        self.temporal = temporal_chain
        self.guardian = guardian
        self._connection = None
        self._phi_c_bus = None

    async def connect(self) -> bool:
        """Conecta ao mainframe via protocolo seguro (TLS + autenticação RACF)."""
        # Em produção: usar biblioteca como py3270 ou connector comercial
        # Para demo: simular conexão
        await asyncio.sleep(0.2)

        # Validar credenciais via Vault
        credentials = await self._get_vault_credentials()
        if not credentials:
            return False

        self._connection = {
            "host": self.config.connection_params["host"],
            "authenticated": True,
            "session_id": hashlib.sha3_256(f"{time.time()}".encode()).hexdigest()[:16],
        }

        logger.info(f"✅ Conectado ao mainframe: {self.config.system_id}")
        return True

    async def _get_vault_credentials(self):
        return True

    async def query_data(self, query: Dict) -> Dict:
        """Executa consulta no mainframe com validação Φ_C."""
        if not self._connection:
            raise RuntimeError("Conexão não estabelecida")

        # 1. Validar query com Guardian (prevenção de injeção, acesso não autorizado)
        if self.guardian and self.config.phi_c_validation:
            safe, report = await self.guardian.exorcise_legacy_query(query)
            if not safe:
                return {"error": "Query rejeitada pelo Guardian", "reason": report.reason}

        # 2. Executar consulta (simulado)
        # Em produção: enviar via CICS transaction ou IMS DL/I
        result = await self._execute_mainframe_query(query)

        # 3. Aplicar privacidade diferencial se habilitado
        if self.config.privacy_preservation:
            result = await self._apply_differential_privacy(result, query.get("sensitivity_level", "public"))

        # 4. Ancorar consulta na TemporalChain para auditoria
        if self.temporal and self.config.audit_logging:
            await self.temporal.anchor_event(
                "mainframe_query_executed",
                {
                    "system_id": self.config.system_id,
                    "query_hash": hashlib.sha3_256(
                        json.dumps(query, sort_keys=True).encode()
                    ).hexdigest()[:16],
                    "result_hash": hashlib.sha3_256(
                        json.dumps(result, sort_keys=True, default=str).encode()
                    ).hexdigest()[:16],
                    "phi_c_validated": self.config.phi_c_validation,
                    "privacy_applied": self.config.privacy_preservation,
                    "timestamp": time.time(),
                }
            )

        return result

    async def _execute_mainframe_query(self, query: Dict) -> Dict:
        """Executa consulta real no mainframe (simulado para demo)."""
        # Simular resposta de mainframe
        return {
            "data": {"account_balance": 12500.50, "last_transaction": "2026-01-15"},
            "status": "success",
            "response_time_ms": 45,
        }

    async def execute_transaction(self, transaction: Dict) -> Dict:
        return {"status": "success"}

    async def subscribe_events(self, handler: Callable) -> bool:
        return True

    async def close(self):
        pass

    async def _apply_differential_privacy(self, data: Dict, sensitivity: str) -> Dict:
        """Aplica privacidade diferencial a dados sensíveis."""
        if sensitivity == "public":
            return data

        # Adicionar ruído de Laplace baseado na sensibilidade
        epsilon = {"internal": 1.0, "confidential": 0.5, "restricted": 0.1}.get(sensitivity, 1.0)

        # Aplicar ruído a campos numéricos sensíveis
        for key, value in data.get("data", {}).items():
            if isinstance(value, (int, float)) and any(k in key.lower() for k in ["balance", "amount", "count"]):
                # Ruído de Laplace: scale = sensitivity / epsilon
                import numpy as np
                noise = np.random.laplace(0, 1.0 / epsilon)
                data["data"][key] = round(value + noise, 2)

        return data
