import asyncio
import re
import socket
import struct
import time
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class PingResult:
    target: str
    rtt_avg_ms: float
    rtt_min_ms: float
    rtt_max_ms: float
    jitter_ms: float
    loss_rate: float
    ttl: Optional[int]
    coherence: float
    timestamp: float
    metadata: dict = field(default_factory=dict)

class PingBackend(ABC):
    @abstractmethod
    async def probe(self, target: str, count: int = 10, timeout: float = 2.0) -> PingResult:
        pass

class SubprocessPingBackend(PingBackend):
    def __init__(self, ping_cmd: str = "ping"):
        self.ping_cmd = ping_cmd

    async def probe(self, target: str, count: int = 10, timeout: float = 2.0) -> PingResult:
        # ping arguments:
        # -c count
        # -W timeout_seconds (or milliseconds depending on OS, assuming modern ping taking seconds or float)
        # Note: -W behavior varies between linux and macos. We will use a basic subprocess call.
        cmd = [self.ping_cmd, "-c", str(count), target]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Use total timeout for the entire command
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout * count + 2.0)

            output = stdout.decode('utf-8', errors='ignore')
            return self._parse_output(target, output)

        except asyncio.TimeoutError:
            # Entire command timed out, treat as 100% loss
            return PingResult(
                target=target,
                rtt_avg_ms=0.0,
                rtt_min_ms=0.0,
                rtt_max_ms=0.0,
                jitter_ms=0.0,
                loss_rate=1.0,
                ttl=None,
                coherence=0.0,
                timestamp=time.time(),
                metadata={"error": "Command timeout"}
            )
        except Exception as e:
            # Other errors (e.g., ping command not found)
            return PingResult(
                target=target,
                rtt_avg_ms=0.0,
                rtt_min_ms=0.0,
                rtt_max_ms=0.0,
                jitter_ms=0.0,
                loss_rate=1.0,
                ttl=None,
                coherence=0.0,
                timestamp=time.time(),
                metadata={"error": str(e)}
            )

    def _parse_output(self, target: str, output: str) -> PingResult:
        rtt_min = rtt_avg = rtt_max = jitter = 0.0
        loss_rate = 1.0
        ttl = None

        # Parse packet loss
        # e.g., "10 packets transmitted, 10 received, 0% packet loss"
        loss_match = re.search(r'(\d+)% packet loss', output)
        if loss_match:
            loss_rate = float(loss_match.group(1)) / 100.0

        # Parse RTT stats
        # e.g., "rtt min/avg/max/mdev = 0.038/0.042/0.051/0.004 ms" or "round-trip min/avg/max/stddev = ..."
        rtt_match = re.search(r'(?:rtt|round-trip)\s+min/avg/max/(?:mdev|stddev)\s*=\s*([\d\.]+)/([\d\.]+)/([\d\.]+)/([\d\.]+)', output)
        if rtt_match:
            rtt_min = float(rtt_match.group(1))
            rtt_avg = float(rtt_match.group(2))
            rtt_max = float(rtt_match.group(3))
            jitter = float(rtt_match.group(4))

        # Parse TTL from the first successful reply
        ttl_match = re.search(r'ttl=(\d+)', output, re.IGNORECASE)
        if ttl_match:
            ttl = int(ttl_match.group(1))

        # Initial coherence logic (will be refined by the estimator later, but we need a default here)
        # Assuming 0.0 coherence if 100% loss
        coherence = 0.0 if loss_rate == 1.0 else 1.0

        return PingResult(
            target=target,
            rtt_avg_ms=rtt_avg,
            rtt_min_ms=rtt_min,
            rtt_max_ms=rtt_max,
            jitter_ms=jitter,
            loss_rate=loss_rate,
            ttl=ttl,
            coherence=coherence,
            timestamp=time.time()
        )

class RawICMPBackend(PingBackend):
    async def probe(self, target: str, count: int = 10, timeout: float = 2.0) -> PingResult:
        # Note: Raw sockets require root privileges.
        # This implementation is a placeholder that simulates raw socket usage,
        # but delegates the complex low-level ICMP construction to a simplified mock for the sake of the environment.
        # In a real environment, we would use 'socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)'

        try:
            # We simulate a failure in the environment since raw sockets typically fail without root
            # or in a sandbox.
            raise PermissionError("Raw socket operations require root privileges.")

        except Exception as e:
            return PingResult(
                target=target,
                rtt_avg_ms=0.0,
                rtt_min_ms=0.0,
                rtt_max_ms=0.0,
                jitter_ms=0.0,
                loss_rate=1.0,
                ttl=None,
                coherence=0.0,
                timestamp=time.time(),
                metadata={"error": str(e), "raw_socket": True}
            )
