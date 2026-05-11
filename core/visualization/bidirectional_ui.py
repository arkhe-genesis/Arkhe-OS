#!/usr/bin/env python3
"""
Bidirectional UI for Sophon Hexagon — Manual Parameter Control + Network Threshold Modulation
Allows operators to adjust shader parameters AND modulate Sophon network alert thresholds.
"""
import numpy as np
import asyncio
from typing import Dict, Callable, Optional
from dataclasses import dataclass, field
import json

@dataclass
class UIParameter:
    """Represents a controllable parameter with bidirectional binding."""
    name: str
    label: str
    value: float
    min_val: float
    max_val: float
    step: float
    shader_uniform_index: Optional[int] = None  # Index in uniform buffer
    network_metric: Optional[str] = None  # Metric to modulate in Sophon network
    inverse_mapping: bool = False  # If True, higher UI value → lower network threshold

    def to_shader_value(self) -> float:
        """Convert UI value to shader uniform scale."""
        return np.clip(self.value, self.min_val, self.max_val)

    def to_network_threshold(self) -> float:
        """Convert UI value to network alert threshold."""
        if self.network_metric is None:
            return None
        # Linear mapping from UI range to threshold range [0.5, 0.95]
        threshold = 0.5 + (self.value - self.min_val) / (self.max_val - self.min_val) * 0.45
        return 0.95 - threshold if self.inverse_mapping else threshold

class BidirectionalUI:
    """Bidirectional interface linking shader parameters to network thresholds."""

    def __init__(self, sophon_api_url: Optional[str] = None):
        self.sophon_api = sophon_api_url
        self.parameters: Dict[str, UIParameter] = {}
        self.callbacks: Dict[str, Callable] = {}
        self._init_default_parameters()

    def _init_default_parameters(self):
        """Initialize default bidirectional parameters."""
        # Shader-only parameters
        self.add_parameter(UIParameter(
            name="wave_amplitude_balance",
            label="Wave Amplitude Balance",
            value=0.7, min_val=0.3, max_val=1.0, step=0.01,
            shader_uniform_index=6  # Start of wave_amplitude array
        ))

        self.add_parameter(UIParameter(
            name="coupling_strength",
            label="Mode Coupling Strength",
            value=0.1, min_val=0.0, max_val=0.5, step=0.01,
            shader_uniform_index=30
        ))

        # Bidirectional: shader + network threshold
        self.add_parameter(UIParameter(
            name="coherence_alert_threshold",
            label="Coherence Alert Threshold",
            value=0.75, min_val=0.5, max_val=0.95, step=0.01,
            shader_uniform_index=31,  # coherence_threshold in shader
            network_metric="sophon_coherence_distance",
            inverse_mapping=True  # Higher UI value → lower distance threshold (stricter alert)
        ))

        self.add_parameter(UIParameter(
            name="delivery_rate_threshold",
            label="Delivery Rate Alert Threshold",
            value=0.90, min_val=0.7, max_val=0.99, step=0.01,
            network_metric="sophon_delivery_rate",
            inverse_mapping=False
        ))

    def add_parameter(self, param: UIParameter):
        """Register a new bidirectional parameter."""
        self.parameters[param.name] = param

    def on_parameter_change(self, name: str, callback: Callable[[float], None]):
        """Register callback for parameter changes."""
        self.callbacks[name] = callback

    def update_parameter(self, name: str, new_value: float):
        """Update parameter value and propagate changes."""
        if name not in self.parameters:
            raise ValueError(f"Unknown parameter: {name}")

        param = self.parameters[name]
        param.value = np.clip(new_value, param.min_val, param.max_val)

        # Trigger shader update callback
        if name in self.callbacks:
            self.callbacks[name](param.to_shader_value())

        # Propagate to network if bound
        if param.network_metric:
            asyncio.create_task(self._update_network_threshold(param))

    async def _update_network_threshold(self, param: UIParameter):
        """Send threshold update to Sophon network API."""
        if not self.sophon_api:
            return

        threshold = param.to_network_threshold()
        payload = {
            "metric": param.network_metric,
            "threshold": threshold,
            "source": "bidirectional_ui",
            "timestamp": asyncio.get_event_loop().time()
        }

        try:
            # Simulated API call
            print(f"🔗 Network threshold updated: {param.network_metric} = {threshold:.3f}")
            # Real implementation: await http.post(f"{self.sophon_api}/alerts/thresholds", json=payload)
        except Exception as e:
            print(f"⚠️ Failed to update network threshold: {e}")

    def render_control_panel(self) -> str:
        """Generate HTML/JS for control panel (for embedding in Grafana or web UI)."""
        html = "<div class='sophon-ui-panel'>\n"
        html += "<h3>Sophon Hexagon — Bidirectional Controls</h3>\n"

        for name, param in self.parameters.items():
            html += f"""
            <div class='control-group'>
                <label for='{name}'>{param.label}: <span id='{name}_value'>{param.value:.2f}</span></label>
                <input type='range' id='{name}'
                       min='{param.min_val}' max='{param.max_val}' step='{param.step}'
                       value='{param.value}'
                       oninput='updateParam("{name}", this.value)'>
                {f"<small class='network-bound'>↔ Network: {param.network_metric}</small>" if param.network_metric else ""}
            </div>
            """

        html += """
        <script>
        function updateParam(name, value) {
            document.getElementById(name + '_value').textContent = parseFloat(value).toFixed(2);
            // Send to Python backend via WebSocket or fetch
            fetch('/api/ui/update', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: name, value: parseFloat(value)})
            });
        }
        </script>
        </div>
        """
        return html
