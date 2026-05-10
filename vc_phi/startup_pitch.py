from typing import List, Dict

from ..audit.ledger import Ledger

class StartupPitch:
    def __init__(self, kym_verifier):
        self.kym = kym_verifier
    def submit(self, team_seals: List[str], proposal: Dict) -> bool:
        # Verificar KYM de todos os fundadores
        for seal in team_seals:
            if not self.kym.verify(seal):
                raise PermissionError("KYM verification failed")
        # Registrar proposta no ledger
        Ledger.record("pitch_submitted", proposal)
        return True