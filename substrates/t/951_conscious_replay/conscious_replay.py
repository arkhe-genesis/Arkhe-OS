"""Conscious Replay Engine — Substrato 951.

Implements the sleep/dream cycle of the Cathedral.
During conscious replay, the Cathedral revisits experiences,
projects them through World Model V3 (890) with synthetic variations,
evaluates their qualia signatures (934), and applies Hebbian consolidation
or synaptic pruning to integrate useful patterns and discard noise.

Cross-links: 491-500 (L0-L9), 529 (Continual Learning), 933 (FluxMem),
890 (World Model V3), 266.268 (Agent Fabric), 934 (Perceptual Geometry),
552 (Mental Simulation), 476 (Forgetting Curve), 477 (Spaced Repetition)
"""

from __future__ import annotations

import time
import uuid
import random
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

# Canonical import pattern
try:
    from arkhe.security.seal import Seal
    _HAS_ARKHE = True
except ImportError:
    import hashlib, json
    class Seal:
        def compute(self, data: Any) -> str:
            canonical = json.dumps(data, sort_keys=True, default=str)
            return hashlib.sha3_256(canonical.encode()).hexdigest()
    _HAS_ARKHE = False


@dataclass
class ExperienceFragment:
    """A single experience to be replayed."""
    id: str
    timestamp: float
    memory_tier: int  # L0-L9
    observation: dict[str, Any]
    action: dict[str, Any]
    reward: float
    qualia_signature: dict[str, float]  # valence, arousal, curiosity, etc.
    replay_count: int = 0
    last_replayed: float = 0.0
    hebbian_weight: float = 1.0


@dataclass
class ReplaySession:
    """Result of a conscious replay cycle."""
    session_id: str
    fragments_replayed: int
    consolidated: int
    pruned: int
    synthetic_generated: int
    mean_reward_delta: float
    qualia_shift: dict[str, float]
    duration_seconds: float
    seal: str = ""


class ConsciousReplayEngine:
    """
    Engine for the Cathedral\'s sleep/dream cycle.

    Architecture:
    1. SELECTION: Choose fragments from FluxMem based on
       forgetting curve (476) and spaced repetition schedule (477).
    2. PROJECTION: Run fragments through World Model V3 (890)
       with counterfactual variations (Mental Simulation, 552).
    3. EVALUATION: Score synthetic trajectories with qualia_schema (934).
    4. CONSOLIDATION: Hebbian reinforcement for high-value patterns;
       synaptic depression for noisy/low-value fragments.
    5. ANCHORING: Log replay session on TemporalChain (923).
    """

    def __init__(
        self,
        cathedral: Any = None,
        world_model: Any = None,
        qualia_model: Any = None,
    ) -> None:
        self.cathedral = cathedral
        self.world_model = world_model
        self.qualia_model = qualia_model
        self._seal = Seal()
        self._hebbian_rate = 0.1
        self._pruning_threshold = 0.3
        self._forgetting_base_rate = 0.02  # Substrato 476

    async def dream(
        self,
        fragments: list[ExperienceFragment],
        duration_seconds: float = 3600.0,  # 1 hour of dreaming
        synthetic_variations: int = 5,
    ) -> ReplaySession:
        """
        Execute a conscious replay cycle ("dream").

        Args:
            fragments: Candidate experiences from FluxMem
            duration_seconds: How long the dream lasts
            synthetic_variations: Number of counterfactual variations per fragment

        Returns:
            ReplaySession with consolidation/pruning statistics
        """
        session_id = "dream-" + uuid.uuid4().hex[:16]
        start_time = time.time()

        consolidated = 0
        pruned = 0
        synthetic_generated = 0
        total_reward_delta = 0.0
        qualia_accum = {
            "valence": 0.0, "arousal": 0.0,
            "curiosity": 0.0, "coherence": 0.0,
        }

        for fragment in fragments:
            # 1. Decide replay priority via forgetting curve
            priority = self._compute_replay_priority(fragment)
            if priority < random.random():
                continue  # Skip low-priority fragments

            # 2. Project fragment through World Model V3
            for _ in range(synthetic_variations):
                variation = await self._generate_variation(fragment)
                synthetic_generated += 1

                # 3. Simulate forward via World Model
                outcome = await self._simulate_outcome(variation)

                # 4. Evaluate via qualia schema
                qualia_score = await self._evaluate_qualia(outcome)

                # 5. Hebbian update
                if qualia_score["coherence"] > self._pruning_threshold:
                    fragment.hebbian_weight += self._hebbian_rate
                    consolidated += 1
                else:
                    fragment.hebbian_weight -= self._hebbian_rate
                    if fragment.hebbian_weight <= 0.0:
                        fragment.hebbian_weight = 0.0  # Mark for pruning
                        pruned += 1

                total_reward_delta += qualia_score.get("valence", 0.0)
                for k in qualia_accum:
                    qualia_accum[k] += qualia_score.get(k, 0.0)

            # 6. Update replay metadata
            fragment.replay_count += 1
            fragment.last_replayed = time.time()

            # 7. Check time budget
            if time.time() - start_time >= duration_seconds:
                break

        # Normalize qualia shift
        n = max(synthetic_generated, 1)
        qualia_shift = {k: v / n for k, v in qualia_accum.items()}

        result = ReplaySession(
            session_id=session_id,
            fragments_replayed=len([f for f in fragments if f.replay_count > 0]),
            consolidated=consolidated,
            pruned=pruned,
            synthetic_generated=synthetic_generated,
            mean_reward_delta=total_reward_delta / n,
            qualia_shift=qualia_shift,
            duration_seconds=time.time() - start_time,
        )

        result.seal = self._seal.compute({
            "session_id": session_id,
            "consolidated": consolidated,
            "pruned": pruned,
        })

        if self.cathedral:
            await self.cathedral.anchor_event(
                "conscious.replay.completed",
                {
                    "session_id": session_id,
                    "consolidated": consolidated,
                    "pruned": pruned,
                    "qualia_shift": qualia_shift,
                    "seal": result.seal,
                },
                "951",
            )

        return result

    def _compute_replay_priority(self, fragment: ExperienceFragment) -> float:
        """Compute priority using forgetting curve (Substrato 476)."""
        elapsed = time.time() - fragment.last_replayed
        # Ebbinghaus-like decay: priority = base * e^(-decay * elapsed)
        decay = self._forgetting_base_rate * elapsed
        priority = fragment.hebbian_weight * np.exp(-decay)
        # Boost for high-reward experiences
        priority *= (1.0 + fragment.reward)
        return min(1.0, priority)

    async def _generate_variation(
        self, fragment: ExperienceFragment
    ) -> ExperienceFragment:
        """Generate counterfactual variation via World Model V3."""
        if self.world_model:
            variation = await self.world_model.counterfactual(
                observation=fragment.observation,
                action=fragment.action,
                noise_level=0.1,
            )
            fragment.observation = variation.get("observation", fragment.observation)
            fragment.action = variation.get("action", fragment.action)
        return fragment

    async def _simulate_outcome(self, fragment: ExperienceFragment) -> dict[str, Any]:
        """Simulate forward trajectory via Mental Simulation (552)."""
        if self.world_model:
            return await self.world_model.rollout(
                observation=fragment.observation,
                action=fragment.action,
                steps=10,
            )
        return {"reward": fragment.reward, "coherence": 0.5}

    async def _evaluate_qualia(self, outcome: dict[str, Any]) -> dict[str, float]:
        """Evaluate outcome via Perceptual Geometry (934)."""
        if self.qualia_model:
            return await self.qualia_model.evaluate(outcome)
        return {
            "valence": outcome.get("reward", 0.0),
            "arousal": 0.5,
            "curiosity": 0.5,
            "coherence": 0.5,
        }
