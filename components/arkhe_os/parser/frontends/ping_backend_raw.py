import asyncio
import socket
import struct
import time
import numpy as np
from typing import Optional
from dataclasses import dataclass

@dataclass
class RawPingResult:
    target: str
    rtt_avg_ms: float
    rtt_min_ms: float
    rtt_max_ms: float
    jitter_ms: float
    loss_rate: float
    ttl: Optional[int]
    coherence: float
    timestamp: float

class RawICMPBackend:
    """Ping assíncrono via socket RAW ICMP (requer privilégios root ou CAP_NET_RAW)."""

    ICMP_ECHO_REQUEST = 8
    ICMP_ECHO_REPLY = 0

    def __init__(self, timeout: float = 2.0, max_ttl: int = 64):
        self.timeout = timeout
        self.max_ttl = max_ttl
        self._socket: Optional[socket.socket] = None

    async def _create_socket(self) -> socket.socket:
        """Cria socket raw ICMP de forma não bloqueante."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        sock.setblocking(False)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, self.max_ttl)
        return sock

    def _build_icmp_packet(self, seq: int) -> bytes:
        """Constrói pacote ICMP Echo Request com checksum."""
        header = struct.pack('!BBHHH', self.ICMP_ECHO_REQUEST, 0, 0, 0, seq)
        payload = b'ARKHE_PING' + struct.pack('!d', time.time())
        checksum = self._compute_checksum(header + payload)
        header = struct.pack('!BBHHH', self.ICMP_ECHO_REQUEST, 0, checksum, 0, seq)
        return header + payload

    def _compute_checksum(self, data: bytes) -> int:
        """Checksum de complemento de 1 (padrão ICMP)."""
        s = 0
        for i in range(0, len(data), 2):
            w = data[i] + (data[i+1] << 8 if i+1 < len(data) else 0)
            s += w
        s = (s >> 16) + (s & 0xffff)
        s += s >> 16
        return ~s & 0xffff

    async def probe(self, target: str, count: int = 10) -> RawPingResult:
        """Executa N pings para o alvo e retorna métricas agregadas."""
        self._socket = await self._create_socket()
        dest = (target, 0)  # porta 0 para ICMP

        rtts = []
        losses = 0
        ttl_received = None

        for seq in range(count):
            packet = self._build_icmp_packet(seq)
            try:
                await asyncio.get_event_loop().sock_sendall(self._socket, packet)
                t_start = time.time()
                # Aguardar resposta com timeout
                reply = await asyncio.wait_for(
                    self._recv_icmp_reply(), timeout=self.timeout
                )
                rtt = (time.time() - t_start) * 1000  # ms
                rtts.append(rtt)
                if reply['ttl'] and not ttl_received:
                    ttl_received = reply['ttl']
            except asyncio.TimeoutError:
                losses += 1
            except OSError:
                losses += 1

        self._socket.close()
        self._socket = None

        return self._compute_result(target, rtts, losses, count, ttl_received)

    async def _recv_icmp_reply(self) -> dict:
        """Recebe um pacote ICMP Echo Reply via loop de eventos."""
        loop = asyncio.get_event_loop()
        while True:
            data, addr = await loop.sock_recvfrom(self._socket, 1024)
            # Extrai TTL do cabeçalho IP (simplificado)
            ttl = data[8] if len(data) > 8 else None
            icmp_type = data[20] if len(data) > 20 else None
            if icmp_type == self.ICMP_ECHO_REPLY:
                return {'ttl': ttl}

    def _compute_result(self, target: str, rtts: list, losses: int, count: int, ttl: int) -> RawPingResult:
        """Calcula métricas e coerência do caminho."""
        if not rtts:
            return RawPingResult(target, 0, 0, 0, 0, 1.0, ttl, 0.0, time.time())

        r_avg = np.mean(rtts)
        r_min = min(rtts)
        r_max = max(rtts)
        jitter = np.std(rtts) if len(rtts) > 1 else 0.0
        loss_rate = losses / count

        # Fórmula de coerência do Substrato 270
        latency_factor = 1.0 if r_avg <= r_min else max(0.0, 1.0 - (r_avg - r_min) / 1000.0)
        coherence = max(0.0, min(1.0,
            latency_factor * (1.0 - loss_rate) * np.exp(-0.1 * jitter)
        ))

        return RawPingResult(
            target=target, rtt_avg_ms=r_avg, rtt_min_ms=r_min, rtt_max_ms=r_max,
            jitter_ms=jitter, loss_rate=loss_rate, ttl=ttl, coherence=coherence,
            timestamp=time.time()
        )
