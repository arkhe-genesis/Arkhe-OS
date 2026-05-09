import torch
import torch.nn as nn
from transformers import PreTrainedModel, PretrainedConfig
from typing import Optional, Tuple, Dict

class CoherenceAwareConfig(PretrainedConfig):
    """Configuração para transformer consciente de coerência."""
    model_type = "coherence_aware_transformer"

    def __init__(
        self,
        vocab_size: int = 50265,  # CodeBERT-like
        hidden_size: int = 768,
        num_hidden_layers: int = 12,
        num_attention_heads: int = 12,
        intermediate_size: int = 3072,
        max_position_embeddings: int = 512,
        latent_dim: int = 256,     # Dimensão do espaço latente para difusão
        coherence_head_hidden: int = 128,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_hidden_layers = num_hidden_layers
        self.num_attention_heads = num_attention_heads
        self.intermediate_size = intermediate_size
        self.max_position_embeddings = max_position_embeddings
        self.latent_dim = latent_dim
        self.coherence_head_hidden = coherence_head_hidden

class CoherenceAwareTransformer(PreTrainedModel):
    """Transformer pré-treinado com heads especializados para coerência."""
    config_class = CoherenceAwareConfig

    def __init__(self, config: CoherenceAwareConfig):
        super().__init__(config)

        # Embeddings multimodais
        self.token_embeddings = nn.Embedding(config.vocab_size, config.hidden_size)
        self.modality_embeddings = nn.Embedding(4, config.hidden_size)  # code/spec/doc/graph
        self.position_embeddings = nn.Embedding(config.max_position_embeddings, config.hidden_size)

        # Backbone transformer
        self.encoder_layers = nn.ModuleList([
            nn.TransformerEncoderLayer(
                d_model=config.hidden_size,
                nhead=config.num_attention_heads,
                dim_feedforward=config.intermediate_size,
                batch_first=True
            ) for _ in range(config.num_hidden_layers)
        ])

        # Head de embedding latente para difusão
        self.latent_projection = nn.Sequential(
            nn.Linear(config.hidden_size, config.hidden_size // 2),
            nn.GELU(),
            nn.Linear(config.hidden_size // 2, config.latent_dim)
        )

        # Head de previsão de coerência
        self.coherence_head = nn.Sequential(
            nn.Linear(config.hidden_size, config.coherence_head_hidden),
            nn.GELU(),
            nn.Linear(config.coherence_head_hidden, 1),
            nn.Sigmoid()  # Output em [0, 1]
        )

        # Head de previsão estrutural (próximo token/grafos)
        self.structure_head = nn.Linear(config.hidden_size, config.vocab_size)

        # Inicialização
        self._init_weights()

    def _init_weights(self):
        """Inicialização padrão de transformers."""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(
        self,
        input_ids: torch.Tensor,
        modality_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        coherence_labels: Optional[torch.Tensor] = None,
        return_dict: bool = True,
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass com múltiplos objetivos de treinamento.

        Args:
            input_ids: [B, L] tokens de entrada
            modality_ids: [B, L] identificadores de modalidade (0=code, 1=spec, etc.)
            attention_mask: [B, L] máscara de atenção
            labels: [B, L] para MLM
            coherence_labels: [B, 1] para previsão de coerência
        """
        # Embeddings combinados
        embeddings = (
            self.token_embeddings(input_ids) +
            self.modality_embeddings(modality_ids) +
            self.position_embeddings(torch.arange(input_ids.size(1), device=input_ids.device))
        )

        # Encoder transformer
        hidden_states = embeddings
        for layer in self.encoder_layers:
            if attention_mask is not None:
                hidden_states = layer(hidden_states, src_key_padding_mask=~attention_mask.bool())
            else:
                hidden_states = layer(hidden_states)

        # Pooling para representação global (mean over non-masked tokens)
        if attention_mask is not None:
            pooled = (hidden_states * attention_mask.unsqueeze(-1)).sum(dim=1) / attention_mask.sum(dim=1, keepdim=True)
        else:
            pooled = hidden_states.mean(dim=1)

        # Heads especializados
        latent_context = self.latent_projection(pooled)  # Para difusão
        coherence_pred = self.coherence_head(pooled).squeeze(-1)  # Para Φ_C prior
        structure_logits = self.structure_head(hidden_states)  # Para MLM/estrutura

        outputs = {
            'last_hidden_state': hidden_states,
            'pooler_output': pooled,
            'latent_context': latent_context,
            'coherence_pred': coherence_pred,
            'structure_logits': structure_logits,
        }

        # Losses se labels fornecidos
        if labels is not None:
            outputs['mlm_loss'] = nn.functional.cross_entropy(
                structure_logits.view(-1, self.config.vocab_size),
                labels.view(-1),
                ignore_index=-100
            )

        if coherence_labels is not None:
            outputs['coherence_loss'] = nn.functional.mse_loss(
                coherence_pred, coherence_labels
            )

        return outputs if return_dict else tuple(outputs.values())

    def encode_for_diffusion(self, input_ids: torch.Tensor, modality_ids: torch.Tensor) -> torch.Tensor:
        """Extrai embedding latente condicionado para uso no difusor."""
        with torch.no_grad():
            outputs = self.forward(input_ids, modality_ids, return_dict=True)
            return outputs['latent_context']  # [B, latent_dim]

    def predict_coherence_prior(self, input_ids: torch.Tensor, modality_ids: torch.Tensor) -> torch.Tensor:
        """Prevê prior de coerência Φ_C^(0) para um artefato."""
        with torch.no_grad():
            outputs = self.forward(input_ids, modality_ids, return_dict=True)
            return outputs['coherence_pred']  # [B, 1]
