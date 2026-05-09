#!/usr/bin/env python3
"""
harvester.py — Recolhe grafos LFIR de todos os substratos
"""
import os
import json
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any
import torch
from dataset import LFIRDataset

class LFIRHarvester:
    def __init__(self, storage_root="/var/lib/agi/training_data"):
        self.storage = Path(storage_root)
        self.storage.mkdir(parents=True, exist_ok=True)
        self.index = []  # lista de metadados

    def harvest_from_substrate(self, substrate_id: int, graph_generator):
        """Invoca o parser do substrato e guarda o grafo."""
        graph = graph_generator()  # ex: parse_agent_spec()
        if not graph:
            return

        example = {
            "graph_id": f"sub_{substrate_id}_{int(time.time())}",
            "source_substrate": substrate_id,
            "timestamp": time.time(),
            "intent": graph.get("intent", "unknown"),
            "coherence_score": graph.get("metrics", {}).get("coherence_score", 0.5),
            "lfir_graph": graph
        }
        self._save_example(example)

    def _save_example(self, example: Dict[str, Any]):
        fname = self.storage / f"{example['graph_id']}.json"
        with open(fname, 'w') as f:
            json.dump(example, f)

        self.index.append({
            "file": str(fname),
            "coherence": example["coherence_score"],
            "substrate": example["source_substrate"]
        })

    def build_dataset(self, tokenizer, max_seq_len=16384) -> torch.utils.data.Dataset:
        """Converte exemplos armazenados para um Dataset PyTorch."""
        return LFIRDataset(self.storage, self.index, tokenizer, max_seq_len)
