import torch
import torch.nn as nn
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class LFIRNode:
    """Representação de nó LFIR para decodificação."""
    node_id: str
    node_type: str
    attributes: Dict[str, any]
    children: List['LFIRNode'] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []

class StructuredGraphDecoder(nn.Module):
    """Decodifica embedding latente em grafo LFIR válido com restrições."""

    def __init__(
        self,
        latent_dim: int = 256,
        max_nodes: int = 50,
        node_type_vocab_size: int = 32,
        attr_embedding_dim: int = 64,
    ):
        super().__init__()
        self.latent_dim = latent_dim
        self.max_nodes = max_nodes
        self.node_type_vocab_size = node_type_vocab_size

        # Projeção inicial
        self.initial_proj = nn.Linear(latent_dim, latent_dim)

        # Decoder autoregressivo para nós
        self.node_decoder = nn.GRU(
            input_size=latent_dim + attr_embedding_dim,
            hidden_size=latent_dim,
            num_layers=2,
            batch_first=True
        )

        # Heads de previsão
        self.node_type_head = nn.Linear(latent_dim, node_type_vocab_size)
        self.attr_value_head = nn.Linear(latent_dim, attr_embedding_dim)
        self.edge_head = nn.Linear(latent_dim * 2 + attr_embedding_dim, 1)  # Binary edge prediction

        # Embeddings de atributos
        self.attr_embeddings = nn.Embedding(1000, attr_embedding_dim)  # Placeholder

        # Validação pós-geração
        self.syntax_validator = LFIRSyntaxValidator()

    def decode(
        self,
        z0: torch.Tensor,
        max_steps: int = 100,
        temperature: float = 0.8,
    ) -> Dict[str, any]:
        """Decodifica embedding latente em estrutura de grafo."""
        batch_size = z0.size(0)
        device = z0.device

        # Estado inicial do decoder
        h0 = torch.tanh(self.initial_proj(z0)).unsqueeze(0)  # [1, B, latent_dim]
        # h0 needs to match the num_layers of GRU, so we duplicate it.
        h0 = h0.repeat(self.node_decoder.num_layers, 1, 1)

        # Sequência de geração autoregressiva
        generated_nodes = []
        hidden = h0

        for step in range(max_steps):
            # Input do passo atual (embedding do nó anterior ou z0 para o primeiro)
            if step == 0:
                # pad with zeros for the attribute dimension to match the input size of the decoder
                padding = torch.zeros(batch_size, 1, self.attr_value_head.out_features, device=device)
                decoder_input = torch.cat([z0.unsqueeze(1), padding], dim=-1)
            else:
                last_node_emb = self._embed_generated_node(generated_nodes[-1], device).to(device)
                decoder_input = last_node_emb.unsqueeze(0).unsqueeze(1).expand(batch_size, 1, -1)

            # Forward do GRU
            output, hidden = self.node_decoder(decoder_input, hidden)
            output = output.squeeze(1)  # [B, latent_dim]

            # Prever tipo de nó
            node_type_logits = self.node_type_head(output)
            if temperature > 0:
                node_type_logits = node_type_logits / temperature
            node_type_probs = torch.softmax(node_type_logits, dim=-1)
            node_type = torch.multinomial(node_type_probs, 1).squeeze(-1)

            # Prever atributos (simplificado: valores discretos)
            attr_logits = self.attr_value_head(output)
            attr_values = torch.argmax(attr_logits, dim=-1)

            # Prever arestas para nós existentes
            edges = []
            if generated_nodes:
                for prev_node in generated_nodes:
                    prev_emb = self._embed_generated_node(prev_node, device).to(device)
                    # expand prev_emb to match batch dimension
                    prev_emb_expanded = prev_emb.unsqueeze(0).expand(batch_size, -1)
                    edge_input = torch.cat([output, prev_emb_expanded], dim=-1)
                    edge_logit = self.edge_head(edge_input).squeeze(-1)
                    edge_prob = torch.sigmoid(edge_logit)
                    if edge_prob.mean() > 0.5:  # Threshold para aresta
                        edges.append(prev_node['node_id'])

            # Criar nó gerado
            node = {
                'node_id': f"node_{step}",
                'node_type': node_type[0].item() if batch_size == 1 else node_type.tolist(),
                'attributes': {'value': attr_values[0].item() if batch_size == 1 else attr_values.tolist()},
                'children': edges,
            }
            generated_nodes.append(node)

            # Critério de parada: probabilidade de fim de grafo
            # pad with zeros for the attribute dimension to match the input size of the edge_head
            padding_edge = torch.zeros(batch_size, self.attr_value_head.out_features, device=device)
            stop_prob = torch.sigmoid(self.edge_head(torch.cat([output, z0, padding_edge], dim=-1)))
            if stop_prob.mean() > 0.9 or len(generated_nodes) >= self.max_nodes:
                break

        # Validar e reparar grafo gerado
        valid_graph = self.syntax_validator.validate_and_repair(generated_nodes)

        return {
            'nodes': valid_graph,
            'num_nodes': len(valid_graph),
            'generation_steps': len(generated_nodes),
        }

    def _embed_generated_node(self, node: Dict, device: torch.device) -> torch.Tensor:
        """Converte nó gerado em embedding para próximo passo."""
        # Placeholder: embedding simples baseado em tipo + atributo
        type_emb = torch.randn(self.latent_dim, device=device)
        attr_val = node['attributes']['value']
        if isinstance(attr_val, list):
             attr_val = attr_val[0]
        attr_emb = self.attr_embeddings(torch.tensor(attr_val, device=device))
        return torch.cat([type_emb, attr_emb], dim=-1)

class LFIRSyntaxValidator:
    """Valida e repara grafos LFIR gerados para garantir sintaxe válida."""

    def validate_and_repair(self, nodes: List[Dict]) -> List[Dict]:
        """Valida estrutura e aplica reparos mínimos se necessário."""
        # Verificar unicidade de IDs
        ids = [n['node_id'] for n in nodes]
        if len(ids) != len(set(ids)):
            # Reparar: renomear duplicatas
            seen = set()
            for i, node in enumerate(nodes):
                while node['node_id'] in seen:
                    node['node_id'] = f"{node['node_id']}_dup{i}"
                seen.add(node['node_id'])

        # Verificar referências válidas em arestas
        valid_ids = set(n['node_id'] for n in nodes)
        for node in nodes:
            node['children'] = [c for c in node['children'] if c in valid_ids]

        # Garantir pelo menos um nó raiz
        if not any(n.get('is_root', False) for n in nodes) and nodes:
            nodes[0]['is_root'] = True

        return nodes
