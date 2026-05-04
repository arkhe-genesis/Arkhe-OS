import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import numpy as np

# Simple mock classes to allow execution without dependencies

@dataclass
class FieldEpisode:
    observations: np.ndarray
    actions: np.ndarray
    rewards: np.ndarray
    gaps: np.ndarray
    metadata: Dict

@dataclass
class DeploymentConfig:
    """Configuração para deployment em campo."""
    nodes: List[str]  # IDs dos T-Beams
    sim_policy_path: str  # política pré-treinada
    field_data_dir: str  # diretório para dados coletados
    oracle_config_path: str  # configuração de oráculos
    arxia_rpc_url: str
    arxia_contract: str
    orchestrator_private_key: str
    transfer_learning_epochs: int = 50
    report_interval_steps: int = 100

class FieldDeploymentPipeline:
    """Pipeline completo para deploy, coleta, fine-tuning e registro on-chain."""

    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.transfer_learner = None
        self.multi_oracle = None
        self.report_registry = None
        self.collected_episodes: List[FieldEpisode] = []

    async def initialize(self):
        """Inicializa componentes do pipeline."""
        print("✅ Componentes inicializados")

    async def collect_field_data(self, duration_minutes: int = 30):
        """Coleta dados em campo dos T-Beams via serial/LoRa."""
        from collections import deque

        print(f"📡 Coletando dados por {duration_minutes} minutos...")
        start_time = time.time()

        connections = {}
        for node_id in self.config.nodes:
            connections[node_id] = deque(maxlen=1000)  # buffer simulado

        simulated_duration = duration_minutes * 6  # Faster simulation: 1 real second = 10 simulated seconds

        while time.time() - start_time < simulated_duration:
            for node_id, conn in connections.items():
                if np.random.random() < 0.1:  # 10% de chance de novo dado
                    data_point = {
                        'timestamp': time.time(),
                        'node_id': node_id,
                        'gap': np.random.uniform(0, 20),
                        'sf': np.random.randint(7, 13),
                        'rssi': np.random.uniform(-90, -50),
                        'hallucination': np.random.random() < 0.05,
                        'temperature': np.random.uniform(20, 35),
                        'battery_pct': np.random.uniform(50, 100)
                    }
                    conn.append(data_point)

            if int(time.time()) % 2 == 0: # Check more frequently in simulation
                for node_id, conn in connections.items():
                    if len(conn) >= 20:  # mínimo para formar episódio
                        episode = self._build_episode(list(conn), node_id)
                        self.collected_episodes.append(episode)
                        conn.clear()
                        print(f"  📦 Episódio coletado de {node_id} (T={len(episode.observations)})")

            await asyncio.sleep(0.1) # Faster simulation sleep

        print(f"✅ Coleta concluída: {len(self.collected_episodes)} episódios")

    def _build_episode(self, data_points: List[Dict], node_id: str) -> FieldEpisode:
        """Converte lista de pontos de dados em episódio para treino."""
        T = len(data_points)
        observations = np.array([
            [dp['gap'], dp['sf'], dp['rssi'],
             dp['temperature'], dp['battery_pct'], dp['hallucination']]
            for dp in data_points
        ])
        actions = np.array([[dp['sf'] - 7] for dp in data_points])  # ação: ajuste de SF
        rewards = np.array([-dp['gap'] * 0.1 for dp in data_points])  # recompensa: gap menor é melhor
        gaps = np.array([dp['gap'] for dp in data_points])

        metadata = {
            'node_id': node_id,
            'start_time': data_points[0]['timestamp'],
            'end_time': data_points[-1]['timestamp'],
            'hallucination': [dp['hallucination'] for dp in data_points]
        }

        return FieldEpisode(
            observations=observations,
            actions=actions,
            rewards=rewards,
            gaps=gaps,
            metadata=metadata
        )

    async def fine_tune_policy(self):
        """Executa fine-tuning da política com dados de campo."""
        if not self.collected_episodes:
            print("⚠️ Nenhum episódio coletado para fine-tuning")
            return

        print(f"🤖 Fine-tuning com {len(self.collected_episodes)} episódios...")
        print(f"✅ Política salva em {self.config.field_data_dir}/field_policy.pt")

    async def generate_and_register_report(self, stage_results: Dict):
        """Gera relatório de desempenho e registra on-chain."""
        import hashlib
        print("📄 Gerando relatório de desempenho...")

        if not self.collected_episodes:
            avg_gap = 0.0
            avg_hall = 0.0
        else:
            avg_gap = np.mean([np.mean(ep.gaps) for ep in self.collected_episodes])
            avg_hall = np.mean([
                np.mean([1 if g else 0 for g in ep.metadata.get('hallucination', [])])
                for ep in self.collected_episodes
            ])

        report = {
            'timestamp': int(time.time()),
            'deployment_id': hashlib.sha256(
                f"{self.config.nodes}{time.time()}".encode()
            ).hexdigest()[:16],
            'nodes': self.config.nodes,
            'episodes_collected': len(self.collected_episodes),
            'avg_gap': float(avg_gap),
            'avg_hallucination_rate': float(avg_hall),
            'oracle_prices': {
                'energy_gj': {'price': 0.12},
                'compute_tflops': {'price': 0.05},
                'bandwidth_mbps': {'price': 0.001}
            },
            'stage_results': stage_results
        }

        print("🔗 Registrando relatório no ledger Arxia...")

        # Mock registration
        registration = {
            'report_hash': hashlib.sha256(str(report).encode()).hexdigest(),
            'tx_hash': '0x' + hashlib.sha256(b'tx').hexdigest(),
            'block_number': 12345
        }

        report['on_chain'] = registration

        Path(self.config.field_data_dir).mkdir(parents=True, exist_ok=True)
        report_path = Path(self.config.field_data_dir) / f"report_{report['deployment_id']}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"✅ Relatório registrado: {report_path}")
        print(f"   Hash: {registration['report_hash'][:16]}...")
        print(f"   TX: {registration['tx_hash'][:16]}...")

        return report

    async def run_full_pipeline(self, stage_results: Optional[Dict] = None):
        """Executa pipeline completo: coleta → fine-tuning → relatório on-chain."""
        await self.initialize()
        await self.collect_field_data(duration_minutes=2)  # Short for demo
        await self.fine_tune_policy()
        report = await self.generate_and_register_report(stage_results or {})
        return report

if __name__ == "__main__":
    config = DeploymentConfig(
        nodes=[f"WFL{i}" for i in range(10)],
        sim_policy_path="sim_policy.pt",
        field_data_dir="field_data",
        oracle_config_path="oracle.json",
        arxia_rpc_url="http://localhost:8545",
        arxia_contract="0x123",
        orchestrator_private_key="0x456"
    )
    pipeline = FieldDeploymentPipeline(config)
    asyncio.run(pipeline.run_full_pipeline())
