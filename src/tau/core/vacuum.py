import time
import logging

class VacuumState:
    """
    O Vácuo Hidrodinâmico (v1.1).
    Gerencia o estado ao vivo (RTDB) vs persistência local (ChromaDB/Git).
    """
    def __init__(self):
        self.live_state = {
            "lambda_mesh": 1.0,
            "last_collapse": time.time(),
            "agents": {},
            "task_queue": [],
            "metrics": {
                "ram_usage_gb": 12.0,
                "firebase_size_mb": 150,
                "actions_budget_pct": 15,
                "success_rate": 1.0,
                "avg_latency_ms": 100.0
            }
        }
        self.logger = logging.getLogger("TAU-Vacuum")

    def update_agent(self, agent_id: str, data: dict):
        self.live_state["agents"][agent_id] = {
            "last_ping": time.time(),
            "data": data,
            "status": "online"
        }
        # Update metrics based on agent data if applicable
        if "latency_ms" in data:
            current_avg = self.live_state["metrics"]["avg_latency_ms"]
            self.live_state["metrics"]["avg_latency_ms"] = (current_avg * 0.9) + (data["latency_ms"] * 0.1)

        if "success" in data:
            current_success = self.live_state["metrics"]["success_rate"]
            val = 1.0 if data["success"] else 0.0
            self.live_state["metrics"]["success_rate"] = (current_success * 0.9) + (val * 0.1)

    def add_task(self, task: dict):
        self.logger.info(f"Injecting task into Vácuo: {task.get('id', 'unknown')}")
        self.live_state["task_queue"].append(task)

    def pop_task(self) -> dict:
        if self.live_state["task_queue"]:
            return self.live_state["task_queue"].pop(0)
        return None

    def get_coherence(self) -> float:
        return self.live_state["lambda_mesh"]

    def set_coherence(self, val: float):
        self.live_state["lambda_mesh"] = val
        self.live_state["last_collapse"] = time.time()

    def get_metrics(self) -> dict:
        return self.live_state["metrics"]
