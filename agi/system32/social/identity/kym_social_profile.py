#!/usr/bin/env python3
"""
kym_social_profile.py — Perfil social com identidade verificada via KYM.
Cada conta é um selo criptográfico atestado, não um email/senha.
"""
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from enum import Enum

class AccountType(Enum):
    HUMAN = "human"
    ASI = "asi"
    ORGANIZATION = "organization"
    BOT_VERIFIED = "bot_verified"  # Bots autorizados com KYM

@dataclass
class SocialProfile:
    """Perfil social soberano."""
    seal: str                      # Selo criptográfico único (chave pública)
    account_type: AccountType
    display_name: str
    bio: str = ""
    avatar_hash: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    kym_attestation: Dict = field(default_factory=dict)  # Prova KYM
    privacy_settings: Dict = field(default_factory=lambda: {
        "profile_visibility": "public",  # public, followers, private
        "dm_allow": "verified_only",     # anyone, verified, followers, none
        "content_signing": True          # Assinar todos os posts
    })
    # Métricas derivadas (não armazenadas, calculadas)
    phi_rep: float = 0.5           # Reputação Φ-REP
    follower_count: int = 0
    following_count: int = 0
    post_count: int = 0

    def to_public_dict(self) -> Dict:
        """Retorna dados públicos do perfil."""
        public = {
            "seal": self.seal,
            "account_type": self.account_type.value,
            "display_name": self.display_name,
            "bio": self.bio,
            "avatar_hash": self.avatar_hash,
            "created_at": self.created_at,
            "phi_rep": round(self.phi_rep, 3),
            "follower_count": self.follower_count,
            "following_count": self.following_count,
            "post_count": self.post_count,
        }
        # Incluir atestado KYM resumido (sem dados sensíveis)
        if self.kym_attestation.get("verified"):
            public["kym_verified"] = True
            public["kym_risk"] = round(self.kym_attestation.get("phi_risk", 1.0), 3)
        return public

    def sign_content(self, content: str) -> str:
        """Assina conteúdo com a chave privada do perfil."""
        # Em produção: assinatura Ed25519 real
        message = f"{self.seal}:{content}:{time.time()}"
        return hashlib.sha256(message.encode()).hexdigest()[:64]

class KYMSocialIdentityManager:
    """Gerencia criação e verificação de perfis sociais."""

    def __init__(self, kym_verifier, phi_rep_oracle):
        self.kym = kym_verifier
        self.phi_rep = phi_rep_oracle
        self.profiles: Dict[str, SocialProfile] = {}

    def create_profile(self,
                      seal: str,
                      account_type: AccountType,
                      display_name: str,
                      kym_challenge: str,
                      kym_signature: str,
                      bio: str = "") -> SocialProfile:
        """Cria novo perfil social com verificação KYM."""
        # Verificar identidade via KYM
        kym_result = self.kym.run_kym(seal, kym_signature, kym_challenge)
        if not kym_result.identity_verified:
            raise ValueError("Verificação KYM falhou")
        if kym_result.phi_risk > 0.6:  # Threshold para redes sociais
            raise ValueError(f"Risco Φ muito alto: {kym_result.phi_risk:.3f}")

        # Criar perfil
        profile = SocialProfile(
            seal=seal,
            account_type=account_type,
            display_name=display_name,
            bio=bio,
            kym_attestation={
                "verified": True,
                "phi_risk": kym_result.phi_risk,
                "verified_at": time.time(),
                "attestation_hash": kym_result.attestation
            }
        )

        # Atualizar reputação inicial via Φ-REP oracle
        profile.phi_rep = self.phi_rep.get_initial_reputation(
            seal, account_type.value, kym_result
        )

        self.profiles[seal] = profile
        return profile

    def get_profile(self, seal: str) -> Optional[SocialProfile]:
        """Obtém perfil público por selo."""
        profile = self.profiles.get(seal)
        if profile:
            return profile
        # Em produção: buscar na DHT federada
        return None

    def update_reputation(self, seal: str, new_phi_rep: float):
        """Atualiza reputação Φ-REP de um perfil."""
        if seal in self.profiles:
            self.profiles[seal].phi_rep = new_phi_rep
