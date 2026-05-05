import torch
import torch.nn as nn
from typing import Dict, List
import copy

class FederatedPersonalizationEngine:
    """
    Manages federated model updates from multiple BCI users.
    Applies differential privacy via Laplacian noise to user gradients/weights
    before aggregating them, ensuring raw data is not exposed.
    """
    def __init__(self, global_model: nn.Module, epsilon: float = 1.0, sensitivity: float = 0.1):
        self.global_model = global_model
        self.epsilon = epsilon
        self.sensitivity = sensitivity
        self.user_updates: List[Dict[str, torch.Tensor]] = []

    def _add_laplacian_noise(self, tensor: torch.Tensor) -> torch.Tensor:
        """
        Adds Laplacian noise for differential privacy.
        Scale = sensitivity / epsilon
        """
        scale = self.sensitivity / self.epsilon
        # torch.distributions.Laplace is an alternative, but we can do it manually for simplicity:
        noise = torch.tensor(
            torch.distributions.Laplace(0, scale).sample(tensor.shape),
            dtype=tensor.dtype,
            device=tensor.device
        )
        return tensor + noise

    def receive_user_update(self, user_model_state_dict: Dict[str, torch.Tensor]) -> None:
        """
        Receives an update from a user, adds differential privacy noise, and stores it.
        """
        noisy_update = {}
        for name, param in user_model_state_dict.items():
            if param.dtype.is_floating_point:
                noisy_update[name] = self._add_laplacian_noise(param.clone())
            else:
                noisy_update[name] = param.clone()
        self.user_updates.append(noisy_update)

    def aggregate_updates(self) -> None:
        """
        Aggregates all received user updates into the global model (FedAvg).
        """
        if not self.user_updates:
            return

        # Initialize the new state dict with zeros
        new_state_dict = copy.deepcopy(self.global_model.state_dict())
        for name in new_state_dict.keys():
            if new_state_dict[name].dtype.is_floating_point:
                new_state_dict[name].zero_()

        # Sum up all the updates
        num_updates = len(self.user_updates)
        for update in self.user_updates:
            for name, param in update.items():
                if param.dtype.is_floating_point:
                    new_state_dict[name] += param

        # Average them
        for name in new_state_dict.keys():
            if new_state_dict[name].dtype.is_floating_point:
                new_state_dict[name] /= float(num_updates)

        # Load back into global model
        self.global_model.load_state_dict(new_state_dict)

        # Clear the buffer
        self.user_updates.clear()
