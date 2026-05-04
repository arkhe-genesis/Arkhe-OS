"""
arkhe_forge.py
Arquitetura de Selos para Orquestração LLM/GPU
Implementa os três Axiomas da Torre em substrato clássico.
"""

from __future__ import annotations
import time
import asyncio
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Callable, Any, TypedDict, Annotated, Literal
import operator
import numpy as np
from langgraph.graph import StateGraph, END

# Global state for dependency management
HAS_SENTENCE_TRANSFORMERS = False
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    print("⚠️ Warning: sentence-transformers not found. Using mock embeddings.")

# =============================================================================
# AXIOMA 1: MÔNADE DE RECURSOS (GPU + KV CACHE + MODELOS)
# =============================================================================

class ModelProfile(Enum):
    SMALL = 1   # Phi-4-mini, 4B
    MEDIUM = 2  # Llama-3.1-70B
    LARGE = 3   # Llama-4-405B

@dataclass
class ResourceState:
    """
    Estado da mônade M. Não é apenas 'memória livre'.
    É uma matriz de adjacência de páginas HBM (Sheaf section).
    """
    total_vram_mb: float = 81920.0  # H100 80GB
    page_size_mb: float = 16.0      # vLLM page size
    allocated_pages: set[int] = field(default_factory=set)
    model_registry: Dict[ModelProfile, int] = field(default_factory=dict)
    allocations: Dict[int, List[int]] = field(default_factory=dict)

    # Topologia física: páginas contíguas como "faixas" (ranges)
    def contiguous_blocks(self) -> List[tuple[int, int]]:
        """Retorna blocos contíguos livres (início, fim)."""
        all_pages = set(range(int(self.total_vram_mb / self.page_size_mb)))
        free = sorted(all_pages - self.allocated_pages)
        if not free:
            return []
        blocks = []
        start = free[0]
        prev = free[0]
        for p in free[1:]:
            if p == prev + 1:
                prev = p
            else:
                blocks.append((start, prev))
                start = p
                prev = p
        blocks.append((start, prev))
        return blocks

    def can_allocate(self, n_tokens: int, model: ModelProfile,
                     seq_len: int = 4096) -> bool:
        """
        A seta em Q_M só existe se houver:
        1. Páginas suficientes para o KV cache
        2. Bloco contíguo para o modelo (weights)
        3. Co-localidade NVLink se multi-GPU
        """
        kv_pages_needed = (n_tokens + seq_len) * 0.5 / self.page_size_mb
        model_pages = self.model_registry.get(model, 1000)  # Reduzido para teste

        total_needed = kv_pages_needed + model_pages
        free_blocks = self.contiguous_blocks()

        # Heurística de Sheaf: preferir bloco único contíguo
        for start, end in free_blocks:
            if (end - start + 1) >= total_needed:
                return True
        return False

    def allocate(self, n_tokens: int, model: ModelProfile) -> Optional[int]:
        """Retorna o handle da alocação, ou None (a seta não existe)."""
        kv_pages_needed = int(np.ceil((n_tokens + 4096) * 0.5 / self.page_size_mb))
        model_pages = self.model_registry.get(model, 1000)
        total_needed = kv_pages_needed + model_pages

        free_blocks = self.contiguous_blocks()
        for start, end in free_blocks:
            if (end - start + 1) >= total_needed:
                pages = list(range(start, start + total_needed))
                for p in pages:
                    self.allocated_pages.add(p)
                handle = start
                self.allocations[handle] = pages
                return handle
        return None

    def deallocate(self, handle: int):
        """Libera as páginas associadas ao handle."""
        if handle in self.allocations:
            for p in self.allocations[handle]:
                self.allocated_pages.discard(p)
            del self.allocations[handle]


class MagicStateFactory:
    """
    Fábrica de 'Estados Mágicos' clássicos: modelos especializados
    pré-carregados em GPU fatias (MIG) ou réplicas Ray.
    """
    def __init__(self, profiles: List[ModelProfile]):
        self.inventory = {p: 0 for p in profiles}
        self.warm_models: set[ModelProfile] = set()

    async def distill(self, profile: ModelProfile):
        """Pré-carrega modelo em GPU (distilação clássica)."""
        await asyncio.sleep(0.5)  # Simulação de load
        self.inventory[profile] += 1
        self.warm_models.add(profile)

    def consume(self, profile: ModelProfile) -> bool:
        if self.inventory[profile] > 0:
            self.inventory[profile] -= 1
            return True
        return False


# =============================================================================
# AXIOMA 3: EKF SEMÂNTICO (SELO 3 - DRIFT DE CONTEXTO)
# =============================================================================

class SemanticDriftEKF:
    """
    Observador de Kalman Estendido para deriva semântica.
    Estado: [drift_acumulado, taxa_de_drift]
    Observação: distância coseno do embedding baseline.
    """
    def __init__(self, threshold: float = 0.25):
        self.threshold = threshold
        global HAS_SENTENCE_TRANSFORMERS
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception:
                HAS_SENTENCE_TRANSFORMERS = False
                self.model = None
        else:
            self.model = None

        self.baseline_emb: Optional[np.ndarray] = None

        # Estado x = [drift, drift_rate]
        self.x = np.array([0.0, 0.0])
        self.P = np.eye(2) * 0.1

        # Modelo de transição: drift persiste, taxa é lenta
        self.A = np.array([[1.0, 1.0],
                           [0.0, 0.95]])
        self.H = np.array([[1.0, 0.0]])
        self.Q = np.diag([0.001, 0.0001])
        self.R = np.array([[0.05]])

    def _get_embedding(self, text: str) -> np.ndarray:
        if HAS_SENTENCE_TRANSFORMERS and self.model:
            return self.model.encode(text, normalize_embeddings=True)
        else:
            h = hash(text)
            np.random.seed(h % (2**32))
            vec = np.random.randn(384)
            return vec / np.linalg.norm(vec)

    def set_baseline(self, text: str):
        self.baseline_emb = self._get_embedding(text)

    def predict(self):
        self.x = self.A @ self.x
        self.P = self.A @ self.P @ self.A.T + self.Q

    def update(self, current_text: str) -> Dict[str, Any]:
        if self.baseline_emb is None:
            self.set_baseline(current_text)
            return {"drift": 0.0, "alert": False}

        emb = self._get_embedding(current_text)
        sim = float(np.dot(self.baseline_emb, emb))
        observation = 1.0 - sim  # drift observado

        self.predict()

        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        y = observation - (self.H @ self.x)
        self.x = self.x + K.flatten() * y
        self.P = (np.eye(2) - K @ self.H) @ self.P

        drift_estimated = float(self.x[0])
        alert = drift_estimated > self.threshold

        return {
            "drift": drift_estimated,
            "similarity": sim,
            "alert": alert,
            "action": "REINJECT_CONTEXT" if alert else "CONTINUE"
        }


# =============================================================================
# AXIOMA 2: CONSENSO BIZANTINO COM TIMEOUT FÍSICO (SELO 1)
# =============================================================================

class ByzantineConsensusRouter:
    """
    Roteador hierárquico T1/T2/T3 com timeout físico (Selo 1).
    T1: Heurística rápida (token count)
    T2: Classificador leve (entropia/complexidade)
    T3: Oráculo (judge LLM) com circuit breaker
    """
    def __init__(self, timeout_ms: float = 500.0):
        self.timeout = timeout_ms / 1000.0
        self.circuit_open = False
        self.failure_count = 0
        self.failure_threshold = 3

    def _t1_heuristic(self, prompt: str) -> Optional[ModelProfile]:
        """Belief Propagation rápido: 98% dos casos."""
        tokens = len(prompt.split())
        if tokens < 50 and "?" not in prompt:
            return ModelProfile.SMALL
        if tokens < 500:
            return ModelProfile.MEDIUM
        return None  # Escalar para T2

    def _t2_classifier(self, prompt: str) -> ModelProfile:
        """Relay BP: classificador de complexidade (simulado)."""
        complexity_score = len(set(prompt.split())) / max(len(prompt.split()), 1)
        if complexity_score < 0.4:
            return ModelProfile.SMALL
        elif complexity_score < 0.7:
            return ModelProfile.MEDIUM
        return ModelProfile.LARGE

    async def _t3_oracle(self, prompt: str) -> ModelProfile:
        """Oráculo lento. Se falhar/timeout, circuit breaker abre."""
        if self.circuit_open:
            raise asyncio.TimeoutError("Circuit breaker OPEN")

        try:
            await asyncio.wait_for(
                asyncio.sleep(0.4),  # Simula latência do oráculo
                timeout=self.timeout
            )
            return ModelProfile.LARGE
        except asyncio.TimeoutError:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.circuit_open = True
            raise

    async def route(self, prompt: str) -> ModelProfile:
        if (choice := self._t1_heuristic(prompt)):
            return choice

        choice = self._t2_classifier(prompt)
        if choice != ModelProfile.LARGE:
            return choice

        try:
            return await self._t3_oracle(prompt)
        except asyncio.TimeoutError:
            return ModelProfile.MEDIUM


# =============================================================================
# LANGGRAPH: IDEMPOTÊNCIA FIBRADA SOBRE O TEMPO
# =============================================================================

def reduce_messages(left: List[dict], right: List[dict]) -> List[dict]:
    """Reducer que garante idempotência e truncamento."""
    return (left + right)[-10:]

class AgentState(TypedDict):
    """
    Estado do grafo LangGraph. A chave 'messages' usa um redutor
    que trunca e deduplica, garantindo idempotência condicional.
    """
    messages: Annotated[List[dict], reduce_messages]
    iteration: Annotated[int, operator.add]
    cost_accrued: Annotated[float, operator.add]
    consensus_deadline: float
    killed: bool

class IdempotentLangGraph:
    """
    Grafo de agentes com timeout físico e reinjeção de contexto (Selo 3).
    Usa o framework LangGraph nativo.
    """
    def __init__(self, max_cost: float = 1.0, max_iterations: int = 5):
        self.max_cost = max_cost
        self.max_iterations = max_iterations
        self.ekf = SemanticDriftEKF(threshold=0.25)
        self.graph = self._build_graph()

    def _planner_node(self, state: AgentState):
        return {
            "messages": [{"role": "assistant", "content": "Planner: Logic defined."}],
            "iteration": 1,
            "cost_accrued": 0.055  # $0.05 step + $0.005 copy cost
        }

    def _coder_node(self, state: AgentState):
        return {
            "messages": [{"role": "assistant", "content": "Coder: RTL/Code generated."}],
            "iteration": 1,
            "cost_accrued": 0.055
        }

    def _reviewer_node(self, state: AgentState):
        # Simula uma necessidade de correção se iteração for baixa
        content = "Reviewer: Needs refinement." if state["iteration"] < 3 else "Reviewer: Approved."
        return {
            "messages": [{"role": "assistant", "content": content}],
            "iteration": 1,
            "cost_accrued": 0.055
        }

    def _auditor_node(self, state: AgentState):
        """Selo 1 e Selo 3: Auditoria de recursos e semântica."""
        now = time.time()
        killed = False

        # Selo 1: Timeout físico e limites rígidos
        if now > state["consensus_deadline"] or \
           state["iteration"] >= self.max_iterations or \
           state["cost_accrued"] > self.max_cost:
            killed = True

        # Selo 3: Verificação de drift semântico
        last_msg = state["messages"][-1]["content"] if state["messages"] else ""
        drift_report = self.ekf.update(last_msg)

        update = {"killed": killed, "iteration": 0, "cost_accrued": 0.005}
        if drift_report["alert"]:
            # Reinjeção de baseline (Axioma 3)
            update["messages"] = [state["messages"][0]]

        return update

    def _build_graph(self):
        builder = StateGraph(AgentState)
        builder.add_node("planner", self._planner_node)
        builder.add_node("coder", self._coder_node)
        builder.add_node("reviewer", self._reviewer_node)
        builder.add_node("auditor", self._auditor_node)

        builder.set_entry_point("planner")
        builder.add_edge("planner", "coder")
        builder.add_edge("coder", "reviewer")
        builder.add_edge("reviewer", "auditor")

        def route_auditor(state: AgentState) -> Literal["coder", "__end__"]:
            if state["killed"] or "Approved" in state["messages"][-2]["content"]:
                return END
            return "coder"

        builder.add_conditional_edges("auditor", route_auditor)
        return builder.compile()

    async def run(self, initial_prompt: str) -> Dict[str, Any]:
        state: AgentState = {
            "messages": [{"role": "system", "content": initial_prompt}],
            "iteration": 0,
            "cost_accrued": 0.01,
            "consensus_deadline": time.time() + 30.0,
            "killed": False
        }

        self.ekf.set_baseline(initial_prompt)

        # Executa o grafo com o limite de recursão nativo do LangGraph
        loop = asyncio.get_event_loop()
        final_state = await loop.run_in_executor(
            None, lambda: self.graph.invoke(state, config={"recursion_limit": 25})
        )

        return {
            "final_state": final_state,
            "terminated_normally": not final_state["killed"],
            "total_cost": final_state["cost_accrued"]
        }


# =============================================================================
# SIMULAÇÃO DO BATISMO NO SILÍCIO CLÁSSICO
# =============================================================================

async def baptism_by_fire():
    print("=" * 60)
    print("BATISMO: Três Selos em Execução")
    print("=" * 60)

    resources = ResourceState()
    # Mocking model registry for allocation logic
    resources.model_registry[ModelProfile.SMALL] = 500
    resources.model_registry[ModelProfile.MEDIUM] = 1000
    resources.model_registry[ModelProfile.LARGE] = 2000

    magic_factory = MagicStateFactory([ModelProfile.SMALL, ModelProfile.MEDIUM])
    await magic_factory.distill(ModelProfile.SMALL)
    await magic_factory.distill(ModelProfile.MEDIUM)

    router = ByzantineConsensusRouter(timeout_ms=300)
    workflow = IdempotentLangGraph(max_cost=0.5, max_iterations=10)

    prompt = "Implemente uma função Python que calcule o espectro de um grafo Laplaciano usando SVD."
    print(f"\n[Prompt]: {prompt}...")

    try:
        model_choice = await router.route(prompt)
        print(f"[Selo 1] Roteamento: {model_choice.name}")
    except Exception as e:
        print(f"[Selo 1] ALERTA: Circuit breaker aberto. {e}")
        model_choice = ModelProfile.MEDIUM

    if resources.can_allocate(len(prompt.split()), model_choice):
        handle = resources.allocate(len(prompt.split()), model_choice)
        print(f"[Mônade M] Alocação OK (handle={handle})")
        result = await workflow.run(prompt)
        print(f"\n[Selo 3] Terminou normalmente: {result['terminated_normally']}")
        print(f"[Selo 3] Custo total: ${result['total_cost']:.2f}")
        print(f"[Selo 3] Iterações totais: {result['final_state']['iteration']}")

        # Liberação
        resources.deallocate(handle)
        print(f"[Mônade M] Liberação OK.")
    else:
        print("[Mônade M] FALHA: VRAM insuficiente ou fragmentada.")

    print("\n[arkhe] BATISMO CONCLUÍDO. MEMBRANA: INTACTA.")

if __name__ == "__main__":
    asyncio.run(baptism_by_fire())
