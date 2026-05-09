import time
from typing import Dict, Any, List

class PhaseStructuredLogger:
    """Logger que injeta metadados de coerência."""
    def __init__(self, service_id: str, oscillator: Any):
        self.service_id = service_id
        self.oscillator = oscillator

    def log(self, event: str, level: str = "INFO", **kwargs):
        log_entry = {
            "timestamp": time.time(),
            "level": level,
            "event": event,
            "service_id": self.service_id,
            "lambda2": self.oscillator.lambda2 if hasattr(self.oscillator, 'lambda2') else 1.0,
            **kwargs
        }
        # print(json.dumps(log_entry))
        return log_entry

class PhaseDistributedTracer:
    """Distributed tracing com atributos de fase."""
    def start_span(self, name: str, current_lambda2: float) -> Dict[str, Any]:
        return {
            "span_name": name,
            "start_time": time.time_ns(),
            "attributes": {
                "phase.lambda2": current_lambda2
            }
        }
