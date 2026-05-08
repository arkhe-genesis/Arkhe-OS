#!/usr/bin/env python3
"""
arkhe-federate.py — ARKHE Federation Registry Daemon (Substrate 321).
Executa em ambiente rootless (Podman + Tor).
Responsável por:
  • Manter uma entrada no DHT anónimo com o estado de coerência.
  • Participar no protocolo gossip para disseminar anúncios.
  • Avaliar reputação de peers.
  • Servir como ponto de bootstrap para novos nós.
"""
import asyncio
import os
import sys
import signal
import logging
from pathlib import Path
from datetime import datetime

# Importar subsistemas
from src.dht import TorKademliaNode
from src.gossip import GossipAgent
from src.reputation import ReputationEngine
from src.utils.coherence_proof import CoherenceProver

logging.basicConfig(level=logging.INFO, format='[FEDERATE] %(message)s')
logger = logging.getLogger(__name__)

class ArkheFederateDaemon:
    def __init__(self, config_path: Path = Path("/etc/agi/federation.yaml")):
        # Carregar configuração
        self.config = self._load_config(config_path)
        self.onion_address = self.config.get("onion_address", None)
        self.dht_port = int(self.config.get("dht_port", 9876))

        # Inicializar componentes
        self.dht = TorKademliaNode(
            node_id=self.onion_address,  # identidade = hash da chave .onion
            port=self.dht_port,
            bootstrap_nodes=self.config.get("bootstrap_nodes", [])
        )
        self.gossip = GossipAgent(self.dht, self.onion_address)
        self.reputation = ReputationEngine()
        self.prover = CoherenceProver()

        self.running = False

    def _load_config(self, path):
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    async def start(self):
        logger.info("🌐 Iniciando arkhe‑federate daemon...")
        self.running = True

        # 1. Iniciar nó DHT (Kademlia sobre Tor)
        await self.dht.listen()
        logger.info(f"DHT escutando na porta {self.dht_port} via Tor")

        # 2. Bootstrap: juntar‑se à rede a partir das seeds
        if not await self.dht.bootstrap():
            logger.error("Falha no bootstrap — a usar lista de seeds estática")
            await self._seed_from_file()

        # 3. Publicar o próprio registo na DHT
        await self._publish_self()

        # 4. Iniciar ciclo de gossip (em background)
        asyncio.create_task(self.gossip.run())

        # 5. Iniciar verificações periódicas de reputação
        asyncio.create_task(self.reputation.run_audit_cycle())

        # Manter o daemon ativo
        while self.running:
            await asyncio.sleep(10)

    async def _publish_self(self):
        """Publica assinatura + coerência na DHT."""
        proof = self.prover.generate_proof()
        record = {
            "onion": self.onion_address,
            "timestamp": datetime.utcnow().isoformat(),
            "coherence": proof["coherence"],
            "signature": proof["signature"],
            "capabilities": ["rcp_v2", "omni_core", "federation"],
        }
        await self.dht.store(hash(self.onion_address), record)
        logger.info(f"Registo próprio publicado: {self.onion_address} (Φ={proof['coherence']:.3f})")

    async def _seed_from_file(self):
        """Lê seeds do ficheiro de bootstrap para descoberta inicial."""
        seed_file = Path(self.config.get("seed_file", "/etc/agi/federation/seeds.txt"))
        if seed_file.exists():
            with open(seed_file) as f:
                for line in f:
                    addr = line.strip()
                    if addr:
                        await self.dht.add_peer(addr)
            logger.info(f"Carregadas {len(self.dht.peers)} seeds do ficheiro")

    async def shutdown(self):
        logger.info("🌐 Encerrando arkhe‑federate...")
        self.running = False
        await self.dht.stop()
        await self.gossip.stop()

def main():
    daemon = ArkheFederateDaemon()
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(daemon.shutdown()))
    loop.run_until_complete(daemon.start())

if __name__ == "__main__":
    main()