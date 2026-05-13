#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mobile_app.py — Substrato Mobile: App para Revisores em Missões
Permite acesso offline/online, votação em campo e sincronização
de revisões com o Mythos Gate usando CRDTs.
"""

import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

class SyncStatus(Enum):
    OFFLINE = "offline"
    SYNCING = "syncing"
    SYNCED = "synced"
    CONFLICT = "conflict"

@dataclass
class MobileReviewTask:
    task_id: str
    package_name: str
    risk_score: float
    deadline: float
    cached_data: Dict
    local_vote: Optional[str] = None
    local_rationale: Optional[str] = None
    sync_status: SyncStatus = SyncStatus.SYNCED

class MobileAppSync:
    """Sincronizador offline-first para o app mobile."""

    def __init__(self, api_client=None):
        self.api_client = api_client
        self.local_store: Dict[str, MobileReviewTask] = {}

    def download_tasks(self, reviewer_id: str) -> List[MobileReviewTask]:
        """Baixa tarefas para acesso offline."""
        # Simula download
        return []

    def save_local_vote(self, task_id: str, vote: str, rationale: str) -> bool:
        """Salva voto localmente para sincronização futura."""
        if task_id in self.local_store:
            task = self.local_store[task_id]
            task.local_vote = vote
            task.local_rationale = rationale
            task.sync_status = SyncStatus.OFFLINE
            return True
        return False

    def sync_with_cathedral(self) -> Dict[str, int]:
        """Sincroniza votos locais com o backend."""
        results = {"synced": 0, "failed": 0}
        if not self.api_client:
            return results

        for task_id, task in self.local_store.items():
            if task.sync_status == SyncStatus.OFFLINE and task.local_vote:
                try:
                    self.api_client.submit_vote(task_id, task.local_vote, task.local_rationale)
                    task.sync_status = SyncStatus.SYNCED
                    results["synced"] += 1
                except Exception:
                    results["failed"] += 1

        return results
