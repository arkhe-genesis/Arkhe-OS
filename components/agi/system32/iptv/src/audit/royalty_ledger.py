"""
royalty_ledger.py — Ledger de audiência e distribuição de royalties.
Integra com Substrato 333 (Auditoria) e KYM (5006).
"""
import hashlib
import time
from typing import Dict

class RoyaltyLedger:
    def __init__(self, kym_gate, rep_engine):
        self.kym = kym_gate
        self.rep = rep_engine
        self.viewing_sessions: Dict[str, Dict] = {}
        self.royalty_pool: Dict[str, float] = {}

    def start_session(self, viewer_seal: str, channel_id: str):
        if not self.kym.verify_and_grant_access(viewer_seal):
            raise PermissionError("KYM verification failed")
        self.viewing_sessions[viewer_seal] = {
            "channel": channel_id,
            "start": time.time(),
            "weight": self.kym.get_viewer_weight(viewer_seal)
        }
        if channel_id not in self.royalty_pool:
            self.royalty_pool[channel_id] = 0.0

    def end_session(self, viewer_seal: str, total_duration: float):
        if viewer_seal not in self.viewing_sessions:
            return
        sess = self.viewing_sessions.pop(viewer_seal)
        watched_ratio = min(1.0, total_duration / max(0.1, time.time() - sess["start"]))
        risk_penalty = self.kym.kym.run_kym(viewer_seal).phi_risk
        royalty = 0.01 * watched_ratio * sess["weight"] * (1 - risk_penalty)
        self.royalty_pool[sess["channel"]] += royalty
        self._commit_to_ledger(viewer_seal, sess["channel"], royalty)

    def _commit_to_ledger(self, viewer: str, channel: str, amount: float):
        """Gera hash canônico e publica no ledger auditável (Substrato 333)."""
        record = f"{viewer}:{channel}:{amount}:{time.time()}"
        tx_hash = hashlib.sha256(record.encode()).hexdigest()
        # Em produção: enviar para ledger federado / DHT
