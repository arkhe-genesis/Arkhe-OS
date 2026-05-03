#!/usr/bin/env python3
import time
from typing import Optional

class SophonHexagonConfig:
    def __init__(self):
        self.coherence_threshold = 0.75

class MockDevice:
    class MockQueue:
        def write_buffer(self, buffer, offset, data):
            pass
    def __init__(self):
        self.queue = self.MockQueue()

class MockRenderer:
    def __init__(self):
        self.device = MockDevice()

class SophonHexagonEngine:
    def __init__(self, config: Optional[SophonHexagonConfig] = None,
                 prometheus_url: Optional[str] = None,
                 bidirectional_ui: bool = True,
                 sophon_api_url: Optional[str] = None):

        self.config = config or SophonHexagonConfig()
        self.uniform_data = [0.0] * 64
        self.uniform_buffer = None
        self.uniform_buffer_dirty = False
        self.renderer = MockRenderer()

        if bidirectional_ui:
            from core.visualization.bidirectional_ui import BidirectionalUI
            self.ui = BidirectionalUI(sophon_api_url=sophon_api_url)
            self._bind_ui_callbacks()
        else:
            self.ui = None

    def _bind_ui_callbacks(self):
        def on_amplitude_change(value):
            for i in range(6):
                self.uniform_data[6 + i] = value
            self._mark_uniform_dirty()

        def on_coupling_change(value):
            self.uniform_data[30] = value
            self._mark_uniform_dirty()

        def on_coherence_threshold_change(value):
            self.uniform_data[31] = value
            self.config.coherence_threshold = value
            self._mark_uniform_dirty()

        self.ui.on_parameter_change("wave_amplitude_balance", on_amplitude_change)
        self.ui.on_parameter_change("coupling_strength", on_coupling_change)
        self.ui.on_parameter_change("coherence_alert_threshold", on_coherence_threshold_change)

    def _mark_uniform_dirty(self):
        self.uniform_buffer_dirty = True

    def update(self):
        if self.ui and self.uniform_buffer_dirty:
            self.renderer.device.queue.write_buffer(
                self.uniform_buffer, 0, self.uniform_data
            )
            self.uniform_buffer_dirty = False

if __name__ == "__main__":
    engine = SophonHexagonEngine()
    print("Sophon Hexagon Engine V2 Mock initialized.")
