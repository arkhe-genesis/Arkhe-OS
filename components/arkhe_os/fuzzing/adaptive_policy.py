import numpy as np
import random
from collections import defaultdict, deque
from typing import Dict, List, Optional

class AdaptiveFuzzingPolicy:
    """RL-based policy for adapting fuzzing strategy — Substrato 259."""

    def __init__(self, state_dim: int = 10, action_dim: int = 4,
                 learning_rate: float = 0.01, discount: float = 0.99):
        self.state_dim = state_dim
        self.action_dim = action_dim  # One per MutationStrategy
        self.lr = learning_rate
        self.gamma = discount

        # Simple Q-table for demonstration (use DQN in production)
        self.q_table = np.zeros((100, action_dim))  # Discretized state space
        self.state_history = deque(maxlen=100)
        self.reward_history = deque(maxlen=100)

        # Strategy performance tracking
        self.strategy_stats = defaultdict(lambda: {
            'trials': 0, 'successes': 0, 'avg_reward': 0.0
        })

    def _discretize_state(self, fuzzing_stats: Dict) -> int:
        """Convert continuous stats to discrete state index."""
        # Features: coherence_avg, crash_rate, novelty_avg, iterations
        features = [
            fuzzing_stats.get('avg_coherence', 0.5) * 10,
            fuzzing_stats.get('crashes_found', 0) / max(1, fuzzing_stats.get('inputs_generated', 1)) * 10,
            fuzzing_stats.get('novel_paths', 0) / max(1, fuzzing_stats.get('inputs_generated', 1)) * 10,
            min(fuzzing_stats.get('inputs_generated', 0) / 100, 10)
        ]
        # Quantize to [0, 9] and combine
        discretized = [int(np.clip(f, 0, 9)) for f in features]
        return sum(d * (10 ** i) for i, d in enumerate(discretized)) % 100

    def select_strategy(self, fuzzing_stats: Dict, exploration: float = 0.1) -> int:
        """Select mutation strategy using ε-greedy policy."""
        state = self._discretize_state(fuzzing_stats)

        if random.random() < exploration:
            # Explore: random strategy
            return random.randint(0, self.action_dim - 1)
        else:
            # Exploit: best Q-value
            return int(np.argmax(self.q_table[state]))

    def update_policy(self, fuzzing_stats: Dict, action: int, reward: float):
        """Update Q-table based on observed reward."""
        state = self._discretize_state(fuzzing_stats)

        # Q-learning update
        current_q = self.q_table[state, action]
        # Simplified: next state is same (one-step update)
        max_next_q = np.max(self.q_table[state])
        self.q_table[state, action] = current_q + self.lr * (
            reward + self.gamma * max_next_q - current_q
        )

        # Update strategy stats
        self.strategy_stats[action]['trials'] += 1
        self.strategy_stats[action]['successes'] += 1 if reward > 0 else 0
        # Running average reward
        stats = self.strategy_stats[action]
        n = stats['trials']
        old_avg = stats['avg_reward']
        stats['avg_reward'] = (old_avg * (n - 1) + reward) / n

        # Record history
        self.state_history.append(state)
        self.reward_history.append(reward)

    def compute_reward(self, observation: Dict, coherence_delta: float) -> float:
        """Compute reward signal from execution observation."""
        reward = 0.0

        # Positive rewards
        if observation.get('crashed'):
            reward += 10.0  # High reward for crash discovery
        if coherence_delta < -0.1:
            reward += 2.0  # Moderate reward for coherence drop
        if observation.get('novelty_score', 0) > 0.5:
            reward += 1.0  # Small reward for novelty

        # Negative rewards (penalize unproductive mutations)
        if observation.get('success') and coherence_delta > 0.05:
            reward -= 0.5  # Slight penalty for "boring" inputs

        return reward

    def get_strategy_recommendations(self) -> Dict:
        """Generate human-readable strategy recommendations."""
        recommendations = {}
        for action, stats in self.strategy_stats.items():
            if stats['trials'] < 10:
                continue  # Insufficient data
            success_rate = stats['successes'] / stats['trials']
            recommendations[action] = {
                'success_rate': round(success_rate, 3),
                'avg_reward': round(stats['avg_reward'], 3),
                'trials': stats['trials'],
                'recommendation': 'INCREASE' if success_rate > 0.3 else
                                 'DECREASE' if success_rate < 0.1 else 'MAINTAIN'
            }
        return recommendations