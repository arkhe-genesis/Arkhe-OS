import json
import hashlib
from dataclasses import dataclass, asdict
from typing import Dict, Optional

@dataclass
class CanonicalPlot:
    plot_type: str
    title: str
    data: Dict
    canonical_hash: Optional[str] = None

    def __post_init__(self):
        if not self.canonical_hash:
            self.canonical_hash = hashlib.sha3_256(json.dumps(self.data, sort_keys=True).encode()).hexdigest()

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, json_str: str) -> 'CanonicalPlot':
        data = json.loads(json_str)
        return cls(**data)

class CanonicalVisualizer:
    pass
