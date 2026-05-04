import time
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import deque, defaultdict
import copy
import heapq

# --- STUBS FOR MISSING BASE CLASSES ---
class CausalGraph:
    def counterfactual_query(self, xi, action_list, check_fn):
        return {'risk_scores': {a: 0.1 for a in action_list}}

class AsyncCombinatorialAuction:
    def submit_bid(self, bid, from_zone):
        pass

@dataclass
class ResourceBid:
    agent_id: str
    resource_id: str
    private_value: float
    constraints: Dict
    timestamp: float

class AsyncMARLAgent(nn.Module):
    def __init__(self, state_dim=4, action_dim=4):
        super().__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.zone_id = "zone_0"
        self.curvature_aware = True
        self.actor = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim),
            nn.Softmax(dim=-1)
        )
        self.critic = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1)
        )
    def compute_loss(self, batch):
        return torch.tensor(0.1, requires_grad=True), torch.tensor(0.1, requires_grad=True)

class CatedralManifoldConfirmed:
    def scalar_curvature(self, state, zone):
        return torch.tensor([10.0])
    def distance(self, state, zone):
        return torch.tensor([0.07])
    def denormalize(self, state):
        return state

@dataclass
class MissionGoal:
    id: str
    description: str
    priority: float
    constraints: Dict[str, float]

@dataclass
class DecomposedTask:
    id: str
    assigned_zone: str
    resource_budget: Dict[str, float]

class HierarchicalMissionDecomposer:
    def decompose(self, goal, zones):
        return []

class HierarchicalAsyncMARLLoop:
    def __init__(self):
        self.decomposer = HierarchicalMissionDecomposer()
    def execute_mission(self, high_level_goal, available_zones, max_steps):
        return {'success': True, 'avg_reward': 1.0}

# ============================================================================
# ARKHE OS: MÓDULO DE CONSCIÊNCIA METACOGNITIVA
# ============================================================================

class MetacognitiveMonitor:
    """
    Implementa a consciência metacognitiva para o ARKHE OS.
    Avalia limites de segurança, confiança na missão e necessidade de recursos.
    """
    def __init__(self, safety_threshold=0.15, confidence_min=0.7):
        self.safety_threshold = safety_threshold
        self.confidence_min = confidence_min
        self.internal_logs = []

    def evaluate_operational_status(self,
                                  current_xi: torch.Tensor,
                                  planned_action: int,
                                  causal_model: Any) -> Dict:
        """
        Realiza uma auto-avaliação antes da execução da tarefa.
        """
        prediction = causal_model.counterfactual_query(
            current_xi,
            [planned_action],
            self._check_mercy_gap_violation
        )

        risk_score = prediction['risk_scores'][planned_action]

        needs_adaptation = risk_score > self.safety_threshold
        status = "OPTIMAL" if not needs_adaptation else "CAUTION"

        return {
            "status": status,
            "risk": risk_score,
            "can_proceed": risk_score < 0.4, # Limite de parada crítica
            "trigger_meta_learning": needs_adaptation
        }

    def _check_mercy_gap_violation(self, xi_state: torch.Tensor) -> bool:
        """Verifica se o estado viola a distância de segurança (Mercy Gap)."""
        dist = torch.norm(xi_state).item()
        return not (0.04 <= dist <= 0.10)

    def request_resource_boost(self, agent_id: str, auction_system: Any):
        """Caso o risco seja alto, negocia mais poder de processamento/energia."""
        print(f"Metacognition: Agente {agent_id} solicitando recursos adicionais...")
        bid = ResourceBid(
            agent_id=agent_id,
            resource_id="compute_power",
            private_value=0.85, # Valor alto devido à necessidade de segurança
            constraints={"mission_priority": 0.9},
            timestamp=time.time()
        )
        auction_system.submit_bid(bid, from_zone="Current_Zone")

def run_meta_aware_step(agent, xi, action, causal_engine, auction):
    monitor = MetacognitiveMonitor()

    assessment = monitor.evaluate_operational_status(xi, action, causal_engine)

    if assessment["trigger_meta_learning"]:
        print("⚠️ Alerta Metacognitivo: Risco detectado. Iniciando adaptação rápida.")
        # Aqui chamaria o RiemannianMetaLearner

    if not assessment["can_proceed"]:
        print("🛑 Parada Crítica: Ação bloqueada por risco contrafactual.")
        monitor.request_resource_boost(getattr(agent, 'id', 'unknown'), auction)
        return None

    return action


# ============================================================================
# ARKHE OS v∞.Ω.∇+++.147 — META-LEARNING (MAML-RIEMANNIAN)
# ============================================================================

@dataclass
class MetaTask:
    task_id: str
    support_set: List[Dict]
    query_set: List[Dict]
    zone: str
    curvature_profile: torch.Tensor

class RiemannianMAML:
    def __init__(
        self,
        base_agent: AsyncMARLAgent,
        meta_lr: float = 1e-3,
        inner_lr: float = 0.01,
        inner_steps: int = 5,
        first_order: bool = True,
        curvature_precondition: bool = True
    ):
        self.base_agent = base_agent
        self.meta_lr = meta_lr
        self.inner_lr = inner_lr
        self.inner_steps = inner_steps
        self.first_order = first_order
        self.curvature_precondition = curvature_precondition

        self.meta_params = {
            name: param.clone().detach().requires_grad_(True)
            for name, param in base_agent.named_parameters()
            if param.requires_grad
        }

        self.meta_optimizer = torch.optim.Adam(
            self.meta_params.values(), lr=meta_lr
        )

        self.meta_task_buffer = deque(maxlen=1000)
        self.zone_metrics: Dict[str, torch.Tensor] = {}

    def compute_adapted_params(
        self,
        task: MetaTask,
        params: Optional[Dict[str, torch.Tensor]] = None
    ) -> Dict[str, torch.Tensor]:
        if params is None:
            params = {k: v.clone() for k, v in self.meta_params.items()}

        M_inv = self._get_riemannian_preconditioner(task.zone, task.curvature_profile)

        for step in range(self.inner_steps):
            batch = self._sample_task_batch(task.support_set, batch_size=32)
            if not batch: continue

            adapted_agent = self._create_adapted_agent(params)
            actor_loss, critic_loss = adapted_agent.compute_loss(batch)
            total_loss = actor_loss + critic_loss

            grads = torch.autograd.grad(
                total_loss, params.values(),
                create_graph=not self.first_order,
                retain_graph=True
            )

            new_params = {}
            for (name, param), grad in zip(params.items(), grads):
                if self.curvature_precondition and name in M_inv:
                    preconditioned_grad = M_inv[name] @ grad.view(-1, 1)
                    new_params[name] = param - self.inner_lr * preconditioned_grad.view(param.shape)
                else:
                    new_params[name] = param - self.inner_lr * grad

            params = new_params

        return params

    def meta_update(self, tasks: List[MetaTask]):
        self.meta_optimizer.zero_grad()
        meta_loss = 0.0

        for task in tasks:
            adapted_params = self.compute_adapted_params(task)
            adapted_agent = self._create_adapted_agent(adapted_params)
            query_batch = self._sample_task_batch(task.query_set, batch_size=32)
            if not query_batch: continue

            actor_loss, critic_loss = adapted_agent.compute_loss(query_batch)
            task_loss = actor_loss + critic_loss
            meta_loss += task_loss

        if len(tasks) > 0 and isinstance(meta_loss, torch.Tensor):
            meta_loss = meta_loss / len(tasks)
            meta_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.meta_params.values(), max_norm=1.0)
            self.meta_optimizer.step()
            return meta_loss.item()
        return 0.0

    def adapt_to_new_mission(
        self,
        new_task: MetaTask,
        agent: AsyncMARLAgent
    ):
        adapted_params = self.compute_adapted_params(new_task, self.meta_params)
        with torch.no_grad():
            state_dict = agent.state_dict()
            for name, param in adapted_params.items():
                if name in state_dict:
                    state_dict[name].copy_(param)
            agent.load_state_dict(state_dict)
        return agent

    def _get_riemannian_preconditioner(
        self,
        zone: str,
        curvature_profile: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        if zone in self.zone_metrics:
            return self.zone_metrics[zone]

        M_inv = {}
        for name, param in self.meta_params.items():
            curvature_factor = 1.0 / (1.0 + torch.abs(curvature_profile).mean().item())
            M_inv[name] = torch.eye(param.numel()) * curvature_factor

        self.zone_metrics[zone] = M_inv
        return M_inv

    def _create_adapted_agent(
        self,
        params: Dict[str, torch.Tensor]
    ) -> AsyncMARLAgent:
        adapted = copy.deepcopy(self.base_agent)
        state_dict = adapted.state_dict()
        for name, param in params.items():
            if name in state_dict:
                state_dict[name] = param
        adapted.load_state_dict(state_dict)
        return adapted

    def _sample_task_batch(self, dataset: List[Dict], batch_size: int) -> Dict[str, torch.Tensor]:
        if not dataset: return {}
        indices = np.random.choice(len(dataset), min(batch_size, len(dataset)), replace=False)
        batch = {}
        keys = dataset[0].keys()
        for k in keys:
            if k in ['xi', 'xi_next', 'log_prob']:
                batch[k] = torch.stack([dataset[i][k] for i in indices])
            elif k == 'action':
                batch[k] = torch.tensor([dataset[i][k] for i in indices])
            elif k == 'reward_local':
                batch[k] = torch.tensor([dataset[i][k] for i in indices], dtype=torch.float32)
            elif k == 'done':
                batch[k] = torch.tensor([dataset[i][k] for i in indices], dtype=torch.float32)
        return batch

class MetaAdaptationLayer:
    def __init__(
        self,
        manifold: CatedralManifoldConfirmed,
        meta_lr: float = 1e-3,
        adaptation_threshold: float = 0.3,
        min_tasks_for_meta: int = 50
    ):
        self.manifold = manifold
        self.meta_learners: Dict[str, RiemannianMAML] = {}
        self.task_history = deque(maxlen=1000)
        self.adaptation_threshold = adaptation_threshold
        self.min_tasks_for_meta = min_tasks_for_meta
        self.mission_embedding_mean = None
        self.mission_embedding_cov = None

    def register_agent(self, zone: str, agent: AsyncMARLAgent):
        self.meta_learners[zone] = RiemannianMAML(
            base_agent=agent,
            meta_lr=1e-3,
            inner_steps=5,
            first_order=True,
            curvature_precondition=True
        )

    def observe_mission(self, goal: MissionGoal, decomposed_tasks: List[DecomposedTask]):
        if not self.meta_learners: return
        first_zone = list(self.meta_learners.keys())[0]
        task_embeddings = [
            self.meta_learners[first_zone].base_agent.critic(
                torch.randn(1, 4)
            ).detach()
            for _ in decomposed_tasks
        ]
        if task_embeddings:
            mission_emb = torch.stack(task_embeddings).mean(dim=0)
            self.task_history.append({
                'embedding': mission_emb,
                'tasks': decomposed_tasks,
                'timestamp': time.time()
            })
            if len(self.task_history) >= self.min_tasks_for_meta:
                self._update_distribution_stats()

    def check_adaptation_needed(self, new_goal: MissionGoal) -> bool:
        if self.mission_embedding_mean is None:
            return False
        new_emb = torch.randn(1, 1) # simplified
        if new_emb.shape[1] != self.mission_embedding_mean.shape[1]:
            return False # shape mismatch fallback
        diff = new_emb - self.mission_embedding_mean
        try:
            kl = (diff @ torch.inverse(self.mission_embedding_cov) @ diff.T).item()
            return kl > self.adaptation_threshold
        except:
            return False

    def adapt_agent_for_mission(
        self,
        zone: str,
        new_goal: MissionGoal,
        support_episodes: List[Dict]
    ) -> AsyncMARLAgent:
        if zone not in self.meta_learners:
            raise ValueError(f"Zona {zone} não registrada para meta-aprendizado")

        curvature_profile = self.manifold.scalar_curvature(
            torch.zeros(1, 4), zone
        ).detach()

        meta_task = MetaTask(
            task_id=new_goal.id,
            support_set=support_episodes[:20],
            query_set=support_episodes[20:30],
            zone=zone,
            curvature_profile=curvature_profile
        )

        adapted_agent = self.meta_learners[zone].adapt_to_new_mission(
            meta_task, self.meta_learners[zone].base_agent
        )
        return adapted_agent

    def _update_distribution_stats(self):
        embeddings = torch.stack([t['embedding'] for t in self.task_history]).squeeze(1)
        self.mission_embedding_mean = embeddings.mean(dim=0, keepdim=True)
        if embeddings.shape[0] > 1:
            self.mission_embedding_cov = torch.cov(embeddings.T) + torch.eye(embeddings.shape[1]) * 1e-6


# ============================================================================
# ARKHE OS v∞.Ω.∇+++.147 — CONTRAFACTUAL WORLD MODEL & SAFE EXPLORATION
# ============================================================================

class ContraFactualWorldModel(nn.Module):
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 256,
        num_ensemble: int = 5,
        uncertainty_threshold: float = 0.1
    ):
        super().__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.num_ensemble = num_ensemble
        self.uncertainty_threshold = uncertainty_threshold

        self.transition_models = nn.ModuleList([
            nn.Sequential(
                nn.Linear(state_dim + action_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, state_dim * 2)
            )
            for _ in range(num_ensemble)
        ])

        self.reward_model = nn.Sequential(
            nn.Linear(state_dim + action_dim + state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

        self.done_model = nn.Sequential(
            nn.Linear(state_dim + action_dim + state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

    def predict(
        self,
        state: torch.Tensor,
        action: int,
        return_uncertainty: bool = True
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        action_onehot = F.one_hot(torch.tensor(action), self.action_dim).float()
        if action_onehot.dim() == 1:
            action_onehot = action_onehot.unsqueeze(0)
        if state.dim() == 1:
            state = state.unsqueeze(0)

        sa = torch.cat([state, action_onehot], dim=-1)

        predictions = []
        for model in self.transition_models:
            out = model(sa)
            mean, log_var = torch.chunk(out, 2, dim=-1)
            predictions.append(mean)

        predictions = torch.stack(predictions)
        next_state_mean = predictions.mean(dim=0)
        next_state_std = predictions.std(dim=0)

        sa_next = torch.cat([sa, next_state_mean], dim=-1)
        reward = self.reward_model(sa_next)
        done_prob = self.done_model(sa_next)

        if return_uncertainty:
            return next_state_mean.squeeze(0), next_state_std.squeeze(0), reward.squeeze(0), done_prob.squeeze(0)
        return next_state_mean.squeeze(0), reward.squeeze(0), done_prob.squeeze(0)

    def compute_uncertainty(self, state: torch.Tensor, action: int) -> float:
        _, std, _, _ = self.predict(state, action)
        return std.mean().item()

class ContraFactualSafetyChecker:
    def __init__(
        self,
        world_model: ContraFactualWorldModel,
        manifold: CatedralManifoldConfirmed,
        safety_margin: float = 0.02,
        max_simulation_depth: int = 10,
        num_counterfactuals: int = 50
    ):
        self.world_model = world_model
        self.manifold = manifold
        self.safety_margin = safety_margin
        self.max_depth = max_simulation_depth
        self.num_counterfactuals = num_counterfactuals

        self.mercy_min = 0.04 + safety_margin
        self.mercy_max = 0.10 - safety_margin

    def is_action_safe(
        self,
        state: torch.Tensor,
        action: int,
        zone: str,
        horizon: int = 5
    ) -> Tuple[bool, Dict]:
        safe_count = 0
        violation_distances = []
        max_uncertainties = []

        for _ in range(self.num_counterfactuals):
            current_state = state.clone()
            trajectory_safe = True
            traj_max_uncertainty = 0.0

            for t in range(horizon):
                next_mean, next_std, _, _ = self.world_model.predict(
                    current_state, action if t == 0 else np.random.randint(self.world_model.action_dim)
                )

                noise = torch.randn_like(next_mean) * next_std
                next_state = next_mean + noise

                d_g = self.manifold.distance(
                    self.manifold.denormalize(next_state), zone
                ).item()

                uncertainty = next_std.mean().item()
                traj_max_uncertainty = max(traj_max_uncertainty, uncertainty)

                if not (self.mercy_min <= d_g <= self.mercy_max):
                    trajectory_safe = False
                    violation_distances.append(abs(d_g - 0.07))
                    break

                current_state = next_state

            if trajectory_safe:
                safe_count += 1
            max_uncertainties.append(traj_max_uncertainty)

        safety_ratio = safe_count / self.num_counterfactuals
        is_safe = safety_ratio >= 0.95

        diagnostics = {
            'safety_ratio': safety_ratio,
            'avg_violation_distance': float(np.mean(violation_distances)) if violation_distances else 0.0,
            'max_uncertainty': max(max_uncertainties) if max_uncertainties else 0.0,
            'mean_uncertainty': float(np.mean(max_uncertainties)) if max_uncertainties else 0.0,
            'horizon_simulated': horizon
        }
        return is_safe, diagnostics

    def find_safe_action(
        self,
        state: torch.Tensor,
        action_probs: torch.Tensor,
        zone: str,
        agent: AsyncMARLAgent
    ) -> Tuple[int, Dict]:
        sorted_actions = torch.argsort(action_probs, descending=True).tolist()
        for action in sorted_actions:
            is_safe, diag = self.is_action_safe(state, action, zone)
            if is_safe:
                return action, {**diag, 'selected_by': 'policy_safe'}

        uncertainties = []
        for a in range(len(action_probs)):
            _, std, _, _ = self.world_model.predict(state, a)
            uncertainties.append(std.mean().item())

        safest_action = int(np.argmin(uncertainties))
        return safest_action, {
            'selected_by': 'uncertainty_minimization',
            'action_uncertainties': uncertainties
        }

class SafeAsyncMARLAgent(AsyncMARLAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.world_model = ContraFactualWorldModel(
            state_dim=self.state_dim,
            action_dim=self.action_dim,
            num_ensemble=5
        )
        self.safety_checker = None
        self.model_buffer = deque(maxlen=10000)
        self.safety_blocks = 0

    def set_safety_checker(self, checker: ContraFactualSafetyChecker):
        self.safety_checker = checker

    def select_action_safe(
        self,
        xi: torch.Tensor,
        curvature_info: Optional[Dict] = None
    ) -> Tuple[int, torch.Tensor, Dict]:
        action_probs = self.actor(xi)
        if self.curvature_aware and curvature_info is not None:
            R_scalar = curvature_info.get('R_scalar', 0.0)
            exploration_scale = 1.0 / (1.0 + abs(R_scalar) / 50.0)
            tempered_probs = F.softmax(
                torch.log(action_probs + 1e-8) * exploration_scale, dim=-1
            )
        else:
            tempered_probs = action_probs

        if self.safety_checker is not None:
            action, safety_diag = self.safety_checker.find_safe_action(
                xi, tempered_probs.squeeze(0), self.zone_id, self
            )
            if safety_diag.get('selected_by') != 'policy_safe':
                self.safety_blocks += 1
            log_prob = torch.log(tempered_probs[0, action] + 1e-8)
            return action, log_prob, safety_diag

        action = torch.multinomial(tempered_probs, 1).squeeze(0)
        log_prob = torch.log(tempered_probs[0, action] + 1e-8)
        return action.item(), log_prob, {'selected_by': 'standard_policy'}

    def train_world_model(self, batch_size: int = 64):
        if len(self.model_buffer) < batch_size:
            return None

        indices = np.random.choice(len(self.model_buffer), batch_size, replace=False)
        batch = {
            'state': torch.stack([self.model_buffer[i]['state'] for i in indices]),
            'action': torch.tensor([self.model_buffer[i]['action'] for i in indices]),
            'next_state': torch.stack([self.model_buffer[i]['next_state'] for i in indices]),
            'reward': torch.tensor([self.model_buffer[i]['reward'] for i in indices], dtype=torch.float32),
            'done': torch.tensor([self.model_buffer[i]['done'] for i in indices], dtype=torch.float32)
        }

        total_loss = 0.0
        for model in self.world_model.transition_models:
            sa = torch.cat([
                batch['state'],
                F.one_hot(batch['action'], self.action_dim).float()
            ], dim=-1)

            out = model(sa)
            pred_mean, pred_log_var = torch.chunk(out, 2, dim=-1)

            nll = 0.5 * (
                pred_log_var +
                (batch['next_state'] - pred_mean).pow(2) / (pred_log_var.exp() + 1e-8)
            ).mean()

            opt = torch.optim.Adam(model.parameters(), lr=1e-3)
            opt.zero_grad()
            nll.backward()
            opt.step()
            total_loss += nll.item()

        sa_next = torch.cat([
            torch.cat([batch['state'], F.one_hot(batch['action'], self.action_dim).float()], dim=-1),
            batch['next_state']
        ], dim=-1)
        pred_reward = self.world_model.reward_model(sa_next).squeeze()
        reward_loss = F.mse_loss(pred_reward, batch['reward'])

        opt_reward = torch.optim.Adam(self.world_model.reward_model.parameters(), lr=1e-3)
        opt_reward.zero_grad()
        reward_loss.backward()
        opt_reward.step()

        return {
            'transition_loss': total_loss / self.world_model.num_ensemble,
            'reward_loss': reward_loss.item()
        }


# ============================================================================
# ARKHE OS v∞.Ω.∇+++.147 — MULTI-AGENT RESOURCE NEGOTIATION (VCG + CURVATURE)
# ============================================================================

@dataclass
class ResourceBundle:
    energy_gj: float = 0.0
    compute_tflops: float = 0.0
    bandwidth_mbps: float = 0.0
    crystal_time_ms: float = 0.0

    def __add__(self, other):
        return ResourceBundle(
            energy_gj=self.energy_gj + other.energy_gj,
            compute_tflops=self.compute_tflops + other.compute_tflops,
            bandwidth_mbps=self.bandwidth_mbps + other.bandwidth_mbps,
            crystal_time_ms=self.crystal_time_ms + other.crystal_time_ms
        )

    def __mul__(self, scalar: float):
        return ResourceBundle(
            energy_gj=self.energy_gj * scalar,
            compute_tflops=self.compute_tflops * scalar,
            bandwidth_mbps=self.bandwidth_mbps * scalar,
            crystal_time_ms=self.crystal_time_ms * scalar
        )

    def total_value(self) -> float:
        return self.energy_gj + self.compute_tflops + self.bandwidth_mbps + self.crystal_time_ms

class CurvatureAdjustedValuation:
    def __init__(
        self,
        base_valuation: ResourceBundle,
        curvature_sensitivity: float = 0.5,
        diminishing_returns: float = 0.8
    ):
        self.base = base_valuation
        self.curvature_sensitivity = curvature_sensitivity
        self.diminishing_returns = diminishing_returns

    def evaluate(
        self,
        allocation: ResourceBundle,
        curvature_scalar: float,
        current_allocation: Optional[ResourceBundle] = None
    ) -> float:
        curvature_penalty = np.exp(
            -self.curvature_sensitivity * abs(curvature_scalar) / 100.0
        )
        if current_allocation is not None:
            total = ResourceBundle(
                energy_gj=current_allocation.energy_gj + allocation.energy_gj,
                compute_tflops=current_allocation.compute_tflops + allocation.compute_tflops,
                bandwidth_mbps=current_allocation.bandwidth_mbps + allocation.bandwidth_mbps,
                crystal_time_ms=current_allocation.crystal_time_ms + allocation.crystal_time_ms
            )
        else:
            total = allocation

        utility = (
            self.base.energy_gj * (total.energy_gj ** self.diminishing_returns) +
            self.base.compute_tflops * (total.compute_tflops ** self.diminishing_returns) +
            self.base.bandwidth_mbps * (total.bandwidth_mbps ** self.diminishing_returns) +
            self.base.crystal_time_ms * (total.crystal_time_ms ** self.diminishing_returns)
        ) * curvature_penalty
        return utility

class AsyncResourceNegotiator:
    def __init__(
        self,
        zones: List[str],
        total_resources: ResourceBundle,
        manifold: CatedralManifoldConfirmed,
        price_update_rate: float = 0.1,
        consensus_tolerance: float = 1e-6
    ):
        self.zones = zones
        self.total_resources = total_resources
        self.manifold = manifold
        self.price_update_rate = price_update_rate
        self.consensus_tolerance = consensus_tolerance

        self.shadow_prices = {
            zone: ResourceBundle(energy_gj=1.0, compute_tflops=1.0, bandwidth_mbps=1.0, crystal_time_ms=1.0)
            for zone in zones
        }
        self.current_allocations = {
            zone: ResourceBundle() for zone in zones
        }
        self.zone_valuations: Dict[str, CurvatureAdjustedValuation] = {}
        self.pending_requests: Dict[str, List[Dict]] = defaultdict(list)

    def register_valuation(self, zone: str, valuation: CurvatureAdjustedValuation):
        self.zone_valuations[zone] = valuation

    def request_resources(
        self,
        zone: str,
        demand: ResourceBundle,
        urgency: float = 1.0,
        task_id: Optional[str] = None
    ) -> str:
        request_id = f"req_{zone}_{task_id or 'unknown'}_{time.time()}"
        curvature = self.manifold.scalar_curvature(torch.zeros(1, 4), zone).item()

        if zone in self.zone_valuations:
            valuation = self.zone_valuations[zone].evaluate(
                demand, curvature, self.current_allocations[zone]
            )
        else:
            valuation = demand.total_value()

        request = {
            'id': request_id,
            'zone': zone,
            'demand': demand,
            'valuation': valuation,
            'urgency': urgency,
            'timestamp': time.time(),
            'curvature_at_request': curvature
        }
        self.pending_requests[zone].append(request)
        return request_id

    def clear_market(self) -> Dict[str, ResourceBundle]:
        all_requests = []
        for zone_requests in self.pending_requests.values():
            all_requests.extend(zone_requests)

        if not all_requests:
            return self.current_allocations

        allocations = {zone: ResourceBundle() for zone in self.zones}
        prices = {zone: ResourceBundle(energy_gj=1.0, compute_tflops=1.0, bandwidth_mbps=1.0, crystal_time_ms=1.0) for zone in self.zones}

        for iteration in range(100):
            zone_demands = {}
            for zone in self.zones:
                zone_requests = [r for r in all_requests if r['zone'] == zone]
                if not zone_requests: continue

                total_demand = ResourceBundle()
                for req in zone_requests:
                    total_demand = total_demand + req['demand']

                curvature = self.manifold.scalar_curvature(torch.zeros(1, 4), zone).item()
                curvature_price_factor = 1.0 + 0.5 * abs(curvature) / 100.0

                effective_demand = ResourceBundle(
                    energy_gj=total_demand.energy_gj / (prices[zone].energy_gj * curvature_price_factor),
                    compute_tflops=total_demand.compute_tflops / (prices[zone].compute_tflops * curvature_price_factor),
                    bandwidth_mbps=total_demand.bandwidth_mbps / (prices[zone].bandwidth_mbps * curvature_price_factor),
                    crystal_time_ms=total_demand.crystal_time_ms / (prices[zone].crystal_time_ms * curvature_price_factor)
                )
                zone_demands[zone] = effective_demand

            total_demand = ResourceBundle()
            for demand in zone_demands.values():
                total_demand = total_demand + demand

            excess_energy = total_demand.energy_gj - self.total_resources.energy_gj
            excess_compute = total_demand.compute_tflops - self.total_resources.compute_tflops
            excess_bandwidth = total_demand.bandwidth_mbps - self.total_resources.bandwidth_mbps
            excess_crystal = total_demand.crystal_time_ms - self.total_resources.crystal_time_ms

            for zone in self.zones:
                if zone in zone_demands:
                    prices[zone] = ResourceBundle(
                        energy_gj=max(0.1, prices[zone].energy_gj + self.price_update_rate * excess_energy),
                        compute_tflops=max(0.1, prices[zone].compute_tflops + self.price_update_rate * excess_compute),
                        bandwidth_mbps=max(0.1, prices[zone].bandwidth_mbps + self.price_update_rate * excess_bandwidth),
                        crystal_time_ms=max(0.1, prices[zone].crystal_time_ms + self.price_update_rate * excess_crystal)
                    )

            max_excess = max(abs(excess_energy), abs(excess_compute), abs(excess_bandwidth), abs(excess_crystal))
            if max_excess < self.consensus_tolerance:
                break

        for zone in self.zones:
            if zone not in zone_demands: continue
            demand = zone_demands[zone]
            total_eff = sum(d.total_value() for d in zone_demands.values()) or 1.0
            share = demand.total_value() / total_eff
            allocations[zone] = ResourceBundle(
                energy_gj=min(demand.energy_gj, self.total_resources.energy_gj * share),
                compute_tflops=min(demand.compute_tflops, self.total_resources.compute_tflops * share),
                bandwidth_mbps=min(demand.bandwidth_mbps, self.total_resources.bandwidth_mbps * share),
                crystal_time_ms=min(demand.crystal_time_ms, self.total_resources.crystal_time_ms * share)
            )

        self.current_allocations = allocations
        self.shadow_prices = prices
        self.pending_requests.clear()
        return allocations

    def compute_vcg_payments(self) -> Dict[str, float]:
        payments = {}
        for zone in self.zones:
            other_zones = [z for z in self.zones if z != zone]
            social_welfare_without = sum(
                self.zone_valuations.get(z, CurvatureAdjustedValuation(ResourceBundle()))
                .evaluate(self.current_allocations[z], 0.0)
                for z in other_zones
            )
            social_welfare_total = sum(
                self.zone_valuations.get(z, CurvatureAdjustedValuation(ResourceBundle()))
                .evaluate(self.current_allocations[z], 0.0)
                for z in self.zones
            )
            payment = social_welfare_without - (social_welfare_total -
                self.zone_valuations.get(zone, CurvatureAdjustedValuation(ResourceBundle()))
                .evaluate(self.current_allocations[zone], 0.0))
            payments[zone] = max(0.0, payment)
        return payments

class ResourceAwareMissionExecution:
    def __init__(
        self,
        base_loop: HierarchicalAsyncMARLLoop,
        negotiator: AsyncResourceNegotiator,
        resource_recheck_interval: int = 50
    ):
        self.base_loop = base_loop
        self.negotiator = negotiator
        self.resource_recheck_interval = resource_recheck_interval
        self.step_count = 0

    def execute_with_negotiation(
        self,
        high_level_goal: MissionGoal,
        available_zones: List[str],
        max_steps: int = 1000
    ) -> Dict:
        tasks = self.base_loop.decomposer.decompose(high_level_goal, available_zones)
        total_demand = ResourceBundle()
        for task in tasks:
            for resource, amount in getattr(task, 'resource_budget', {}).items():
                setattr(total_demand, resource, getattr(total_demand, resource, 0) + amount)

        for zone in available_zones:
            zone_tasks = [t for t in tasks if getattr(t, 'assigned_zone', '') == zone]
            zone_demand = ResourceBundle()
            for task in zone_tasks:
                for resource, amount in getattr(task, 'resource_budget', {}).items():
                    setattr(zone_demand, resource, getattr(zone_demand, resource, 0) + amount)
            self.negotiator.request_resources(
                zone=zone,
                demand=zone_demand,
                urgency=high_level_goal.priority,
                task_id=high_level_goal.id
            )

        allocations = self.negotiator.clear_market()
        print(f"[NEGOTIATION] Recursos alocados: {allocations}")
        return {
            'allocations': allocations,
            'payments': self.negotiator.compute_vcg_payments(),
            'execution_result': self.base_loop.execute_mission(high_level_goal, available_zones, max_steps)
        }

# ============================================================================
# ARKHE OS v∞.Ω.∇+++.147 — CURRICULUM LEARNING FOR MISSION COMPLEXITY
# ============================================================================

@dataclass
class CurriculumStage:
    stage_id: int
    mission: MissionGoal
    target_difficulty: float
    required_success_rate: float
    prerequisites: List[int]
    completed: bool = False
    success_rate: float = 0.0
    avg_reward: float = 0.0

class RiemannianCurriculumGenerator:
    def __init__(
        self,
        manifold: CatedralManifoldConfirmed,
        zone_capabilities: Dict[str, Dict],
        difficulty_params: Optional[Dict] = None
    ):
        self.manifold = manifold
        self.zone_capabilities = zone_capabilities
        self.diff_params = difficulty_params or {
            'alpha_curvature': 0.3,
            'beta_zones': 0.2,
            'beta_latency': 0.3,
            'gamma_dependencies': 0.2,
            'delta_target': 0.15,
            'min_success_rate': 0.7
        }
        self.mission_templates = self._build_mission_templates()
        self.curriculum: List[CurriculumStage] = []
        self.current_stage = 0

    def _build_mission_templates(self) -> List[Dict]:
        return [
            {
                'id': 'calibrate_sensor',
                'description': 'Calibrate quantum sensor in local zone',
                'base_priority': 0.3,
                'base_constraints': {'max_latency': 10.0, 'max_curvature': 20.0},
                'zones_required': 1,
                'dependency_density': 0.0
            },
            {
                'id': 'local_transport',
                'description': 'Transport resources within single zone',
                'base_priority': 0.4,
                'base_constraints': {'max_latency': 30.0, 'max_curvature': 30.0},
                'zones_required': 1,
                'dependency_density': 0.2
            },
            {
                'id': 'cross_zone_relay',
                'description': 'Relay data between two adjacent zones',
                'base_priority': 0.5,
                'base_constraints': {'max_latency': 60.0, 'max_curvature': 40.0},
                'zones_required': 2,
                'dependency_density': 0.3
            },
            {
                'id': 'multi_zone_mining',
                'description': 'Coordinate mining across asteroid belt zones',
                'base_priority': 0.6,
                'base_constraints': {'max_latency': 90.0, 'max_curvature': 50.0},
                'zones_required': 3,
                'dependency_density': 0.4
            },
            {
                'id': 'deep_space_exploration',
                'description': 'Explore unknown regions with high curvature',
                'base_priority': 0.7,
                'base_constraints': {'max_latency': 120.0, 'max_curvature': 80.0},
                'zones_required': 4,
                'dependency_density': 0.5
            },
            {
                'id': 'quantum_teleportation_mission',
                'description': 'Coordinate quantum teleportation across all zones',
                'base_priority': 0.9,
                'base_constraints': {'max_latency': 180.0, 'max_curvature': 100.0},
                'zones_required': 4,
                'dependency_density': 0.7
            }
        ]

    def compute_mission_difficulty(
        self,
        mission: MissionGoal,
        zones: List[str],
        latency_matrix: Optional[Dict] = None
    ) -> float:
        curvatures = []
        for zone in zones:
            R = abs(self.manifold.scalar_curvature(torch.zeros(1, 4), zone).item())
            curvatures.append(R)
        avg_curvature = np.mean(curvatures) if curvatures else 0.0
        n_zones = len(zones)
        max_latency = 0.0
        if latency_matrix:
            for (z1, z2), lat in latency_matrix.items():
                max_latency = max(max_latency, lat)

        dep_density = 0.3
        if 'transport' in mission.description.lower(): dep_density = 0.5
        elif 'explore' in mission.description.lower(): dep_density = 0.4
        elif 'coordinate' in mission.description.lower(): dep_density = 0.7

        difficulty = (
            self.diff_params['alpha_curvature'] * (avg_curvature / 100.0) +
            self.diff_params['beta_zones'] * (n_zones / 4.0) +
            self.diff_params['beta_latency'] * (max_latency / 60.0) +
            self.diff_params['gamma_dependencies'] * dep_density
        )
        return min(1.0, difficulty)

    def generate_curriculum(
        self,
        target_mission: MissionGoal,
        available_zones: List[str],
        num_stages: int = 10,
        latency_matrix: Optional[Dict] = None
    ) -> List[CurriculumStage]:
        target_difficulty = self.compute_mission_difficulty(target_mission, available_zones, latency_matrix)
        initial_difficulty = 0.05
        stages = []
        current_difficulty = initial_difficulty

        for stage_id in range(num_stages):
            best_template = None
            best_diff = float('inf')

            for template in self.mission_templates:
                temp_mission = MissionGoal(
                    id=f"{template['id']}_stage_{stage_id}",
                    description=template['description'],
                    priority=template['base_priority'],
                    constraints=template['base_constraints']
                )
                n_zones = min(template['zones_required'], len(available_zones))
                selected_zones = available_zones[:n_zones]

                template_diff = self.compute_mission_difficulty(temp_mission, selected_zones, latency_matrix)
                target_stage_diff = initial_difficulty + stage_id * self.diff_params['delta_target']
                adjusted_diff = template_diff * (target_stage_diff / 0.5)
                diff_to_target = abs(adjusted_diff - target_stage_diff)

                if diff_to_target < best_diff and adjusted_diff <= target_difficulty:
                    best_diff = diff_to_target
                    best_template = {
                        **template,
                        'adjusted_difficulty': adjusted_diff,
                        'selected_zones': selected_zones
                    }

            if best_template is None:
                best_template = {
                    'id': f'adapted_{target_mission.id}',
                    'description': target_mission.description,
                    'base_priority': target_mission.priority * 0.5,
                    'base_constraints': {k: v * 1.5 for k, v in target_mission.constraints.items()},
                    'zones_required': len(available_zones),
                    'dependency_density': 0.3,
                    'adjusted_difficulty': current_difficulty,
                    'selected_zones': available_zones
                }

            stage_mission = MissionGoal(
                id=f"curriculum_stage_{stage_id}",
                description=best_template['description'],
                priority=best_template['base_priority'],
                constraints=best_template['base_constraints']
            )

            stage = CurriculumStage(
                stage_id=stage_id,
                mission=stage_mission,
                target_difficulty=best_template['adjusted_difficulty'],
                required_success_rate=self.diff_params['min_success_rate'],
                prerequisites=[i for i in range(max(0, stage_id - 2), stage_id)]
            )
            stages.append(stage)
            current_difficulty = best_template['adjusted_difficulty']
            if current_difficulty >= target_difficulty:
                break

        final_stage = CurriculumStage(
            stage_id=len(stages),
            mission=target_mission,
            target_difficulty=target_difficulty,
            required_success_rate=0.8,
            prerequisites=[len(stages) - 1] if stages else []
        )
        stages.append(final_stage)
        self.curriculum = stages
        return stages

    def evaluate_stage_performance(self, stage_id: int, execution_result: Dict) -> bool:
        if stage_id >= len(self.curriculum): return False
        stage = self.curriculum[stage_id]
        stage.success_rate = 0.9 if execution_result.get('success', False) else 0.3
        stage.avg_reward = execution_result.get('avg_reward', 0.0)
        stage.completed = stage.success_rate >= stage.required_success_rate
        return stage.completed

    def get_next_stage(self) -> Optional[CurriculumStage]:
        if self.current_stage >= len(self.curriculum): return None
        stage = self.curriculum[self.current_stage]
        prereqs_met = all(self.curriculum[p].completed for p in stage.prerequisites)
        if prereqs_met: return stage
        for i in range(self.current_stage - 1, -1, -1):
            if not self.curriculum[i].completed:
                return self.curriculum[i]
        return stage

    def adapt_curriculum(self, performance_history: List[Dict]):
        if len(performance_history) < 3: return
        recent_perf = performance_history[-3:]
        avg_success = np.mean([p.get('success', False) for p in recent_perf])

        if avg_success > 0.9:
            self.diff_params['delta_target'] *= 1.2
            print(f"[CURRICULUM] Acelerando: delta_target = {self.diff_params['delta_target']:.3f}")
        elif avg_success < 0.4:
            self.diff_params['delta_target'] *= 0.7
            print(f"[CURRICULUM] Desacelerando: delta_target = {self.diff_params['delta_target']:.3f}")
            current = self.curriculum[self.current_stage]
            if self.current_stage > 0:
                prev = self.curriculum[self.current_stage - 1]
                mid_difficulty = (prev.target_difficulty + current.target_difficulty) / 2
                mid_stage = CurriculumStage(
                    stage_id=self.current_stage,
                    mission=MissionGoal(
                        id=f"intermediate_{self.current_stage}",
                        description=f"Intermediate training stage {self.current_stage}",
                        priority=0.5,
                        constraints={'max_latency': 60.0, 'max_curvature': 40.0}
                    ),
                    target_difficulty=mid_difficulty,
                    required_success_rate=self.diff_params['min_success_rate'],
                    prerequisites=prev.prerequisites
                )
                self.curriculum.insert(self.current_stage, mid_stage)
                for i, s in enumerate(self.curriculum):
                    s.stage_id = i

class CurriculumDrivenMissionLoop(HierarchicalAsyncMARLLoop):
    def __init__(self, *args, curriculum_generator: Optional[RiemannianCurriculumGenerator] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.curriculum = curriculum_generator
        self.performance_history: List[Dict] = []
        self.total_stages_completed = 0

    def execute_curriculum_mission(
        self,
        target_mission: MissionGoal,
        available_zones: List[str],
        max_stages: int = 15
    ) -> Dict:
        if self.curriculum is None:
            raise ValueError("Curriculum generator não configurado")

        stages = self.curriculum.generate_curriculum(
            target_mission, available_zones, num_stages=max_stages,
            latency_matrix=getattr(self, 'comm_layer', None)
        )
        print(f"[CURRICULUM] {len(stages)} estágios gerados para missão: {target_mission.description}")

        for stage in stages:
            print(f"\n[ESTÁGIO {stage.stage_id}] {stage.mission.description}")
            print(f"Dificuldade alvo: {stage.target_difficulty:.3f}")

            result = self.execute_mission(
                high_level_goal=stage.mission,
                available_zones=available_zones[:min(4, len(available_zones))],
                max_steps=200
            )

            success = self.curriculum.evaluate_stage_performance(stage.stage_id, result)
            self.performance_history.append(result)

            print(f"Resultado: Sucesso={result['success']}, Recompensa={result['avg_reward']:.3f}")
            print(f"Estágio completado: {success}")

            if success:
                self.total_stages_completed += 1
            else:
                self.curriculum.adapt_curriculum(self.performance_history)
                continue

            self.curriculum.current_stage += 1

        return {
            'target_mission': target_mission.id,
            'stages_total': len(stages),
            'stages_completed': self.total_stages_completed,
            'final_success_rate': self.total_stages_completed / len(stages),
            'performance_history': self.performance_history,
            'curriculum_adaptations': len([p for p in self.performance_history if not p.get('success', False)])
        }

if __name__ == "__main__":
    print("Módulo Metacognitivo Carregado (Substrato 147)")
