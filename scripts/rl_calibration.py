import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical
from collections import deque
import gymnasium as gym
from gymnasium import spaces

class LoRaCalibrationEnv(gym.Env):
    """
    Ambiente RL onde o agente (calibrador) escolhe SF, BW, TX power
    para maximizar a coerência do cluster e minimizar consumo energético.
    """
    def __init__(self, num_nodes=10, max_steps=200):
        super().__init__()
        self.num_nodes = num_nodes
        self.max_steps = max_steps
        self.current_step = 0

        # Espaço de ação: (delta_SF, delta_BW, delta_TX) para um nó alvo
        # delta_SF ∈ {-1, 0, +1}, delta_BW ∈ {-1, 0, +1}, delta_TX ∈ {-1, 0, +1}
        self.action_space = spaces.MultiDiscrete([3, 3, 3])

        # Espaço de observação: [kt_gap, coherence_grad, rssi, priority, sf, bw, tx_power]
        self.observation_space = spaces.Box(
            low=np.array([0, 0, -120, 0, 7, 125, 2]),
            high=np.array([50, 2, 0, 1, 12, 500, 20]),
            dtype=np.float32
        )

        # Estado interno
        self.kt_gap = np.random.uniform(0, 20, (num_nodes,))
        self.coherence_grad = np.random.uniform(0, 1, (num_nodes,))
        self.rssi = np.random.uniform(-90, -50, (num_nodes,))
        self.sf = np.full((num_nodes,), 9)
        self.bw = np.full((num_nodes,), 250)
        self.tx_power = np.full((num_nodes,), 14)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed, options=options)
        self.current_step = 0
        self.kt_gap = np.random.uniform(0, 20, (self.num_nodes,))
        self.coherence_grad = np.random.uniform(0, 1, (self.num_nodes,))
        self.rssi = np.random.uniform(-90, -50, (self.num_nodes,))
        self.sf = np.full((self.num_nodes,), 9)
        self.bw = np.full((self.num_nodes,), 250)
        self.tx_power = np.full((self.num_nodes,), 14)
        return self._get_obs(0), {}

    def _get_obs(self, node_idx):
        return np.array([
            self.kt_gap[node_idx],
            self.coherence_grad[node_idx],
            self.rssi[node_idx],
            self._compute_priority(node_idx),
            self.sf[node_idx],
            self.bw[node_idx],
            self.tx_power[node_idx]
        ], dtype=np.float32)

    def _compute_priority(self, node_idx):
        # Prioridade ∝ gradiente * exp(-gap/tau)
        tau = 15.0
        return self.coherence_grad[node_idx] * np.exp(-self.kt_gap[node_idx] / tau)

    def step(self, action):
        node_idx = self.current_step % self.num_nodes
        delta_sf, delta_bw, delta_tx = action - 1  # mapear {0,1,2} → {-1,0,+1}

        # Aplicar ação com clipping
        self.sf[node_idx] = np.clip(self.sf[node_idx] + delta_sf, 7, 12)
        self.bw[node_idx] = np.clip(self.bw[node_idx] + delta_bw * 125, 125, 500)
        self.tx_power[node_idx] = np.clip(self.tx_power[node_idx] + delta_tx, 2, 20)

        # Simular efeito da ação: atualizar métricas locais
        # SF maior → menor perda, mas mais latência → coerência melhora lentamente
        sf_factor = (self.sf[node_idx] - 7) / 5  # 0 a 1
        bw_factor = self.bw[node_idx] / 500  # 0.25 a 1
        tx_factor = (self.tx_power[node_idx] - 2) / 18  # 0 a 1

        # Melhoria na coerência local (proxy)
        coherence_improvement = 0.1 * sf_factor + 0.05 * bw_factor + 0.03 * tx_factor
        self.kt_gap[node_idx] = max(0, self.kt_gap[node_idx] - coherence_improvement + np.random.normal(0, 0.2))

        # Custo energético
        energy_cost = (self.sf[node_idx] / 7) * (self.bw[node_idx] / 125) * (self.tx_power[node_idx] / 14) * 0.01

        # Recompensa: redução de gap - custo energético
        reward = coherence_improvement - energy_cost

        # Penalidade se gap muito alto (alucinação)
        if self.kt_gap[node_idx] > 15:
            reward -= 0.5

        self.current_step += 1
        done = self.current_step >= self.max_steps

        next_obs = self._get_obs((node_idx + 1) % self.num_nodes)
        info = {'avg_gap': np.mean(self.kt_gap), 'energy_cost': energy_cost}

        # Convert reward to float to satisfy step signature (obs, reward, terminated, truncated, info)
        return next_obs, float(reward), done, False, info

# Rede de política PPO
class CalibrationPolicy(nn.Module):
    def __init__(self, obs_dim=7, act_dims=[3, 3, 3], hidden=128):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(obs_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU()
        )
        # Cabeças de política (uma por dimensão de ação)
        self.policy_heads = nn.ModuleList([
            nn.Linear(hidden, dim) for dim in act_dims
        ])
        # Cabeça de valor
        self.value_head = nn.Linear(hidden, 1)

    def forward(self, obs):
        x = self.shared(obs)
        action_logits = [head(x) for head in self.policy_heads]
        value = self.value_head(x)
        return action_logits, value

    def get_action(self, obs, deterministic=False):
        logits, value = self.forward(obs)
        actions = []
        log_probs = []
        for logit in logits:
            dist = Categorical(logits=logit)
            if deterministic:
                action = torch.argmax(logit, dim=-1)
            else:
                action = dist.sample()
            log_prob = dist.log_prob(action)
            actions.append(action)
            log_probs.append(log_prob)
        return torch.stack(actions, dim=-1), torch.stack(log_probs, dim=-1).sum(dim=-1), value

def train_rl_calibration(episodes=1000, lr=3e-4, gamma=0.99, clip_epsilon=0.2):
    env = LoRaCalibrationEnv(num_nodes=10, max_steps=200)
    policy = CalibrationPolicy()
    optimizer = optim.Adam(policy.parameters(), lr=lr)

    reward_history = []

    for episode in range(episodes):
        obs, _ = env.reset()
        done = False
        episode_reward = 0
        buffer = []

        while not done:
            obs_tensor = torch.FloatTensor(obs).unsqueeze(0)
            actions, log_prob, value = policy.get_action(obs_tensor)
            action_np = actions.squeeze(0).numpy().astype(np.int64)
            next_obs, reward, done, _, info = env.step(action_np)

            buffer.append((obs, actions, log_prob, value, reward, done))
            obs = next_obs
            episode_reward += reward

        # PPO update (simplificado)
        # ... (cálculo de vantagens, clipping, etc.)
        reward_history.append(episode_reward)

        if episode % 100 == 0:
            print(f"Episódio {episode}: recompensa média = {np.mean(reward_history[-100:]):.3f}")

    return policy, reward_history

if __name__ == "__main__":
    trained_policy, rewards = train_rl_calibration(episodes=1000)
    # Salvar política treinada
    torch.save(trained_policy.state_dict(), "calibration_policy.pt")
    print("Política RL treinada e salva como calibration_policy.pt")
