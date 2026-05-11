#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
multiverse_sheaf.py — Substrate 6044.3
Model MultiverseRouter branches as sheaves over a topological base.

Mathematical Foundation:
  A sheaf ℱ on a topological space (X, τ) assigns:
    - To each open U ⊆ X: a set ℱ(U) of "sections over U"
    - To each inclusion V ⊆ U: a restriction map ρ_{UV}: ℱ(U) → ℱ(V)
  Satisfying:
    1. ℱ(∅) = {*} (empty set has unique section)
    2. ρ_{UU} = id (restriction to self is identity)
    3. ρ_{WV} ∘ ρ_{UV} = ρ_{UW} (transitivity)
    4. Gluing: if {U_i} covers U and s_i ∈ ℱ(U_i) agree on overlaps,
       then ∃! s ∈ ℱ(U) with ρ_{U U_i}(s) = s_i

Application to MultiverseRouter:
  - Base space X = set of temporal indices (ℝ with order topology)
  - Open sets = temporal intervals [t₁, t₂)
  - Sections over U = consistent branches valid during U
  - Restriction = projecting a branch to a sub-interval
  - Gluing = merging compatible branches into a unified timeline

This provides:
  - Formal semantics for "possibility" (◇) and "necessity" (□)
  - Unified treatment of probability and branching
  - Categorical foundation for branch reconciliation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Set, TypeVar
from enum import Enum
import hashlib
import json
import time

# ============================================================================
# TOPOLOGICAL BASE: TEMPORAL INTERVALS
# ============================================================================

@dataclass(frozen=True)
class TemporalInterval:
    """Open interval in temporal base space."""
    start: float
    end: float

    def __post_init__(self):
        if self.start >= self.end:
            raise ValueError("Invalid interval: start >= end")

    def contains(self, t: float) -> bool:
        return self.start <= t < self.end

    def intersects(self, other: 'TemporalInterval') -> bool:
        return self.start < other.end and other.start < self.end

    def intersection(self, other: 'TemporalInterval') -> Optional['TemporalInterval']:
        if not self.intersects(other):
            return None
        return TemporalInterval(
            start=max(self.start, other.start),
            end=min(self.end, other.end)
        )

    def __le__(self, other: 'TemporalInterval') -> bool:
        """Inclusion: self ⊆ other"""
        return other.start <= self.start and self.end <= other.end

# ============================================================================
# SHEAF STRUCTURE
# ============================================================================

Section = TypeVar('Section')

@dataclass
class Sheaf(Generic[Section]):
    """
    Sheaf ℱ on temporal base space.

    ℱ(U) = set of consistent branches valid over interval U
    ρ_{UV}: ℱ(U) → ℱ(V) = restriction to sub-interval
    """

    # Sections over each interval
    sections: Dict[TemporalInterval, Set[Section]] = field(default_factory=dict)

    # Restriction maps: ρ_{UV}(s) for V ⊆ U
    restrictions: Dict[Tuple[TemporalInterval, TemporalInterval], Callable[[Section], Section]] = field(default_factory=dict)

    def add_section(self, interval: TemporalInterval, section: Section):
        """Add a section (branch) valid over an interval."""
        if interval not in self.sections:
            self.sections[interval] = set()
        self.sections[interval].add(section)

    def restrict(self, section: Section, from_interval: TemporalInterval,
                 to_interval: TemporalInterval) -> Optional[Section]:
        """
        Restrict section to sub-interval: ρ_{UV}(s).
        Returns None if restriction is undefined.
        """
        if not (to_interval <= from_interval):
            return None

        key = (from_interval, to_interval)
        if key in self.restrictions:
            return self.restrictions[key](section)

        # Default restriction: project branch to sub-interval
        # (In production: use actual branch projection logic)
        return section  # Simplified

    def glue(self, intervals: List[TemporalInterval],
             sections: List[Section],
             target: TemporalInterval) -> Optional[Section]:
        """
        Glue compatible sections over a cover {U_i} of target interval.

        Returns glued section if compatibility conditions hold, None otherwise.
        """
        # Verify cover
        if not all(U <= target for U in intervals):
            return None
        if not any(U.intersects(target) for U in intervals):
            return None

        # Verify compatibility on overlaps
        for i, U_i in enumerate(intervals):
            for j, U_j in enumerate(intervals[i+1:], i+1):
                overlap = U_i.intersection(U_j)
                if overlap:
                    s_i_restricted = self.restrict(sections[i], U_i, overlap)
                    s_j_restricted = self.restrict(sections[j], U_j, overlap)
                    if s_i_restricted != s_j_restricted:
                        return None  # Incompatible on overlap

        # Gluing: create unified section (simplified)
        # In production: merge branch states, reconcile temporal indices
        glued = self._merge_sections(sections, target)
        self.add_section(target, glued)
        return glued

    def _merge_sections(self, sections: List[Section], target: TemporalInterval) -> Section:
        """Merge multiple sections into one (branch reconciliation)."""
        # Simplified: return first section
        # In production: implement actual branch merging logic
        return sections[0] if sections else None

    def stalk(self, t: float) -> Set[Section]:
        """
        Stalk at point t: germ of sections defined near t.
        ℱ_t = colim_{U ∋ t} ℱ(U)
        """
        germs = set()
        for interval, secs in self.sections.items():
            if interval.contains(t):
                germs.update(secs)
        return germs

# ============================================================================
# MULTIVERSE SHEAF: BRANCHES AS SECTIONS
# ============================================================================

@dataclass
class BranchSection:
    """A branch of the multiverse, valid over a temporal interval."""
    branch_id: str
    temporal_range: TemporalInterval
    ledger_state: Dict  # State of ledger during this interval
    consistency_score: float
    parent_branches: List[str] = field(default_factory=list)

    def restrict_to(self, new_range: TemporalInterval) -> 'BranchSection':
        """Restrict branch to sub-interval."""
        return BranchSection(
            branch_id=f"{self.branch_id}|{new_range.start:.0f}-{new_range.end:.0f}",
            temporal_range=new_range,
            ledger_state=self.ledger_state,  # Simplified
            consistency_score=self.consistency_score,
            parent_branches=self.parent_branches
        )

class MultiverseSheafRouter:
    """
    MultiverseRouter with sheaf semantics.

    Branches are sections of a sheaf over temporal base space.
    Branch reconciliation is sheaf gluing.
    Modal operators emerge from sheaf semantics:
      - □p = "p holds in all sections over every neighborhood"
      - ◇p = "p holds in some section over some neighborhood"
    """

    def __init__(self):
        self.branch_sheaf: Sheaf[BranchSection] = Sheaf()
        self.temporal_base: Set[TemporalInterval] = set()

        # Register restriction maps for branch sections
        self.branch_sheaf.restrictions[
            (TemporalInterval(0, float('inf')), TemporalInterval(0, float('inf')))
        ] = lambda s: s.restrict_to(s.temporal_range)  # Identity

    def register_branch(self, branch: BranchSection):
        """Register a branch as a section over its temporal range."""
        self.branch_sheaf.add_section(branch.temporal_range, branch)
        self.temporal_base.add(branch.temporal_range)

    def reconcile_branches(self, branch_ids: List[str],
                          target_interval: TemporalInterval) -> Optional[BranchSection]:
        """
        Reconcile multiple branches via sheaf gluing.
        Returns unified branch if compatible, None if paradox detected.
        """
        # Fetch sections
        sections = []
        intervals = []
        for bid in branch_ids:
            # Find section with matching branch_id
            for interval, secs in self.branch_sheaf.sections.items():
                for sec in secs:
                    if sec.branch_id == bid and interval.intersects(target_interval):
                        sections.append(sec)
                        intervals.append(interval)
                        break

        if not sections:
            return None

        # Attempt gluing
        return self.branch_sheaf.glue(intervals, sections, target_interval)

    def evaluate_modal(self, proposition: Callable[[BranchSection], bool],
                      modality: str, t: float) -> bool:
        """
        Evaluate modal formula at temporal point t.

        modality:
          - 'necessity' (□): proposition holds in ALL sections near t
          - 'possibility' (◇): proposition holds in SOME section near t
        """
        stalk = self.branch_sheaf.stalk(t)

        if modality == 'necessity':
            return all(prop(sec) for sec in stalk)
        elif modality == 'possibility':
            return any(prop(sec) for sec in stalk)
        else:
            raise ValueError(f"Unknown modality: {modality}")

    def get_branch_at(self, branch_id: str, t: float) -> Optional[BranchSection]:
        """Get branch section valid at temporal point t."""
        for interval, sections in self.branch_sheaf.sections.items():
            if interval.contains(t):
                for sec in sections:
                    if sec.branch_id == branch_id:
                        return sec
        return None

class BranchSheaf:
    """
    Feixe de proposições sobre o espaço topológico dos branches.
    Um elemento da seção F(U) para um aberto U (conjunto de branches compatíveis)
    é uma proposição temporal que é segura em todos os branches de U.
    """
    def __init__(self, router):
        self.router = router
        self._sections = {}  # branch_set → TemporalMessage

    def restrict(self, branch, sub_branch_set) -> 'TemporalMessage':
        """Restrição: a proposição em um branch maior implica a do subconjunto."""
        return self._sections.get(sub_branch_set)

    def glue(self, cover, local_sections) -> bool:
        """
        Condição de feixe: se proposições coincidem nas interseções,
        existe uma única proposição global que as cola.
        """
        return all(
            local_sections[bi].consistent and
            local_sections[bj].consistent and
            local_sections[bi].score == local_sections[bj].score
            for bi in cover for bj in cover
        )
