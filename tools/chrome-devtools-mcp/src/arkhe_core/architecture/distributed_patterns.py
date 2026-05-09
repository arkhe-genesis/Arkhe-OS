from typing import Dict, Any, List, Callable
import uuid

class SagaManager:
    """
    Saga Pattern: Manages distributed transactions via compensation logic.
    Ensures 'Consistent Hashing' of concerns across the Arkhe Federation.
    """
    def __init__(self):
        self.transactions = {}

    def start_saga(self, saga_id: str, steps: List[Dict[str, Callable]]):
        """
        Executes a sequence of steps. If one fails, executes compensation for all previous steps.
        Each step is a dict: {'execute': func, 'compensate': func}
        """
        self.transactions[saga_id] = []
        executed_steps = []

        print(f"[Saga] Starting Saga {saga_id}")
        try:
            for step in steps:
                step['execute']()
                executed_steps.append(step)
                self.transactions[saga_id].append("SUCCESS")
            print(f"[Saga] Saga {saga_id} completed successfully.")
        except Exception as e:
            print(f"[Saga] Saga {saga_id} failed at step {len(executed_steps)}. Initiating compensation...")
            for step in reversed(executed_steps):
                step['compensate']()
            self.transactions[saga_id].append(f"FAILED: {str(e)}")

class CQRSEngine:
    """
    CQRS: Command Query Responsibility Segregation.
    Separates the Write Model (Commands) from the Read Model (Queries).
    """
    def __init__(self):
        self._write_store = {} # Private write store
        self._read_cache = {}  # Public read cache

    def execute_command(self, command_type: str, data: Any):
        """
        Handles state updates.
        """
        event_id = str(uuid.uuid4())
        # Event Sourcing: Store the command as an event
        self._write_store[event_id] = {'type': command_type, 'data': data}

        # Project into Read Model
        self._update_read_model(command_type, data)
        return event_id

    def _update_read_model(self, command_type: str, data: Any):
        # Simplified projection logic
        if command_type == "UPDATE_COHERENCE":
            self._read_cache['current_omega'] = data['omega']
        elif command_type == "REGISTER_NODE":
            nodes = self._read_cache.get('nodes', [])
            nodes.append(data['node_id'])
            self._read_cache['nodes'] = nodes

    def query(self, query_type: str) -> Any:
        """
        Handles data retrieval from the Read Model.
        """
        return self._read_cache.get(query_type)

class CircuitBreaker:
    """
    Circuit Breaker: Prevents cascading failures.
    """
    def __init__(self, failure_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self.failures = 0
        self.state = "CLOSED" # CLOSED, OPEN, HALF-OPEN

    def call(self, func: Callable, *args, **kwargs):
        if self.state == "OPEN":
            raise Exception("Circuit Breaker is OPEN. Request blocked.")

        try:
            result = func(*args, **kwargs)
            self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self.state = "OPEN"
                print("[CircuitBreaker] State changed to OPEN")
            raise e

class RateLimiter:
    """
    Rate Limiting: Protects at every layer.
    """
    def __init__(self, limit: int = 100):
        self.limit = limit
        self.requests = 0

    def allow_request(self) -> bool:
        if self.requests < self.limit:
            self.requests += 1
            return True
        return False

class ConsistentHasher:
    """
    Consistent Hashing: Scale without reshuffling.
    """
    def __init__(self):
        self.ring = {}

    def add_node(self, node_id: str):
        # Simplified: map node to a 'hash' point
        h = hash(node_id) % 1000
        self.ring[h] = node_id

    def get_node(self, key: str) -> str:
        h = hash(key) % 1000
        # Find closest node in ring
        for point in sorted(self.ring.keys()):
            if point >= h:
                return self.ring[point]
        return self.ring[min(self.ring.keys())] if self.ring else None

# Architectural Documentation for Arkhe Federated Architecture:
# 1. CAP Theorem: System prioritizes Partition Tolerance and Availability (AP).
# 2. Load Balancing: Implemented via Intent-Aware routing (see arkhe.ts).
# 3. Database Sharding: Horizontal sharding across nodes via Consistent Hashing.
# 4. Read Replicas: Nodes maintain local caches (Read Models) for high performance.
# 5. Event Sourcing: State transitions stored as immutable events in CQRSEngine.

if __name__ == "__main__":
    # Test CQRS
    cqrs = CQRSEngine()
    cqrs.execute_command("UPDATE_COHERENCE", {"omega": 0.98})
    print(f"CQRS Query current_omega: {cqrs.query('current_omega')}")

    # Test Saga
    saga = SagaManager()
    def do_task(): print("Task executed")
    def undo_task(): print("Task compensated")

    steps = [{'execute': do_task, 'compensate': undo_task}]
    saga.start_saga("test-saga-001", steps)
