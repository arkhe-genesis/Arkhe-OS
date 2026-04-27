#!/usr/bin/env python3
"""
dashboard.py
"""
import json, time, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional
import numpy as np

class TelemetryHandler(BaseHTTPRequestHandler):
    orchestrator = None

    def log_message(self, format, *args): pass

    def _send_json_response(self, data: Dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def do_GET(self):
        if self.path == "/metrics":
            self._send_json_response(self._get_core_metrics())
        elif self.path == "/health":
            self._send_json_response({"status": "healthy", "timestamp": time.time_ns()})
        else:
            self.send_response(404)
            self.end_headers()

    def _get_core_metrics(self) -> Dict:
        if not self.orchestrator: return {"error": "init"}
        return {
            "omega": {"current_value": round(self.orchestrator.field.get_network_omega(), 4)},
            "k_eth": {"current_value": 0.9385},
            "system": {"odometro": "002143", "status": "OPERATIONAL", "phase": "v18_ai_kernels"}
        }

class TelemetryServer:
    def __init__(self, orchestrator, host: str = "0.0.0.0", port: int = 9080):
        self.orchestrator = orchestrator
        self.host = host
        self.port = port
        TelemetryHandler.orchestrator = orchestrator

    def start(self):
        self.server = HTTPServer((self.host, self.port), TelemetryHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        print(f"✅ Telemetry server live at http://{self.host}:{self.port}/metrics")

    def stop(self):
        if hasattr(self, 'server'): self.server.shutdown()
