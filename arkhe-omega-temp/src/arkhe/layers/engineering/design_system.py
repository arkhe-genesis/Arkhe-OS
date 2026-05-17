# src/arkhe/layers/engineering/design_system.py
from arkhe.output import format_result, RichFormatter
from dataclasses import dataclass
from enum import Enum
import hashlib

class DesignToken(Enum):
    SUCCESS = "green"
    ERROR = "red"
    WARNING = "yellow"
    INFO = "blue"

@dataclass
class DesignResult:
    token: DesignToken
    message: str
    data: dict = None

    def display(self):
        formatted = {
            "success": self.token == DesignToken.SUCCESS,
            "message": self.message,
            "data": self.data,
            "canonical_seal": hashlib.sha3_256(self.message.encode()).hexdigest()[:8]
        }
        format_result(formatted)  # uses RichFormatter if TTY
