import gymnasium as gym
from gymnasium import spaces
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv

class LoRaCalibrationEnv(gym.Env):
    """Ambiente Gym para treinar política de calibração LoRa via RL."""

    def __init__(self, num_nodes: int = 10, episode_steps: int = 200):
        super().__init__()
        self.num_nodes = num_nodes
        self.episode_steps = episode_steps

        # Espaço de observação: [gap, gradient, RSSI, SF, T_tx, loss_rate] por nó
        self.observation_space = spaces.Box(
            low=np.array([0, -10, -100, 7, 10, 0] * num_nodes),
            high=np.array([50, 10, -30, 12, 120, 1] * num_nodes),
            shape=(num_nodes * 6,),
            dtype=np.float32
        )

        # Ação: ajuste discreto de SF, T_tx, P_tx por nó
        self.action_space = spaces.MultiDiscrete([3, 3, 3] * num_nodes)  # -1, 0, +1 para cada parâmetro

        self.current_step = 0
        self._reset_state()

    def _reset_state(self):
        """Inicializa estado aleatório realista."""
        self.gaps = np.random.uniform(1, 20, self.num_nodes)
        self.gradients = np.random.uniform(-2, 2, self.num_nodes)
        self.rssi = np.random.uniform(-90, -50, self.num_nodes)
        self.sf = np.ones(self.num_nodes, dtype=np.int8) * 9
        self.tx_interval = np.ones(self.num_nodes) * 30
        self.loss_rate = np.random.uniform(0.05, 0.2, self.num_nodes)
        self.current_step = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self._reset_state()
        return self._get_obs(), {}

    def _get_obs(self) -> np.ndarray:
        """Concatena estado em vetor único."""
        return np.concatenate([
            self.gaps, self.gradients, self.rssi,
            self.sf.astype(float), self.tx_interval, self.loss_rate
        ]).astype(np.float32)

    def step(self, action: np.ndarray):
        """Executa ação e retorna (obs, reward, terminated, truncated, info)."""
        # Aplicar ação: ajustar SF, T_tx, P_tx
        for i in range(self.num_nodes):
            # Ações: [-1, 0, +1] para cada parâmetro
            sf_adj = action[i*3] - 1  # -1, 0, +1
            tx_adj = action[i*3+1] - 1
            # p_adj = action[i*3+2] - 1  # reservado para futuro

            self.sf[i] = np.clip(self.sf[i] + sf_adj, 7, 12)
            self.tx_interval[i] = np.clip(self.tx_interval[i] + tx_adj * 5, 10, 120)

        # Simular evolução do ambiente
        self.gaps += np.random.normal(-0.1 * self.gradients, 0.3, self.num_nodes)
        self.gaps = np.clip(self.gaps, 0, 50)
        self.gradients = np.random.uniform(-1, 1, self.num_nodes)  # ruído
        self.rssi = np.clip(self.rssi + np.random.normal(0, 2, self.num_nodes), -100, -30)

        # Calcular recompensa
        gap_penalty = -np.mean(self.gaps) * 0.1
        energy_cost = -np.mean(self.sf / 7.0 * 0.05)  # SF maior → mais energia
        throughput_bonus = np.mean(1.0 / (self.tx_interval / 30.0)) * 0.05
        reward = gap_penalty + energy_cost + throughput_bonus

        self.current_step += 1
        terminated = self.current_step >= self.episode_steps
        truncated = False

        info = {
            'avg_gap': np.mean(self.gaps),
            'avg_sf': np.mean(self.sf),
            'avg_tx_interval': np.mean(self.tx_interval)
        }

        return self._get_obs(), float(reward), terminated, truncated, info

def train_calibration_policy(
    num_nodes: int = 10,
    total_timesteps: int = 100_000,
    model_path: str = "ppo_lora_calibrator.zip"
):
    """Treina política PPO para calibração LoRa."""
    # Criar ambiente vetorizado
    env = DummyVecEnv([lambda: LoRaCalibrationEnv(num_nodes=num_nodes)])

    # Configurar PPO
    model = PPO(
        "MlpPolicy", env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        verbose=1
    )

    # Treinar
    print(f"🤖 Treinando política de calibração por {total_timesteps} passos...")
    model.learn(total_timesteps=total_timesteps)

    # Salvar modelo
    model.save(model_path)
    print(f"✅ Modelo salvo em {model_path}")

    return model

def evaluate_policy(model_path: str, num_nodes: int = 10, eval_episodes: int = 10):
    """Avalia política treinada."""
    from stable_baselines3 import PPO
    model = PPO.load(model_path)
    env = LoRaCalibrationEnv(num_nodes=num_nodes)

    rewards = []
    for ep in range(eval_episodes):
        obs, _ = env.reset()
        done = False
        ep_reward = 0
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, _ = env.step(action)
            ep_reward += reward
            done = terminated or truncated
        rewards.append(ep_reward)

    print(f"📊 Avaliação ({eval_episodes} episódios):")
    print(f"  Recompensa média: {np.mean(rewards):.3f} ± {np.std(rewards):.3f}")
    print(f"  Melhor episódio: {np.max(rewards):.3f}")

    return np.mean(rewards)
