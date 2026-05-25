#!/usr/bin/env python3
"""
functor_learner.py — Substrato 826.4
Aprendizado de Funtores entre Domínios (Category Theory)
Arquiteto: ORCID 0009-0005-2697-4668 | Data: 2026-05-25
"""

import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Tuple, Callable
from dataclasses import dataclass


@dataclass
class Category:
    """Representação simplificada de uma categoria."""
    name: str
    objects: List[str]  # Nomes dos objetos
    morphisms: List[Tuple[str, str, str]]  # (source, target, label)

    def __hash__(self):
        return hash(self.name)


class FunctorLearner(nn.Module):
    """
    Aprende um functor entre duas categorias:
    F: C → D que preserva estrutura (objetos e morfismos).
    """

    def __init__(self, source_dim: int, target_dim: int, hidden_dim: int = 128):
        super().__init__()

        # Mapeamento de objetos: embedding → embedding
        self.object_mapper = nn.Sequential(
            nn.Linear(source_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, target_dim),
        )

        # Mapeamento de morfismos: preservação da composição
        self.morphism_mapper = nn.Sequential(
            nn.Linear(source_dim * 2, hidden_dim),  # source + target
            nn.ReLU(),
            nn.Linear(hidden_dim, target_dim * 2),
        )

        # Verificador de preservação de composição
        self.composition_checker = nn.Sequential(
            nn.Linear(target_dim * 3, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid(),
        )

    def map_object(self, obj_embedding: torch.Tensor) -> torch.Tensor:
        """Mapeia um objeto da categoria fonte para a categoria alvo."""
        return self.object_mapper(obj_embedding)

    def map_morphism(self, src_embedding: torch.Tensor, tgt_embedding: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Mapeia um morfismo preservando domínio e codomínio.
        Retorna (F(source), F(target)).
        """
        combined = torch.cat([src_embedding, tgt_embedding], dim=-1)
        mapped = self.morphism_mapper(combined)

        mid = mapped.size(-1) // 2
        return mapped[..., :mid], mapped[..., mid:]

    def check_composition_preservation(self,
                                       f_src: torch.Tensor, f_tgt: torch.Tensor,
                                       g_src: torch.Tensor, g_tgt: torch.Tensor,
                                       h_src: torch.Tensor, h_tgt: torch.Tensor) -> float:
        """
        Verifica se F(g ∘ f) = F(g) ∘ F(f) = h.
        Retorna score de preservação.
        """
        # h deve ser igual a g_tgt (que é f_src) mapeado
        combined = torch.cat([f_src, f_tgt, g_tgt], dim=-1)
        score = self.composition_checker(combined)
        return score.item()

    def compute_functor_quality(self,
                                source_category: Category,
                                target_category: Category,
                                obj_embeddings_source: Dict[str, torch.Tensor],
                                obj_embeddings_target: Dict[str, torch.Tensor]) -> Dict:
        """
        Computa a qualidade do functor aprendido.
        Retorna métricas de preservação estrutural.
        """
        # Mapear todos os objetos
        mapped_objects = {}
        for obj in source_category.objects:
            if obj in obj_embeddings_source:
                mapped = self.map_object(obj_embeddings_source[obj])
                mapped_objects[obj] = mapped

        # Verificar preservação de morfismos
        morphism_scores = []
        for src, tgt, label in source_category.morphisms:
            if src in obj_embeddings_source and tgt in obj_embeddings_source:
                mapped_src, mapped_tgt = self.map_morphism(
                    obj_embeddings_source[src],
                    obj_embeddings_source[tgt]
                )

                # Verificar se o morfismo mapeado existe na categoria alvo
                target_morphism_exists = any(
                    (ms == src and mt == tgt) or
                    (self._embedding_similarity(mapped_src, obj_embeddings_target.get(ms)) > 0.9 and
                     self._embedding_similarity(mapped_tgt, obj_embeddings_target.get(mt)) > 0.9)
                    for ms, mt, _ in target_category.morphisms
                )

                morphism_scores.append(1.0 if target_morphism_exists else 0.0)

        # Score geral (ι - iota)
        iota = np.mean(morphism_scores) if morphism_scores else 0.0

        return {
            "iota": float(iota),
            "mapped_objects": len(mapped_objects),
            "total_objects": len(source_category.objects),
            "morphism_preservation": float(np.mean(morphism_scores)) if morphism_scores else 0.0,
            "is_canonical": iota > 0.95,
            "is_strong": iota > 0.8,
            "is_suggestive": iota > 0.6,
        }

    def _embedding_similarity(self, emb1: torch.Tensor, emb2: torch.Tensor) -> float:
        """Computa similaridade cosseno entre embeddings."""
        if emb2 is None:
            return 0.0

        cos_sim = torch.nn.functional.cosine_similarity(emb1.unsqueeze(0), emb2.unsqueeze(0))
        return cos_sim.item()


def create_example_categories() -> Tuple[Category, Category]:
    """Cria duas categorias de exemplo: Física (Fluxo) e Economia (Mercado)."""

    # Categoria Física: Dinâmica de Fluidos
    physics = Category(
        name="FluidDynamics",
        objects=["velocity_field", "pressure", "density", "viscosity", "flux"],
        morphisms=[
            ("velocity_field", "flux", "generates"),
            ("pressure", "velocity_field", "drives"),
            ("density", "pressure", "determines"),
            ("viscosity", "flux", "resists"),
            ("flux", "velocity_field", "is_integral_of"),
        ]
    )

    # Categoria Economia: Dinâmica de Mercado
    economics = Category(
        name="MarketDynamics",
        objects=["price_velocity", "demand_pressure", "supply_density", "market_friction", "trade_flow"],
        morphisms=[
            ("price_velocity", "trade_flow", "generates"),
            ("demand_pressure", "price_velocity", "drives"),
            ("supply_density", "demand_pressure", "determines"),
            ("market_friction", "trade_flow", "resists"),
            ("trade_flow", "price_velocity", "is_integral_of"),
        ]
    )

    return physics, economics


def create_embeddings_for_category(category: Category, dim: int = 16) -> Dict[str, torch.Tensor]:
    """Cria embeddings aleatórios para objetos de uma categoria."""
    embeddings = {}
    for obj in category.objects:
        # Seed baseado no nome para reprodutibilidade
        torch.manual_seed(hash(obj) % 2**32)
        embeddings[obj] = torch.randn(dim)
    return embeddings


def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   FUNCTOR LEARNER — SUBSTRATO 826.4                      ║")
    print("║   Category Theory | Deep Learning | ξM-Field           ║")
    print("╚════════════════════════════════════════════════════════════╝")

    # Criar categorias de exemplo
    physics, economics = create_example_categories()

    print("\n📐 Source Category: " + physics.name)
    print("   Objects: " + str(physics.objects))
    print("   Morphisms: " + str(len(physics.morphisms)))

    print("\n📈 Target Category: " + economics.name)
    print("   Objects: " + str(economics.objects))
    print("   Morphisms: " + str(len(economics.morphisms)))

    # Criar embeddings
    physics_embeddings = create_embeddings_for_category(physics, dim=16)
    economics_embeddings = create_embeddings_for_category(economics, dim=16)

    # Criar functor learner
    functor = FunctorLearner(source_dim=16, target_dim=16, hidden_dim=128)

    # Computar qualidade do functor
    quality = functor.compute_functor_quality(
        physics, economics,
        physics_embeddings, economics_embeddings
    )

    print("\n🎯 Functor Quality (ι - iota):")
    print("   ι = {:.4f}".format(quality['iota']))
    print("   Mapped objects: " + str(quality['mapped_objects']) + "/" + str(quality['total_objects']))
    print("   Morphism preservation: {:.4f}".format(quality['morphism_preservation']))
    print("   Is canonical (ι > 0.95): " + str(quality['is_canonical']))
    print("   Is strong (ι > 0.8): " + str(quality['is_strong']))
    print("   Is suggestive (ι > 0.6): " + str(quality['is_suggestive']))

    # Interpretação
    if quality['is_canonical']:
        print("\n✅ ISOMORFISMO CANÔNICO DETECTADO!")
        print("   O functor F: " + physics.name + " → " + economics.name + " é canônico.")
        print("   Transferência de aprendizado autorizada.")
    elif quality['is_strong']:
        print("\n⚡ Isomorfismo forte detectado (com exceções).")
    elif quality['is_suggestive']:
        print("\n💡 Analogia sugestiva — requer validação humana.")
    else:
        print("\n❌ Ruído — descartar candidato.")


if __name__ == "__main__":
    main()
