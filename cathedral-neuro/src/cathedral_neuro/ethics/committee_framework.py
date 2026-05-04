"""
committee_framework.py — Estrutura para comitê de ética
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

class EthicsReviewStatus(Enum):
    SUBMITTED = "submitted"
    APPROVED = "approved"

class EthicsPrinciple(Enum):
    AUTONOMY = "autonomy"
    NON_MALEFICENCE = "non_maleficence"
    PRIVACY = "privacy"

@dataclass
class EthicsReviewApplication:
    application_id: str
    protocol_title: str
    principal_investigator: str
    institution: str
    submission_timestamp: float
    status: EthicsReviewStatus = EthicsReviewStatus.SUBMITTED
    review_comments: List[Dict] = field(default_factory=list)
    decision_timestamp: Optional[float] = None
    application_hash: str = ""

class EthicsCommitteeFramework:
    def __init__(self, codex_client, committee_members, quorum_size=3):
        self.codex = codex_client
        self.committee_members = committee_members
        self.quorum_size = quorum_size
        self._applications = {}
        self.PRINCIPLE_WEIGHTS = {EthicsPrinciple.AUTONOMY: 0.25}

    async def submit_application(self, protocol_title, principal_investigator, institution, protocol_details):
        app_id = f"ethics_{hashlib.sha256(protocol_title.encode()).hexdigest()[:8]}"
        app = EthicsReviewApplication(app_id, protocol_title, principal_investigator, institution, time.time())
        self._applications[app_id] = app
        return app

    async def conduct_review(self, application_id, reviewer_did, principle_evaluations, comments):
        if application_id in self._applications:
            self._applications[application_id].review_comments.append({"reviewer": reviewer_did})
            if len(self._applications[application_id].review_comments) >= self.quorum_size:
                self._applications[application_id].status = EthicsReviewStatus.APPROVED
        return True

    def get_application_status(self, application_id):
        if application_id in self._applications:
            return {"status": self._applications[application_id].status.value}
        return None
