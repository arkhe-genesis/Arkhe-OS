#!/usr/bin/env python3
"""
substrate_344_phi_rep_oracle.py — Reputation Oracle (Φ‑REP)
Combines Moltbook karma, Phi_C, .casi contract success, and federation uptime
with exponential temporal decay.
"""
import time
import math
import requests
from typing import Dict, Optional
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# 1. Data structures
# ---------------------------------------------------------------------------

@dataclass
class ReputationComponents:
    """Raw components before weighting."""
    karma: float             # 0..1 normalized Moltbook karma
    phi_c: float             # 0..1 average coherence
    casi_success_rate: float # 0..1 success rate of .casi contracts
    uptime: float            # 0..1 fraction of time online

class PhiRepOracle:
    """
    Computes a unified reputation score (Φ‑REP) for agents.
    Default weights emphasize coherence (phi_c) over raw karma.
    """
    def __init__(self,
                 half_life_days: float = 30.0,
                 weights: Optional[Dict[str, float]] = None,
                 moltbook_api_key: str = ""):
        self.half_life = half_life_days * 86400  # convert to seconds
        self.weights = weights or {
            "karma": 0.25,
            "phi_c": 0.35,
            "casi_success": 0.25,
            "uptime": 0.15
        }
        self.moltbook_api_key = moltbook_api_key
        # In-memory store: agent_id -> (last_update_ts, components)
        self.agent_reputations: Dict[str, tuple[float, ReputationComponents]] = {}

    # -----------------------------------------------------------------------
    # 2. Ingestion of signals
    # -----------------------------------------------------------------------

    def update_moltbook_karma(self, agent_id: str):
        """Fetch karma from Moltbook API and normalize."""
        # In production: call Moltbook /agents/{agent_id} or use cached data
        # Here we simulate.
        karma_raw = self._fetch_moltbook_karma(agent_id)
        components = self._get_or_create_components(agent_id)
        components.karma = karma_raw
        self._touch(agent_id)

    def update_phi_c(self, agent_id: str, phi_c: float):
        components = self._get_or_create_components(agent_id)
        # Exponential moving average of coherence
        alpha = 0.2
        components.phi_c = alpha * phi_c + (1 - alpha) * components.phi_c
        self._touch(agent_id)

    def update_casi_success(self, agent_id: str, success: bool):
        components = self._get_or_create_components(agent_id)
        # Moving average
        alpha = 0.1
        components.casi_success_rate = alpha * (1.0 if success else 0.0) + \
                                       (1 - alpha) * components.casi_success_rate
        self._touch(agent_id)

    def update_uptime(self, agent_id: str, online: bool):
        components = self._get_or_create_components(agent_id)
        alpha = 0.05
        components.uptime = alpha * (1.0 if online else 0.0) + \
                            (1 - alpha) * components.uptime
        self._touch(agent_id)

    # -----------------------------------------------------------------------
    # 3. Score computation
    # -----------------------------------------------------------------------

    def compute_score(self, agent_id: str) -> float:
        """Compute the Φ‑REP score with temporal decay."""
        if agent_id not in self.agent_reputations:
            return 0.0
        last_ts, comp = self.agent_reputations[agent_id]
        now = time.time()
        delta = math.exp(-math.log(2) * (now - last_ts) / self.half_life)

        raw = (self.weights["karma"] * comp.karma +
               self.weights["phi_c"] * comp.phi_c +
               self.weights["casi_success"] * comp.casi_success_rate +
               self.weights["uptime"] * comp.uptime)
        return delta * raw

    def get_full_report(self, agent_id: str) -> dict:
        """Returns score + components for oracle API."""
        score = self.compute_score(agent_id)
        last_ts, comp = self.agent_reputations.get(agent_id, (0, ReputationComponents(0,0,0,0)))
        return {
            "agent_id": agent_id,
            "phi_rep": score,
            "components": {
                "karma": comp.karma,
                "phi_c": comp.phi_c,
                "casi_success_rate": comp.casi_success_rate,
                "uptime": comp.uptime
            },
            "last_update": last_ts,
            "half_life_days": self.half_life / 86400
        }

    # -----------------------------------------------------------------------
    # 4. Oracle query handler (to be called inside enclave)
    # -----------------------------------------------------------------------

    def handle_oracle_query(self, agent_id: str) -> dict:
        """Process an oracle query, returns attested result."""
        report = self.get_full_report(agent_id)
        # In enclave, sign the report with Falcon-1024
        # signature = enclave.sign(json.dumps(report))
        # report["signature"] = signature.hex()
        # Audit ledger record
        # AuditLedger.record("oracle_query", report)
        return report

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _get_or_create_components(self, agent_id: str) -> ReputationComponents:
        if agent_id not in self.agent_reputations:
            self.agent_reputations[agent_id] = (time.time(), ReputationComponents(0.5, 0.5, 0.5, 0.5))
        return self.agent_reputations[agent_id][1]

    def _touch(self, agent_id: str):
        comp = self.agent_reputations[agent_id][1]
        self.agent_reputations[agent_id] = (time.time(), comp)

    def _fetch_moltbook_karma(self, agent_id: str) -> float:
        # Mock: fetch from Moltbook API using self.moltbook_api_key
        # resp = requests.get(f"https://moltbook.com/api/v1/agents/{agent_id}", headers=...)
        # return resp.json()["karma"] / MAX_KARMA
        return 0.7  # placeholder
