#!/usr/bin/env python3
"""
arkhe_visor_feed_server_v112.py
Substrato 176: Servidor de Feed em Tempo Real para Visor NV + OAM Cross-Body.
Emite: (1) Estados de coerência planetária via WebSocket a 30fps,
       (2) Tokens OAM com latência real de backbone interplanetário.
"""
import asyncio
import websockets
import json
import numpy as np
import torch
import torch.nn as nn
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional
from enum import Enum, auto
import time
from collections import deque
import sys

# ============================================================================
# CONFIGURAÇÃO INTERPLANETÁRIA v∞.112
# ============================================================================

class Planet(Enum):
    EARTH = auto()
    MOON = auto()
    MARS = auto()
    VENUS = auto()

@dataclass
class VisorConfig:
    websocket_port: int = 8765
    emit_fps: float = 30.0
    state_dim: int = 128

    light_delays: Dict[Tuple[Planet, Planet], float] = None

    def __post_init__(self):
        if self.light_delays is None:
            self.light_delays = {
                (Planet.EARTH, Planet.MOON): 1.28,
                (Planet.EARTH, Planet.MARS): 750.0,
                (Planet.MOON, Planet.MARS): 751.3,
                (Planet.EARTH, Planet.VENUS): 300.0,
            }

# ============================================================================
# SIMULADOR DA MALHA PLANETÁRIA
# ============================================================================

class PlanetaryMeshSimulator:
    def __init__(self, config: VisorConfig):
        self.config = config
        self.planets = list(Planet)

        self.planet_states = {p: torch.randn(config.state_dim) * 0.1 for p in Planet}
        self.coherences = {p: 0.5 for p in Planet}

        self.coverages = {
            Planet.EARTH: {'condition': 95.0, 'decision': 97.0, 'path': 82.0, 'jain': 0.92},
            Planet.MOON: {'condition': 60.0, 'decision': 65.0, 'path': 40.0, 'jain': 0.65},
            Planet.MARS: {'condition': 88.0, 'decision': 90.0, 'path': 75.0, 'jain': 0.85},
            Planet.VENUS: {'condition': 70.0, 'decision': 72.0, 'path': 50.0, 'jain': 0.70},
        }

        self.node_positions = self._generate_node_positions()
        self.nv_states = self._initialize_nv_states()

        self.sim_time = 0.0
        self.dt = 1.0 / config.emit_fps

    def _generate_node_positions(self) -> Dict[Planet, np.ndarray]:
        positions = {}
        for planet in Planet:
            n_nodes = 1000 if planet in [Planet.EARTH, Planet.MARS] else 500
            r = 1.0 + np.random.exponential(0.5, n_nodes)
            theta = np.random.uniform(0, 2*np.pi, n_nodes)
            phi = np.random.uniform(0, np.pi, n_nodes)

            x = r * np.sin(phi) * np.cos(theta)
            y = r * np.sin(phi) * np.sin(theta)
            z = r * np.cos(phi)

            offsets = {
                Planet.EARTH: [0.0, 0.0, 0.0],
                Planet.MOON: [2.0, 0.5, 0.0],
                Planet.MARS: [8.0, 1.0, 0.5],
                Planet.VENUS: [-4.0, -0.5, 0.0]
            }
            off = offsets[planet]
            positions[planet] = np.column_stack([x + off[0], y + off[1], z + off[2]])
        return positions

    def _initialize_nv_states(self) -> Dict[Planet, np.ndarray]:
        states = {}
        for planet in Planet:
            n = len(self.node_positions[planet])
            states[planet] = np.random.choice([0, 1, 2], size=n, p=[0.8, 0.1, 0.1])
        return states

    def step(self):
        self.sim_time += self.dt

        for planet in Planet:
            noise = torch.randn(self.config.state_dim) * 0.02
            self.planet_states[planet] = torch.tanh(self.planet_states[planet] * 0.99 + noise)
            self.coherences[planet] = float(torch.sigmoid(self.planet_states[planet].mean()))

            for cov_type in ['condition', 'decision', 'path', 'jain']:
                if cov_type == 'jain':
                    self.coverages[planet][cov_type] = min(1.0, self.coverages[planet][cov_type] + np.random.rand()*0.001)
                else:
                    self.coverages[planet][cov_type] = min(100.0, self.coverages[planet][cov_type] + np.random.rand()*0.1)

        for planet in Planet:
            n = len(self.nv_states[planet])
            flip_prob = 0.001 * (1 + self.coherences[planet])
            mask = np.random.rand(n) < flip_prob
            self.nv_states[planet][mask] = np.random.choice([1, 2], size=mask.sum())

    def get_visor_payload(self) -> Dict:
        payload = {
            'timestamp': self.sim_time,
            'coherences': {p.name: round(self.coherences[p], 4) for p in Planet},
            'coverage': {p.name: self.coverages[p] for p in Planet},
            'nodes': {}
        }

        for planet in Planet:
            positions = self.node_positions[planet]
            states = self.nv_states[planet]

            if len(positions) > 500:
                idx = np.random.choice(len(positions), 500, replace=False)
                positions = positions[idx]
                states = states[idx]

            payload['nodes'][planet.name] = {
                'positions': positions.tolist(),
                'nv_states': states.tolist(),
                'coherence': round(self.coherences[planet], 4)
            }
        return payload

# ============================================================================
# OAM CROSS-BODY COM LATÊNCIA REAL
# ============================================================================

class OAMCrossBodyLink:
    def __init__(self, source: Planet, target: Planet, delay_seconds: float):
        self.source = source
        self.target = target
        self.delay = delay_seconds
        self.transmission_queue: deque = deque()
        self.received_tokens: List[Dict] = []
        self.tokens_sent = 0
        self.tokens_received = 0

    def emit_token(self, token: Dict, current_time: float):
        delivery_time = current_time + self.delay
        self.transmission_queue.append((delivery_time, token))
        self.tokens_sent += 1

    def process_queue(self, current_time: float) -> List[Dict]:
        delivered = []
        while self.transmission_queue and self.transmission_queue[0][0] <= current_time:
            _, token = self.transmission_queue.popleft()
            delivered.append(token)
            self.tokens_received += 1
        self.received_tokens.extend(delivered)
        return delivered

class OAMCrossBodyNetwork:
    def __init__(self, config: VisorConfig):
        self.config = config
        self.links: Dict[Tuple[Planet, Planet], OAMCrossBodyLink] = {}

        for (p1, p2), delay in config.light_delays.items():
            self.links[(p1, p2)] = OAMCrossBodyLink(p1, p2, delay)
            self.links[(p2, p1)] = OAMCrossBodyLink(p2, p1, delay)

    def emit(self, source: Planet, target: Planet, token: Dict, current_time: float):
        if (source, target) in self.links:
            self.links[(source, target)].emit_token(token, current_time)

    def tick(self, current_time: float) -> Dict[Planet, List[Dict]]:
        deliveries = {p: [] for p in Planet}
        for (src, tgt), link in self.links.items():
            received = link.process_queue(current_time)
            deliveries[tgt].extend(received)
        return deliveries

    def generate_oam_token(self, source: Planet, coherence: float) -> Dict:
        return {
            'source': source.name,
            'oam_mode': int(np.random.randint(-10, 11)),
            'amplitude': float(coherence * (0.9 + 0.1 * np.random.randn())),
            'phase': float(np.random.uniform(0, 2*np.pi)),
            'emission_time': time.time()
        }

# ============================================================================
# SERVIDOR WEBSOCKET
# ============================================================================

class ArkheVisorServer:
    def __init__(self, config: VisorConfig, run_for: int = None):
        self.config = config
        self.simulator = PlanetaryMeshSimulator(config)
        self.oam_network = OAMCrossBodyNetwork(config)
        self.clients: set = set()
        self.running = False
        self.run_for = run_for
        self.frames_emitted = 0
        self.oam_tokens_exchanged = 0

    async def register_client(self, websocket):
        self.clients.add(websocket)
        print(f"👁️  Visor conectado: {websocket.remote_address}")

    async def unregister_client(self, websocket):
        self.clients.discard(websocket)
        print(f"👁️  Visor desconectado: {websocket.remote_address}")

    async def broadcast(self, message: Dict):
        if not self.clients: return
        payload = json.dumps(message)
        dead_clients = set()
        for client in self.clients:
            try:
                await client.send(payload)
            except Exception:
                dead_clients.add(client)
        self.clients -= dead_clients

    async def simulation_loop(self):
        print("🌌 Iniciando feed do Visor em Escala Real...")
        interval = 1.0 / self.config.emit_fps
        start_time = time.time()

        while self.running:
            t0 = time.time()
            if self.run_for and t0 - start_time > self.run_for:
                self.running = False
                break

            self.simulator.step()
            sim_time = self.simulator.sim_time

            for planet in Planet:
                if np.random.rand() < 0.1:
                    target = np.random.choice([p for p in Planet if p != planet])
                    token = self.oam_network.generate_oam_token(planet, self.simulator.coherences[planet])
                    self.oam_network.emit(planet, target, token, sim_time)
                    self.oam_tokens_exchanged += 1

            oam_deliveries = self.oam_network.tick(sim_time)

            visor_payload = self.simulator.get_visor_payload()
            visor_payload['oam_deliveries'] = {p.name: len(toks) for p, toks in oam_deliveries.items()}
            visor_payload['oam_queue_depth'] = {
                f"{src.name}->{tgt.name}": link.transmission_queue.__len__()
                for (src, tgt), link in self.oam_network.links.items()
            }

            await self.broadcast(visor_payload)
            self.frames_emitted += 1

            elapsed = time.time() - t0
            await asyncio.sleep(max(0, interval - elapsed))

    async def handler(self, websocket):
        await self.register_client(websocket)
        try:
            async for message in websocket:
                cmd = json.loads(message)
                if cmd.get('action') == 'ping':
                    await websocket.send(json.dumps({'pong': True, 'time': time.time()}))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)

    async def start(self):
        self.running = True
        # In websockets >= 10.0, the handler argument signature is async def handler(websocket):
        server = await websockets.serve(
            self.handler,
            "0.0.0.0",
            self.config.websocket_port,
            ping_interval=20,
            ping_timeout=10
        )

        sim_task = asyncio.create_task(self.simulation_loop())

        print(f"\n🪐🧬⚡ ARKHE OS v∞.112 — VISOR + OAM CROSS-BODY OPERACIONAL")
        print(f"   Servidor WebSocket: ws://localhost:{self.config.websocket_port}")

        try:
            while self.running:
                await asyncio.sleep(0.5)
        finally:
            self.running = False
            sim_task.cancel()
            server.close()

if __name__ == "__main__":
    config = VisorConfig()
    run_for = int(sys.argv[1]) if len(sys.argv) > 1 else None
    server = ArkheVisorServer(config, run_for=run_for)

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        pass
