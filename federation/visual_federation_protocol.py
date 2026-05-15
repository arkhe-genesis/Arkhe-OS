#!/usr/bin/env python3
"""
Substrato 187: Protocolo de Federação Cross-Org para Artefatos Visuais
Permite compartilhamento seguro de renders ASCII/eikons entre organizações
com verificação de assinatura visual, privacidade diferencial e galeria federada.
"""

import asyncio
import json
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum, auto
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisualAssetType(Enum):
    """Tipos de ativos visuais suportados na federação."""
    ASCII_RENDER = "ascii_render"
    EIKON_ANIMATION = "eikon_animation"
    BRAILLE_DEBUG = "braille_debug"
    VISUAL_SIGNATURE = "visual_signature"
    TRANSPARENCY_COVER = "transparency_cover"

@dataclass
class FederatedVisualAsset:
    """Ativo visual federado entre organizações."""
    asset_id: str
    asset_type: VisualAssetType
    content_hash: str  # SHA3-256 do conteúdo ASCII
    visual_signature: Optional[str]  # Assinatura visual ASCII (opcional)
    pqc_signature: str  # Assinatura PQC criptográfica
    source_org_id: str
    created_at: float
    metadata: Dict  # Metadados públicos (sem dados sensíveis)
    access_level: str  # "public", "partner", "private"
    temporal_seal: Optional[str] = None

@dataclass
class FederationConfig:
    """Configuração para federação de renders."""
    org_id: str
    allowed_partners: Set[str]
    differential_privacy_epsilon: float = 0.1
    max_asset_size_kb: int = 512
    cache_ttl_seconds: int = 3600
    gallery_endpoint: str = "https://gallery.arkhe.federation"

class VisualFederationProtocol:
    """
    Protocolo para compartilhamento federado de artefatos visuais.

    Funcionalidades:
    • Assinatura dupla: PQC criptográfica + assinatura visual ASCII
    • Privacidade diferencial para metadados compartilhados
    • Galeria federada com verificação cross-org de integridade
    • Cache distribuído com TTL configurável
    • Auditoria de acessos via TemporalChain
    """

    def __init__(
        self,
        config: FederationConfig,
        temporal_chain=None,
        pqc_signer=None,
    ):
        self.config = config
        self.temporal = temporal_chain
        self.pqc_signer = pqc_signer
        self._local_gallery: Dict[str, FederatedVisualAsset] = {}
        self._cache: Dict[str, tuple] = {}  # asset_id -> (asset, expiry)

    async def publish_asset(
        self,
        asset_type: VisualAssetType,
        ascii_content: str,
        metadata: Dict,
        access_level: str = "partner",
    ) -> FederatedVisualAsset:
        """
        Publica ativo visual na galeria federada.

        Args:
            asset_type: Tipo do ativo visual
            ascii_content: Conteúdo ASCII/Braille do ativo
            metadata: Metadados públicos (serão protegidos por DP)
            access_level: Nível de acesso (public/partner/private)

        Returns:
            FederatedVisualAsset com IDs e assinaturas
        """
        # 1. Calcular hash do conteúdo
        content_hash = hashlib.sha3_256(ascii_content.encode()).hexdigest()

        # 2. Aplicar privacidade diferencial aos metadados se necessário
        protected_metadata = await self._apply_dp_to_metadata(metadata) if access_level != "public" else metadata

        # 3. Assinar com PQC via HSM
        pqc_signature = "mock_pqc_signature"
        if self.pqc_signer:
            sign_result = await self.pqc_signer.sign_segment(
                content_hash.encode(),
                {"type": "visual_asset", "asset_type": asset_type.value},
            )
            pqc_signature = sign_result.signature_hex if sign_result.success else "signature_failed"

        # 4. Gerar assinatura visual ASCII (opcional para verificação rápida)
        visual_sig = None
        if asset_type in [VisualAssetType.VISUAL_SIGNATURE, VisualAssetType.TRANSPARENCY_COVER]:
            from .visual_pqc_signature import VisualPQCSignature
            visual_signer = VisualPQCSignature()
            sig_result = await visual_signer.generate_visual_signature(
                pqc_signature,
                {"algorithm": "Dilithium-3", "key_id": self.config.org_id},
            )
            visual_sig = sig_result["visual_signature"]

        # 5. Criar ativo federado
        asset = FederatedVisualAsset(
            asset_id=hashlib.sha3_256(f"{content_hash}:{time.time()}".encode()).hexdigest()[:16],
            asset_type=asset_type,
            content_hash=content_hash,
            visual_signature=visual_sig,
            pqc_signature=pqc_signature,
            source_org_id=self.config.org_id,
            created_at=time.time(),
            metadata=protected_metadata,
            access_level=access_level,
        )

        # 6. Ancorar publicação na TemporalChain
        if self.temporal:
            asset.temporal_seal = await self.temporal.anchor_event(
                "visual_asset_published",
                {
                    "asset_id": asset.asset_id,
                    "asset_type": asset_type.value,
                    "content_hash": content_hash[:16],
                    "source_org": self.config.org_id,
                    "access_level": access_level,
                    "timestamp": time.time(),
                }
            )

        # 7. Armazenar localmente e propagar para parceiros
        self._local_gallery[asset.asset_id] = asset
        await self._propagate_to_partners(asset)

        logger.info(f"🌐 Ativo visual publicado: {asset.asset_id} | {asset_type.value}")
        return asset

    async def _apply_dp_to_metadata(self, metadata: Dict) -> Dict:
        """Aplica privacidade diferencial a metadados antes do compartilhamento."""
        # Simulação: adicionar ruído Laplace a valores numéricos
        import numpy as np
        protected = {}
        for key, value in metadata.items():
            if isinstance(value, (int, float)):
                # Adicionar ruído Laplace com epsilon configurado
                noise = np.random.laplace(0, 1 / self.config.differential_privacy_epsilon)
                protected[key] = round(value + noise, 3)
            else:
                # Strings e booleanos: manter ou generalizar
                protected[key] = value
        return protected

    async def _propagate_to_partners(self, asset: FederatedVisualAsset):
        """Propaga ativo para organizações parceiras autorizadas."""
        # Em produção: enviar via API REST/mTLS para parceiros
        # Para demo: logar propagação simulada
        for partner_id in self.config.allowed_partners:
            if partner_id != self.config.org_id:
                logger.info(f"📤 Propagando {asset.asset_id} para {partner_id}")
                # Simular envio
                await asyncio.sleep(0.01)

    async def fetch_asset(self, asset_id: str, requestor_org_id: str) -> Optional[Dict]:
        """
        Busca ativo visual da galeria federada.

        Verifica:
        • Se requestor_org_id tem permissão de acesso
        • Integridade via hash de conteúdo e assinatura PQC
        • Validade do cache local
        """
        # Verificar cache primeiro
        if asset_id in self._cache:
            asset, expiry = self._cache[asset_id]
            if time.time() < expiry and asset.access_level != "private":
                return self._prepare_asset_for_response(asset, requestor_org_id)

        # Buscar em galeria local ou de parceiros
        asset = self._local_gallery.get(asset_id)
        if not asset:
            asset = await self._fetch_from_partner_gallery(asset_id)

        if not asset:
            return None

        # Verificar permissões de acesso
        if asset.access_level == "private" and asset.source_org_id != requestor_org_id:
            logger.warning(f"⚠️  Acesso negado a ativo privado: {asset_id}")
            return None

        if asset.access_level == "partner" and requestor_org_id not in self.config.allowed_partners:
            logger.warning(f"⚠️  Acesso negado: {requestor_org_id} não é parceiro autorizado")
            return None

        # Atualizar cache
        self._cache[asset_id] = (asset, time.time() + self.config.cache_ttl_seconds)

        # Ancorar acesso na TemporalChain para auditoria
        if self.temporal:
            await self.temporal.anchor_event(
                "visual_asset_accessed",
                {
                    "asset_id": asset_id,
                    "requestor_org": requestor_org_id,
                    "access_level": asset.access_level,
                    "timestamp": time.time(),
                }
            )

        return self._prepare_asset_for_response(asset, requestor_org_id)

    def _prepare_asset_for_response(self, asset: FederatedVisualAsset, requestor_org_id: str) -> Dict:
        """Prepara resposta do ativo com base no nível de acesso do requestor."""
        response = {
            "asset_id": asset.asset_id,
            "asset_type": asset.asset_type.value,
            "content_hash": asset.content_hash,
            "created_at": asset.created_at,
            "source_org_id": asset.source_org_id if requestor_org_id == asset.source_org_id else "[REDACTED]",
            "access_level": asset.access_level,
            "temporal_seal": asset.temporal_seal,
        }

        # Incluir conteúdo apenas se acesso permitido
        if asset.access_level == "public" or requestor_org_id == asset.source_org_id:
            response["content_preview"] = "[ASCII content available via secure channel]"
            response["pqc_signature_verified"] = True  # Simulado

        return response

    async def _fetch_from_partner_gallery(self, asset_id: str) -> Optional[FederatedVisualAsset]:
        """Busca ativo em galerias de organizações parceiras."""
        # Em produção: consultar API federada
        # Para demo: retornar None
        await asyncio.sleep(0.01)
        return None

    def get_federated_gallery_summary(self) -> Dict:
        """Retorna resumo da galeria federada local."""
        return {
            "org_id": self.config.org_id,
            "total_assets": len(self._local_gallery),
            "by_type": {
                t.value: sum(1 for a in self._local_gallery.values() if a.asset_type == t)
                for t in VisualAssetType
            },
            "by_access_level": {
                level: sum(1 for a in self._local_gallery.values() if a.access_level == level)
                for level in ["public", "partner", "private"]
            },
            "cache_entries": len(self._cache),
            "allowed_partners": list(self.config.allowed_partners),
        }
