#!/usr/bin/env python3
"""
transport/plugins/direct_tcp_adapter.py — Plugin Direct TCP
Fallback simples para ambientes não-censurados
"""
import asyncio
import socket
from typing import Dict, Optional, Tuple

from ..adapter import BaseTransportAdapter, TransportConfig

class DirectTCPAdapter(BaseTransportAdapter):
    """Adapter para transporte via TCP direto (fallback)."""

    def __init__(self, config: TransportConfig, coherence_monitor):
        super().__init__(config, coherence_monitor)
        self.timeout = config.config.get('timeout', 10)
        self.keepalive = config.config.get('keepalive', True)

    async def connect(self) -> bool:
        """Conecta (sempre true para direct tcp, gerencia conexoes por pedido)."""
        self._initialized = True
        return True

    async def disconnect(self):
        """Desconecta (sem operacao persistente neste nivel de teste)."""
        self._initialized = False

    async def send(self, data: bytes, destination: str,
                   timeout: float = 30.0) -> Tuple[bool, Optional[str]]:
        """Envia dados via TCP direto."""
        try:
            if ':' in destination:
                host, port_str = destination.rsplit(':', 1)
                port = int(port_str)
            else:
                host = destination
                port = 80

            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=self.timeout
            )
            writer.write(data)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return True, None
        except Exception as e:
            return False, f"Direct TCP send failed: {e}"

    async def receive(self, source: Optional[str] = None,
                      timeout: float = 30.0) -> Tuple[Optional[bytes], Optional[str]]:
        """Recebe dados (nao suportado para cliente simples)."""
        return None, "Direct TCP adapter supports client mode only"

    async def health_check(self) -> Dict[str, float]:
        """Verifica saúde do Direct TCP."""
        import time

        start = time.time()
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection('1.1.1.1', 53), timeout=self.timeout
            )
            writer.close()
            await writer.wait_closed()
            latency = (time.time() - start) * 1000

            return {
                'latency_ms': latency,
                'packet_loss_rate': 0.0,
                'jitter_ms': 0.0,
            }
        except Exception as e:
            return {
                'latency_ms': float('inf'),
                'packet_loss_rate': 1.0,
                'jitter_ms': float('inf'),
            }
