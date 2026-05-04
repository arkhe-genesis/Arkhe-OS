from .base import TAUAgent

class MessengerAgent(TAUAgent):
    """
    DELTA (Mensageiro): DAC Interface / qBridge.
    Interface com o mundo externo (Telegram/Firebase).
    """
    def __init__(self):
        super().__init__("DELTA", "Δ", "DAC Interface / qBridge")

    def run_cycle(self) -> bytes:
        self.logger.info("Polling external messages (Telegram Webhook mock)...")
        return self.qhttp_msg({"messages_read": 0}, confidence=1.0)
