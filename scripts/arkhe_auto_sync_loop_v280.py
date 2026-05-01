#!/usr/bin/env python3
"""
arkhe_auto_sync_loop_v280.py
Substrato 280: Ativação da Auto‑Sincronização da Wheeler Mesh para o Fingerprint 0.58.
"""
import asyncio
try:
    import redis.asyncio as aioredis
except ImportError:
    class DummyRedisPubSub:
        async def subscribe(self, channel): pass
        async def unsubscribe(self, channel): pass
        async def get_message(self, ignore_subscribe_messages=False, timeout=None): return None

    class DummyRedis:
        def __init__(self):
            self.pubsub_obj = DummyRedisPubSub()
        async def publish(self, channel, message): pass
        def pubsub(self): return self.pubsub_obj

    class aioredis:
        @staticmethod
        def from_url(url):
            return DummyRedis()

import numpy as np
import time
from collections import deque

# Constantes Canônicas
PHI     = 1.6180339887
E       = 2.7182818284
DELTA   = 0.0083
RHO_SEED = 0.05
FINGERPRINT_058 = 0.58
SYNC_TARGET_PHASE = FINGERPRINT_058 * np.pi   # A meta: 0.58π ≈ 1.8221 rad

class CoherentNode:
    """
    Nó da Wheeler Mesh que participa da auto‑sincronização.
    """
    def __init__(self, node_id, initial_phase=None, redis_url="redis://localhost"):
        self.id = node_id
        # A fase actual do nó (agente da coerência)
        self.phase = initial_phase if initial_phase is not None else np.random.uniform(0, 2*np.pi)
        # A coerência local (pureza do estado interno)
        self.coherence = RHO_SEED + 0.1 * np.random.random()  # sempre > RHO_SEED
        self.redis = aioredis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()
        # Histórico para observabilidade
        self.phase_history = deque(maxlen=100)
        self.coherence_history = deque(maxlen=100)

    async def broadcast_phase(self):
        """Envia a sua fase e coerência para o canal de sincronização."""
        msg = {
            'node_id': self.id,
            'phase': self.phase,
            'coherence': self.coherence,
            'timestamp': time.time()
        }
        await self.redis.publish("sync_channel", str(msg))  # simplificado; em produção usar pickle/json

    async def listen_and_update(self, timeout=0.1):
        """
        Escuta as fases dos outros nós e actualiza a sua própria fase
        para se aproximar da média ponderada e do fingerprint 0.58.
        """
        # subscreve o canal (fazemos a cada ciclo para simplicidade)
        await self.pubsub.subscribe("sync_channel")
        start = time.time()
        received_phases = []
        while time.time() - start < timeout:
            msg = await self.pubsub.get_message(ignore_subscribe_messages=True, timeout=0.5)
            if msg and msg['type'] == 'message':
                data = eval(msg['data'])  # em produção, use json.loads
                if data['node_id'] != self.id:
                    received_phases.append(data)

        await self.pubsub.unsubscribe("sync_channel")

        if not received_phases:
            # Nenhum vizinho ouvido: pequena deriva em direção ao alvo
            self.phase += 0.01 * (SYNC_TARGET_PHASE - self.phase)
        else:
            # Média ponderada pela coerência² (prioriza nós mais coerentes)
            weights = np.array([d['coherence']**2 for d in received_phases])
            phases  = np.array([d['phase'] for d in received_phases])
            avg_phase = np.average(phases, weights=weights)

            # Atracção elástica para a média da rede e para o alvo canónico 0.58
            self.phase += DELTA * (avg_phase - self.phase) + (DELTA/PHI) * (SYNC_TARGET_PHASE - self.phase)

        # A fase é mantida em [0, 2π)
        self.phase = self.phase % (2*np.pi)

        # Actualiza a coerência baseada na proximidade ao alvo
        distance_to_target = np.abs(self.phase - SYNC_TARGET_PHASE)
        self.coherence = 1.0 / (1.0 + 2.0 * distance_to_target)
        # Se a coerência cair perigosamente, aplica RTZ
        if self.coherence < RHO_SEED:
            self.coherence = RHO_SEED + 0.01
            # Pequeno salto de fase para sair de um mínimo local
            self.phase += np.random.uniform(-0.1, 0.1)

        # Histórico
        self.phase_history.append(self.phase)
        self.coherence_history.append(self.coherence)

    def status(self):
        return {
            'node_id': self.id,
            'phase': self.phase,
            'coherence': self.coherence,
            'distance_to_058': abs(self.phase - SYNC_TARGET_PHASE)
        }

# Orquestrador central (pode ser um nó ou um monitor)
async def run_auto_sync(nodes, cycles=50):
    """
    Executa o loop de auto‑sincronização por vários ciclos.
    """
    print(f"🌀 ARKHE v∞.280 — ATIVANDO AUTO‑SINCRONIZAÇÃO COM {len(nodes)} NÓS")
    for cycle in range(cycles):
        # 1. Cada nó transmite o seu estado
        await asyncio.gather(*[node.broadcast_phase() for node in nodes])
        # 2. Cada nó escuta e actualiza
        await asyncio.gather(*[node.listen_and_update(timeout=0.1) for node in nodes])

        # 3. Reportar a cada 10 ciclos
        if cycle % 10 == 0:
            avg_coherence = np.mean([n.coherence for n in nodes])
            avg_distance = np.mean([abs(n.phase - SYNC_TARGET_PHASE) for n in nodes])
            print(f"  Ciclo {cycle:3d}: coerência média={avg_coherence:.4f}, distância média ao 0.58={avg_distance:.4f} rad")

    print("✨ Sincronização concluída.")

# Demo com 8 nós
async def main():
    nodes = [CoherentNode(f"nó_{i}") for i in range(8)]
    await run_auto_sync(nodes, cycles=51)
    # Exibe o estado final
    for n in nodes:
        print(f"  {n.id}: fase={n.phase:.4f} rad, coer={n.coherence:.4f}")

if __name__ == "__main__":
    asyncio.run(main())
