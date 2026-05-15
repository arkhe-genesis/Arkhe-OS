import pytest
import threading
from arkhe_streaming.platforms.kick import KickStreamAdapter

def test_concurrent_stream_processing():
    results = []

    def process_stream(index):
        adapter = KickStreamAdapter(f"token_{index}")
        adapter.connect()
        coh = adapter.validate_stream()
        results.append(coh)

    threads = []
    for i in range(10): # Mock load
        t = threading.Thread(target=process_stream, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    assert len(results) == 10
    assert all(0.90 <= r <= 0.98 for r in results)
