# arkhe_os/fuzzing/fuzzing_coherence_bridge.py
import hashlib

# ing the collector
class TestMetricsCollector:
    def record_test(self, test_id, status, duration, error_message=None, substrate_hints=None, markers=None):
        pass

class FuzzingCoherenceBridge:
    """
    Ponte entre o fuzzer (AFL++/libFuzzer) e o canal de coerência.
    Cada input de fuzzing gera um 'teste virtual' que é submetido
    como finding de coerência via pytest-arkhe.
    """

    def __init__(self, collector, target_label: str):
        self.collector = collector
        self.target_label = target_label

    def record_fuzzing_event(self, input_data: bytes, result: str,
                            coherence: float, execution_time: float):
        """
        Registra evento de fuzzing como se fosse um teste.
        - input que causou crash → status='failed', coherence=0.0
        - input normal → status='passed', coherence=medida
        - input de baixa coerência → status='warning', coherence=coherence
        """
        status = 'failed' if result == 'crash' else 'passed'
        if result == 'low_coherence':
            status = 'warning'

        self.collector.record_test(
            test_id=f"fuzz://{self.target_label}/{hashlib.sha256(input_data).hexdigest()[:16]}",
            status=status,
            duration=execution_time,
            error_message=f"Fuzz crash: {result}" if status == 'failed' else None,
            substrate_hints={"substrate_id": "274"},  # Fuzzing Canonical
            markers=["fuzzing", self.target_label],
        )
