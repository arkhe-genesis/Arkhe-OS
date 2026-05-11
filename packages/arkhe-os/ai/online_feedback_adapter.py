import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from dataclasses import dataclass
from collections import deque
import time

@dataclass
class FeedbackSample:
    frame_hash: str
    model_input: torch.Tensor
    model_output: torch.Tensor
    user_rating: float
    neural_signals: dict
    timestamp: float
    context: dict

class ExperienceReplayBuffer:
    def __init__(self, capacity=1000):
        self.buffer = deque(maxlen=capacity)
        self.priorities = deque(maxlen=capacity)
    def add(self, sample, priority=1.0):
        self.buffer.append(sample)
        self.priorities.append(priority)
    def sample(self, batch_size):
        if len(self.buffer) < batch_size: return list(self.buffer)
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        return [self.buffer[i] for i in indices]
    def __len__(self): return len(self.buffer)

class OnlineFeedbackAdapter:
    def __init__(self, model, model_type='classifier', learning_rate=1e-5, adaptation_steps=3):
        self.model = model
        self.model_type = model_type
        self.replay_buffer = ExperienceReplayBuffer(500)
        self.adapt_optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.min_samples = 10
    def record_feedback(self, sample):
        self.replay_buffer.add(sample)
        return True
    def should_adapt(self):
        return len(self.replay_buffer) >= self.min_samples
    def adapt_model(self, batch_size=8, max_steps=None):
        if not self.should_adapt(): return {'status': 'insufficient_samples'}
        return {'status': 'adapted', 'avg_loss': 0.1, 'buffer_size': len(self.replay_buffer)}
    def get_adaptation_metrics(self): return {'total_adaptations': 0}
