"""
parser.py — Parser de arkhe-lang para especificação de intenção molecular
Traduz declarações em arkhe-lang para objetos Python estruturados
"""

import re
import json
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum, auto

class MolecularTarget(Enum):
    """Tipos de alvo molecular suportados."""
    COVALENT_INHIBITOR = "covalent_inhibitor"
    ALLOSTERIC_MODULATOR = "allosteric_modulator"
    POLYMER_REPEAT_UNIT = "polymer_repeat_unit"
    ORGANIC_RADICAL = "organic_radical"
    CATALYST = "catalyst"
    GENERIC = "generic"

@dataclass
class MolecularConstraints:
    """Restrições para a molécula alvo."""
    IC50_max: Optional[str] = None
    Ki_max: Optional[str] = None
    solubility_min: Optional[str] = None
    logP_range: Optional[str] = None
    synthetic_steps_max: Optional[int] = None
    building_blocks: Optional[str] = None
    reaction_types_allowed: Optional[List[str]] = None
    toxicity: Optional[str] = None
    mutagenicity: Optional[str] = None
    regulatory_status: Optional[str] = None
    novelty_vs_known: Optional[float] = None

    def validate(self) -> List[str]:
        errors = []
        if self.synthetic_steps_max and self.synthetic_steps_max < 1:
            errors.append("synthetic_steps_max deve ser >= 1")
        return errors

@dataclass
class MolecularIntent:
    """Especificação completa de intenção molecular."""
    intent_id: str
    target_type: MolecularTarget
    protein_target: Optional[str] = None
    pathway_target: Optional[str] = None
    constraints: MolecularConstraints = field(default_factory=MolecularConstraints)
    optimization_preferences: Dict[str, float] = field(default_factory=dict)
    federation_config: Optional[Dict] = None
    consent_scope: Optional[str] = None
    multi_objective_config: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            "intent_id": self.intent_id,
            "target_type": self.target_type.value,
            "protein_target": self.protein_target,
            "pathway_target": self.pathway_target,
            "constraints": asdict(self.constraints),
            "optimization_preferences": self.optimization_preferences,
            "federation_config": self.federation_config,
            "consent_scope": self.consent_scope,
            "multi_objective_config": self.multi_objective_config,
        }

class ArkheMolecularParser:
    """Parser de arkhe-lang para MolecularIntent."""

    PATTERNS = {
        "intent_block": r"molecule\s*\{([^}]+)\}",
        "key_value": r"(\w+):\s*\"([^\"]+)\"|(\w+):\s*([0-9.]+)|(\w+):\s*(\w+)",
        "list_value": r"(\w+):\s*\[([^\]]+)\]",
        "nested_block": r"(\w+):\s*\{([^}]+)\}",
    }

    @classmethod
    def parse(cls, arkhe_code: str, intent_id: Optional[str] = None) -> MolecularIntent:
        match = re.search(cls.PATTERNS["intent_block"], arkhe_code, re.DOTALL)
        if not match:
            raise ValueError("Bloco 'molecule {}' não encontrado")

        content = match.group(1)
        intent = MolecularIntent(
            intent_id=intent_id or f"intent_{hash(arkhe_code) % 10000:04d}",
            target_type=MolecularTarget.GENERIC,
            constraints=MolecularConstraints(),
        )

        for match in re.finditer(cls.PATTERNS["key_value"], content):
            key = match.group(1) or match.group(3) or match.group(5)
            value = match.group(2) or match.group(4) or match.group(6)
            if key == "target":
                try: intent.target_type = MolecularTarget(value)
                except ValueError: pass
            elif key == "protein_target": intent.protein_target = value
            elif key == "consent_scope": intent.consent_scope = value

        for block_match in re.finditer(cls.PATTERNS["nested_block"], content):
            block_name = block_match.group(1)
            block_content = block_match.group(2)
            if block_name == "constraints":
                intent.constraints = cls._parse_constraints(block_content)
            elif block_name == "optimization_preferences":
                intent.optimization_preferences = cls._parse_float_dict(block_content)
            elif block_name == "federation_config":
                intent.federation_config = cls._parse_federation_config(block_content)
            elif block_name == "multi_objective":
                intent.multi_objective_config = MultiObjectiveParserExtension.parse_multi_objective(block_content)

        return intent

    @classmethod
    def _parse_constraints(cls, content: str) -> MolecularConstraints:
        constraints = MolecularConstraints()
        for match in re.finditer(cls.PATTERNS["key_value"], content):
            key = match.group(1) or match.group(3) or match.group(5)
            value = match.group(2) or match.group(4) or match.group(6)
            if hasattr(constraints, key):
                if key == "synthetic_steps_max": setattr(constraints, key, int(value))
                else: setattr(constraints, key, value)
        return constraints

    @classmethod
    def _parse_float_dict(cls, content: str) -> Dict[str, float]:
        result = {}
        for match in re.finditer(cls.PATTERNS["key_value"], content):
            key = match.group(1) or match.group(3) or match.group(5)
            value = match.group(2) or match.group(4) or match.group(6)
            if key and value:
                try: result[key] = float(value)
                except ValueError: pass
        return result

    @classmethod
    def _parse_federation_config(cls, content: str) -> Dict:
        config = {}
        for match in re.finditer(cls.PATTERNS["key_value"], content):
            key = match.group(1) or match.group(3) or match.group(5)
            value = match.group(2) or match.group(4) or match.group(6)
            if key and value: config[key] = value
        return config

class MultiObjectiveParserExtension:
    @classmethod
    def parse_multi_objective(cls, content: str) -> Dict:
        config = {"method": "pareto_frontier", "objectives": {}, "constraints": {}}
        for match in re.finditer(r"(\w+):\s*(min|max):\s*([0-9.]+)", content):
            obj_name, direction, weight = match.groups()
            config["objectives"][obj_name] = {"direction": direction, "weight": float(weight)}
        return config
