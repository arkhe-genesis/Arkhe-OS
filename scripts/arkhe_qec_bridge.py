#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# scripts/arkhe_qec_bridge.py
# Bridge between Arkhé(N) and the NVIDIA Ising-Decoder

import os
import sys
import torch
import numpy as np
from pathlib import Path
from omegaconf import OmegaConf
from copy import deepcopy

# Add ising-decoding/code to path
REPO_ROOT = Path(__file__).resolve().parents[1]
ISING_CODE_DIR = REPO_ROOT / "ising-decoding" / "code"
sys.path.insert(0, str(ISING_CODE_DIR))

try:
    from model.factory import ModelFactory
    from workflows.config_validator import apply_public_defaults_and_model, validate_public_config
    from training.distributed import DistributedManager
    from evaluation.logical_error_rate import PreDecoderMemoryEvalModule, _build_stab_maps
except ImportError as e:
    print(f"Error: Could not import ising-decoding modules. {e}")
    sys.exit(1)

class ArkheQECBridge:
    def __init__(self, model_id=1, distance=7, n_rounds=7, checkpoint_path=None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Load and validate config
        cfg_path = REPO_ROOT / "ising-decoding" / "conf" / "config_public.yaml"
        self.cfg = OmegaConf.load(str(cfg_path))
        self.cfg.model_id = model_id
        self.cfg.distance = distance
        self.cfg.n_rounds = n_rounds
        self.cfg.workflow.task = "inference"

        model_spec = validate_public_config(self.cfg)
        self.cfg = apply_public_defaults_and_model(self.cfg, model_spec)

        # Load model
        if checkpoint_path is None:
            # Default to Fast model for R=9, Accurate for R=13
            if model_spec.receptive_field == 9:
                checkpoint_path = REPO_ROOT / "ising-decoding" / "models" / "Ising-Decoder-SurfaceCode-1-Fast.pt"
            else:
                checkpoint_path = REPO_ROOT / "ising-decoding" / "models" / "Ising-Decoder-SurfaceCode-1-Accurate.pt"

        self.model = ModelFactory.create_model(self.cfg).to(self.device)
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Model weights not found at {checkpoint_path}. Please download them using 'git lfs pull' or manually.")

        state_dict = torch.load(checkpoint_path, map_location=self.device, weights_only=True)
        if isinstance(state_dict, dict) and "model_state_dict" in state_dict:
            state_dict = state_dict["model_state_dict"]
        # Strip DDP prefix if present
        state_dict = {(k[len("module."):] if k.startswith("module.") else k): v for k, v in state_dict.items()}
        self.model.load_state_dict(state_dict)
        self.model.eval()

        # Initialize evaluation module for X and Z bases
        self.maps = _build_stab_maps(distance, self.cfg.data.code_rotation)

        self.eval_modules = {}
        for basis in ["X", "Z"]:
            basis_cfg = deepcopy(self.cfg)
            basis_cfg.test.meas_basis_test = basis
            self.eval_modules[basis] = PreDecoderMemoryEvalModule(self.model, basis_cfg, self.maps, self.device).to(self.device)
            self.eval_modules[basis].eval()

    @torch.inference_mode()
    def process_syndrome(self, syndrome_bits, basis="X"):
        """
        Process a syndrome through the neural pre-decoder.

        Args:
            syndrome_bits: numpy array or torch tensor of shape (B, 2*T*half)
            basis: "X" or "Z"

        Returns:
            dict with 'pre_L' and 'residual'
        """
        if isinstance(syndrome_bits, np.ndarray):
            syndrome_bits = torch.from_numpy(syndrome_bits)

        syndrome_bits = syndrome_bits.to(self.device).to(torch.uint8)
        if syndrome_bits.ndim == 1:
            syndrome_bits = syndrome_bits.unsqueeze(0)

        output = self.eval_modules[basis](syndrome_bits)

        # Output format from PreDecoderMemoryEvalModule is [pre_L, residual...]
        pre_L = output[:, 0].cpu().numpy()
        residual = output[:, 1:].cpu().numpy()

        return {
            "pre_L": pre_L,
            "residual": residual
        }

if __name__ == "__main__":
    # Simple test
    bridge = ArkheQECBridge(model_id=1, distance=7, n_rounds=7)
    print("Bridge initialized successfully.")

    # Dummy syndrome (all zeros)
    half = (7*7 - 1) // 2
    dummy_syndrome = np.zeros((1, 2 * 7 * half), dtype=np.uint8)
    res = bridge.process_syndrome(dummy_syndrome, basis="X")
    print(f"Pre-L: {res['pre_L']}")
    print(f"Residual shape: {res['residual'].shape}")
