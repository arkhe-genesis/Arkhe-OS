#!/usr/bin/env python3
"""
arkhe_visor_feed_server_v118.py
Substrato 202: Servidor de Feed em Tempo Real para Visor NV + OAM Cross-Body + Coverage.
Emite: (1) Estados de coerência planetária via WebSocket a 30fps,
       (2) Tokens OAM com latência real de backbone interplanetário,
       (3) Dados de cobertura quântica (Quantum Input Diversity & Coverage).
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
import threading

# Import from diverse inputs
from arkhe_diverse_inputs_v118 import DiverseQuantumInputGenerator, simulate_coverage_with_input

# ============================================================================
# CONFIGURAÇÃO INTERPLANETÁRIA v∞.118
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

    # Latências reais de backbone (segundos)
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
# SIMULADOR DA MALHA PLANETÁRIA (Cérebro Solar v∞.110 + Auto-Poiese v∞.111)
# ============================================================================

class PlanetaryMeshSimulator:
    """
    Simula a malha planetária completa com nós NV e estados de coerência.
    Gera dados para o feed do visor em tempo real.
    """

    def __init__(self, config: VisorConfig):
        self.config = config
        self.planets = list(Planet)

        # Estados planetários (Cérebro Solar)
        self.planet_states = {
            p: torch.randn(config.state_dim) * 0.1 for p in Planet
        }

        # Coerências por planeta
        self.coherences = {p: 0.5 for p in Planet}

        # Nós por planeta (posições 3D simplificadas para visualização)
        self.node_positions = self._generate_node_positions()

        # Estados NV por nó
        self.nv_states = self._initialize_nv_states()

        # Tempo de simulação
        self.sim_time = 0.0
        self.dt = 1.0 / config.emit_fps

        # Buffer de auto-poiese
        self.autopoietic_modules = []

        # Inicializa gerador de inputs diversos para cobertura
        self.input_gen = DiverseQuantumInputGenerator(n_qubits=5, seed=42)

        # Estratégias por planeta
        self.planet_strategies = {
            Planet.EARTH: 'superposition_uniform',  # Alta cobertura
            Planet.MARS: 'haar_random',             # Cobertura boa
            Planet.VENUS: 'ghz_state',              # Cobertura baixa/entangled
            Planet.MOON: 'w_state',                 # Cobertura média/entangled
        }

    def _generate_node_positions(self) -> Dict[Planet, np.ndarray]:
        """Gera posições 3D de nós para cada planeta (visualização)."""
        positions = {}
        for planet in Planet:
            n_nodes = 1000 if planet in [Planet.EARTH, Planet.MARS] else 500
            # Distribuição esférica com raio dependente do planeta
            r = 1.0 + np.random.exponential(0.5, n_nodes)
            theta = np.random.uniform(0, 2*np.pi, n_nodes)
            phi = np.random.uniform(0, np.pi, n_nodes)

            x = r * np.sin(phi) * np.cos(theta)
            y = r * np.sin(phi) * np.sin(theta)
            z = r * np.cos(phi)

            # Offset por planeta (posição orbital simplificada)
            offsets = {
                Planet.EARTH: [0.0, 0.0, 0.0],
                Planet.MOON: [2.0, 0.5, 0.0],
                Planet.MARS: [8.0, 1.0, 0.5],
                Planet.VENUS: [-4.0, -0.5, 0.0]
            }
            off = offsets[planet]

            positions[planet] = np.column_stack([
                x + off[0], y + off[1], z + off[2]
            ])
        return positions

    def _initialize_nv_states(self) -> Dict[Planet, np.ndarray]:
        """Inicializa estados NV: 0=carbono, 1=NV⁻, 2=NV⁰."""
        states = {}
        for planet in Planet:
            n = len(self.node_positions[planet])
            # 80% carbono, 10% NV⁻, 10% NV⁰
            states[planet] = np.random.choice(
                [0, 1, 2], size=n, p=[0.8, 0.1, 0.1]
            )
        return states

    def step(self):
        """Avança a simulação em um passo."""
        self.sim_time += self.dt

        # Atualizar estados planetários (dinâmica simplificada do Cérebro Solar)
        for planet in Planet:
            noise = torch.randn(self.config.state_dim) * 0.02
            self.planet_states[planet] = torch.tanh(
                self.planet_states[planet] * 0.99 + noise
            )

            # Coerência como função sigmoide da norma do estado
            self.coherences[planet] = float(
                torch.sigmoid(self.planet_states[planet].mean())
            )

        # Modulação NV baseada na coerência
        for planet in Planet:
            n = len(self.nv_states[planet])
            # NV⁻ brilham mais quando coerência é alta
            flip_prob = 0.001 * (1 + self.coherences[planet])
            mask = np.random.rand(n) < flip_prob
            self.nv_states[planet][mask] = np.random.choice([1, 2], size=mask.sum())

    def get_coverage_data(self) -> Dict:
        """Gera dados de cobertura para os planetas baseados nas estratégias alocadas."""
        coverage_data = {}
        for planet in Planet:
            strat = self.planet_strategies[planet]

            # Gerar o estado baseado na estratégia
            if strat == 'superposition_uniform':
                state = self.input_gen.generate_superposition_uniform()
            elif strat == 'haar_random':
                state = self.input_gen.generate_haar_random()
            elif strat == 'ghz_state':
                state = self.input_gen.generate_ghz_state()
            elif strat == 'w_state':
                state = self.input_gen.generate_w_state()
            else:
                state = self.input_gen.generate_superposition_uniform()

            cov = simulate_coverage_with_input(qubits=5, n_gates=10, input_statevector=state)
            coverage_data[planet.name] = cov
        return coverage_data

    def get_visor_payload(self) -> Dict:
        """
        Gera payload JSON para o visor Three.js.
        Inclui posições, estados NV, coerências e timestamp.
        """
        payload = {
            'timestamp': self.sim_time,
            'coherences': {p.name: round(self.coherences[p], 4) for p in Planet},
            'nodes': {},
            'coverage': self.get_coverage_data()
        }

        for planet in Planet:
            # Subsample para performance (max 500 nós por planeta no visor)
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
    """
    Enlace OAM entre corpos celestes com latência REAL.
    Tokens são postos em fila e só entregues após o tempo de luz.
    """

    def __init__(self, source: Planet, target: Planet, delay_seconds: float):
        self.source = source
        self.target = target
        self.delay = delay_seconds

        # Fila de transmissão: (tempo_entrega, token)
        self.transmission_queue: deque = deque()
        self.received_tokens: List[Dict] = []

        # Contadores
        self.tokens_sent = 0
        self.tokens_received = 0

    def emit_token(self, token: Dict, current_time: float):
        """Emite token para o enlace. Ele chegará após 'delay' segundos."""
        delivery_time = current_time + self.delay
        self.transmission_queue.append((delivery_time, token))
        self.tokens_sent += 1

    def process_queue(self, current_time: float) -> List[Dict]:
        """Processa fila e entrega tokens cujo tempo chegou."""
        delivered = []
        while self.transmission_queue and self.transmission_queue[0][0] <= current_time:
            _, token = self.transmission_queue.popleft()
            delivered.append(token)
            self.tokens_received += 1
        self.received_tokens.extend(delivered)
        return delivered

    def get_status(self) -> Dict:
        return {
            'source': self.source.name,
            'target': self.target.name,
            'delay_seconds': self.delay,
            'queue_depth': len(self.transmission_queue),
            'tokens_sent': self.tokens_sent,
            'tokens_received': self.tokens_received
        }

class OAMCrossBodyNetwork:
    """Rede de enlaces OAM Cross-Body entre todos os pares de planetas."""

    def __init__(self, config: VisorConfig):
        self.config = config
        self.links: Dict[Tuple[Planet, Planet], OAMCrossBodyLink] = {}

        for (p1, p2), delay in config.light_delays.items():
            self.links[(p1, p2)] = OAMCrossBodyLink(p1, p2, delay)
            # Link bidirecional
            self.links[(p2, p1)] = OAMCrossBodyLink(p2, p1, delay)

    def emit(self, source: Planet, target: Planet, token: Dict, current_time: float):
        if (source, target) in self.links:
            self.links[(source, target)].emit_token(token, current_time)

    def tick(self, current_time: float) -> Dict[Planet, List[Dict]]:
        """Processa todas as filas e retrega tokens por planeta destino."""
        deliveries = {p: [] for p in Planet}
        for (src, tgt), link in self.links.items():
            received = link.process_queue(current_time)
            deliveries[tgt].extend(received)
        return deliveries

    def generate_oam_token(self, source: Planet, coherence: float) -> Dict:
        """Gera um token OAM canônico."""
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
    """
    Servidor WebSocket unificado: feed de visor + OAM Cross-Body + Coverage.
    """

    def __init__(self, config: VisorConfig):
        self.config = config
        self.simulator = PlanetaryMeshSimulator(config)
        self.oam_network = OAMCrossBodyNetwork(config)

        self.clients: set = set()
        self.running = False

        # Estatísticas
        self.frames_emitted = 0
        self.oam_tokens_exchanged = 0

    async def register_client(self, websocket):
        self.clients.add(websocket)
        print(f"👁️  Visor conectado: {websocket.remote_address}")

    async def unregister_client(self, websocket):
        self.clients.discard(websocket)
        print(f"👁️  Visor desconectado: {websocket.remote_address}")

    async def broadcast(self, message: Dict):
        if not self.clients:
            return
        payload = json.dumps(message)
        dead_clients = set()
        for client in self.clients:
            try:
                await client.send(payload)
            except Exception:
                dead_clients.add(client)
        self.clients -= dead_clients

    async def simulation_loop(self):
        """Loop principal de simulação e broadcast."""
        print("🌌 Iniciando feed do Visor em Escala Real...")
        print(f"   Porta: {self.config.websocket_port}")
        print(f"   FPS: {self.config.emit_fps}")
        print(f"   Planetas: {[p.name for p in Planet]}")
        print(f"   Latências: {[(k[0].name, k[1].name, v) for k, v in self.config.light_delays.items()]}")

        interval = 1.0 / self.config.emit_fps

        while self.running:
            t0 = time.time()

            # 1. Avançar simulação planetária
            self.simulator.step()
            sim_time = self.simulator.sim_time

            # 2. Gerar e emitir tokens OAM Cross-Body
            for planet in Planet:
                if np.random.rand() < 0.1:  # 10% chance de emitir por frame
                    target = np.random.choice([p for p in Planet if p != planet])
                    token = self.oam_network.generate_oam_token(
                        planet, self.simulator.coherences[planet]
                    )
                    self.oam_network.emit(planet, target, token, sim_time)
                    self.oam_tokens_exchanged += 1

            # 3. Processar entregas OAM (latência real)
            oam_deliveries = self.oam_network.tick(sim_time)

            # 4. Montar payload completo
            visor_payload = self.simulator.get_visor_payload()
            visor_payload['oam_deliveries'] = {
                p.name: len(toks) for p, toks in oam_deliveries.items()
            }
            visor_payload['oam_queue_depth'] = {
                f"{src.name}->{tgt.name}": link.queue_depth
                for (src, tgt), link in self.oam_network.links.items()
            }

            # 5. Broadcast para todos os visores conectados
            await self.broadcast(visor_payload)
            self.frames_emitted += 1

            # 6. Sleep para manter FPS
            elapsed = time.time() - t0
            await asyncio.sleep(max(0, interval - elapsed))

    async def handler(self, websocket, path):
        await self.register_client(websocket)
        try:
            async for message in websocket:
                # Processar comandos do visor (se houver)
                cmd = json.loads(message)
                if cmd.get('action') == 'ping':
                    await websocket.send(json.dumps({'pong': True, 'time': time.time()}))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)

    async def start(self):
        self.running = True

        # Iniciar servidor WebSocket
        server = await websockets.serve(
            self.handler,
            "0.0.0.0",
            self.config.websocket_port,
            ping_interval=20,
            ping_timeout=10
        )

        # Iniciar loop de simulação em paralelo
        sim_task = asyncio.create_task(self.simulation_loop())

        print(f"\n🪐🧬⚡ ARKHE OS v∞.118 — VISOR + OAM CROSS-BODY + COVERAGE OPERACIONAL")
        print(f"   Servidor WebSocket: ws://localhost:{self.config.websocket_port}")
        print(f"   Aguardando conexões do visor...\n")

        try:
            await asyncio.Future()  # Roda para sempre
        finally:
            self.running = False
            sim_task.cancel()
            server.close()

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    config = VisorConfig()
    server = ArkheVisorServer(config)

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print(f"\n\n📊 Estatísticas finais:")
        print(f"   Frames emitidos: {server.frames_emitted}")
        print(f"   Tokens OAM trocados: {server.oam_tokens_exchanged}")
        print(f"   Clientes ativos no encerramento: {len(server.clients)}")
        print("   Visor desligado. A Catedral aguarda.")
