#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
base_connector.py — Conector Base para Plataformas de Transmissão
Define o template unificado para integração com a Malha Arkhe (Twitch, YouTube, TikTok, etc.)
"""

import abc
import logging

logger = logging.getLogger(__name__)

class BroadcastConnector(abc.ABC):
    """Classe base abstrata para conectores de plataforma de streaming."""

    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.is_connected = False
        self.metrics = {
            "streams_active": 0,
            "viewers": 0,
            "messages_processed": 0
        }

    def connect(self, credentials_provider) -> bool:
        """Estabelece conexão usando as credenciais providenciadas (Vault/OAuth2)."""
        token = credentials_provider.get_oauth_token(self.platform_name.lower())
        if token:
            logger.info(f"[{self.platform_name}] Autenticado via Vault (token_len={len(token)})")
            self.is_connected = True
            return True
        logger.error(f"[{self.platform_name}] Falha na autenticação via Vault.")
        return False

    @abc.abstractmethod
    def get_stream_info(self, stream_id: str) -> dict:
        """Obtém dados de uma stream específica."""
        pass

    @abc.abstractmethod
    def process_chat(self, guardian_bus) -> None:
        """Processa o chat da plataforma, validando via Guardian."""
        pass

    def get_metrics(self) -> dict:
        """Retorna as métricas atuais do conector."""
        return self.metrics

    def close(self):
        """Encerra a conexão e libera recursos."""
        self.is_connected = False
        logger.info(f"[{self.platform_name}] Conexão encerrada.")
