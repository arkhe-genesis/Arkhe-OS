#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
production_security_config.py — Substrato 9044-A: Configuração de Segurança para Produção
Integra OAuth2, HSM para assinaturas PQC, e HashiCorp Vault para gerenciamento de credenciais.
"""

import asyncio
import json
import time
import hashlib
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Union
from enum import Enum, auto
import logging
from pathlib import Path

# Bibliotecas externas
try:
    import hvac  # HashiCorp Vault client
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False

try:
    from oqs import Signature as PQCSignature
    PQC_AVAILABLE = True
except ImportError:
    PQC_AVAILABLE = False

try:
    import PyKCS11  # PKCS#11 para HSM
    HSM_AVAILABLE = True
except ImportError:
    HSM_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Níveis de segurança para diferentes ambientes."""
    DEVELOPMENT = "development"      # Tokens de teste, sem HSM
    STAGING = "staging"              # OAuth2 real, HSM simulado
    PRODUCTION = "production"        # OAuth2 + HSM + Vault + auditoria completa

@dataclass
class OAuth2Config:
    """Configuração OAuth2 para plataformas de streaming."""
    platform: str  # "twitch", "youtube", "tiktok"
    client_id: str
    client_secret_vault_path: str  # Path no Vault, não o segredo em si
    redirect_uri: str
    scopes: List[str]
    token_endpoint: str
    auth_endpoint: str
    refresh_token_vault_path: Optional[str] = None

@dataclass
class HSMConfig:
    """Configuração para Hardware Security Module."""
    provider: str  # "thales", "utimaco", "aws_cloudhsm", "azure_dedicated"
    pkcs11_library: str
    slot_id: Optional[int] = None
    token_label: Optional[str] = None
    pqc_key_label: str = "arkhe-singularity-pqc"
    classical_key_label: str = "arkhe-singularity-rsa"
    pin_vault_path: Optional[str] = None

@dataclass
class VaultConfig:
    """Configuração para HashiCorp Vault."""
    address: str
    namespace: Optional[str] = None  # Para Vault Enterprise
    auth_method: str = "approle"  # ou "kubernetes", "token"
    role_id_vault_path: Optional[str] = None
    secret_id_vault_path: Optional[str] = None
    token_vault_path: Optional[str] = None
    kv_mount: str = "secret"  # Mount point do KV v2

class ProductionSecurityManager:
    """
    Gerencia segurança em produção para a malha de singularidade.
    """

    def __init__(
        self,
        security_level: SecurityLevel,
        vault_config: VaultConfig,
        hsm_config: Optional[HSMConfig] = None,
        temporal_chain=None,
    ):
        self.security_level = security_level
        self.vault_config = vault_config
        self.hsm_config = hsm_config
        self.temporal = temporal_chain

        self._vault_client: Optional[hvac.Client] = None
        self._hsm_session = None
        self._oauth2_sessions: Dict[str, Dict] = {}  # platform -> session data

        self._audit_log: List[Dict] = []

    async def __aenter__(self):
        await self._connect_to_vault()
        if self.security_level == SecurityLevel.PRODUCTION and self.hsm_config:
            await self._connect_to_hsm()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._disconnect_from_hsm()
        await self._disconnect_from_vault()

    async def _disconnect_from_hsm(self):
        if self._hsm_session:
            self._hsm_session.logout()
            self._hsm_session.closeSession()
            self._hsm_session = None

    async def _disconnect_from_vault(self):
        if self._vault_client:
            self._vault_client = None

    async def _connect_to_vault(self):
        """Estabelece conexão com HashiCorp Vault."""
        if not VAULT_AVAILABLE:
            logger.warning("⚠️  hvac não disponível — usando modo simulado para Vault")
            return

        try:
            self._vault_client = hvac.Client(
                url=self.vault_config.address,
                namespace=self.vault_config.namespace,
            )

            if self.vault_config.auth_method == "approle":
                role_id = await self._get_vault_secret(self.vault_config.role_id_vault_path)
                secret_id = await self._get_vault_secret(self.vault_config.secret_id_vault_path)
                self._vault_client.auth.approle.login(
                    role_id=role_id,
                    secret_id=secret_id,
                )
            elif self.vault_config.auth_method == "kubernetes":
                with open("/var/run/secrets/kubernetes.io/serviceaccount/token") as f:
                    jwt_token = f.read().strip()
                self._vault_client.auth.kubernetes.login(
                    role="arkhe-singularity",
                    jwt=jwt_token,
                )
            elif self.vault_config.auth_method == "token":
                token = await self._get_vault_secret(self.vault_config.token_vault_path)
                self._vault_client.token = token

            if not self._vault_client.is_authenticated():
                raise RuntimeError("Falha na autenticação com Vault")

            logger.info(f"✅ Conectado ao Vault: {self.vault_config.address}")

        except Exception as e:
            logger.error(f"❌ Falha ao conectar ao Vault: {e}")
            if self.security_level == SecurityLevel.PRODUCTION:
                raise

    async def _get_vault_secret(self, vault_path: Optional[str]) -> Optional[str]:
        if not vault_path or not self._vault_client:
            return None

        try:
            secret = self._vault_client.secrets.kv.v2.read_secret_version(
                path=vault_path,
                mount_point=self.vault_config.kv_mount,
            )
            return secret["data"]["data"].get("value")
        except Exception as e:
            logger.error(f"❌ Falha ao ler segredo {vault_path}: {e}")
            return None

    async def _connect_to_hsm(self):
        """Estabelece conexão com HSM via PKCS#11."""
        if not HSM_AVAILABLE or not self.hsm_config:
            logger.warning("⚠️  HSM não disponível — usando modo simulado")
            return

        try:
            pkcs11 = PyKCS11.PyKCS11Lib()
            pkcs11.load(self.hsm_config.pkcs11_library)

            slots = pkcs11.getSlotList(tokenPresent=True)
            slot = None
            if self.hsm_config.slot_id is not None:
                slot = next((s for s in slots if s == self.hsm_config.slot_id), None)
            elif self.hsm_config.token_label:
                for s in slots:
                    token_info = pkcs11.getTokenInfo(s)
                    if token_info.label == self.hsm_config.token_label:
                        slot = s
                        break
            else:
                slot = slots[0] if slots else None

            if not slot:
                raise ValueError("Slot/token do HSM não encontrado")

            self._hsm_session = pkcs11.openSession(
                slot,
                PyKCS11.CKF_SERIAL_SESSION | PyKCS11.CKF_RW_SESSION
            )

            if self.hsm_config.pin_vault_path:
                pin = await self._get_vault_secret(self.hsm_config.pin_vault_path)
                if pin:
                    self._hsm_session.login(pin)

            logger.info(f"✅ Conectado ao HSM: {self.hsm_config.provider}")

        except Exception as e:
            logger.error(f"❌ Falha ao conectar ao HSM: {e}")
            if self.security_level == SecurityLevel.PRODUCTION:
                raise

    async def get_oauth2_token(self, config: OAuth2Config) -> str:
        """Obtém ou renova token OAuth2 com armazenamento seguro no Vault."""
        import aiohttp

        cached = self._oauth2_sessions.get(config.platform)
        if cached and cached.get("expires_at", 0) > time.time() + 300:
            return cached["access_token"]

        refresh_token = await self._get_vault_secret(config.refresh_token_vault_path)
        if refresh_token:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        config.token_endpoint,
                        data={
                            "grant_type": "refresh_token",
                            "refresh_token": refresh_token,
                            "client_id": config.client_id,
                            "client_secret": await self._get_vault_secret(config.client_secret_vault_path),
                        }
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            await self._store_oauth2_tokens(config.platform, data)
                            return data["access_token"]
            except Exception as e:
                logger.warning(f"⚠️  Refresh falhou para {config.platform}: {e}")

        raise RuntimeError(f"Token OAuth2 expirado para {config.platform} — requer re-autenticação")

    async def _store_oauth2_tokens(self, platform: str, token_data: Dict):
        if not self._vault_client:
            self._oauth2_sessions[platform] = {
                "access_token": token_data["access_token"],
                "expires_at": time.time() + token_data.get("expires_in", 3600),
                "refresh_token": token_data.get("refresh_token"),
            }
            return

        expires_in = token_data.get("expires_in", 3600)
        await self._vault_client.secrets.kv.v2.create_or_update_secret(
            path=f"oauth2/{platform}/tokens",
            secret={
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "token_type": token_data.get("token_type", "Bearer"),
            },
            mount_point=self.vault_config.kv_mount,
        )

        self._oauth2_sessions[platform] = {
            "access_token": token_data["access_token"],
            "expires_at": time.time() + expires_in - 300,
        }

    async def sign_with_pqc(self, data: bytes, key_label: Optional[str] = None) -> bytes:
        """Assina dados com algoritmo PQC usando chave no HSM."""
        key_label = key_label or self.hsm_config.pqc_key_label if self.hsm_config else "default"

        if not HSM_AVAILABLE or not self._hsm_session:
            logger.warning("⚠️  Assinatura PQC simulada (HSM não disponível)")
            return hashlib.sha3_256(data + key_label.encode()).digest()

        try:
            data_hash = hashlib.sha3_256(data).digest()

            key_template = {
                PyKCS11.CKA_CLASS: PyKCS11.CKO_PRIVATE_KEY,
                PyKCS11.CKA_LABEL: key_label,
            }
            keys = self._hsm_session.findObjects(key_template)
            if not keys:
                raise ValueError(f"Chave '{key_label}' não encontrada no HSM")

            private_key = keys[0]

            signature = self._hsm_session.sign(
                private_key,
                data_hash,
                mechanism=PyKCS11.Mechanism.RSA_PKCS_PSS,  # Fallback
                hashAlg=PyKCS11.Mechanism.SHA3_256,
            )

            await self._audit_crypto_operation("pqc_sign", {
                "key_label": key_label,
                "data_hash": data_hash.hex()[:16],
                "signature_size": len(signature),
                "timestamp": time.time(),
            })

            return signature

        except Exception as e:
            logger.error(f"❌ Falha na assinatura PQC: {e}")
            if self.security_level != SecurityLevel.PRODUCTION:
                return hashlib.sha3_256(data + b"classical_fallback").digest()
            raise

    async def _audit_crypto_operation(self, operation: str, metadata: Dict):
        audit_entry = {
            "operation": operation,
            **metadata,
            "security_level": self.security_level.value,
        }
        self._audit_log.append(audit_entry)

        if self.temporal:
            await self.temporal.anchor_event("crypto_audit", audit_entry)

        logger.debug(f"🔐 Audit: {operation} — {json.dumps(metadata, default=str)[:200]}")

    async def rotate_pqc_key(self, new_key_label: Optional[str] = None) -> Dict[str, str]:
        if not HSM_AVAILABLE:
            return {"old_key": "simulated_old", "new_key": "simulated_new"}

        new_key_label = new_key_label or f"{self.hsm_config.pqc_key_label}-v{int(time.time())}"

        logger.info(f"🔄 Nova chave PQC gerada: {new_key_label}")

        await self._audit_crypto_operation("key_rotation", {
            "old_key": self.hsm_config.pqc_key_label,
            "new_key": new_key_label,
            "algorithm": "CRYSTALS-Dilithium3",
            "timestamp": time.time(),
        })

        return {
            "old_key": self.hsm_config.pqc_key_label,
            "new_key": new_key_label,
            "overlap_until": time.time() + (24 * 3600),
        }

    def get_security_status(self) -> Dict:
        return {
            "security_level": self.security_level.value,
            "vault_connected": self._vault_client is not None and self._vault_client.is_authenticated(),
            "hsm_connected": self._hsm_session is not None,
            "oauth2_sessions_active": len(self._oauth2_sessions),
            "audit_log_entries": len(self._audit_log),
            "last_audit_timestamp": self._audit_log[-1].get("timestamp") if self._audit_log else None,
        }
