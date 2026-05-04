import asyncio
import random
import torch
from typing import Dict
from .arkhe_cathedral import CliffordBiocomputer

class MonsterMind:
    def __init__(self, monster_id: str, monster_type: str):
        self.id = monster_id
        self.type = monster_type
        self.cathedral = CliffordBiocomputer(input_dim=16, cell_dim=16)
        self.position = {"x": 0.0, "y": 0.0}

    def _observe_environment(self, player_pos: Dict) -> torch.Tensor:
        obs = torch.zeros(1, 16)
        dx = player_pos['x'] - self.position['x']
        dy = player_pos['y'] - self.position['y']
        obs[0, 0] = dx / 1000.0
        obs[0, 1] = dy / 1000.0
        return obs

    async def pulse(self, player_pos: Dict):
        input_signal = self._observe_environment(player_pos)
        action_vector, states = self.cathedral(input_signal)
        energy = states['energy'].item()
        hesitation = states['hesitation'].item()
        if energy > 0.8: intent = "aggressive_pursuit"
        elif hesitation > 0.5: intent = "hesitant_observation"
        else: intent = "idle_drift"
        print(f"[Monstro:{self.id}] Intent: {intent} | Power: {action_vector.norm().item():.4f}")

async def monster_simulation():
    monsters = [MonsterMind("m-01", "STONE_WORM")]
    player_pos = {"x": 500.0, "y": 500.0}
    for _ in range(3):
        for m in monsters: await m.pulse(player_pos)
        await asyncio.sleep(0.1)

if __name__ == "__main__":
    asyncio.run(monster_simulation())
