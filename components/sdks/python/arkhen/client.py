import requests
from typing import Dict, Any, Optional

class ArkhenClient:
    """
    Client for the Arkhe(n) Hybrid Architecture API (ℂ × ℤ → ℝ⁴)
    Interfaces with the Tzinor Gate and Parametrized WASM Core.
    """
    def __init__(self, base_url: str = "http://localhost:3000", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        self.session.headers.update({"X-Arkhen-Client": "python-sdk/1.0.0"})

    def get_health(self) -> Dict[str, Any]:
        """Check system coherence and health."""
        res = self.session.get(f"{self.base_url}/api/health")
        res.raise_for_status()
        return res.json()

    def update_parameters(self, coupling_strength: Optional[float] = None, 
                          lambda_threshold: Optional[float] = None, 
                          auto_mitigate: Optional[bool] = None) -> Dict[str, Any]:
        """Update Kuramoto coupling and Tzinor gate thresholds."""
        payload = {}
        if coupling_strength is not None: payload["couplingStrength"] = coupling_strength
        if lambda_threshold is not None: payload["lambdaThreshold"] = lambda_threshold
        if auto_mitigate is not None: payload["autoMitigate"] = auto_mitigate
        
        res = self.session.post(f"{self.base_url}/api/parameters", json=payload)
        res.raise_for_status()
        return res.json()

    def inject_threat(self, threat_type: str) -> Dict[str, Any]:
        """Inject a simulated threat vector into the coherence field."""
        res = self.session.post(f"{self.base_url}/api/trigger-attack", json={"type": threat_type})
        res.raise_for_status()
        return res.json()

    def emit_python_orb(self) -> Dict[str, Any]:
        """Trigger the emission of a Python Orb into the ASTL."""
        res = self.session.post(f"{self.base_url}/api/emit-python")
        res.raise_for_status()
        return res.json()
