#!/usr/bin/env python3
"""
transport/plugins/direct_tcp_adapter.py — Plugin Direct TCP
Fallback simples para conexão TCP direta.
"""
import socket
from typing import Dict, Optional, Tuple
from ..adapter import BaseTransportAdapter, TransportConfig

class DirectTCPAdapter(BaseTransportAdapter):
    """Adapter para transporte via TCP direto (Fallback)."""

    async def connect(self) -> bool:
        self._initialized = True
        return True

    async def disconnect(self):
        self._initialized = False

    async def send(self, data: bytes, destination: str, timeout: float = 30.0) -> Tuple[bool, Optional[str]]:
        try:
            if ':' in destination:
                host, port_str = destination.rsplit(':', 1)
                port = int(port_str)
            else:
                host = destination
                port = 80

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            sock.sendall(data)
            sock.close()
            return True, None
        except Exception as e:
            return False, str(e)

    async def receive(self, source: Optional[str] = None, timeout: float = 30.0) -> Tuple[Optional[bytes], Optional[str]]:
        return None, "Not implemented"

    async def health_check(self) -> Dict[str, float]:
        import time
        start = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(("8.8.8.8", 53))
            sock.close()
            latency = (time.time() - start) * 1000
            return {'latency_ms': latency, 'packet_loss_rate': 0.0, 'jitter_ms': 0.0}
        except:
            return {'latency_ms': float('inf'), 'packet_loss_rate': 1.0, 'jitter_ms': float('inf')}
