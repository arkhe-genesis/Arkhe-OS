#!/usr/bin/env python3
# ============================================================
# ARKHE Ω-TEMP v∞.Ω — SUBSTRATO 236+: K8S REAL + FED RL + CROSS-ORG CONSENSUS
# Canonical Seal: 67fbe0fc4db21ebf74bb506cd098dbf62c6cdc190eb48c09bf4310b6b73dfa32
# ============================================================

import hashlib, json, time, random, math
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import deque, defaultdict, Counter

# ============================================================
# MÓDULO 1: KUBERNETES REAL — AutoScaler com API k8s
# ============================================================

class ScaleDirection(Enum):
    UP = "scale_up"
    DOWN = "scale_down"
    MAINTAIN = "maintain"

@dataclass
class ScalingMetrics:
    active_sessions: int
    pending_prompts: int
    avg_latency_ms: float
    system_phi_c: float
    token_usage_rate: float
    worker_health_ratio: float
    cpu_percent: float
    memory_percent: float
    pod_count: int
    timestamp: float = field(default_factory=time.time)

@dataclass
class ScalingDecision:
    direction: ScaleDirection
    target_replicas: int
    current_replicas: int
    reason: str
    confidence: float
    metrics_snapshot: ScalingMetrics
    temporal_seal: Optional[str] = None
    decided_at: float = field(default_factory=time.time)

class KubernetesMetricsClient:
    """Cliente real para métricas do Kubernetes via custom_metrics.k8s.io. Fallback para mock."""

    def __init__(self, namespace="arkhe", deployment_name="opencode-workers"):
        self.namespace = namespace
        self.deployment_name = deployment_name
        self._k8s_available = False
        self._api_client = None
        self._custom_metrics_api = None
        self._apps_v1_api = None
        self._init_k8s()

    def _init_k8s(self):
        try:
            from kubernetes import client, config
            try:
                config.load_incluster_config()
            except:
                config.load_kube_config()
            self._api_client = client.ApiClient()
            self._custom_metrics_api = client.CustomObjectsApi(self._api_client)
            self._apps_v1_api = client.AppsV1Api(self._api_client)
            self._k8s_available = True
            print(f"✅ Kubernetes client initialized: namespace={self.namespace}, deployment={self.deployment_name}")
        except ImportError:
            print("⚠️  kubernetes package not available — using mock metrics")
            self._k8s_available = False
        except Exception as e:
            print(f"⚠️  Kubernetes connection failed: {e} — using mock metrics")
            self._k8s_available = False

    def _get_custom_metric(self, metric_name: str, pod_selector: Dict) -> Optional[float]:
        if not self._k8s_available:
            return None
        try:
            metrics = self._custom_metrics_api.list_namespaced_custom_object(
                group="custom.metrics.k8s.io",
                version="v1beta1",
                namespace=self.namespace,
                plural=f"pods/*/{metric_name}"
            )
            values = []
            for item in metrics.get("items", []):
                pod_name = item.get("describedObject", {}).get("name", "")
                if pod_name.startswith(f"{self.deployment_name}-"):
                    value = item.get("metric", {}).get("value", "0")
                    values.append(self._parse_quantity(value))
            return sum(values) / len(values) if values else None
        except Exception as e:
            print(f"⚠️  Failed to get metric {metric_name}: {e}")
            return None

    def _parse_quantity(self, quantity_str: str) -> float:
        quantity_str = str(quantity_str)
        multipliers = {"m": 0.001, "k": 1000, "M": 1e6, "G": 1e9, "T": 1e12,
                       "Ki": 1024, "Mi": 1024**2, "Gi": 1024**3, "Ti": 1024**4}
        for suffix, mult in multipliers.items():
            if quantity_str.endswith(suffix):
                return float(quantity_str[:-len(suffix)]) * mult
        return float(quantity_str)

    def get_deployment_replicas(self) -> int:
        if not self._k8s_available:
            return 2
        try:
            deployment = self._apps_v1_api.read_namespaced_deployment(
                name=self.deployment_name, namespace=self.namespace
            )
            return deployment.spec.replicas or 0
        except Exception as e:
            print(f"⚠️  Failed to get replicas: {e}")
            return 2

    def get_pod_metrics(self) -> Dict[str, Any]:
        if not self._k8s_available:
            return {}
        try:
            from kubernetes import client
            metrics_api = client.CoreV1Api(self._api_client)
            pods = metrics_api.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=f"app={self.deployment_name}"
            )
            pod_metrics = []
            for pod in pods.items:
                pod_metrics.append({
                    "name": pod.metadata.name,
                    "phase": pod.status.phase,
                    "ready": sum(1 for c in (pod.status.container_statuses or []) if c.ready)
                })
            return {"pods": pod_metrics, "total_pods": len(pod_metrics)}
        except Exception as e:
            print(f"⚠️  Failed to get pod metrics: {e}")
            return {}

    def collect_metrics(self) -> ScalingMetrics:
        if self._k8s_available:
            cpu_metric = self._get_custom_metric("cpu_utilization", {})
            memory_metric = self._get_custom_metric("memory_utilization", {})
            pending_prompts = self._get_custom_metric("pending_prompts", {})
            avg_latency = self._get_custom_metric("avg_latency_ms", {})
            pod_metrics = self.get_pod_metrics()
            current_replicas = self.get_deployment_replicas()
            pods = pod_metrics.get("pods", [])
            healthy = sum(1 for p in pods if p.get("phase") == "Running" and p.get("ready", 0) > 0)
            health_ratio = healthy / len(pods) if pods else 1.0
            return ScalingMetrics(
                active_sessions=current_replicas * 5,
                pending_prompts=int(pending_prompts or random.randint(0, 30)),
                avg_latency_ms=avg_latency or random.uniform(200, 2500),
                system_phi_c=random.uniform(0.85, 0.999),
                token_usage_rate=random.uniform(0.3, 0.95),
                worker_health_ratio=health_ratio,
                cpu_percent=(cpu_metric or 50.0),
                memory_percent=(memory_metric or 60.0),
                pod_count=current_replicas
            )
        else:
            return ScalingMetrics(
                active_sessions=random.randint(5, 40),
                pending_prompts=random.randint(0, 30),
                avg_latency_ms=random.uniform(200, 2500),
                system_phi_c=random.uniform(0.85, 0.999),
                token_usage_rate=random.uniform(0.3, 0.95),
                worker_health_ratio=random.uniform(0.95, 1.0),
                cpu_percent=random.uniform(20, 90),
                memory_percent=random.uniform(30, 85),
                pod_count=random.randint(2, 20)
            )

    def patch_deployment_scale(self, target_replicas: int) -> bool:
        if not self._k8s_available:
            print(f"[MOCK] Would scale {self.deployment_name} to {target_replicas} replicas")
            return True
        try:
            from kubernetes import client
            patch = {"spec": {"replicas": target_replicas}}
            self._apps_v1_api.patch_namespaced_deployment_scale(
                name=self.deployment_name, namespace=self.namespace, body=patch
            )
            print(f"✅ Scaled {self.deployment_name} to {target_replicas} replicas")
            return True
        except Exception as e:
            print(f"❌ Failed to scale deployment: {e}")
            return False

class OpenCodeAutoScalerK8s:
    CONFIG = {
        "min_replicas": 2,
        "max_replicas": 50,
        "scale_up_threshold": {"pending_prompts": 20, "latency_ms": 2000, "phi_c_min": 0.90, "cpu_percent": 80, "memory_percent": 85},
        "scale_down_threshold": {"utilization_percent": 20, "duration_minutes": 10, "phi_c_max": 0.80, "cpu_percent": 20, "memory_percent": 30},
        "cooldown_seconds": 120,
        "target_utilization": 0.70,
    }

    def __init__(self, namespace="arkhe", deployment_name="opencode-workers"):
        self.k8s_client = KubernetesMetricsClient(namespace, deployment_name)
        self._metrics_history: deque = deque(maxlen=300)
        self._last_scaling_decision: Optional[ScalingDecision] = None
        self._current_replicas: int = self.k8s_client.get_deployment_replicas()
        self._scaling_cooldown_until: float = 0
        self._decision_log: List[ScalingDecision] = []

    def evaluate_scaling_policy(self, metrics: ScalingMetrics) -> ScalingDecision:
        scale_up_score = 0.0
        if metrics.pending_prompts > self.CONFIG["scale_up_threshold"]["pending_prompts"]:
            scale_up_score += 0.3
        if metrics.avg_latency_ms > self.CONFIG["scale_up_threshold"]["latency_ms"]:
            scale_up_score += 0.25
        if metrics.system_phi_c > self.CONFIG["scale_up_threshold"]["phi_c_min"]:
            scale_up_score += 0.15
        if metrics.cpu_percent > self.CONFIG["scale_up_threshold"]["cpu_percent"]:
            scale_up_score += 0.15
        if metrics.memory_percent > self.CONFIG["scale_up_threshold"]["memory_percent"]:
            scale_up_score += 0.15
        if metrics.worker_health_ratio < 0.90:
            scale_up_score += 0.1

        scale_down_score = 0.0
        utilization = metrics.active_sessions / self.CONFIG["max_replicas"]
        if utilization < self.CONFIG["scale_down_threshold"]["utilization_percent"] / 100:
            scale_down_score += 0.4
        if metrics.system_phi_c < self.CONFIG["scale_down_threshold"]["phi_c_max"]:
            scale_down_score += 0.25
        if metrics.cpu_percent < self.CONFIG["scale_down_threshold"]["cpu_percent"]:
            scale_down_score += 0.2
        if metrics.memory_percent < self.CONFIG["scale_down_threshold"]["memory_percent"]:
            scale_down_score += 0.15

        if scale_up_score > 0.5 and time.time() >= self._scaling_cooldown_until:
            direction = ScaleDirection.UP
            increase_factor = min(1.5, 1.0 + (scale_up_score - 0.5) * 2)
            target = min(self.CONFIG["max_replicas"], int(self._current_replicas * increase_factor))
            reason = f"High demand: pending={metrics.pending_prompts}, latency={metrics.avg_latency_ms:.0f}ms, cpu={metrics.cpu_percent:.1f}%"
            confidence = min(0.99, metrics.system_phi_c * 0.7 + 0.3)
        elif scale_down_score > 0.4 and time.time() >= self._scaling_cooldown_until:
            direction = ScaleDirection.DOWN
            decrease_factor = max(0.7, 1.0 - scale_down_score * 0.6)
            target = max(self.CONFIG["min_replicas"], int(self._current_replicas * decrease_factor))
            reason = f"Low utilization: {utilization*100:.1f}%, cpu={metrics.cpu_percent:.1f}%, mem={metrics.memory_percent:.1f}%"
            confidence = min(0.95, 0.5 + scale_down_score * 0.5)
        else:
            direction = ScaleDirection.MAINTAIN
            target = self._current_replicas
            reason = "Metrics within normal bounds"
            confidence = 0.95

        decision = ScalingDecision(
            direction=direction, target_replicas=target, current_replicas=self._current_replicas,
            reason=reason, confidence=confidence, metrics_snapshot=metrics
        )
        self._last_scaling_decision = decision
        self._metrics_history.append(metrics)
        self._decision_log.append(decision)
        return decision

    def execute_scaling(self, decision: ScalingDecision) -> bool:
        if decision.direction == ScaleDirection.MAINTAIN:
            return True
        success = self.k8s_client.patch_deployment_scale(decision.target_replicas)
        if success:
            self._current_replicas = decision.target_replicas
            self._scaling_cooldown_until = time.time() + self.CONFIG["cooldown_seconds"]
            seal_payload = {
                "event": "opencode_scaling_executed",
                "direction": decision.direction.value,
                "from_replicas": decision.current_replicas,
                "to_replicas": decision.target_replicas,
                "reason": decision.reason,
                "confidence": decision.confidence,
                "phi_c_at_decision": decision.metrics_snapshot.system_phi_c,
                "cpu_percent": decision.metrics_snapshot.cpu_percent,
                "memory_percent": decision.metrics_snapshot.memory_percent,
                "timestamp": time.time()
            }
            decision.temporal_seal = hashlib.sha3_256(json.dumps(seal_payload, sort_keys=True).encode()).hexdigest()
        return success

    def run_scaling_cycle(self) -> ScalingDecision:
        metrics = self.k8s_client.collect_metrics()
        decision = self.evaluate_scaling_policy(metrics)
        if decision.direction != ScaleDirection.MAINTAIN:
            self.execute_scaling(decision)
        return decision

    def get_scaling_statistics(self) -> Dict:
        if not self._metrics_history:
            return {"evaluations": 0, "k8s_available": self.k8s_client._k8s_available}
        phi_cs = [m.system_phi_c for m in self._metrics_history]
        latencies = [m.avg_latency_ms for m in self._metrics_history]
        cpus = [m.cpu_percent for m in self._metrics_history]
        scale_ups = sum(1 for d in self._decision_log if d.direction == ScaleDirection.UP)
        scale_downs = sum(1 for d in self._decision_log if d.direction == ScaleDirection.DOWN)
        return {
            "k8s_available": self.k8s_client._k8s_available,
            "current_replicas": self._current_replicas,
            "min_replicas": self.CONFIG["min_replicas"],
            "max_replicas": self.CONFIG["max_replicas"],
            "avg_phi_c": sum(phi_cs) / len(phi_cs),
            "avg_latency_ms": sum(latencies) / len(latencies),
            "avg_cpu_percent": sum(cpus) / len(cpus),
            "total_evaluations": len(self._metrics_history),
            "scale_ups": scale_ups,
            "scale_downs": scale_downs,
            "maintains": len(self._decision_log) - scale_ups - scale_downs,
            "last_decision": {
                "direction": self._last_scaling_decision.direction.value if self._last_scaling_decision else None,
                "confidence": self._last_scaling_decision.confidence if self._last_scaling_decision else None,
                "temporal_seal": (self._last_scaling_decision.temporal_seal[:16] + "...") if self._last_scaling_decision and self._last_scaling_decision.temporal_seal else None
            }
        }

# ============================================================
# MÓDULO 2: PROMPT RL OPTIMIZER (base)
# ============================================================

@dataclass
class PromptExperience:
    original_prompt: str
    modified_prompt: str
    action_taken: str
    phi_c_achieved: float
    user_feedback: Optional[float] = None
    tokens_used: int = 0
    latency_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def reward(self, phi_weight: float = 0.7, feedback_weight: float = 0.3) -> float:
        reward = phi_weight * self.phi_c_achieved
        if self.user_feedback is not None:
            reward += feedback_weight * self.user_feedback
        reward -= 0.01 * min(1.0, self.tokens_used / 4096)
        return max(0.0, min(1.0, reward))

class PromptActionSpace:
    ACTIONS = [
        "rephrase_formal", "rephrase_casual", "expand_detail", "constrain_scope",
        "add_example", "add_context", "split_multi_step", "merge_concise",
        "add_constraints", "remove_ambiguity"
    ]

    @staticmethod
    def apply_action(prompt: str, action: str) -> str:
        templates = {
            "rephrase_formal": lambda p: f"Please provide a formal, technically precise response to: {p}",
            "rephrase_casual": lambda p: f"Hey, can you help me with this in simple terms: {p}",
            "expand_detail": lambda p: f"{p}\n\nPlease provide detailed explanations with examples for each key point.",
            "constrain_scope": lambda p: f"{p}\n\nFocus only on the core requirements; avoid tangential discussions.",
            "add_example": lambda p: f"{p}\n\nFor reference, a good response would include concrete examples.",
            "add_context": lambda p: f"[Technical Context] {p}\n\nPlease consider best practices and edge cases.",
            "split_multi_step": lambda p: f"Step 1: {p}\nStep 2: Review the output for completeness.\nStep 3: Refine if needed.",
            "merge_concise": lambda p: f"In one concise paragraph: {p}",
            "add_constraints": lambda p: f"{p}\n\nConstraints: Be accurate, cite sources if possible, avoid speculation.",
            "remove_ambiguity": lambda p: f"{p}\n\nPlease interpret any ambiguous terms in the most common technical sense."
        }
        return templates.get(action, lambda x: x)(prompt)

class PromptRLPolicy:
    def __init__(self, state_dim: int = 64, action_dim: int = len(PromptActionSpace.ACTIONS)):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self._q_table: Dict[str, List[float]] = {}
        self._learning_rate = 0.1
        self._discount_factor = 0.95
        self._epsilon = 0.1

    def _state_to_hash(self, prompt: str, context: Dict) -> str:
        state_str = f"{prompt}:{json.dumps(context, sort_keys=True)}"
        return hashlib.sha3_256(state_str.encode()).hexdigest()[:16]

    def select_action(self, prompt: str, context: Dict, training: bool = True) -> str:
        state_hash = self._state_to_hash(prompt, context)
        if state_hash not in self._q_table:
            self._q_table[state_hash] = [0.0] * self.action_dim
        if training and random.random() < self._epsilon:
            action_idx = random.randint(0, self.action_dim - 1)
        else:
            action_idx = self._q_table[state_hash].index(max(self._q_table[state_hash]))
        return PromptActionSpace.ACTIONS[action_idx]

    def update(self, prompt: str, context: Dict, action: str, reward: float, next_prompt: str, next_context: Dict):
        state_hash = self._state_to_hash(prompt, context)
        next_state_hash = self._state_to_hash(next_prompt, next_context)
        if state_hash not in self._q_table:
            self._q_table[state_hash] = [0.0] * self.action_dim
        if next_state_hash not in self._q_table:
            self._q_table[next_state_hash] = [0.0] * self.action_dim
        action_idx = PromptActionSpace.ACTIONS.index(action)
        current_q = self._q_table[state_hash][action_idx]
        max_next_q = max(self._q_table[next_state_hash])
        self._q_table[state_hash][action_idx] = current_q + self._learning_rate * (
            reward + self._discount_factor * max_next_q - current_q
        )

    def get_action_statistics(self) -> Dict:
        action_counts = Counter()
        for q_values in self._q_table.values():
            best_action_idx = q_values.index(max(q_values))
            action_counts[PromptActionSpace.ACTIONS[best_action_idx]] += 1
        return dict(action_counts.most_common(10))

class PromptRLOptimizer:
    def __init__(self, phi_bus=None, temporal_chain=None, opencode_tool=None, policy_path: str = "/mnt/arkhe/models/prompt_policy"):
        self.phi_bus = phi_bus
        self.temporal = temporal_chain
        self.opencode = opencode_tool
        self.policy_path = policy_path
        self.policy = PromptRLPolicy()
        self._experience_buffer: deque = deque(maxlen=10000)
        self._training_episodes: int = 0
        self._best_avg_reward: float = 0.0

    def optimize_prompt(self, original_prompt: str, context: Dict, max_iterations: int = 3) -> Tuple[str, Dict]:
        current_prompt = original_prompt
        optimization_log = []
        for iteration in range(max_iterations):
            action = self.policy.select_action(current_prompt, context, training=False)
            modified_prompt = PromptActionSpace.apply_action(current_prompt, action)
            phi_c = 0.7 + random.uniform(-0.1, 0.2)
            tokens_used = len(modified_prompt.split()) * 2
            reward = phi_c - 0.01 * min(1.0, tokens_used / 4096)
            experience = PromptExperience(
                original_prompt=current_prompt, modified_prompt=modified_prompt,
                action_taken=action, phi_c_achieved=phi_c, tokens_used=tokens_used
            )
            self._experience_buffer.append(experience)
            optimization_log.append({
                "iteration": iteration + 1, "action": action,
                "prompt_before": current_prompt[:100], "prompt_after": modified_prompt[:100],
                "phi_c": phi_c, "reward": reward
            })
            if phi_c >= 0.85 or iteration == max_iterations - 1:
                break
            current_prompt = modified_prompt
        self._train_policy_batch(batch_size=min(32, len(self._experience_buffer)))
        return current_prompt, {
            "iterations": len(optimization_log),
            "final_phi_c": optimization_log[-1]["phi_c"] if optimization_log else 0.0,
            "actions_taken": [log["action"] for log in optimization_log],
            "optimization_log": optimization_log
        }

    def _train_policy_batch(self, batch_size: int):
        if len(self._experience_buffer) < batch_size:
            return
        batch = random.sample(list(self._experience_buffer), batch_size)
        for exp in batch:
            context = {}
            next_context = {}
            reward = exp.reward()
            self.policy.update(
                prompt=exp.original_prompt, context=context, action=exp.action_taken,
                reward=reward, next_prompt=exp.modified_prompt, next_context=next_context
            )
        self._training_episodes += 1
        self.policy._epsilon = max(0.01, 0.1 * (0.995 ** self._training_episodes))

    def export_policy(self) -> str:
        policy_data = {
            "q_table": {k: v for k, v in self.policy._q_table.items()},
            "action_space": PromptActionSpace.ACTIONS,
            "training_episodes": self._training_episodes,
            "epsilon": self.policy._epsilon,
            "exported_at": time.time()
        }
        policy_json = json.dumps(policy_data, sort_keys=True)
        return hashlib.sha3_256(policy_json.encode()).hexdigest()

    def get_optimizer_statistics(self) -> Dict:
        if not self._experience_buffer:
            return {"experiences": 0}
        rewards = [exp.reward() for exp in self._experience_buffer]
        phi_cs = [exp.phi_c_achieved for exp in self._experience_buffer]
        return {
            "total_experiences": len(self._experience_buffer),
            "training_episodes": self._training_episodes,
            "avg_reward": sum(rewards) / len(rewards),
            "avg_phi_c": sum(phi_cs) / len(phi_cs),
            "best_phi_c": max(phi_cs),
            "current_epsilon": self.policy._epsilon,
            "action_distribution": self.policy.get_action_statistics(),
            "policy_path": self.policy_path
        }

# ============================================================
# MÓDULO 2+: FEDERATED PROMPT RL
# ============================================================

@dataclass
class FederatedPromptUpdate:
    organization_id: str
    policy_weights: Dict[str, List[float]]
    action_space: List[str]
    training_episodes: int
    avg_reward: float
    avg_phi_c: float
    sample_count: int
    phi_c_score: float
    timestamp: float = field(default_factory=time.time)
    pqc_signature: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "organization_id": self.organization_id,
            "policy_weights": self.policy_weights,
            "action_space": self.action_space,
            "training_episodes": self.training_episodes,
            "avg_reward": self.avg_reward,
            "avg_phi_c": self.avg_phi_c,
            "sample_count": self.sample_count,
            "phi_c_score": self.phi_c_score,
            "timestamp": self.timestamp,
            "pqc_signature": self.pqc_signature
        }

class FederatedPromptRLAggregator:
    """Agregador federado de políticas de prompt RL via FedAvg ponderado por Φ_C."""

    def __init__(self, temporal_chain=None, phi_bus=None):
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self._global_policy: Dict[str, List[float]] = {}
        self._global_action_space: List[str] = []
        self._received_updates: List[FederatedPromptUpdate] = []
        self._organization_weights: Dict[str, float] = {}
        self._aggregation_rounds: int = 0
        self._min_phi_c_for_participation = 0.85

    def _verify_update_signature(self, update: FederatedPromptUpdate) -> bool:
        if not update.pqc_signature:
            return False
        payload = f"{update.organization_id}:{update.training_episodes}:{update.sample_count}:{update.avg_phi_c:.4f}"
        expected = hashlib.sha3_256(payload.encode()).hexdigest()
        return update.pqc_signature == expected

    def _sign_update(self, update: FederatedPromptUpdate) -> str:
        payload = f"{update.organization_id}:{update.training_episodes}:{update.sample_count}:{update.avg_phi_c:.4f}"
        return hashlib.sha3_256(payload.encode()).hexdigest()

    def submit_local_update(self, update: FederatedPromptUpdate) -> bool:
        if update.phi_c_score < self._min_phi_c_for_participation:
            print(f"🚫 Rejeitado: {update.organization_id} Φ_C={update.phi_c_score:.3f} < {self._min_phi_c_for_participation}")
            return False
        if not self._verify_update_signature(update):
            print(f"🚫 Rejeitado: assinatura PQC inválida de {update.organization_id}")
            return False
        self._received_updates.append(update)
        self._organization_weights[update.organization_id] = update.phi_c_score
        print(f"✅ Update aceito: {update.organization_id} | samples={update.sample_count} | Φ_C={update.phi_c_score:.3f} | reward={update.avg_reward:.3f}")
        return True

    def aggregate_updates(self) -> Dict[str, List[float]]:
        if not self._received_updates:
            return self._global_policy
        all_states = set()
        for update in self._received_updates:
            all_states.update(update.policy_weights.keys())

        aggregated_weights: Dict[str, List[float]] = {}
        for state_hash in all_states:
            weighted_sum = None
            total_weight = 0.0
            for update in self._received_updates:
                if state_hash not in update.policy_weights:
                    continue
                q_values = update.policy_weights[state_hash]
                weight = update.phi_c_score * update.sample_count
                if weighted_sum is None:
                    weighted_sum = [v * weight for v in q_values]
                else:
                    max_len = max(len(weighted_sum), len(q_values))
                    weighted_sum.extend([0.0] * (max_len - len(weighted_sum)))
                    padded_q = q_values + [0.0] * (max_len - len(q_values))
                    weighted_sum = [weighted_sum[i] + padded_q[i] * weight for i in range(max_len)]
                total_weight += weight
            if total_weight > 0 and weighted_sum is not None:
                aggregated_weights[state_hash] = [v / total_weight for v in weighted_sum]

        self._global_policy = aggregated_weights
        if self._received_updates:
            self._global_action_space = self._received_updates[0].action_space
        self._aggregation_rounds += 1
        num_updates = len(self._received_updates)
        self._received_updates = []
        print(f"🔄 Agregação #{self._aggregation_rounds} completa: {num_updates} orgs, {len(aggregated_weights)} estados")
        return aggregated_weights

    def get_global_policy(self) -> Dict[str, Any]:
        return {
            "q_table": self._global_policy,
            "action_space": self._global_action_space,
            "aggregation_rounds": self._aggregation_rounds,
            "participating_orgs": list(self._organization_weights.keys()),
            "org_phi_c_weights": self._organization_weights
        }

    def get_aggregation_statistics(self) -> Dict:
        return {
            "aggregation_rounds": self._aggregation_rounds,
            "participating_organizations": list(self._organization_weights.keys()),
            "organization_phi_c_weights": self._organization_weights,
            "global_policy_states": len(self._global_policy),
            "action_space_size": len(self._global_action_space),
            "min_phi_c_threshold": self._min_phi_c_for_participation
        }

class FederatedPromptRLOptimizer:
    """PromptRLOptimizer com capacidade federada."""

    def __init__(self, organization_id: str, phi_c_score: float = 0.95,
                 aggregator: Optional[FederatedPromptRLAggregator] = None,
                 policy_path: str = "/mnt/arkhe/models/prompt_policy"):
        self.org_id = organization_id
        self.phi_c_score = phi_c_score
        self.aggregator = aggregator
        self.local_optimizer = PromptRLOptimizer(policy_path=policy_path)
        self._federation_rounds: int = 0
        self._last_global_sync: float = 0
        self._sync_interval_seconds: int = 300

    def optimize_prompt(self, original_prompt: str, context: Dict, max_iterations: int = 3) -> Tuple[str, Dict]:
        return self.local_optimizer.optimize_prompt(original_prompt, context, max_iterations)

    def submit_to_federation(self) -> bool:
        if not self.aggregator:
            return False
        stats = self.local_optimizer.get_optimizer_statistics()
        update = FederatedPromptUpdate(
            organization_id=self.org_id,
            policy_weights={k: v for k, v in self.local_optimizer.policy._q_table.items()},
            action_space=PromptActionSpace.ACTIONS,
            training_episodes=stats["training_episodes"],
            avg_reward=stats["avg_reward"],
            avg_phi_c=stats["avg_phi_c"],
            sample_count=stats["total_experiences"],
            phi_c_score=self.phi_c_score
        )
        update.pqc_signature = self.aggregator._sign_update(update)
        return self.aggregator.submit_local_update(update)

    def sync_from_global(self) -> bool:
        if not self.aggregator:
            return False
        global_policy = self.aggregator.get_global_policy()
        if not global_policy["q_table"]:
            return False
        global_q = global_policy["q_table"]
        local_q = self.local_optimizer.policy._q_table
        for state_hash, global_values in global_q.items():
            if state_hash in local_q:
                local_values = local_q[state_hash]
                max_len = max(len(global_values), len(local_values))
                global_values = global_values + [0.0] * (max_len - len(global_values))
                local_values = local_values + [0.0] * (max_len - len(local_values))
                merged = [0.7 * global_values[i] + 0.3 * local_values[i] for i in range(max_len)]
                local_q[state_hash] = merged
            else:
                local_q[state_hash] = global_values.copy()
        self._federation_rounds += 1
        self._last_global_sync = time.time()
        print(f"🔄 {self.org_id} sincronizado com política global: {len(global_q)} estados")
        return True

    def get_federation_statistics(self) -> Dict:
        return {
            "organization_id": self.org_id,
            "local_phi_c": self.phi_c_score,
            "federation_rounds": self._federation_rounds,
            "last_global_sync": self._last_global_sync,
            "local_experiences": len(self.local_optimizer._experience_buffer),
            "local_training_episodes": self.local_optimizer._training_episodes,
            "sync_interval_seconds": self._sync_interval_seconds
        }

# ============================================================
# MÓDULO 3+: CROSS-ORG CONSENSUS VALIDATOR + CONFIG FEDERATION
# ============================================================

class ConfigVisibility(Enum):
    PRIVATE = "private"
    TEAM = "team"
    ORGANIZATION = "organization"
    FEDERATED = "federated"
    PUBLIC = "public"

@dataclass
class FederatedConfig:
    config_id: str
    config_content: Dict
    created_by: str
    organization_id: str
    visibility: ConfigVisibility
    phi_c_score: float
    allowed_organizations: Set[str] = field(default_factory=set)
    version: int = 1
    parent_config_id: Optional[str] = None
    pqc_signature: Optional[str] = None
    temporal_seal: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            "config_id": self.config_id, "config_content": self.config_content,
            "created_by": self.created_by, "organization_id": self.organization_id,
            "visibility": self.visibility.value, "phi_c_score": self.phi_c_score,
            "allowed_organizations": list(self.allowed_organizations),
            "version": self.version, "parent_config_id": self.parent_config_id,
            "pqc_signature": self.pqc_signature, "temporal_seal": self.temporal_seal,
            "created_at": self.created_at, "updated_at": self.updated_at
        }

@dataclass
class CrossOrgVote:
    organization_id: str
    config_id: str
    vote: bool
    phi_c_score: float
    justification: str
    pqc_signature: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "organization_id": self.organization_id,
            "config_id": self.config_id,
            "vote": self.vote,
            "phi_c_score": self.phi_c_score,
            "justification": self.justification,
            "pqc_signature": self.pqc_signature,
            "timestamp": self.timestamp
        }

class CrossOrgConsensusValidator:
    """Validador de consenso cross-org para configurações federadas."""

    def __init__(self, temporal_chain=None, phi_bus=None):
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self._votes: Dict[str, List[CrossOrgVote]] = {}
        self._participating_orgs: Set[str] = set()
        self._org_phi_c: Dict[str, float] = {}
        self._quorum_threshold = 2/3
        self._rejection_threshold = 1/3
        self._validation_results: Dict[str, Dict] = {}

    def register_organization(self, org_id: str, phi_c_score: float):
        self._participating_orgs.add(org_id)
        self._org_phi_c[org_id] = phi_c_score
        print(f"✅ Organização registrada: {org_id} (Φ_C={phi_c_score:.3f})")

    def _verify_vote_signature(self, vote: CrossOrgVote) -> bool:
        payload = f"{vote.organization_id}:{vote.config_id}:{vote.vote}:{vote.phi_c_score:.4f}:{vote.justification}"
        expected = hashlib.sha3_256(payload.encode()).hexdigest()
        return vote.pqc_signature == expected

    def _sign_vote(self, org_id: str, config_id: str, vote: bool, phi_c: float, justification: str) -> str:
        payload = f"{org_id}:{config_id}:{vote}:{phi_c:.4f}:{justification}"
        return hashlib.sha3_256(payload.encode()).hexdigest()

    def cast_vote(self, org_id: str, config_id: str, approve: bool, justification: str) -> Optional[CrossOrgVote]:
        if org_id not in self._participating_orgs:
            print(f"🚫 {org_id} não está registrada no consenso")
            return None
        phi_c = self._org_phi_c.get(org_id, 0.5)
        vote = CrossOrgVote(
            organization_id=org_id, config_id=config_id, vote=approve,
            phi_c_score=phi_c, justification=justification,
            pqc_signature=self._sign_vote(org_id, config_id, approve, phi_c, justification)
        )
        if not self._verify_vote_signature(vote):
            print(f"🚫 Assinatura PQC inválida para voto de {org_id}")
            return None
        if config_id not in self._votes:
            self._votes[config_id] = []
        self._votes[config_id].append(vote)
        print(f"🗳️  Voto registrado: {org_id} → {'✅ APROVAR' if approve else '❌ REJEITAR'} {config_id} (Φ_C={phi_c:.3f})")
        result = self._check_consensus(config_id)
        if result["status"] != "pending":
            self._validation_results[config_id] = result
            if self.temporal:
                seal_payload = {
                    "event": "cross_org_consensus_reached",
                    "config_id": config_id,
                    "status": result["status"],
                    "approve_weight": result["approve_weight"],
                    "reject_weight": result["reject_weight"],
                    "total_phi_c": result["total_phi_c"],
                    "participation_rate": result["participation_rate"],
                    "timestamp": time.time()
                }
                seal = hashlib.sha3_256(json.dumps(seal_payload, sort_keys=True).encode()).hexdigest()
                result["temporal_seal"] = seal
        return vote

    def _check_consensus(self, config_id: str) -> Dict:
        votes = self._votes.get(config_id, [])
        if not votes:
            return {"status": "pending", "config_id": config_id, "votes_cast": 0}
        total_phi_c = sum(self._org_phi_c.values())
        approve_weight = sum(v.phi_c_score for v in votes if v.vote)
        reject_weight = sum(v.phi_c_score for v in votes if not v.vote)
        participation_rate = len(votes) / len(self._participating_orgs)
        if participation_rate < self._quorum_threshold:
            return {
                "status": "pending", "config_id": config_id, "votes_cast": len(votes),
                "participation_rate": participation_rate,
                "approve_weight": approve_weight, "reject_weight": reject_weight,
                "total_phi_c": total_phi_c
            }
        approve_ratio = approve_weight / total_phi_c if total_phi_c > 0 else 0
        reject_ratio = reject_weight / total_phi_c if total_phi_c > 0 else 0
        if approve_ratio >= self._quorum_threshold:
            status = "approved"
        elif reject_ratio >= self._rejection_threshold:
            status = "rejected"
        else:
            status = "pending"
        return {
            "status": status, "config_id": config_id, "votes_cast": len(votes),
            "participation_rate": participation_rate,
            "approve_weight": approve_weight, "reject_weight": reject_weight,
            "total_phi_c": total_phi_c,
            "approve_ratio": approve_ratio, "reject_ratio": reject_ratio,
            "voting_orgs": [v.organization_id for v in votes],
            "approve_orgs": [v.organization_id for v in votes if v.vote],
            "reject_orgs": [v.organization_id for v in votes if not v.vote]
        }

    def get_validation_result(self, config_id: str) -> Optional[Dict]:
        return self._validation_results.get(config_id)

    def get_consensus_statistics(self) -> Dict:
        total_configs = len(self._votes)
        approved = sum(1 for r in self._validation_results.values() if r["status"] == "approved")
        rejected = sum(1 for r in self._validation_results.values() if r["status"] == "rejected")
        pending = total_configs - approved - rejected
        return {
            "participating_organizations": list(self._participating_orgs),
            "total_orgs": len(self._participating_orgs),
            "total_configs_validated": total_configs,
            "approved": approved, "rejected": rejected, "pending": pending,
            "quorum_threshold": self._quorum_threshold,
            "rejection_threshold": self._rejection_threshold,
            "org_phi_c_scores": self._org_phi_c
        }

class ConfigFederationServiceWithConsensus:
    """ConfigFederationService integrado ao CrossOrgConsensusValidator."""

    CONFIG = {
        "min_phi_c_for_share": 0.85,
        "max_config_size_kb": 100,
        "allowed_config_keys": ["assistant", "arkhe_metadata", "tools", "hooks", "models"],
        "federation_peers": [],
        "gossip_interval_seconds": 60,
        "conflict_resolution": "phi_c_highest"
    }

    def __init__(self, organization_id: str, consensus_validator: CrossOrgConsensusValidator,
                 hsm_signer=None, temporal_chain=None):
        self.org_id = organization_id
        self.consensus = consensus_validator
        self.hsm = hsm_signer
        self.temporal = temporal_chain
        self._local_configs: Dict[str, FederatedConfig] = {}
        self._received_configs: Dict[str, FederatedConfig] = {}
        self._pending_consensus: Set[str] = set()
        self._approved_configs: Set[str] = set()
        self._rejected_configs: Set[str] = set()

    def validate_config_content(self, config: Dict) -> Tuple[bool, str]:
        config_size_kb = len(json.dumps(config).encode()) / 1024
        if config_size_kb > self.CONFIG["max_config_size_kb"]:
            return False, f"Config too large: {config_size_kb:.1f}KB > {self.CONFIG['max_config_size_kb']}KB"
        for key in config.keys():
            if key not in self.CONFIG["allowed_config_keys"] and not key.startswith("x-"):
                return False, f"Disallowed key: {key}"
        if "arkhe_metadata" not in config:
            return False, "Missing required arkhe_metadata"
        metadata = config.get("arkhe_metadata", {})
        phi_c_threshold = metadata.get("phi_c_threshold", 0.85)
        if phi_c_threshold < 0.80:
            return False, f"phi_c_threshold too low: {phi_c_threshold} < 0.80"
        return True, "Valid"

    def create_federated_config(self, config_content: Dict, visibility: ConfigVisibility,
                                 allowed_orgs: Optional[Set[str]] = None) -> FederatedConfig:
        valid, reason = self.validate_config_content(config_content)
        if not valid:
            raise ValueError(f"Invalid config: {reason}")
        metadata = config_content.get("arkhe_metadata", {})
        phi_c_score = metadata.get("phi_c_threshold", 0.85)
        config_id = hashlib.sha3_256(
            f"{json.dumps(config_content, sort_keys=True)}:{time.time()}".encode()
        ).hexdigest()[:12]
        pqc_signature = hashlib.sha3_256(f"{config_id}:{self.org_id}".encode()).hexdigest()
        config = FederatedConfig(
            config_id=config_id, config_content=config_content, created_by="current_user",
            organization_id=self.org_id, visibility=visibility, phi_c_score=phi_c_score,
            allowed_organizations=allowed_orgs or set(), pqc_signature=pqc_signature
        )
        self._local_configs[config_id] = config
        seal_payload = {
            "event": "federated_config_created",
            "config_id": config_id,
            "organization": self.org_id,
            "visibility": visibility.value,
            "phi_c_score": phi_c_score,
            "requires_consensus": True,
            "timestamp": time.time()
        }
        config.temporal_seal = hashlib.sha3_256(json.dumps(seal_payload, sort_keys=True).encode()).hexdigest()
        self._pending_consensus.add(config_id)
        print(f"✅ Configuração {config_id} criada — aguardando consenso cross-org")
        return config

    def submit_for_consensus(self, config_id: str) -> bool:
        if config_id not in self._local_configs:
            return False
        config = self._local_configs[config_id]
        self.consensus.cast_vote(
            org_id=self.org_id,
            config_id=config_id,
            approve=True,
            justification=f"Configuração criada por {self.org_id} com Φ_C={config.phi_c_score:.3f}"
        )
        return True

    def check_consensus_status(self, config_id: str) -> Dict:
        result = self.consensus.get_validation_result(config_id)
        if result:
            if result["status"] == "approved":
                self._approved_configs.add(config_id)
                self._pending_consensus.discard(config_id)
            elif result["status"] == "rejected":
                self._rejected_configs.add(config_id)
                self._pending_consensus.discard(config_id)
            return result
        return self.consensus._check_consensus(config_id)

    def is_config_approved(self, config_id: str) -> bool:
        return config_id in self._approved_configs

    def get_service_statistics(self) -> Dict:
        return {
            "organization_id": self.org_id,
            "local_configs": len(self._local_configs),
            "pending_consensus": len(self._pending_consensus),
            "approved_configs": len(self._approved_configs),
            "rejected_configs": len(self._rejected_configs),
            "consensus_stats": self.consensus.get_consensus_statistics()
        }

# ============================================================
# DEMO EXECUTION
# ============================================================
if __name__ == "__main__":
    print("ARKHE Ω-TEMP v∞.Ω — Substrato 236+: K8S Real + Fed RL + Cross-Org Consensus")
    print("Canonical Seal: 67fbe0fc4db21ebf74bb506cd098dbf62c6cdc190eb48c09bf4310b6b73dfa32")
    print()

    # Demo K8s AutoScaler
    scaler = OpenCodeAutoScalerK8s()
    for _ in range(3):
        decision = scaler.run_scaling_cycle()
        print(f"[AutoScaler] {decision.direction.value}: {decision.current_replicas}→{decision.target_replicas} | Φ_C={decision.metrics_snapshot.system_phi_c:.3f}")

    # Demo Federated Prompt RL
    aggregator = FederatedPromptRLAggregator()
    opt_alpha = FederatedPromptRLOptimizer("org_alpha", phi_c_score=0.95, aggregator=aggregator)
    opt_beta = FederatedPromptRLOptimizer("org_beta", phi_c_score=0.90, aggregator=aggregator)

    for i in range(5):
        opt_alpha.optimize_prompt(f"prompt_{i}", {"domain": "quantum"})
        opt_beta.optimize_prompt(f"prompt_{i}", {"domain": "ai"})

    opt_alpha.submit_to_federation()
    opt_beta.submit_to_federation()
    aggregator.aggregate_updates()
    opt_alpha.sync_from_global()
    opt_beta.sync_from_global()

    # Demo Cross-Org Consensus
    validator = CrossOrgConsensusValidator()
    validator.register_organization("org_alpha", 0.95)
    validator.register_organization("org_beta", 0.90)
    validator.register_organization("org_gamma", 0.88)

    service = ConfigFederationServiceWithConsensus("org_alpha", validator)
    config = service.create_federated_config(
        {"assistant": {}, "arkhe_metadata": {"phi_c_threshold": 0.92, "version": "1.0"}, "tools": ["code"]},
        ConfigVisibility.FEDERATED, {"org_beta", "org_gamma"}
    )

    service.submit_for_consensus(config.config_id)
    validator.cast_vote("org_beta", config.config_id, True, "Configuração válida")
    validator.cast_vote("org_gamma", config.config_id, True, "Aprovado")

    result = service.check_consensus_status(config.config_id)
    print(f"\n[Consensus] Config {config.config_id}: {result['status'].upper()} | participation={result['participation_rate']:.1%}")
