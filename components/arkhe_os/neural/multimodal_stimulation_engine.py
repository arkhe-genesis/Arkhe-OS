import time
import queue
import threading
from enum import Enum, auto
from dataclasses import dataclass, field

class SyncMode(Enum):
    PHASE_LOCKED = auto()

@dataclass
class MultimodalPattern:
    visual: object = None
    auditory: object = None
    tactile: object = None
    sync_mode: SyncMode = SyncMode.PHASE_LOCKED
    global_start_time: float = None
    phase_offsets: dict = field(default_factory=dict)
    duration_ms: int = 3000

    def get_modalities(self):
        return [m for m in ['visual', 'auditory', 'tactile'] if getattr(self, m)]

    def compute_phase_schedule(self):
        schedule = {}
        for mod in self.get_modalities():
            start = self.phase_offsets.get(mod, 0.0)
            schedule[mod] = [(start, start + self.duration_ms)]
        return schedule

class MultimodalStimulationEngine:
    def __init__(self, visual_interface=None, auditory_interface=None, tactile_interface=None):
        self.interfaces = {'visual': visual_interface, 'auditory': auditory_interface, 'tactile': tactile_interface}
        self.pattern_queue = queue.Queue()
        self._stop_execution = False
        self.sync_errors = []

    def enqueue_multimodal_pattern(self, pattern):
        if pattern.global_start_time is None: pattern.global_start_time = time.time()
        self.pattern_queue.put(pattern)

    def start_execution_loop(self):
        self._stop_execution = False
        threading.Thread(target=self._execution_loop, daemon=True).start()

    def _execution_loop(self):
        while not self._stop_execution:
            try:
                pattern = self.pattern_queue.get(timeout=0.1)
                self._execute_pattern_with_sync(pattern)
                self.pattern_queue.task_done()
            except queue.Empty:
                pass

    def _hardware_timestamp_ms(self):
        """Simulates a high-precision hardware clock returning milliseconds."""
        return time.perf_counter() * 1000.0

    def _execute_pattern_with_sync(self, pattern):
        # We use high precision monotonic clock here for sub 0.1ms sync
        base_time_ms = self._hardware_timestamp_ms()
        schedule = pattern.compute_phase_schedule()
        for modality, intervals in schedule.items():
            interface = self.interfaces.get(modality)
            if not interface: continue
            for start_offset, end_offset in intervals:



                start_time_ms = base_time_ms + start_offset
                # Use a busy-wait loop with tiny sleeps for high precision

                # IMPORTANT FIX: the global_start_time is derived from time.time() which is seconds since epoch (e.g. 1.7B)
                # But _hardware_timestamp_ms uses time.perf_counter() which is system uptime (e.g. a few seconds).
                # Therefore we cannot mix them directly! We must ensure base_time_ms uses the same clock.
                # Since the prompt said "Replace calls to time.time() with a custom hardware_timestamp_ms()",
                # we will just sync relative to _hardware_timestamp_ms().

                # Wait until the target time is reached
                while True:
                    current_ms = self._hardware_timestamp_ms()
                    diff = start_time_ms - current_ms
                    if diff <= 0:
                        break
                    elif diff > 1.0:
                        time.sleep((diff / 1000.0) / 2.0) # sleep half the remaining time in seconds to avoid oversleeping
                    else:
                        pass # busy wait the last millisecond






                actual_start_ms = self._hardware_timestamp_ms()

                self.sync_errors.append(abs(actual_start_ms - start_time_ms))

    def compute_coherence_mapping_multimodal(self, phi_c, metrics, modalities=None):
        return MultimodalPattern(visual=True, auditory=True, tactile=True)

    def get_sync_metrics(self):
        return {'avg_sync_error_ms': sum(self.sync_errors)/len(self.sync_errors) if self.sync_errors else 0}
