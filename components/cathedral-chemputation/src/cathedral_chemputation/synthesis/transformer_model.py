"""
transformer_model.py — Modelo Transformer para retrossíntese diferenciável
Baseado em arquitetura encoder-decoder com atenção multi‑head
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

@dataclass
class ReactionPrediction:
    """Predição de reação retrossintética."""
    reactants: List[str]  # Lista de SMILES dos reagentes previstos
    probability: float    # Probabilidade da transformação
    conditions: Optional[List[str]] = None  # Condições de reação (catalisador, solvente, temperatura)
    template_id: Optional[str] = None  # ID do template de reação usado

class RetrosynthesisTransformer(nn.Module):
    """
    Transformer para previsão de desconexões retrossintéticas.
    """

    def __init__(
        self,
        vocab_size: int = 512,
        d_model: int = 512,
        nhead: int = 8,
        num_encoder_layers: int = 6,
        num_decoder_layers: int = 6,
        dim_feedforward: int = 2048,
        dropout: float = 0.1,
        max_seq_len: int = 256,
    ):
        super().__init__()

        self.d_model = d_model
        self.max_seq_len = max_seq_len

        # Embeddings
        self.product_embedding = nn.Embedding(vocab_size, d_model)
        self.reactant_embedding = nn.Embedding(vocab_size, d_model)
        self.positional_encoding = PositionalEncoding(d_model, dropout, max_seq_len)

        # Transformer
        self.transformer = nn.Transformer(
            d_model=d_model,
            nhead=nhead,
            num_encoder_layers=num_encoder_layers,
            num_decoder_layers=num_decoder_layers,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
        )

        # Output
        self.output_projection = nn.Linear(d_model, vocab_size)

        # Gumbel‑Softmax temperature (para diferenciabilidade)
        self.temperature = 1.0

    def forward(
        self,
        product_tokens: torch.Tensor,  # (batch, seq_len)
        reactant_tokens: Optional[torch.Tensor] = None,  # (batch, seq_len) para teacher forcing
        return_logits: bool = True,
    ) -> torch.Tensor:
        """
        Forward pass do transformer de retrossíntese.
        """
        batch_size, seq_len = product_tokens.shape

        # Embeddings + positional encoding
        product_emb = self.product_embedding(product_tokens) * math.sqrt(self.d_model)
        product_emb = self.positional_encoding(product_emb)

        if reactant_tokens is not None:
            # Teacher forcing
            reactant_emb = self.reactant_embedding(reactant_tokens) * math.sqrt(self.d_model)
            reactant_emb = self.positional_encoding(reactant_emb)
            tgt_mask = self.transformer.generate_square_subsequent_mask(reactant_tokens.size(1))
            output = self.transformer(src=product_emb, tgt=reactant_emb, tgt_mask=tgt_mask)
        else:
            # Inferência
            memory = self.transformer.encoder(product_emb)
            output = memory.unsqueeze(1).expand(-1, self.max_seq_len, -1)

        # Projeção para vocabulário
        logits = self.output_projection(output)

        if return_logits:
            return logits

        # Aplicar Gumbel‑Softmax para tornar a saída diferenciável
        return F.gumbel_softmax(logits, tau=self.temperature, hard=False, dim=-1)

    def predict_reactions(
        self,
        product_smiles: str,
        tokenizer,
        top_k: int = 10,
        temperature: float = 1.0,
    ) -> List[ReactionPrediction]:
        """Prediz reações retrossintéticas para um produto."""
        self.eval()
        self.temperature = temperature
        tokens = tokenizer.encode(product_smiles).unsqueeze(0)

        with torch.no_grad():
            logits = self.forward(tokens, return_logits=True)
            predictions = []
            for k in range(top_k):
                reactant_tokens = []
                for pos in range(self.max_seq_len):
                    pos_logits = logits[0, pos, :]
                    if k == 0:
                        token_id = pos_logits.argmax().item()
                    else:
                        probs = F.softmax(pos_logits / temperature, dim=-1)
                        token_id = torch.multinomial(probs, 1).item()

                    if token_id == tokenizer.eos_token_id:
                        break
                    reactant_tokens.append(token_id)

                reactant_smiles = tokenizer.decode(reactant_tokens)
                predictions.append(ReactionPrediction(
                    reactants=[reactant_smiles],
                    probability=0.85 - (k * 0.05), # Mock probability
                ))

        return predictions

    def differentiable_predict(
        self,
        product_emb: torch.Tensor,
        num_samples: int = 5,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Predição diferenciável usando Gumbel‑Softmax."""
        self.train()
        batch_size = product_emb.size(0)
        product_tokens = torch.zeros(batch_size, 1, dtype=torch.long, device=product_emb.device)

        gumbel_samples = []
        for _ in range(num_samples):
            probs = self.forward(product_tokens, return_logits=False)
            gumbel_samples.append(probs)

        gumbel_samples = torch.stack(gumbel_samples, dim=0)
        reactant_logits = gumbel_samples.mean(dim=0)
        return reactant_logits, gumbel_samples


class PositionalEncoding(nn.Module):
    """Codificação posicional para o Transformer."""

    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        pe = torch.zeros(max_len, 1, d_model)
        pe[:, 0, 0::2] = torch.sin(position * div_term)
        pe[:, 0, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:x.size(0)]
        return self.dropout(x)
