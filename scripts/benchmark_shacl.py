import time
from src.arkhe_core.ontology.shacl_dependency import SHACLValidator

def benchmark():
    validator = SHACLValidator()
    payload = {
        "arkhe:assignedTo": {"@id": "http://arkhe.ai/ontology/2026#Agent_001"},
        "arkhe:priority": 5
    }

    times = []
    for _ in range(10):
        t0 = time.perf_counter()
        validator.validate_payload(payload, "Task")
        times.append((time.perf_counter() - t0) * 1000)

    print(f"Mean: {sum(times)/len(times):.3f}ms")

if __name__ == "__main__":
    benchmark()
