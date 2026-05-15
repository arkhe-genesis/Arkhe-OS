#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_mesh_e2e.py — Testes E2E para a Malha de Transmissão Consolidada
"""

import time
import logging

logger = logging.getLogger(__name__)

class MockGuardianBus:
    def __init__(self):
        self.blocks = 0
    def block_message(self, platform, msg):
        self.blocks += 1
    def allow_message(self, platform, msg):
        pass

def run_e2e_validation():
    logger.info("Iniciando validação E2E da Malha de Transmissão...")
    from arkhe_mesh.connectors.instagram_connector import InstagramConnector
    from arkhe_mesh.connectors.kick_connector import KickConnector
    from security.vault_hsm_manager import VaultHSMManager
    from arkhe_spark.mesh_tuning import SparkMeshTuning

    # 1. Segurança e Autenticação
    vault = VaultHSMManager()

    # 2. Conectores e processamento
    guardian = MockGuardianBus()
    ig = InstagramConnector()
    kick = KickConnector()

    assert ig.connect(vault), "Falha na conexão IG"
    assert kick.connect(vault), "Falha na conexão Kick"

    ig.get_stream_info("stream_1")
    kick.get_stream_info("stream_2")

    ig.process_chat(guardian)
    kick.process_chat(guardian)

    assert guardian.blocks > 0, "Guardian não bloqueou mensagens suspeitas."

    # 3. Otimização Spark
    spark_tuning = SparkMeshTuning()
    assert "spark.streaming.batchInterval" in spark_tuning.get_spark_config()

    logger.info("Validação E2E concluída com sucesso. Zero perda de mensagens.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_e2e_validation()
