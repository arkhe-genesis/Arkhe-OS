import sys

prompt_text = """
def enable_recovery_email(self, config: EmailConfig):
        self.gateway = RecoveryEmailGateway(self.ledger, self.chain, self.validator, config)
        log.info("Recovery Email habilitado no roteador.")

    def send_message_with_fallback(self, msg: TemporalMessage) -> bool:
        # Simula falha do transporte primário
        if np.random.random() > self._primary_fail_rate:
            log.info("📡 Transporte primário: SUCESSO (%s)", msg.id[:12])
            msg.delivered = True
            self.ledger.record("primary_delivered", {'msg_id': msg.id})
            return True
        # Fallback para e-mail
        log.warning("📡 Transporte primário: FALHA (%s) -> fallback para e-mail", msg.id[:12])
        if self.gateway:
            vr = self.validator.validate(msg)
            self.gateway.enqueue(msg, vr.score, self.chain.head_hash())
            return True
        return False
"""
print("head_hash()" in prompt_text)
