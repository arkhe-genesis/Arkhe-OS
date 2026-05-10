import torch
import torch.nn as nn
import torch.nn.functional as F
import math

# ----------------------------------------------------------------------
# 🜏 Hypernetwork Module
# ----------------------------------------------------------------------
class HyperNetwork(nn.Module):
    """
    Takes a set of "operator token" embeddings (context) and outputs
    a small adapter (a linear transformation) that will be used later
    in the same forward pass.
    """
    def __init__(self, embed_dim, adapter_dim, hidden_dim=64):
        super().__init__()
        # Project operator token embeddings to a small hidden vector
        self.fc1 = nn.Linear(embed_dim, hidden_dim)
        # Then produce the weight matrix and bias for the adapter
        # We generate a simple linear layer: adapter(x) = W * x + b
        # Weight shape: (adapter_dim, embed_dim)
        self.fc_W = nn.Linear(hidden_dim, adapter_dim * embed_dim)
        self.fc_b = nn.Linear(hidden_dim, adapter_dim)

    def forward(self, operator_tokens):
        """
        operator_tokens: (batch, num_operators, embed_dim)
        Returns: (W, b) for a linear adapter of shape (adapter_dim, embed_dim)
        """
        # Pool operator tokens (e.g., mean) to get a single vector
        op_mean = operator_tokens.mean(dim=1)   # (batch, embed_dim)
        hidden = torch.relu(self.fc1(op_mean))   # (batch, hidden_dim)

        # Generate weight and bias
        W_flat = self.fc_W(hidden)              # (batch, adapter_dim * embed_dim)
        b = self.fc_b(hidden)                  # (batch, adapter_dim)

        # Reshape weight to (batch, adapter_dim, embed_dim)
        W = W_flat.view(-1, adapter_dim, operator_tokens.size(-1))
        return W, b

# ----------------------------------------------------------------------
# 🜏 Minimal Transformer with Hypernetwork-in-Inference
# ----------------------------------------------------------------------
class HypernetTransformer(nn.Module):
    """
    A small transformer that implements the "Intelligence Composing Itself" pattern.
    - Takes a sequence of tokens (including special "operator tokens").
    - Uses the operator tokens to generate a hypernetwork (adapter).
    - Applies that adapter to the final hidden states during inference.
    """
    def __init__(self, vocab_size, embed_dim=64, num_heads=4, num_layers=3,
                 max_seq_len=32, adapter_dim=64):
        super().__init__()
        self.embed_dim = embed_dim
        self.token_embedding = nn.Embedding(vocab_size, embed_dim)
        self.pos_embedding = nn.Embedding(max_seq_len, embed_dim)

        # Transformer encoder layers
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim, nhead=num_heads, batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # Hypernetwork that generates an adapter
        self.hypernet = HyperNetwork(embed_dim, adapter_dim)

        # Output layer: first the adapter is applied, then a final linear to vocab
        self.out_proj = nn.Linear(adapter_dim, vocab_size)

    def forward(self, input_ids, operator_mask):
        """
        input_ids: (batch, seq_len) – token indices.
        operator_mask: (batch, seq_len) – 1 for positions that are "operator tokens",
                      0 otherwise. The hypernetwork will be built from the embeddings
                      at positions where operator_mask == 1.
        """
        B, S = input_ids.shape

        # Token + position embeddings
        positions = torch.arange(S, device=input_ids.device).unsqueeze(0).expand(B, S)
        x = self.token_embedding(input_ids) + self.pos_embedding(positions)

        # Pass through transformer
        x = self.transformer(x)                     # (B, S, embed_dim)

        # Extract operator tokens (where mask == 1)
        # Using a safer extraction that handles batch indexing
        operator_embeds = []
        for i in range(B):
            mask = operator_mask[i] > 0
            if mask.any():
                operator_embeds.append(x[i, mask])
            else:
                # Fallback: mean of all tokens if no operator specified
                operator_embeds.append(x[i].mean(dim=0, keepdim=True))

        # Standardize operator context
        operator_context = torch.stack([e.mean(dim=0, keepdim=True) for e in operator_embeds]).squeeze(1)
        # Add a dummy dimension for the hypernet's pooling
        operator_context = operator_context.unsqueeze(1) # (B, 1, embed_dim)

        # Generate adapter from operator tokens
        W, b = self.hypernet(operator_context)        # W: (B, adapter_dim, embed_dim), b: (B, adapter_dim)

        # Apply adapter to the last hidden state
        last_hidden = x[:, -1, :]                    # (B, embed_dim)

        # Reshape for batch matrix multiplication
        adapted = torch.bmm(W, last_hidden.unsqueeze(-1)).squeeze(-1) + b  # (B, adapter_dim)

        # Final projection to vocabulary
        logits = self.out_proj(adapted)              # (B, vocab_size)
        return logits

# 🜏 Synthesis logic for PNT or sequences
if __name__ == "__main__":
    print("🜏 Hypernet Transformer Module Initialized.")
    # Example instantiation
    model = HypernetTransformer(vocab_size=1000)
    print(f"Model Parameters: {sum(p.numel() for p in model.parameters())}")
