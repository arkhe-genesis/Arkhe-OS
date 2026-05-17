import hashlib
import json
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass, field

@dataclass
class ReactionRule:
    rule_id: str
    pattern: str
    confidence_score: float = 0.5
    training_samples: int = 0

class ASTReactionRuleLearner:
    """Mock rule learner for tests since the actual file seems to be missing from the project or I need to create it"""
    def __init__(self):
        self._rules: Dict[str, ReactionRule] = {}

    def validate_reaction_code(self, code: str) -> Tuple[bool, List[str], Dict]:
        return True, [], {}

    def record_learning_feedback(self, code: str, validation_result: bool, human_feedback: bool, rule_id: str):
        if rule_id not in self._rules:
            self._rules[rule_id] = ReactionRule(rule_id=rule_id, pattern="")
        rule = self._rules[rule_id]
        rule.confidence_score = min(1.0, rule.confidence_score + 0.1 if human_feedback else -0.1)
        rule.training_samples += 1
