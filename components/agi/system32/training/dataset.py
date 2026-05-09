#!/usr/bin/env python3
"""
dataset.py — Carregamento de batches para treino do Transformer AGI
"""
import torch
import json
from pathlib import Path
from typing import List, Dict

class LFIRDataset(torch.utils.data.Dataset):
    def __init__(self, storage: Path, index: List[Dict], tokenizer, max_len=16384):
        self.storage = storage
        self.index = index
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.index)

    def __getitem__(self, idx):
        meta = self.index[idx]
        with open(Path(meta["file"]), 'r') as f:
            example = json.load(f)
        graph = example["lfir_graph"]

        # Tokenizar o grafo inteiro como sequência de entrada
        src_tokens = self.tokenizer.tokenize_graph(graph)

        # Para treino auto‑regressivo, o target é a própria sequência deslocada
        tgt_input = src_tokens[:-1]
        tgt_output = src_tokens[1:]

        # Padding/máscara
        src_len = src_tokens.size(0)
        if src_len < self.max_len:
            pad = torch.full((self.max_len - src_len,), self.tokenizer.SPECIAL_TOKENS['[PAD]'], dtype=torch.long)
            src_tokens = torch.cat([src_tokens, pad])
            tgt_input = torch.cat([tgt_input, pad[:-1] if pad.size(0) > 0 else pad])
            tgt_output = torch.cat([tgt_output, pad[:-1] if pad.size(0) > 0 else pad])
            # Handle tgt_input and tgt_output sizes correctly when adding padding
            tgt_input = src_tokens[:-1]
            tgt_output = src_tokens[1:]
        else:
            src_tokens = src_tokens[:self.max_len]
            tgt_input = tgt_input[:self.max_len-1]
            tgt_output = tgt_output[:self.max_len-1]

        # Coerência alvo (para o termo de perda)
        target_coherence = example.get("coherence_score", 0.5)

        return {
            "src": src_tokens,
            "tgt_input": tgt_input,
            "tgt_output": tgt_output,
            "target_coherence": torch.tensor(target_coherence, dtype=torch.float),
            "coherence_matrix": self._build_coherence_matrix(graph, src_tokens)
        }

    def _build_coherence_matrix(self, graph, src_tokens):
        # Matriz esparsa que indica conexões do LFIR (1 se conectados, 0 caso contrário)
        seq_len = src_tokens.size(0)
        mat = torch.zeros(seq_len, seq_len)
        # Mapeamento aproximado: usar posições dos nós no grafo
        # (implementação real: parsear tokens para extrair conexões)
        return mat
