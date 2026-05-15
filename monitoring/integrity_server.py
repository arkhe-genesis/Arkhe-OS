#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
integrity_server.py — Servidor WebSocket para monitoramento de integridade em tempo real.
Publica métricas de integridade, alertas de tampering e atualizações de Φ_C para clientes conectados.
"""

import asyncio
import json
import time
import hashlib
import websockets
from typing import Dict, Set, Optional
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

@dataclass
class ServerConfig:
    """Configuração do servidor de monitoramento."""
    host: str = "0.0.0.0"
    port: int = 8080
    metrics_interval: float = 1.0  # segundos entre atualizações
    phi_c_check_interval: float = 5.0
    tampering_detection_enabled: bool = True
    alert_retention_hours: int = 24

# ============================================================================
# GERENCIADOR DE CONEXÕES E PUBLICAÇÃO
# ============================================================================

class IntegrityServer:
    """Servidor WebSocket para publicação de métricas de integridade."""

    def __init__(self, config: ServerConfig):
        self.config = config
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.subscriptions: Dict[str, Set[websockets.WebSocketServerProtocol]] = {
            "metrics": set(),
            "alerts": set(),
            "phi_c": set(),
        }
        self.running = False

        # Estado interno de métricas
        self.current_metrics: Dict[str, float] = {}
        self.phi_c_value = 0.9973

    async def register(self, websocket: websockets.WebSocketServerProtocol):
        """Registra nova conexão de cliente."""
        self.clients.add(websocket)
        logger.info(f"🔗 Cliente conectado: {websocket.remote_address}")

        try:
            async for message in websocket:
                await self._handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 Cliente desconectado: {websocket.remote_address}")
        finally:
            self.clients.discard(websocket)
            for channel in self.subscriptions.values():
                channel.discard(websocket)

    async def _handle_client_message(self, websocket: websockets.WebSocketServerProtocol, message: str):
        """Processa mensagem recebida de cliente."""
        try:
            data = json.loads(message)
            action = data.get("action")

            if action == "subscribe":
                channels = data.get("channels", [])
                for channel in channels:
                    if channel in self.subscriptions:
                        self.subscriptions[channel].add(websocket)
                        logger.info(f"📡 {websocket.remote_address} subscribed to {channel}")

                # Enviar confirmação
                await websocket.send(json.dumps({
                    "type": "subscribed",
                    "channels": channels,
                    "timestamp": time.time()
                }))

            elif action == "unsubscribe":
                channels = data.get("channels", [])
                for channel in channels:
                    if channel in self.subscriptions:
                        self.subscriptions[channel].discard(websocket)

            elif action == "acknowledge_alert":
                alert_id = data.get("alert_id")
                # Processar reconhecimento de alerta (em produção: atualizar banco de dados)
                logger.info(f"✅ Alert {alert_id} acknowledged by {websocket.remote_address}")

        except json.JSONDecodeError:
            logger.warning(f"⚠️  Invalid JSON from {websocket.remote_address}: {message[:100]}")

    async def publish_metric(self, component: str, metric_name: str, value: float,
                            threshold_warning: float = 0.95, threshold_critical: float = 0.90):
        """Publica atualização de métrica para clientes assinantes."""
        payload = {
            "type": "metric_update",
            "payload": {
                "component": component,
                "metric_name": metric_name,
                "value": value,
                "threshold_warning": threshold_warning,
                "threshold_critical": threshold_critical,
                "timestamp": time.time()
            }
        }

        message = json.dumps(payload)
        for client in self.subscriptions["metrics"]:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                pass

        # Atualizar estado interno
        key = f"{component}:{metric_name}"
        self.current_metrics[key] = value

    async def publish_alert(self, alert_data: Dict):
        """Publica alerta de tampering para clientes assinantes."""
        payload = {
            "type": "alert",
            "payload": {
                "alert_id": hashlib.sha3_256(f"{alert_data['component']}:{time.time()}".encode()).hexdigest()[:16],
                "timestamp": time.time(),
                **alert_data
            }
        }

        message = json.dumps(payload)
        for client in self.subscriptions["alerts"]:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                pass

        logger.warning(f"🚨 Alert published: {alert_data['alert_type']} on {alert_data['component']}")

    async def publish_phi_c_update(self, value: float):
        """Publica atualização de coerência Φ_C."""
        self.phi_c_value = value

        payload = {
            "type": "phi_c_update",
            "payload": {
                "value": value,
                "timestamp": time.time(),
                "trend": "stable"  # Em produção: calcular tendência real
            }
        }

        message = json.dumps(payload)
        for client in self.subscriptions["phi_c"]:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                pass

    async def _monitoring_loop(self):
        """Loop principal de monitoramento."""
        logger.info("🔄 Starting integrity monitoring loop...")

        while self.running:
            try:
                # 1. Verificar integridade do driver
                driver_hash = self._compute_driver_hash()
                expected_hash = "c4f3e2a1b0d5f6e7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1"

                if driver_hash != expected_hash:
                    await self.publish_alert({
                        "component": "catedral.sys",
                        "alert_type": "hash_mismatch",
                        "severity": "critical",
                        "description": "Driver hash mismatch detected — possible tampering",
                        "evidence": {
                            "expected": expected_hash[:16] + "...",
                            "actual": driver_hash[:16] + "...",
                        }
                    })
                else:
                    await self.publish_metric("catedral.sys", "hash_integrity", 1.0)

                # 2. Verificar coerência Φ_C
                phi_c = self._measure_phi_c()
                await self.publish_phi_c_update(phi_c)

                if phi_c < 0.95:
                    await self.publish_alert({
                        "component": "system",
                        "alert_type": "phi_c_drop",
                        "severity": "critical",
                        "description": f"Φ_C coherence dropped to {phi_c:.4f} — below critical threshold",
                        "evidence": {"current": phi_c, "threshold": 0.95}
                    })

                # 3. Verificar assinatura do catálogo
                catalog_valid = self._verify_catalog_signature()
                await self.publish_metric("catedral.cat", "signature_valid", 1.0 if catalog_valid else 0.0)

                if not catalog_valid:
                    await self.publish_alert({
                        "component": "catedral.cat",
                        "alert_type": "signature_invalid",
                        "severity": "high",
                        "description": "Security catalog signature validation failed",
                        "evidence": {"validation_result": "invalid"}
                    })

                # 4. Verificar acessos não autorizados (simulado)
                if self.config.tampering_detection_enabled:
                    unauthorized = self._detect_unauthorized_access()
                    if unauthorized:
                        await self.publish_alert({
                            "component": "system",
                            "alert_type": "unauthorized_access",
                            "severity": "high",
                            "description": "Potential unauthorized access attempt detected",
                            "evidence": unauthorized
                        })

                await asyncio.sleep(self.config.metrics_interval)

            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Backoff em caso de erro

    def _compute_driver_hash(self) -> str:
        """Computa hash SHA3-256 do driver (simulado)."""
        # Em produção: ler arquivo real e calcular hash
        return "c4f3e2a1b0d5f6e7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1"

    def _measure_phi_c(self) -> float:
        """Mede coerência Φ_C atual (simulado)."""
        # Em produção: consultar Φ_C bus real
        import numpy as np
        # Simular pequena variação em torno do valor base
        return np.clip(0.9973 + np.random.normal(0, 0.0001), 0.90, 1.0)

    def _verify_catalog_signature(self) -> bool:
        """Verifica assinatura do catálogo (simulado)."""
        # Em produção: usar Test-FileCatalog ou API equivalente
        return True

    def _detect_unauthorized_access(self) -> Optional[Dict]:
        """Detecta acessos não autorizados (simulado)."""
        # Em produção: analisar logs de auditoria, detectar padrões suspeitos
        # Para demo: retornar None (sem detecção)
        return None

    async def start(self):
        """Inicia o servidor."""
        self.running = True

        # Iniciar loop de monitoramento em background
        asyncio.create_task(self._monitoring_loop())

        # Iniciar servidor WebSocket
        async with websockets.serve(
            self.register,
            self.config.host,
            self.config.port,
            ping_interval=20,
            ping_timeout=10,
        ):
            logger.info(f"🚀 Integrity server started on ws://{self.config.host}:{self.config.port}")
            await asyncio.Future()  # Rodar indefinidamente

    def stop(self):
        """Para o servidor."""
        self.running = False
        logger.info("🛑 Integrity server stopped")

# ============================================================================
# ENTRY POINT
# ============================================================================

async def main():
    config = ServerConfig()
    server = IntegrityServer(config)

    try:
        await server.start()
    except KeyboardInterrupt:
        server.stop()
        logger.info("👋 Server shutdown by user")

if __name__ == "__main__":
    asyncio.run(main())
