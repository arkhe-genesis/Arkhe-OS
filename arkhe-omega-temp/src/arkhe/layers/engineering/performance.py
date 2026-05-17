# src/arkhe/layers/engineering/performance.py
import time, hashlib

def measure_and_anchor(fn, *args, **kwargs):
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = time.perf_counter() - start
    seal = hashlib.sha3_256(f"{fn.__name__}:{elapsed:.6f}".encode()).hexdigest()[:8]
    return {"result": result, "elapsed_ms": elapsed*1000, "seal": seal}
