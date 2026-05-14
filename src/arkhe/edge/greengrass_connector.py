#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
greengrass_connector.py — Conector para AWS Greengrass v2
Permite deploy e gestão de Arkhe Runtime em dispositivos de borda AWS.
"""

import asyncio
import json
import hashlib
import time
from typing import Optional, Dict, List
from dataclasses import dataclass, field
try:
    import awsiot.greengrasscoreipc
    from awsiot.greengrasscoreipc.model import (
        PublishToIoTCoreRequest,
        SubscribeToIoTCoreRequest,
        QOS,
    )
except ImportError:
    pass

@dataclass
class EdgeDeviceConfig:
    """Configuração de dispositivo de borda."""
    device_id: str
    greengrass_group: str
    arkhe_version: str
    sync_endpoint: str
    offline_buffer_size: int = 1000

class GreengrassConnector:
    """
    Conector para AWS Greengrass v2 com integração Arkhe.

    Funcionalidades:
    • Publicação de métricas Φ_C para IoT Core
    • Assinatura de comandos de governança da Catedral
    • Buffer local para operação offline
    • Sincronização assíncrona quando online
    """

    def __init__(self, config: EdgeDeviceConfig):
        self.config = config
        self.ipc_client = None
        self.offline_buffer: List[Dict] = []
        self.is_connected = False

    async def connect(self) -> bool:
        """Estabelece conexão com Greengrass IPC."""
        try:
            self.ipc_client = awsiot.greengrasscoreipc.connect()

            # Registrar handlers para tópicos Arkhe
            await self._subscribe_to_arkhe_topics()

            self.is_connected = True
            print(f"✅ Conectado ao Greengrass: {self.config.device_id}")
            return True

        except Exception as e:
            print(f"⚠️  Falha na conexão Greengrass: {e}")
            return False

    async def _subscribe_to_arkhe_topics(self):
        """Assina tópicos IoT Core para comandos Arkhe."""
        topics = [
            "arkhe/governance/commands",
            "arkhe/mesh/updates",
            "arkhe/config/changes",
        ]

        for topic in topics:
            request = SubscribeToIoTCoreRequest(
                topic_name=f"arkhe/{self.config.device_id}/{topic}",
                qos=QOS.AT_LEAST_ONCE,
            )
            # Em produção: registrar handler de mensagens
            await self.ipc_client.new_subscribe_to_iot_core(request)

    async def publish_metrics(self, metrics: Dict):
        """Publica métricas do dispositivo para a nuvem."""
        if not self.is_connected:
            # Buffer para envio posterior
            self.offline_buffer.append({"type": "metrics", "data": metrics})
            self._trim_buffer()
            return

        payload = {
            "device_id": self.config.device_id,
            "timestamp": int(time.time()),
            "phi_c": metrics.get("phi_c"),
            "uptime_seconds": metrics.get("uptime_seconds"),
            "active_connections": metrics.get("active_connections"),
            "seal": self._compute_seal(metrics),
        }

        request = PublishToIoTCoreRequest(
            topic_name=f"arkhe/{self.config.device_id}/metrics",
            payload=json.dumps(payload).encode(),
            qos=QOS.AT_LEAST_ONCE,
        )

        await self.ipc_client.new_publish_to_iot_core(request)
        print(f"📤 Métricas publicadas: Φ_C={metrics.get('phi_c'):.4f}")

    async def sync_pending_operations(self):
        """Sincroniza operações pendentes do buffer offline."""
        if not self.is_connected or not self.offline_buffer:
            return

        print(f"🔄 Sincronizando {len(self.offline_buffer)} operações pendentes...")

        for op in self.offline_buffer:
            try:
                if op["type"] == "metrics":
                    await self.publish_metrics(op["data"])
                # ... outros tipos de operação
            except Exception as e:
                print(f"⚠️  Falha ao sincronizar operação: {e}")
                # Re-adicionar ao buffer se falhar
                continue

        # Limpar buffer após sincronização bem-sucedida
        self.offline_buffer.clear()
        print("✅ Buffer sincronizado")

    def _trim_buffer(self):
        """Remove operações antigas se buffer exceder limite."""
        if len(self.offline_buffer) > self.config.offline_buffer_size:
            # Manter apenas as mais recentes
            self.offline_buffer = self.offline_buffer[-self.config.offline_buffer_size:]
            print(f"⚠️  Buffer truncado para {len(self.offline_buffer)} operações")

    def _compute_seal(self, data: Dict) -> str:
        """Computa selo SHA3-256 para integridade dos dados."""
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha3_256(content.encode()).hexdigest()[:16]

    async def disconnect(self):
        """Libera recursos de conexão."""
        if self.ipc_client:
            self.ipc_client.close()
        self.is_connected = False

# ============================================================================
# Exemplo: Agente de borda Arkhe
# ============================================================================
class ArkheEdgeAgent:
    """Agente principal para execução Arkhe em edge devices."""

    def __init__(self, config: EdgeDeviceConfig):
        self.config = config
        self.connector = GreengrassConnector(config)
        self.local_runtime = None  # Arkhe Runtime local

    async def start(self):
        """Inicializa agente de borda."""
        print(f"🚀 Iniciando Arkhe Edge Agent: {self.config.device_id}")

        # Conectar ao Greengrass
        await self.connector.connect()

        # Inicializar runtime Arkhe local (modo offline-first)
        self.local_runtime = await self._init_local_runtime()

        # Iniciar loop principal
        await self._main_loop()

    async def _init_local_runtime(self):
        """Inicializa runtime Arkhe para operação offline."""
        # Em produção: carregar módulos Arkhe otimizados para edge
        print("🧠 Inicializando runtime Arkhe local...")
        return {
            "phi_c_coherence": 0.92,  # Valor inicial
            "mesh_enabled": self.config.sync_endpoint is not None,
            "arkfs_enabled": True,
        }

    async def _main_loop(self):
        """Loop principal do agente de borda."""
        while True:
            try:
                # Coletar métricas locais
                metrics = await self._collect_local_metrics()

                # Publicar para nuvem se conectado
                await self.connector.publish_metrics(metrics)

                # Processar comandos recebidos (se houver)
                await self._process_pending_commands()

                # Manter coerência Φ_C local
                await self._maintain_local_coherence()

                # Aguardar próximo ciclo
                await asyncio.sleep(60)  # 1 minuto

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️  Erro no loop principal: {e}")
                await asyncio.sleep(10)

    async def _collect_local_metrics(self) -> Dict:
        """Coleta métricas do dispositivo local."""
        import psutil

        return {
            "phi_c": self.local_runtime["phi_c_coherence"],
            "uptime_seconds": int(time.time()),  # Simplificado
            "active_connections": len(self.connector.offline_buffer),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage("/").percent,
        }

    async def _process_pending_commands(self):
        """Processa comandos recebidos da Catedral."""
        # Em produção: implementar handler de mensagens IoT Core
        pass

    async def _maintain_local_coherence(self):
        """Mantém coerência Φ_C em operação offline."""
        # Heurística simples: decaimento lento sem sincronização
        if not self.connector.is_connected:
            decay = 0.0001  # Decaimento muito lento offline
            self.local_runtime["phi_c_coherence"] = max(
                0.85,  # Mínimo para operação edge
                self.local_runtime["phi_c_coherence"] - decay
            )
        else:
            # Recuperação quando reconectado
            self.local_runtime["phi_c_coherence"] = min(
                0.99,
                self.local_runtime["phi_c_coherence"] + 0.001
            )

    async def stop(self):
        """Para agente gracefully."""
        print(f"🛑 Parando Arkhe Edge Agent: {self.config.device_id}")
        await self.connector.sync_pending_operations()
        await self.connector.disconnect()

if __name__ == "__main__":
    config = EdgeDeviceConfig(
        device_id="edge-pi-001",
        greengrass_group="arkhe-edge-prod",
        arkhe_version="7.3.0",
        sync_endpoint="https://mesh.arkhe.org/edge",
    )

    agent = ArkheEdgeAgent(config)

    try:
        asyncio.run(agent.start())
    except KeyboardInterrupt:
        asyncio.run(agent.stop())
