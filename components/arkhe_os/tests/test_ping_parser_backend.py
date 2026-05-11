import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock

from arkhe_os.parser.frontends.ping_frontend_async import SubprocessPingBackend, RawICMPBackend

@pytest.mark.asyncio
async def test_subprocess_ping_parsing():
    backend = SubprocessPingBackend()

    # Mocking successful ping output based on linux ping command
    sample_output = """
PING 127.0.0.1 (127.0.0.1) 56(84) bytes of data.
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.038 ms
64 bytes from 127.0.0.1: icmp_seq=2 ttl=64 time=0.042 ms

--- 127.0.0.1 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1001ms
rtt min/avg/max/mdev = 0.038/0.040/0.042/0.002 ms
"""

    result = backend._parse_output("127.0.0.1", sample_output)

    assert result.target == "127.0.0.1"
    assert result.rtt_min_ms == 0.038
    assert result.rtt_avg_ms == 0.040
    assert result.rtt_max_ms == 0.042
    assert result.jitter_ms == 0.002
    assert result.loss_rate == 0.0
    assert result.ttl == 64
    assert result.coherence == 1.0
    assert result.timestamp <= time.time()

@pytest.mark.asyncio
async def test_fuzzing_ping_output():
    backend = SubprocessPingBackend()

    # Passing garbage text or empty string to ensure parser doesn't crash
    result_empty = backend._parse_output("127.0.0.1", "")
    assert result_empty.loss_rate == 1.0 # default if not found
    assert result_empty.rtt_avg_ms == 0.0
    assert result_empty.coherence == 0.0

    result_garbage = backend._parse_output("127.0.0.1", "some random characters without numbers")
    assert result_garbage.loss_rate == 1.0
    assert result_garbage.rtt_avg_ms == 0.0
    assert result_garbage.coherence == 0.0

@pytest.mark.asyncio
async def test_mock_raw_icmp_failure():
    backend = RawICMPBackend()

    # The default mock simply raises a simulated PermissionError
    result = await backend.probe("127.0.0.1")

    assert result.target == "127.0.0.1"
    assert result.loss_rate == 1.0
    assert result.coherence == 0.0
    assert "Raw socket operations require root privileges." in result.metadata["error"]
