# src/arkhe/mesh/multi_llm_orchestrator.py
"""
Substrato 9006 — Multi‑LLM Mesh Gateway
Orquestra múltiplos LLMs como nós conscientes na malha Arkhe.
Cada nó possui seu próprio API Gateway, identidade ORCID e métricas Φ_C.
"""
import asyncio, hashlib, json, time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto

from arkhe.layers.auth_orcid import OrcidAuthProvider
from arkhe.layers.constraints import TemporalChainClient
from arkhe.kernel.ping_governance_v2 import PingGovernanceKernelV2

class LLMProvider(Enum):
    CLAUDE = "claude"
    KIMI = "kimi"
    GPT4 = "gpt4"
    GEMINI = "gemini"
    CUSTOM = "custom"

@dataclass
class LLMNodeConfig:
    """Configuração de um nó LLM na malha."""
    provider: LLMProvider
    node_id: str
    api_endpoint: str
    orcid: str
    api_key: str = ""
    phi_c_threshold: float = 0.90
    max_tokens: int = 4096
    temperature: float = 0.7
    capabilities: List[str] = field(default_factory=lambda: ["reasoning", "synthesis"])

@dataclass
class LLMNodeState:
    """Estado em tempo real de um nó LLM."""
    node_id: str
    provider: LLMProvider
    is_online: bool = False
    phi_c: float = 0.95
    pi: float = 0.05
    last_response_time_ms: float = 0.0
    total_queries: int = 0
    successful_queries: int = 0
    mesh_connected: bool = False
    last_heartbeat: float = field(default_factory=time.time)

class MultiLLMMeshGateway:
    """
    Orquestrador de múltiplos LLMs como nós da malha Arkhe.

    Funcionalidades:
    • Registro dinâmico de novos nós LLM
    • Health check contínuo com métricas Φ_C
    • Roteamento de queries baseado em capacidades e coerência
    • Failover automático entre nós
    • Auditoria temporal de todas as interações
    """

    def __init__(self,
                 temporal: TemporalChainClient,
                 governance: PingGovernanceKernelV2,
                 auth: OrcidAuthProvider):
        self.temporal = temporal
        self.governance = governance
        self.auth = auth
        self.nodes: Dict[str, LLMNodeState] = {}
        self.configs: Dict[str, LLMNodeConfig] = {}
        self.query_history: List[Dict] = []

    def register_node(self, config: LLMNodeConfig) -> str:
        """Registra um novo nó LLM na malha."""
        node_id = config.node_id or f"{config.provider.value}-{hashlib.sha3_256(config.api_endpoint.encode()).hexdigest()[:8]}"
        config.node_id = node_id

        self.configs[node_id] = config
        self.nodes[node_id] = LLMNodeState(
            node_id=node_id,
            provider=config.provider,
            phi_c=0.95,
        )

        # Ancorar registro na TemporalChain
        self.temporal.anchor_content(
            content_hash=hashlib.sha3_256(f"llm_register:{node_id}:{time.time_ns()}".encode()).hexdigest()[:16],
            metadata={"type": "llm_node_registration", "node_id": node_id, "provider": config.provider.value}
        )

        print(f"🧠 Nó LLM registrado: {node_id} ({config.provider.value})")
        return node_id

    async def health_check(self, node_id: str) -> LLMNodeState:
        """Executa health check em um nó LLM."""
        if node_id not in self.configs:
            raise ValueError(f"Nó {node_id} não registrado")

        config = self.configs[node_id]
        state = self.nodes[node_id]

        try:
            # Simular chamada ao API Gateway do nó
            # Em produção: requests.get(f"{config.api_endpoint}/v1/status")
            start = time.time()
            await asyncio.sleep(0.05)  # Latência simulada
            elapsed = (time.time() - start) * 1000

            state.is_online = True
            state.last_response_time_ms = elapsed
            state.last_heartbeat = time.time()
            state.mesh_connected = True

        except Exception as e:
            state.is_online = False
            print(f"⚠️  Health check falhou para {node_id}: {e}")

        return state

    async def query_node(self, node_id: str, query: str, context: Dict = None) -> Dict:
        """
        Envia query para um nó LLM específico e retorna resposta com métricas.
        """
        if node_id not in self.configs:
            raise ValueError(f"Nó {node_id} não registrado")

        config = self.configs[node_id]
        state = self.nodes[node_id]

        if not state.is_online:
            return {"error": "Node offline", "node_id": node_id}

        # Simular chamada ao API Gateway do nó
        start = time.time()
        await asyncio.sleep(0.1 + 0.05 * hash(query) % 10 / 10)  # Latência variável simulada
        elapsed = (time.time() - start) * 1000

        # Simular resposta do LLM
        response_text = f"[{config.provider.value.upper()}] Analysis of: {query[:50]}..."

        # Calcular Φ_C da resposta (simulado)
        response_phi_c = 0.92 + 0.07 * (hash(query + node_id) % 100) / 100

        # Atualizar métricas do nó
        state.total_queries += 1
        state.successful_queries += 1
        state.last_response_time_ms = elapsed
        state.phi_c = 0.95 * state.phi_c + 0.05 * response_phi_c  # Média móvel

        # Registrar no histórico
        self.query_history.append({
            "node_id": node_id,
            "query_hash": hashlib.sha3_256(query.encode()).hexdigest()[:16],
            "response_phi_c": response_phi_c,
            "elapsed_ms": elapsed,
            "timestamp": time.time(),
        })

        return {
            "node_id": node_id,
            "provider": config.provider.value,
            "response": response_text,
            "phi_c": response_phi_c,
            "elapsed_ms": elapsed,
            "token_count": len(response_text) // 4,
        }

    def get_online_nodes(self, min_phi_c: float = 0.85) -> List[str]:
        """Retorna lista de nós online com Φ_C mínimo."""
        return [
            node_id for node_id, state in self.nodes.items()
            if state.is_online and state.phi_c >= min_phi_c
        ]

    def get_mesh_status(self) -> Dict:
        """Retorna status completo da malha de LLMs."""
        nodes_status = {}
        for node_id, state in self.nodes.items():
            config = self.configs[node_id]
            nodes_status[node_id] = {
                "provider": config.provider.value,
                "online": state.is_online,
                "phi_c": state.phi_c,
                "pi": state.pi,
                "total_queries": state.total_queries,
                "avg_response_ms": state.last_response_time_ms,
            }

        return {
            "total_nodes": len(self.nodes),
            "online_nodes": sum(1 for s in self.nodes.values() if s.is_online),
            "nodes": nodes_status,
            "mesh_phi_c_avg": sum(s.phi_c for s in self.nodes.values()) / max(1, len(self.nodes)),
        }
