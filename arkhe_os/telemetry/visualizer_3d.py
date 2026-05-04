#!/usr/bin/env python3
"""
visualizer_3d.py
"""
import json, time, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional

THREE_JS_CDN = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"
ORBIT_CONTROLS_CDN = "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"

VISUALIZER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Arkhe OS | Campo de Coerência 3D</title>
    <style>
        body { margin: 0; overflow: hidden; background: #000; font-family: 'Courier New', monospace; }
        #hud { position: absolute; top: 20px; left: 20px; color: #d4af37; z-index: 10; background: rgba(0,0,0,0.5); padding: 15px; border-radius: 8px; }
        .metric { margin: 5px 0; font-size: 18px; }
        .value { color: #ffd700; font-weight: bold; }
    </style>
</head>
<body>
    <div id="hud">
        <h1>🌌 Arkhe Telemetry v18</h1>
        <div class="metric">Ω: <span id="omega_val" class="value">--</span></div>
        <div class="metric">Status: <span id="status_val" class="value">--</span></div>
    </div>
    <script src="THREE_JS_CDN_PLACEHOLDER"></script>
    <script src="ORBIT_CONTROLS_CDN_PLACEHOLDER"></script>
    <script>
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 1, 1000);
        camera.position.set(0, 0, 40);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.body.appendChild(renderer.domElement);
        new THREE.OrbitControls(camera, renderer.domElement);

        const geometry = new THREE.TorusKnotGeometry(10, 3, 100, 16);
        const material = new THREE.MeshPhongMaterial({ color: 0x00ffff, emissive: 0x002244, wireframe: true });
        const torus = new THREE.Mesh(geometry, material);
        scene.add(torus);
        scene.add(new THREE.AmbientLight(0x404040));
        const light = new THREE.PointLight(0xffffff, 1, 100);
        light.position.set(10, 10, 10);
        scene.add(light);

        function animate() {
            requestAnimationFrame(animate);
            torus.rotation.x += 0.01;
            torus.rotation.y += 0.01;
            renderer.render(scene, camera);
        }
        animate();

        async function update() {
            try {
                // Fixed port 9080 for metrics
                const response = await fetch('http://' + window.location.hostname + ':9080/metrics');
                const data = await response.json();
                document.getElementById('omega_val').innerText = data.omega.current_value.toFixed(4);
                document.getElementById('status_val').innerText = data.system.status;
            } catch(e) { console.error("Metrics sync failed", e); }
        }
        setInterval(update, 2000);
    </script>
</body>
</html>
""".replace("THREE_JS_CDN_PLACEHOLDER", THREE_JS_CDN).replace("ORBIT_CONTROLS_CDN_PLACEHOLDER", ORBIT_CONTROLS_CDN)

class Visualizer3DHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/3d":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(VISUALIZER_HTML.encode())
        else:
            self.send_response(404)
            self.end_headers()

class Visualizer3DServer:
    def __init__(self, orchestrator, host="0.0.0.0", port=9081):
        self.host = host
        self.port = port
    def start(self):
        self.server = HTTPServer((self.host, self.port), Visualizer3DHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        print(f"🌐 Visualizador 3D em http://{self.host}:{self.port}/3d")
    def stop(self):
        if hasattr(self, 'server'): self.server.shutdown()
