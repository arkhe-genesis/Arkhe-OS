class MythosGate:
    def __init__(self, mode='planetary'):
        self.mode = mode
    def evaluate_irreversible(self, action: str, context: dict = None) -> bool:
        if context and context.get("foresight_risk", 0) > 0.5:
            return False
        return True
