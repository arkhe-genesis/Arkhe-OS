#!/usr/bin/env python3
"""
transport/plugins/masterdnsvpn_adapter.py — Plugin MasterDnsVPN
Integra com MasterDnsVPN via subprocess + socket local.
"""
import asyncio
import subprocess
import socket
import json
from pathlib import Path
from typing import Dict, Optional, Tuple

from ..adapter import BaseTransportAdapter, TransportConfig

class MasterDnsVPNAdapter(BaseTransportAdapter):
    """Adapter para transporte via MasterDnsVPN (DNS tunneling)."""

    def __init__(self, config: TransportConfig, coherence_monitor):
        super().__init__(config, coherence_monitor)
        self.mdv_config_path = Path(config.config.get('config_path', '/etc/masterdnsvpn/client_config.toml'))
        self.mdv_binary = Path(config.config.get('binary_path', '/usr/local/bin/masterdnsvpn-client'))
        self.local_socks_port = config.config.get('local_socks_port', 18000)
        self._process: Optional[subprocess.Popen] = None

    async def connect(self) -> bool:
        """Inicia cliente MasterDnsVPN como subprocesso."""
        if not self.mdv_binary.exists():
            print(f"❌ Binary não encontrado: {self.mdv_binary}")
            return False

        try:
            # Iniciar MasterDnsVPN client
            self._process = subprocess.Popen(
                [str(self.mdv_binary), '-config', str(self.mdv_config_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True  # Isolar do processo pai
            )

            # Aguardar inicialização (verificar porta SOCKS)
            for _ in range(30):  # 30 segundos de timeout
                await asyncio.sleep(1)
                if self._check_socks_port():
                    self._initialized = True
                    return True

            # Timeout
            if self._process and self._process.poll() is None:
                self._process.terminate()
            return False
        except Exception as e:
            print(f"❌ Falha ao iniciar MasterDnsVPN: {e}")
            return False

    def _check_socks_port(self) -> bool:
        """Verifica se porta SOCKS local está escutando."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', self.local_socks_port))
            sock.close()
            return result == 0
        except:
            return False

    async def disconnect(self):
        """Encerra processo MasterDnsVPN."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            self._process.wait(timeout=10)
        self._process = None
        self._initialized = False

    async def send(self, data: bytes, destination: str,
                   timeout: float = 30.0) -> Tuple[bool, Optional[str]]:
        """Envia dados via SOCKS proxy do MasterDnsVPN."""
        try:
            import socks

            # Parse destination
            if ':' in destination:
                host, port_str = destination.rsplit(':', 1)
                port = int(port_str)
            else:
                host = destination
                port = 80

            # Conectar via SOCKS
            sock = socks.socksocket()
            sock.set_proxy(socks.SOCKS5, "127.0.0.1", self.local_socks_port)
            sock.settimeout(timeout)
            sock.connect((host, port))
            sock.sendall(data)
            sock.close()
            return True, None
        except Exception as e:
            return False, f"MasterDnsVPN send failed: {e}"

    async def receive(self, source: Optional[str] = None,
                      timeout: float = 30.0) -> Tuple[Optional[bytes], Optional[str]]:
        """Recebe dados (modo servidor não suportado via subprocess)."""
        return None, "MasterDnsVPN adapter supports client mode only"

    async def health_check(self) -> Dict[str, float]:
        """Verifica saúde do túnel MasterDnsVPN."""
        import time

        start = time.time()
        try:
            # Testar latência via túnel DNS
            import socks
            sock = socks.socksocket()
            sock.set_proxy(socks.SOCKS5, "127.0.0.1", self.local_socks_port)
            sock.settimeout(10)
            sock.connect(("1.1.1.1", 53))  # DNS público como teste
            sock.send(b"\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x06google\x03com\x00\x00\x01\x00\x01")
            sock.recv(512)
            sock.close()

            latency = (time.time() - start) * 1000

            # Estimar perda via múltiplas tentativas
            losses = 0
            for _ in range(5):
                try:
                    test_sock = socks.socksocket()
                    test_sock.set_proxy(socks.SOCKS5, "127.0.0.1", self.local_socks_port)
                    test_sock.settimeout(2)
                    test_sock.connect(("1.1.1.1", 53))
                    test_sock.close()
                except:
                    losses += 1

            return {
                'latency_ms': latency,
                'packet_loss_rate': losses / 5.0,
                'jitter_ms': 0.0,  # Simplificado
                'tunnel_status': 'active' if self._check_socks_port() else 'inactive',
            }
        except Exception as e:
            return {
                'latency_ms': float('inf'),
                'packet_loss_rate': 1.0,
                'jitter_ms': float('inf'),
                'error': str(e),
            }
