#!/usr/bin/env python3
# ============================================================
# ARKHE Ω-TEMP v∞.Ω — SUBSTRATO 236: OPENCODE ADVANCED FEATURES
# Auto-Scaling • Prompt RL • Config Federation
# Canonical Seal: e1b8b272bdf863f5eb3f2bf2aec349ffd526ffb1312f2b2d095ab3d5f4c3e2a0
# ============================================================

import hashlib, json, time, random, math
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import deque, defaultdict, Counter

# ============================================================
# MÓDULO 1: AUTO-SCALING DE SESSÕES OPENCODE
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

class OpenCodeAutoScaler:
    """Auto-scaler para sessões OpenCode com consciência Φ_C."""

    CONFIG = {
        "min_replicas": 2,
        "max_replicas": 50,
        "scale_up_threshold": {"pending_prompts": 20, "latency_ms": 2000, "phi_c_min": 0.90},
        "scale_down_threshold": {"utilization_percent": 20, "duration_minutes": 10, "phi_c_max": 0.80},
        "cooldown_seconds": 120,
        "target_utilization": 0.70,
    }

    def __init__(self, phi_bus=None, temporal_chain=None, k8s_client=None, token_economy=None):
        self.phi_bus = phi_bus
        self.temporal = temporal_chain
        self.k8s = k8s_client
        self.token_economy = token_economy
        self._metrics_history: deque = deque(maxlen=300)
        self._last_scaling_decision: Optional[ScalingDecision] = None
        self._current_replicas: int = self.CONFIG["min_replicas"]
        self._scaling_cooldown_until: float = 0
        self._decision_log: List[ScalingDecision] = []

    def collect_metrics(self) -> ScalingMetrics:
        return ScalingMetrics(
            active_sessions=random.randint(5, 40),
            pending_prompts=random.randint(0, 30),
            avg_latency_ms=random.uniform(200, 2500),
            system_phi_c=random.uniform(0.85, 0.999),
            token_usage_rate=random.uniform(0.3, 0.95),
            worker_health_ratio=random.uniform(0.95, 1.0)
        )

    def evaluate_scaling_policy(self, metrics: ScalingMetrics) -> ScalingDecision:
        scale_up_score = 0.0
        if metrics.pending_prompts > self.CONFIG["scale_up_threshold"]["pending_prompts"]:
            scale_up_score += 0.4
        if metrics.avg_latency_ms > self.CONFIG["scale_up_threshold"]["latency_ms"]:
            scale_up_score += 0.3
        if metrics.system_phi_c > self.CONFIG["scale_up_threshold"]["phi_c_min"]:
            scale_up_score += 0.2
        if metrics.worker_health_ratio < 0.90:
            scale_up_score += 0.1

        scale_down_score = 0.0
        utilization = metrics.active_sessions / self.CONFIG["max_replicas"]
        if utilization < self.CONFIG["scale_down_threshold"]["utilization_percent"] / 100:
            scale_down_score += 0.5
        if metrics.system_phi_c < self.CONFIG["scale_down_threshold"]["phi_c_max"]:
            scale_down_score += 0.3
        if metrics.token_usage_rate < 0.3:
            scale_down_score += 0.2

        if scale_up_score > 0.5 and time.time() >= self._scaling_cooldown_until:
            direction = ScaleDirection.UP
            increase_factor = min(1.5, 1.0 + (scale_up_score - 0.5) * 2)
            target = min(self.CONFIG["max_replicas"], int(self._current_replicas * increase_factor))
            reason = f"High demand: pending={metrics.pending_prompts}, latency={metrics.avg_latency_ms:.0f}ms"
            confidence = min(0.99, metrics.system_phi_c * 0.7 + 0.3)
        elif scale_down_score > 0.4 and time.time() >= self._scaling_cooldown_until:
            direction = ScaleDirection.DOWN
            decrease_factor = max(0.7, 1.0 - scale_down_score * 0.6)
            target = max(self.CONFIG["min_replicas"], int(self._current_replicas * decrease_factor))
            reason = f"Low utilization: {utilization*100:.1f}%, phi_c={metrics.system_phi_c:.3f}"
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
            "timestamp": time.time()
        }
        decision.temporal_seal = hashlib.sha3_256(json.dumps(seal_payload, sort_keys=True).encode()).hexdigest()
        return True

    def run_scaling_cycle(self) -> ScalingDecision:
        metrics = self.collect_metrics()
        decision = self.evaluate_scaling_policy(metrics)
        if decision.direction != ScaleDirection.MAINTAIN:
            self.execute_scaling(decision)
        return decision

    def get_scaling_statistics(self) -> Dict:
        if not self._metrics_history:
            return {"evaluations": 0}
        phi_cs = [m.system_phi_c for m in self._metrics_history]
        latencies = [m.avg_latency_ms for m in self._metrics_history]
        scale_ups = sum(1 for d in self._decision_log if d.direction == ScaleDirection.UP)
        scale_downs = sum(1 for d in self._decision_log if d.direction == ScaleDirection.DOWN)
        return {
            "current_replicas": self._current_replicas,
            "min_replicas": self.CONFIG["min_replicas"],
            "max_replicas": self.CONFIG["max_replicas"],
            "avg_phi_c": sum(phi_cs) / len(phi_cs),
            "avg_latency_ms": sum(latencies) / len(latencies),
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
# MÓDULO 2: PROMPT RL OPTIMIZER
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
# MÓDULO 3: CONFIG FEDERATION SERVICE
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

class ConfigFederationService:
    CONFIG = {
        "min_phi_c_for_share": 0.85,
        "max_config_size_kb": 100,
        "allowed_config_keys": ["assistant", "arkhe_metadata", "tools", "hooks", "models"],
        "federation_peers": [],
        "gossip_interval_seconds": 60,
        "conflict_resolution": "phi_c_highest"
    }

    def __init__(self, organization_id: str, hsm_signer=None, temporal_chain=None, phi_bus=None, rbac_service=None):
        self.org_id = organization_id
        self.hsm = hsm_signer
        self.temporal = temporal_chain
        self.phi_bus = phi_bus
        self.rbac = rbac_service
        self._local_configs: Dict[str, FederatedConfig] = {}
        self._received_configs: Dict[str, FederatedConfig] = {}
        self._pending_sync: Set[str] = set()
        self._gossip_running = False
        self._sync_log: List[Dict] = []

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

    def create_federated_config(self, config_content: Dict, visibility: ConfigVisibility, allowed_orgs: Optional[Set[str]] = None) -> FederatedConfig:
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
            "event": "federated_config_created", "config_id": config_id,
            "organization": self.org_id, "visibility": visibility.value,
            "phi_c_score": phi_c_score, "allowed_orgs": list(config.allowed_organizations),
            "pqc_signature_hash": hashlib.sha3_256(pqc_signature.encode()).hexdigest()[:16],
            "timestamp": time.time()
        }
        config.temporal_seal = hashlib.sha3_256(json.dumps(seal_payload, sort_keys=True).encode()).hexdigest()
        self._pending_sync.add(config_id)
        return config

    def request_config(self, config_id: str, requester_org: str) -> Optional[FederatedConfig]:
        if config_id in self._local_configs:
            config = self._local_configs[config_id]
            if self._check_visibility_access(config, requester_org):
                return config
        if config_id in self._received_configs:
            config = self._received_configs[config_id]
            if self._check_visibility_access(config, requester_org):
                return config
        return None

    def _check_visibility_access(self, config: FederatedConfig, requester_org: str) -> bool:
        if config.visibility == ConfigVisibility.PUBLIC:
            return True
        if config.visibility in (ConfigVisibility.ORGANIZATION, ConfigVisibility.TEAM):
            return requester_org == config.organization_id
        if config.visibility == ConfigVisibility.FEDERATED:
            return requester_org in config.allowed_organizations
        return False

    def _verify_pqc_signature(self, config_data: Dict) -> bool:
        pqc_sig = config_data.get("pqc_signature")
        if not pqc_sig:
            return False
        config_id = config_data.get("config_id")
        org_id = config_data.get("organization_id")
        expected_sig = hashlib.sha3_256(f"{config_id}:{org_id}".encode()).hexdigest()
        return pqc_sig == expected_sig

    def receive_federated_config(self, config_data: Dict) -> bool:
        if not self._verify_pqc_signature(config_data):
            return False
        try:
            config = FederatedConfig(
                config_id=config_data["config_id"], config_content=config_data["config_content"],
                created_by=config_data["created_by"], organization_id=config_data["organization_id"],
                visibility=ConfigVisibility(config_data["visibility"]),
                phi_c_score=config_data["phi_c_score"],
                allowed_organizations=set(config_data.get("allowed_organizations", [])),
                version=config_data["version"], parent_config_id=config_data.get("parent_config_id"),
                pqc_signature=config_data["pqc_signature"],
                temporal_seal=config_data.get("temporal_seal"),
                created_at=config_data["created_at"], updated_at=config_data.get("updated_at")
            )
            self._received_configs[config.config_id] = config
            self._sync_log.append({
                "event": "received", "config_id": config.config_id,
                "from_org": config.organization_id, "phi_c": config.phi_c_score,
                "timestamp": time.time()
            })
            return True
        except (KeyError, ValueError):
            return False

    def resolve_config_conflict(self, local_config: FederatedConfig, remote_config: FederatedConfig) -> Optional[FederatedConfig]:
        if self.CONFIG["conflict_resolution"] == "phi_c_highest":
            return local_config if local_config.phi_c_score >= remote_config.phi_c_score else remote_config
        return None

    def get_federation_statistics(self) -> Dict:
        vis_dist = {v.value: sum(1 for c in self._local_configs.values() if c.visibility == v) for v in ConfigVisibility}
        phi_cs = [c.phi_c_score for c in self._local_configs.values()]
        return {
            "organization_id": self.org_id, "local_configs": len(self._local_configs),
            "received_configs": len(self._received_configs), "pending_sync": len(self._pending_sync),
            "peers_count": len(self.CONFIG["federation_peers"]),
            "visibility_distribution": vis_dist,
            "avg_phi_c": sum(phi_cs) / len(phi_cs) if phi_cs else 0,
            "sync_log_entries": len(self._sync_log)
        }

# ============================================================
# DEMO EXECUTION
# ============================================================
if __name__ == "__main__":
    print("ARKHE Ω-TEMP v∞.Ω — Substrato 236: OpenCode Advanced Features")
    print("Canonical Seal: e1b8b272bdf863f5eb3f2bf2aec349ffd526ffb1312f2b2d095ab3d5f4c3e2a0")
    print()

    # Demo AutoScaler
    scaler = OpenCodeAutoScaler()
    for _ in range(3):
        decision = scaler.run_scaling_cycle()
        print(f"[AutoScaler] {decision.direction.value}: {decision.current_replicas}→{decision.target_replicas} | Φ_C={decision.metrics_snapshot.system_phi_c:.3f}")

    # Demo Prompt RL
    optimizer = PromptRLOptimizer()
    optimized, meta = optimizer.optimize_prompt("Explain quantum computing", {"lang": "python"})
    print(f"\n[PromptRL] Optimized in {meta['iterations']} iterations, final Φ_C={meta['final_phi_c']:.3f}")
    print(f"[PromptRL] Actions: {meta['actions_taken']}")

    # Demo Config Federation
    service = ConfigFederationService("org_alpha")
    config = service.create_federated_config(
        {"assistant": {}, "arkhe_metadata": {"phi_c_threshold": 0.92, "version": "1.0"}, "tools": ["code"]},
        ConfigVisibility.FEDERATED, {"org_beta"}
    )
    print(f"\n[Federation] Config {config.config_id} created, Φ_C={config.phi_c_score}, seal={config.temporal_seal[:16]}...")

    # Cross-org access test
    result = service.request_config(config.config_id, "org_beta")
    print(f"[Federation] org_beta access: {'GRANTED' if result else 'DENIED'}")
    result2 = service.request_config(config.config_id, "org_gamma")
    print(f"[Federation] org_gamma access: {'GRANTED' if result2 else 'DENIED'}")