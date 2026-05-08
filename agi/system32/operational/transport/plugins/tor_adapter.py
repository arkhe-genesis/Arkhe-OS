#!/usr/bin/env python3
"""
transport/plugins/tor_adapter.py — Plugin Tor para TransportAdapter
Usa stem + pysocks para roteamento via rede Tor.
"""
import asyncio
import socks
import socket
from typing import Dict, Optional, Tuple

try:
    from stem import Signal
    from stem.control import Controller
except ImportError:
    Controller = None

from ..adapter import BaseTransportAdapter, TransportConfig

class TorAdapter(BaseTransportAdapter):
    """Adapter para transporte via rede Tor (SOCKS5)."""

    def __init__(self, config: TransportConfig, coherence_monitor):
        super().__init__(config, coherence_monitor)
        self.tor_control_port = config.config.get('control_port', 9051)
        self.tor_socks_port = config.config.get('socks_port', 9050)
        self._controller = None

    async def connect(self) -> bool:
        """Conecta ao Tor via control port."""
        if not Controller:
            print("❌ stem module not found, Tor plugin disabled.")
            return False
        try:
            self._controller = Controller.from_port(port=self.tor_control_port)
            self._controller.authenticate()

            # Verificar se Tor está pronto
            status = self._controller.get_status()
            if status.get('bootstrapped', '0') != '100':
                # Aguardar bootstrap (simplificado)
                await asyncio.sleep(2)

            # Testar conexão SOCKS
            test_sock = socks.socksocket()
            test_sock.set_proxy(socks.SOCKS5, "127.0.0.1", self.tor_socks_port)
            test_sock.settimeout(5)
            test_sock.connect(("check.torproject.org", 80))
            test_sock.close()

            self._initialized = True
            return True
        except Exception as e:
            print(f"❌ Falha ao conectar ao Tor: {e}")
            return False

    async def disconnect(self):
        """Desconecta do Tor."""
        if self._controller:
            self._controller.close()
            self._controller = None
        self._initialized = False

    async def send(self, data: bytes, destination: str,
                   timeout: float = 30.0) -> Tuple[bool, Optional[str]]:
        """Envia dados via Tor (destino pode ser .onion ou IP)."""
        try:
            # Parse destination: hostname:port ou .onion:port
            if ':' in destination:
                host, port_str = destination.rsplit(':', 1)
                port = int(port_str)
            else:
                host = destination
                port = 80  # Default HTTP

            # Criar socket SOCKS5 via Tor
            sock = socks.socksocket()
            sock.set_proxy(socks.SOCKS5, "127.0.0.1", self.tor_socks_port)
            sock.settimeout(timeout)

            # Conectar e enviar
            sock.connect((host, port))
            sock.sendall(data)

            # Aguardar confirmação (simplificado: apenas enviar)
            sock.close()
            return True, None
        except Exception as e:
            return False, f"Tor send failed: {e}"

    async def receive(self, source: Optional[str] = None,
                      timeout: float = 30.0) -> Tuple[Optional[bytes], Optional[str]]:
        """Recebe dados via Tor (modo servidor simplificado)."""
        # Nota: Tor hidden services requerem configuração adicional
        # Esta implementação é para cliente; servidor requer HiddenServiceDir
        return None, "Receive via Tor requires hidden service configuration"

    async def health_check(self) -> Dict[str, float]:
        """Verifica saúde da conexão Tor."""
        import time

        start = time.time()
        try:
            # Testar latência via circuito Tor
            sock = socks.socksocket()
            sock.set_proxy(socks.SOCKS5, "127.0.0.1", self.tor_socks_port)
            sock.settimeout(10)
            sock.connect(("check.torproject.org", 80))
            sock.send(b"GET / HTTP/1.1\r\nHost: check.torproject.org\r\n\r\n")
            sock.recv(1024)  # Receber resposta mínima
            sock.close()

            latency = (time.time() - start) * 1000  # ms

            return {
                'latency_ms': latency,
                'packet_loss_rate': 0.0,  # Tor não reporta perda diretamente
                'jitter_ms': 0.0,  # Simplificado
                'circuit_status': self._controller.get_info('status/circuit-established') if self._controller else 'unknown',
            }
        except Exception as e:
            return {
                'latency_ms': float('inf'),
                'packet_loss_rate': 1.0,
                'jitter_ms': float('inf'),
                'error': str(e),
            }
