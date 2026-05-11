#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
interoperability_morphism.py — Substrate 6044.2
Natural Transformations between ARKHE Topos and other consensus systems.

Mathematical Foundation:
  Given two topoi 𝒜 (ARKHE) and ℬ (e.g., Ethereum/Casper),
  a geometric morphism f: 𝒜 → ℬ consists of:
    - f*: ℬ → 𝒜 (inverse image, preserves finite limits)
    - f*: 𝒜 → ℬ (direct image, right adjoint to f*)

  A natural transformation η: F ⇒ G between functors F,G: 𝒜 → ℬ
  assigns to each object X ∈ 𝒜 a morphism η_X: F(X) → G(X)
  such that for every morphism h: X → Y, the square commutes:
        F(X) --η_X--> G(X)
         |            |
      F(h)|            |G(h)
         ▼            ▼
        F(Y) --η_Y--> G(Y)

Application:
  - Map ARKHE TemporalMessage → Casper Estimate
  - Map ARKHE ConsistencyOracle → Casper SafetyOracle
  - Preserve intuitionistic logic across the translation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Generic, TypeVar
from abc import ABC, abstractmethod
import hashlib
import json
import time

# ============================================================================
# CATEGORY THEORY PRIMITIVES (simplified for implementation)
# ============================================================================

Obj = TypeVar('Obj')
Mor = TypeVar('Mor')

class Category(ABC):
    """Abstract category with objects and morphisms."""
    @abstractmethod
    def compose(self, f: Mor, g: Mor) -> Optional[Mor]:
        """Compose morphisms f ∘ g if cod(f) = dom(g)."""
        pass

    @abstractmethod
    def identity(self, obj: Obj) -> Mor:
        """Identity morphism for object."""
        pass

@dataclass
class Functor(Generic[Obj, Mor]):
    """Functor between categories: maps objects and morphisms."""
    map_obj: Callable[[Obj], Obj]
    map_mor: Callable[[Mor], Mor]

    def __call__(self, x):
        """Apply functor: F(x) for object or morphism."""
        return self.map_mor(x) if isinstance(x, Mor) else self.map_obj(x)

@dataclass
class NaturalTransformation(Generic[Obj, Mor]):
    """
    Natural transformation η: F ⇒ G between functors F,G: 𝒜 → ℬ.

    For each object X, η_X: F(X) → G(X) such that:
      G(h) ∘ η_X = η_Y ∘ F(h)  for all h: X → Y
    """
    F: Functor
    G: Functor
    component: Callable[[Obj], Mor]  # η_X for each object X

    def naturality_square(self, h: Mor, X: Obj, Y: Obj) -> bool:
        """
        Verify commutativity: G(h) ∘ η_X = η_Y ∘ F(h)
        Returns True if the square commutes.
        """
        eta_X = self.component(X)
        eta_Y = self.component(Y)
        F_h = self.F.map_mor(h)
        G_h = self.G.map_mor(h)

        # Simplified equality check (in production: use categorical equality)
        lhs = self.G.compose(G_h, eta_X)
        rhs = self.G.compose(eta_Y, F_h)
        return lhs == rhs

# ============================================================================
# MOCKS FOR ARKHE
# ============================================================================
@dataclass
class TemporalMessage:
    id: str
    content: str
    source_timestamp: float
    target_timestamp: float
    sender_seal: str
    receiver_seal: str
    consistency_score: float = 1.0

# ============================================================================
# ARKHE → CASPER MORPHISM (example: Ethereum Casper FFG)
# ============================================================================

@dataclass
class CasperEstimate:
    """Casper FFG estimate: checkpoint + justification."""
    checkpoint_hash: str
    justification_epoch: int
    score: float  # [0,1] safety score

@dataclass
class ArkheToCasperMorphism:
    """
    Geometric morphism f: ArkheTopos → CasperTopos.

    Inverse image f*: Casper → Arkhe (pulls back Casper structures)
    Direct image f*: Arkhe → Casper (pushes forward Arkhe structures)
    """

    # Direct image: map ARKHE structures to Casper
    def direct_image_message(self, arkhe_msg: 'TemporalMessage') -> CasperEstimate:
        """Map TemporalMessage → CasperEstimate."""
        # Extract checkpoint-like hash from message
        checkpoint = hashlib.sha3_256(
            f"{arkhe_msg.sender_seal}:{arkhe_msg.content}".encode()
        ).hexdigest()[:16]

        # Map temporal index to epoch
        epoch = int(arkhe_msg.source_timestamp // 32)  # 32s slots

        # Map consistency score to Casper safety score
        # (simplified: use minimum of checks)
        score = min(0.999, arkhe_msg.consistency_score)

        return CasperEstimate(
            checkpoint_hash=checkpoint,
            justification_epoch=epoch,
            score=score
        )

    # Inverse image: map Casper structures to ARKHE
    def inverse_image_estimate(self, casper_est: CasperEstimate) -> 'TemporalMessage':
        """Map CasperEstimate → TemporalMessage (pullback)."""
        return TemporalMessage(
            id=f"casper-import-{casper_est.checkpoint_hash}",
            content=json.dumps({
                'checkpoint': casper_est.checkpoint_hash,
                'epoch': casper_est.justification_epoch,
                'casper_score': casper_est.score
            }),
            source_timestamp=casper_est.justification_epoch * 32,
            target_timestamp=casper_est.justification_epoch * 32 + 32,
            sender_seal=f"CASPER-{casper_est.checkpoint_hash[:8]}",
            receiver_seal="ARKHE-IMPORT",
            consistency_score=casper_est.score
        )

    # Natural transformation: η: Oracle_ARKHE ⇒ Oracle_Casper ∘ f*
    def oracle_natural_transformation(
        self,
        arkhe_msg: 'TemporalMessage',
        arkhe_oracle_score: float,
        casper_oracle: Callable[[CasperEstimate], float]
    ) -> bool:
        """
        Verify naturality of oracle mapping.

        η_msg: Oracle_ARKHE(msg) → Oracle_Casper(f*(msg))

        Naturality condition:
          For any morphism h: msg₁ → msg₂,
          Oracle_Casper(f*(h)) ∘ η_msg₁ = η_msg₂ ∘ Oracle_ARKHE(h)
        """
        # Map ARKHE message to Casper
        casper_est = self.direct_image_message(arkhe_msg)

        # Evaluate both oracles
        arkhe_score = arkhe_oracle_score
        casper_score = casper_oracle(casper_est)

        # Natural transformation component: η_msg = score mapping
        # (simplified: scores should be within tolerance)
        tolerance = 0.05
        return abs(arkhe_score - casper_score) < tolerance

# ============================================================================
# INTEROPERABILITY PROTOCOL
# ============================================================================

class CrossConsensusBridge:
    """
    Bridge between ARKHE and external consensus systems.
    Uses natural transformations to preserve logical structure.
    """

    def __init__(self, arkhe_oracle, external_oracle, morphism: ArkheToCasperMorphism):
        self.arkhe_oracle = arkhe_oracle
        self.external_oracle = external_oracle
        self.morphism = morphism
        self.verified_mappings: List[Dict] = []

    def import_external_message(self, external_msg) -> Optional['TemporalMessage']:
        """
        Import message from external consensus via inverse image.
        Returns ARKHE TemporalMessage if verification succeeds.
        """
        # Pull back via inverse image
        arkhe_msg = self.morphism.inverse_image_estimate(external_msg)

        # Verify via ARKHE oracle
        report = self.arkhe_oracle.evaluate(arkhe_msg)

        if getattr(report, "consistent", False) and getattr(report, "score", 0) >= 0.90:
            # Record verified mapping
            self.verified_mappings.append({
                'external_hash': external_msg.checkpoint_hash,
                'arkhe_id': arkhe_msg.id,
                'score': report.score,
                'timestamp': time.time()
            })
            return arkhe_msg
        return None

    def export_arkhe_message(self, arkhe_msg: 'TemporalMessage'):
        """
        Export ARKHE message to external consensus via direct image.
        Returns external representation if naturality holds.
        """
        # Evaluate ARKHE oracle
        arkhe_report = self.arkhe_oracle.evaluate(arkhe_msg)

        # Map to external format
        external_est = self.morphism.direct_image_message(arkhe_msg)

        # Evaluate external oracle
        external_score = self.external_oracle(external_est)

        # Verify naturality of transformation
        if self.morphism.oracle_natural_transformation(
            arkhe_msg, getattr(arkhe_report, "score", 0), self.external_oracle
        ):
            return external_est
        return None
