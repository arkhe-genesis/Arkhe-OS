# dynamic_consent_protocol.py — Protocolo de consentimento dinâmico e adaptativo

import logging
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from explainability_engine import ExplanationPersona

class PrivacyProfile(Enum):
    CONSERVATIVE = auto()  # Alta privacidade, uso mínimo de dados, explicações focadas em direitos
    BALANCED = auto()      # Privacidade média, uso padrão, explicações claras e diretas
    OPEN = auto()          # Menor privacidade para maior personalização, explicações detalhadas

@dataclass
class CitizenPrivacyProfile:
    citizen_id: str
    profile: PrivacyProfile
    consents: Dict[str, bool] # Mapeamento de propósito para consentimento dado

class DataCategory(Enum):
    HEALTH = auto()
    SENSORIAL = auto()
    TOPOLOGICAL = auto()
    GENERIC = auto()

class ConsentManager:
    """Mock for ConsentManager if it's expected by other parts of the system."""
    def __init__(self):
        self.profiles: Dict[str, Any] = {}

    def validate_action(self, citizen_id: str, action_purpose: str) -> bool:
        return True # Default to True for the mock

class DynamicConsentProtocol:
    """
    Protocolo de consentimento dinâmico que adapta explicações e ações
    com base no perfil de privacidade do cidadão.
    """

    def __init__(self, explainability_engine: Any):
        self.explainability = explainability_engine
        self.citizen_profiles: Dict[str, CitizenPrivacyProfile] = {}

    def set_citizen_profile(self, citizen_id: str, profile: PrivacyProfile, consents: Dict[str, bool]):
        """Define ou atualiza o perfil de um cidadão."""
        self.citizen_profiles[citizen_id] = CitizenPrivacyProfile(
            citizen_id=citizen_id,
            profile=profile,
            consents=consents
        )
        logging.info(f"[CONSENT] Perfil do cidadão {citizen_id} definido como {profile.name}")

    def get_adapted_persona(self, citizen_id: str) -> ExplanationPersona:
        """
        Determina qual persona de explicação usar com base no perfil de privacidade.
        """
        profile_data = self.citizen_profiles.get(citizen_id)
        if not profile_data:
            return ExplanationPersona.CITIZEN # Padrão seguro

        if profile_data.profile == PrivacyProfile.CONSERVATIVE:
            # Para perfis conservadores, focamos na linguagem de direitos do cidadão
            return ExplanationPersona.CITIZEN
        elif profile_data.profile == PrivacyProfile.OPEN:
            # Para perfis abertos, podemos fornecer detalhes mais técnicos ou executivos
            return ExplanationPersona.TECHNICAL
        else:
            return ExplanationPersona.CITIZEN

    def validate_action(self, citizen_id: str, action_purpose: str) -> bool:
        """
        Verifica se uma ação pretendida possui consentimento dinâmico.
        """
        profile_data = self.citizen_profiles.get(citizen_id)
        if not profile_data:
            logging.warning(f"[CONSENT] Cidadão {citizen_id} não encontrado. Ação {action_purpose} negada.")
            return False

        has_consent = profile_data.consents.get(action_purpose, False)

        if not has_consent:
            logging.warning(f"[CONSENT] Cidadão {citizen_id} não deu consentimento para {action_purpose}.")

        return has_consent

    def adapt_data_retention(self, citizen_id: str, base_days: int) -> int:
        """
        Adapta o prazo de retenção de dados com base no perfil.
        """
        profile_data = self.citizen_profiles.get(citizen_id)
        if not profile_data:
            return min(base_days, 7) # Padrão restritivo

        if profile_data.profile == PrivacyProfile.CONSERVATIVE:
            return min(base_days, 3) # Retenção curta
        elif profile_data.profile == PrivacyProfile.OPEN:
            return max(base_days, 30) # Permite retenção longa para análise
        else:
            return base_days

    def get_privacy_notice(self, citizen_id: str) -> str:
        """
        Gera um aviso de privacidade adaptado ao perfil.
        """
        profile_data = self.citizen_profiles.get(citizen_id)
        if not profile_data:
            return "Seus dados são protegidos pela Catedral sob a LGPD."

        if profile_data.profile == PrivacyProfile.CONSERVATIVE:
            return "Privacidade Total: Seus dados são usados apenas para o estritamente necessário e apagados rapidamente."
        elif profile_data.profile == PrivacyProfile.OPEN:
            return "Experiência Personalizada: Utilizamos seus dados para otimizar sua interação com a Catedral."
        else:
            return "Uso Equilibrado: Seus dados são usados com transparência para melhorar nossos serviços."
