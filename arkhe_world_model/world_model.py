import numpy as np
import torch
import torch.nn as nn
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from enum import Enum

class MaturityLevel(Enum):
    EMBRYO = "embryo"
    INFANT = "infant"
    ADULT = "adult"

class DevelopmentStage(Enum):
    TOKEN_GROUNDING = 1
    PHYSICS_PRIORS = 2
    MULTIMODAL_FUSION = 3
    EMBODIED_SIMULATION = 4
    CAUSAL_REASONING = 5
    SELF_MODELING = 6

@dataclass
class WorldModelConfig:
    maturity: MaturityLevel = MaturityLevel.EMBRYO
    d_model: int = 512
    state_dim: int = 256
    n_vars: int = 10
    vocab_size: int = 32000
    max_seq_len: int = 4096

    lambda_ce: float = 1.0
    lambda_mse: float = 0.5
    lambda_causal: float = 0.3

    sim_dt: float = 0.02
    sim_substeps: int = 10
    sim_scene: str = "pendulum"

    batch_size: int = 32
    learning_rate: float = 1e-4
    max_epochs: int = 100

    rl_algorithm: str = "ppo"
    rl_timesteps: int = 100000

class WorldModelEmbryo(nn.Module):
    def __init__(self, config: Optional[WorldModelConfig] = None):
        super().__init__()
        self.config = config or WorldModelConfig()
        self.maturity = self.config.maturity
        self.active_stages = self._get_active_stages()

        self._llm_engine = None
        self._physics_priors = None
        self._multimodal_fusion = None
        self._simulator = None
        self._causal_reasoner = None
        self._self_model = None

        self._current_stage = DevelopmentStage.TOKEN_GROUNDING
        self._training_history: List[Dict] = []
        self._is_trained = False

        # adding dummy parameter to make model have at least 1 parameter
        self.dummy_param = nn.Parameter(torch.tensor([1.0], requires_grad=True))

    def _get_active_stages(self) -> List[DevelopmentStage]:
        if self.maturity == MaturityLevel.EMBRYO:
            return [
                DevelopmentStage.TOKEN_GROUNDING,
                DevelopmentStage.PHYSICS_PRIORS,
            ]
        elif self.maturity == MaturityLevel.INFANT:
            return [
                DevelopmentStage.TOKEN_GROUNDING,
                DevelopmentStage.PHYSICS_PRIORS,
                DevelopmentStage.MULTIMODAL_FUSION,
                DevelopmentStage.EMBODIED_SIMULATION,
            ]
        else:  # ADULT
            return list(DevelopmentStage)

    @property
    def llm_engine(self):
        if self._llm_engine is None:
            from .llm_engine import ArkheLLMEngine
            self._llm_engine = ArkheLLMEngine(
                model_path="models/arkhe-os.gguf",
                n_ctx=self.config.max_seq_len,
            )
        return self._llm_engine

    @property
    def physics_priors(self):
        if self._physics_priors is None:
            from .physics_priors import PhysicsPriorsModule
            self._physics_priors = PhysicsPriorsModule(
                d_model=self.config.d_model,
                state_dim=self.config.state_dim,
            )
        return self._physics_priors

    @property
    def multimodal_fusion(self):
        if self._multimodal_fusion is None:
            from .multimodal_fusion import MultimodalFusionModule
            self._multimodal_fusion = MultimodalFusionModule(
                d_model=self.config.d_model,
                state_dim=self.config.state_dim,
            )
        return self._multimodal_fusion

    @property
    def simulator(self):
        if self._simulator is None:
            from .brax_simulator import ArkheBraxSimulator
            self._simulator = ArkheBraxSimulator(
                scene=self.config.sim_scene,
            )
        return self._simulator

    @property
    def causal_reasoner(self):
        if self._causal_reasoner is None:
            from .causal_reasoning import ArkheCausalReasoner
            self._causal_reasoner = ArkheCausalReasoner(
                n_vars=self.config.n_vars,
            )
        return self._causal_reasoner

    @property
    def self_model(self):
        if self._self_model is None:
            from .self_model import SelfModelingModule
            self._self_model = SelfModelingModule(
                d_model=self.config.d_model,
            )
        return self._self_model

    def forward(
        self,
        text_input: str,
        visual_input: Optional[np.ndarray] = None,
        action: Optional[np.ndarray] = None,
    ) -> Dict[str, np.ndarray]:
        outputs = {}

        if DevelopmentStage.TOKEN_GROUNDING in self.active_stages:
            text, llm_emb = self.llm_engine.generate(text_input, max_tokens=256)
            grounding_2d = self.llm_engine.token_grounding_2d(llm_emb)
            outputs["stage1"] = {
                "text": text,
                "embedding": llm_emb,
                "grounding_2d": grounding_2d,
            }

        if DevelopmentStage.PHYSICS_PRIORS in self.active_stages:
            physics_emb = self.physics_priors(llm_emb)
            outputs["stage2"] = {
                "physics_embedding": physics_emb,
            }

        if DevelopmentStage.MULTIMODAL_FUSION in self.active_stages:
            fused_emb = self.multimodal_fusion(
                text_emb=llm_emb,
                visual_emb=visual_input,
                physics_emb=physics_emb if DevelopmentStage.PHYSICS_PRIORS in self.active_stages else None,
            )
            outputs["stage3"] = {
                "fused_embedding": fused_emb,
            }

        if DevelopmentStage.EMBODIED_SIMULATION in self.active_stages:
            sim_state = self.simulator.reset()
            if action is not None:
                sim_state = self.simulator.step(sim_state, action)
            world_emb = self.simulator.get_world_embedding(sim_state)
            outputs["stage4"] = {
                "sim_state": sim_state,
                "world_embedding": world_emb,
            }

        if DevelopmentStage.CAUSAL_REASONING in self.active_stages:
            causal_data = world_emb[:self.config.n_vars].reshape(1, -1)
            if self.causal_reasoner.is_trained:
                factual, counter = self.causal_reasoner.counterfactual(
                    var_idx=0, value=1.0, observed=causal_data[0]
                )
                outputs["stage5"] = {
                    "factual": factual,
                    "counterfactual": counter,
                }

        if DevelopmentStage.SELF_MODELING in self.active_stages:
            self_emb = self.self_model(fused_emb if DevelopmentStage.MULTIMODAL_FUSION in self.active_stages else llm_emb)
            outputs["stage6"] = {
                "self_embedding": self_emb,
            }

        return outputs

    def predict(
        self,
        text_input: str,
        visual_input: Optional[np.ndarray] = None,
        action: Optional[np.ndarray] = None,
    ) -> Dict[str, np.ndarray]:
        self.eval()
        with torch.no_grad():
            return self.forward(text_input, visual_input, action)

    def save(self, path: str):
        checkpoint = {
            "config": self.config,
            "maturity": self.maturity.value,
            "state_dict": self.state_dict(),
            "training_history": self._training_history,
            "is_trained": self._is_trained,
            "substrate": "890",
            "seal": __import__("os").environ.get("ARKHE_SEAL"),
        }
        torch.save(checkpoint, path)

    def load(self, path: str):
        checkpoint = torch.load(path, weights_only=True)
        self.load_state_dict(checkpoint["state_dict"])
        self._training_history = checkpoint.get("training_history", [])
        self._is_trained = checkpoint.get("is_trained", False)
