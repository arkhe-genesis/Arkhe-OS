#!/usr/bin/env python3
"""
metabolic_router.py — Substrato 6061
Flux Balance Analysis applied to the ARKHE temporal routing graph.
"""
import numpy as np
from scipy.optimize import linprog

class MetabolicTemporalRouter:
    """
    Treats the routing table as a genome-scale metabolic model.
    Every CausalEdge is a biochemical reaction.
    """
    def __init__(self, routing_table):
        self.rt = routing_table
        self._build_stoichiometry()

    def _build_stoichiometry(self):
        # S[metabolite, reaction] = stoichiometric coefficient
        # Here, "metabolites" are (sender, receiver) pairs plus a global "temporal_coherence".
        self.S = np.zeros((len(self.rt.nodes), len(self.rt.edges)))
        for j, edge in enumerate(self.rt.edges):
            self.S[self.rt.node_index(edge.src), j] = -1   # consume source
            self.S[self.rt.node_index(edge.dst), j] = +1   # produce destination

    def enforce_oracle_constraints(self, v, oracle):
        """Zero out fluxes that fail the enzyme (Oracle) check."""
        for j, edge in enumerate(self.rt.edges):
            score = oracle.evaluate_causal_edge(edge)
            if score < 0.85:
                v[j] = 0.0
        return v

    def maximize_delivery(self, source, target, oracle):
        """FBA: maximize flux from source to target, subject to Oracle constraints."""
        n_edges = len(self.rt.edges)
        c = np.zeros(n_edges)
        # Identify target edges (those directly delivering to target)
        for j, edge in enumerate(self.rt.edges):
            if edge.dst == target:
                c[j] = 1.0

        # Constraints: Sv = 0, but with flexibility for temporal storage
        # We enforce Sv = 0 only for intermediate nodes, dropping source and target rows.
        # This allows flux to enter at the source and exit at the target.
        mask = np.ones(self.S.shape[0], dtype=bool)
        if source in self.rt.nodes:
            mask[self.rt.node_index(source)] = False
        if target in self.rt.nodes:
            mask[self.rt.node_index(target)] = False

        S_eq = self.S[mask]
        # if S_eq is empty (e.g. only source and target in nodes), use a dummy constraint
        if S_eq.shape[0] == 0:
            S_eq = np.zeros((1, n_edges))

        b = np.zeros(S_eq.shape[0])
        bounds = [(0, 1000) for _ in range(n_edges)]

        # Solve linear program
        res = linprog(-c, A_eq=S_eq, b_eq=b, bounds=bounds, method='highs')
        if res.success:
            return self.enforce_oracle_constraints(res.x, oracle)
        return np.zeros(n_edges)
