import pytest
import math
from scripts.entropy_monitor import EntropyMonitor

def test_entropy_reduction_with_numa():
    monitor = EntropyMonitor()

    # Linha de base: sem bloqueios DNS
    monitor.record_translation('observe')
    monitor.record_translation('entangle')
    entropy_no_numa = monitor.compute_shannon_entropy()

    # Com bloqueios DNS
    monitor.record_dns_block(100)
    entropy_with_numa = monitor.compute_shannon_entropy()

    assert entropy_with_numa < entropy_no_numa
    assert entropy_with_numa == max(0.0, entropy_no_numa - 0.1 * math.log2(1 + 100))

def test_heat_dissipation_reset():
    monitor = EntropyMonitor()
    monitor.record_dns_block(50)
    monitor.record_translation('observe')

    monitor.dissipate_heat(0.5)

    assert monitor.dns_entropy_buffer == 0
    assert len(monitor.translation_counter) == 0
