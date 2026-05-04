# chaos_injector.py — Framework para injeção de falhas controlada e reversível

import asyncio
import time
import json
import hashlib
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum, auto
from contextlib import asynccontextmanager

# Mock implementation for environment without kubernetes client
class MockK8s:
    def list_namespaced_pod(self, namespace, label_selector):
        class Item:
            def __init__(self, name):
                self.metadata = type('obj', (object,), {'name': name, 'namespace': 'cathedral', 'resource_version': '1'})
                self.status = type('obj', (object,), {'phase': 'Running'})
        return type('obj', (object,), {'items': [Item('pod-1'), Item('pod-2')]})
    def delete_namespaced_pod(self, name, namespace, grace_period_seconds, propagation_policy):
        return True
    def create_namespaced_custom_object(self, group, version, namespace, plural, body):
        return True
    def delete_namespaced_custom_object(self, group, version, namespace, plural, name):
        return True

class InjectionType(Enum):
    """Tipos de injeção de falha suportados."""
    POD_KILL = auto()
    NETWORK_PARTITION = auto()
    LATENCY_INJECTION = auto()
    CPU_STRESS = auto()
    MEMORY_STRESS = auto()
    DISK_CORRUPTION = auto()
    CONFIG_TAMPER = auto()
    CONSENSUS_TIMEOUT = auto()

@dataclass
class InjectionDefinition:
    """Definição de uma injeção de falha."""
    name: str
    injection_type: InjectionType
    target_selector: Dict[str, str]  # Labels para selecionar alvo
    parameters: Dict[str, Any]  # Parâmetros específicos do tipo
    duration_s: float  # Duração da injeção
    blast_radius: str  # "namespace", "region", "cluster"
    reversible: bool = True
    undo_action: Optional[Callable] = None  # Ação para reverter
    pre_injection_hash: Optional[str] = None  # Hash do estado pré-injeção

@dataclass
class InjectionResult:
    """Resultado de uma injeção de falha."""
    injection_id: str
    definition: InjectionDefinition
    start_time: float
    end_time: float
    success: bool
    pre_state_hash: str
    post_state_hash: str
    reversible: bool
    undo_executed: bool
    observations: List[str] = field(default_factory=list)

class ChaosInjector:
    """
    Framework para injeção de falhas controlada e reversível.
    """

    def __init__(self, k8s_config_path: Optional[str] = None):
        self.k8s_api = MockK8s()
        self.k8s_core = MockK8s()
        self.active_injections: Dict[str, InjectionResult] = {}
        self.injection_history: List[InjectionResult] = []

    @asynccontextmanager
    async def inject_context(
        self,
        definition: InjectionDefinition,
        timeout_s: float = 300
    ):
        """
        Context manager para injeção reversível.
        Garante que a injeção seja revertida ao sair do contexto.
        """
        injection_id = f"{definition.name}_{int(time.time())}"
        pre_state_hash = await self._capture_state_hash(definition.target_selector)

        try:
            # Executa injeção
            result = await self._execute_injection(injection_id, definition, pre_state_hash)
            self.active_injections[injection_id] = result

            yield result

        finally:
            # Reverte injeção se configurado como reversível
            if definition.reversible and definition.undo_action:
                await self._execute_undo(injection_id, definition)
                if injection_id in self.active_injections:
                    self.active_injections[injection_id].undo_executed = True

            # Remove de active e adiciona ao histórico
            if injection_id in self.active_injections:
                self.injection_history.append(self.active_injections.pop(injection_id))

    async def _execute_injection(
        self,
        injection_id: str,
        definition: InjectionDefinition,
        pre_state_hash: str
    ) -> InjectionResult:
        """Executa a injeção de falha."""
        start_time = time.time()
        observations = []

        try:
            if definition.injection_type == InjectionType.POD_KILL:
                await self._inject_pod_kill(definition, observations)
            elif definition.injection_type == InjectionType.NETWORK_PARTITION:
                await self._inject_network_partition(definition, observations)

            # Aguarda duração da injeção
            await asyncio.sleep(min(definition.duration_s, 5.0)) # Capped for simulation

            post_state_hash = await self._capture_state_hash(definition.target_selector)

            return InjectionResult(
                injection_id=injection_id,
                definition=definition,
                start_time=start_time,
                end_time=time.time(),
                success=True,
                pre_state_hash=pre_state_hash,
                post_state_hash=post_state_hash,
                reversible=definition.reversible,
                undo_executed=False,
                observations=observations
            )

        except Exception as e:
            observations.append(f"Erro na injeção: {str(e)}")
            return InjectionResult(
                injection_id=injection_id,
                definition=definition,
                start_time=start_time,
                end_time=time.time(),
                success=False,
                pre_state_hash=pre_state_hash,
                post_state_hash="",
                reversible=definition.reversible,
                undo_executed=False,
                observations=observations
            )

    async def _inject_pod_kill(self, definition: InjectionDefinition, observations: List[str]):
        """Injeta falha: mata pods selecionados."""
        percent_to_kill = definition.parameters.get("percent", 30)
        pods = self.k8s_core.list_namespaced_pod(
            namespace=definition.target_selector.get("namespace", "default"),
            label_selector=",".join(f"{k}={v}" for k, v in definition.target_selector.items() if k != "namespace")
        )

        import random
        count = int(len(pods.items) * percent_to_kill / 100)
        pods_to_kill = random.sample(pods.items, max(1, count))

        for pod in pods_to_kill:
            self.k8s_core.delete_namespaced_pod(
                name=pod.metadata.name,
                namespace=pod.metadata.namespace,
                grace_period_seconds=0,
                propagation_policy="Foreground"
            )
            observations.append(f"Pod morto: {pod.metadata.name}")

    async def _inject_network_partition(self, definition: InjectionDefinition, observations: List[str]):
        """Injeta falha: partição de rede via Chaos Mesh."""
        chaos_spec = {
            "apiVersion": "chaos-mesh.org/v1alpha1",
            "kind": "NetworkChaos",
            "metadata": {
                "name": f"partition-{int(time.time())}",
                "namespace": "cathedral"
            },
            "spec": {
                "action": "partition",
                "mode": "fixed-percent",
                "value": str(definition.parameters.get("percent", 50)),
                "selector": definition.target_selector,
                "duration": f"{int(definition.duration_s)}s"
            }
        }
        self.k8s_api.create_namespaced_custom_object(
            group="chaos-mesh.org", version="v1alpha1", namespace="cathedral", plural="networkchaos", body=chaos_spec
        )
        observations.append(f"NetworkChaos criado: {chaos_spec['metadata']['name']}")

    async def _execute_undo(self, injection_id: str, definition: InjectionDefinition):
        """Executa ação de undo para reverter injeção."""
        if definition.undo_action:
            if asyncio.iscoroutinefunction(definition.undo_action):
                await definition.undo_action(injection_id, definition)
            else:
                definition.undo_action(injection_id, definition)

    async def _capture_state_hash(self, selector: Dict[str, str]) -> str:
        """Captura hash do estado atual dos recursos alvo."""
        state_data = []
        pods = self.k8s_core.list_namespaced_pod(
            namespace=selector.get("namespace", "default"),
            label_selector=",".join(f"{k}={v}" for k, v in selector.items() if k != "namespace")
        )
        for pod in pods.items:
            state_data.append(f"{pod.metadata.name}:{pod.status.phase}:{pod.metadata.resource_version}")
        return hashlib.sha3_256(json.dumps(state_data, sort_keys=True).encode()).hexdigest()[:16]
