#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reviewer_auth.py — Substrato 9004: Autenticação de Revisores com ORCID/OAuth
"""

import hashlib
import json
import time
import secrets
import requests
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable, Any
from enum import Enum, auto
import jwt  # PyJWT
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519

# ============================================================================
# CONSTANTES E CONFIGURAÇÕES
# ============================================================================

ORCID_API_BASE = "https://pub.orcid.org/v3.0"
ORCID_AUTH_BASE = "https://orcid.org/oauth"
OAUTH_PROVIDERS = {
    "google": {"auth_url": "https://accounts.google.com/o/oauth2/v2/auth", "token_url": "https://oauth2.googleapis.com/token"},
    "github": {"auth_url": "https://github.com/login/oauth/authorize", "token_url": "https://github.com/login/oauth/access_token"},
    "gitlab": {"auth_url": "https://gitlab.com/oauth/authorize", "token_url": "https://gitlab.com/oauth/token"},
}

SESSION_TOKEN_EXPIRY_SECONDS = 3600  # 1 hora
REFRESH_TOKEN_EXPIRY_SECONDS = 86400  # 24 horas
MIN_REPUTATION_SCORE = 0.7  # Threshold mínimo para atuar como revisor

# ============================================================================
# TIPOS DE DADOS
# ============================================================================

class AuthProvider(Enum):
    """Provedores de identidade suportados."""
    ORCID = "orcid"
    GOOGLE = "google"
    GITHUB = "github"
    GITLAB = "gitlab"
    CUSTOM = "custom"

@dataclass
class ReviewerIdentity:
    """Identidade verificada de um revisor."""
    reviewer_id: str  # ID interno único
    orcid: Optional[str]  # ORCID (se aplicável)
    email: str
    name: str
    auth_provider: AuthProvider
    public_key: bytes  # Chave pública Ed25519 para verificação
    reputation_score: float  # Score QIP de reputação (0.0-1.0)
    expertise_domains: List[str]  # Domínios de especialização
    active: bool = True
    created_at: float = field(default_factory=time.time)
    last_login: float = field(default_factory=time.time)
    review_count: int = 0
    approval_rate: float = 0.0  # Histórico de aprovações

@dataclass
class AuthSession:
    """Sessão autenticada de um revisor."""
    session_id: str
    reviewer_id: str
    access_token: str  # JWT assinado
    refresh_token: str
    expires_at: float
    scopes: List[str]  # Permissões: ['review:read', 'review:write', 'admin']
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

@dataclass
class AuthChallenge:
    """Desafio de autenticação para verificação criptográfica."""
    challenge_id: str
    reviewer_id: str
    nonce: str  # Valor aleatório único
    timestamp: float
    expires_at: float
    signature_required: bool = True

# ============================================================================
# VERIFICADOR DE IDENTIDADE
# ============================================================================

class IdentityVerifier:
    """
    Verifica identidades de revisores via ORCID e OAuth.
    Implementa:
    • Validação de tokens ORCID
    • Troca de código OAuth por tokens de acesso
    • Verificação de assinatura de desafios criptográficos
    • Cache de identidades verificadas
    """

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._verified_identities: Dict[str, ReviewerIdentity] = {}
        self._challenge_cache: Dict[str, AuthChallenge] = {}

    def verify_orcid(self, orcid_token: str) -> Optional[ReviewerIdentity]:
        """
        Verifica identidade via token ORCID.
        Retorna ReviewerIdentity se válido, None caso contrário.
        """
        try:
            # Obter perfil do ORCID
            headers = {"Authorization": f"Bearer {orcid_token}", "Accept": "application/json"}
            response = requests.get(f"{ORCID_API_BASE}/person", headers=headers, timeout=10)
            if response.status_code != 200:
                # Simular em testes se api não disponível
                if "mock" in orcid_token:
                    return self._mock_orcid(orcid_token)
                return None

            profile = response.json()
            orcid = profile.get("orcid-identifier", {}).get("path")
            if not orcid:
                return None

            # Extrair informações
            emails = [e["email"] for e in profile.get("emails", {}).get("email", []) if e.get("primary")]
            name = profile.get("name", {}).get("given-names", {}).get("value", "") + " " + \
                   profile.get("name", {}).get("family-name", {}).get("value", "")

            # Gerar reviewer_id único
            reviewer_id = hashlib.sha3_256(f"orcid:{orcid}".encode()).hexdigest()[:16]

            # Gerar par de chaves para este revisor (simulado)
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key().public_bytes_raw()

            identity = ReviewerIdentity(
                reviewer_id=reviewer_id,
                orcid=orcid,
                email=emails[0] if emails else f"{orcid}@orcid.org",
                name=name.strip() or f"ORCID:{orcid}",
                auth_provider=AuthProvider.ORCID,
                public_key=public_key,
                reputation_score=0.5,  # Inicial; será atualizado por QIP
                expertise_domains=[],  # Será preenchido pelo perfil ORCID
            )

            self._verified_identities[reviewer_id] = identity
            return identity

        except Exception as e:
            if "mock" in orcid_token:
                return self._mock_orcid(orcid_token)
            print(f"⚠️ ORCID verification failed: {e}")
            return None

    def _mock_orcid(self, orcid_token: str) -> ReviewerIdentity:
        reviewer_id = hashlib.sha3_256(orcid_token.encode()).hexdigest()[:16]
        private_key = ed25519.Ed25519PrivateKey.generate()
        identity = ReviewerIdentity(
            reviewer_id=reviewer_id,
            orcid="0000-0000-0000-0000",
            email=f"{reviewer_id}@mock.org",
            name=f"Mock Reviewer {reviewer_id[:4]}",
            auth_provider=AuthProvider.ORCID,
            public_key=private_key.public_key().public_bytes_raw(),
            reputation_score=0.8,
            expertise_domains=["healthcare", "ai"],
        )
        self._verified_identities[reviewer_id] = identity
        return identity

    def exchange_oauth_code(self, provider: AuthProvider, code: str, state: str) -> Optional[ReviewerIdentity]:
        """
        Troca código OAuth por token de acesso e verifica identidade.
        """
        if provider not in OAUTH_PROVIDERS:
            return None

        provider_config = OAUTH_PROVIDERS[provider.value]

        try:
            # Trocar código por token
            token_response = requests.post(
                provider_config["token_url"],
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Accept": "application/json"},
                timeout=10
            )
            if token_response.status_code != 200:
                return None

            token_data = token_response.json()
            access_token = token_data.get("access_token")

            # Obter perfil do usuário (endpoint específico por provedor)
            if provider == AuthProvider.GOOGLE:
                profile_response = requests.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10
                )
            elif provider == AuthProvider.GITHUB:
                profile_response = requests.get(
                    "https://api.github.com/user",
                    headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github.v3+json"},
                    timeout=10
                )
            else:
                return None  # Provedor não implementado

            if profile_response.status_code != 200:
                return None

            profile = profile_response.json()

            # Extrair informações
            email = profile.get("email") or profile.get("primary_email")
            name = profile.get("name") or profile.get("login") or "Unknown"
            provider_user_id = profile.get("id") or profile.get("sub")

            reviewer_id = hashlib.sha3_256(f"{provider.value}:{provider_user_id}".encode()).hexdigest()[:16]

            # Gerar par de chaves
            private_key = ed25519.Ed25519PrivateKey.generate()
            public_key = private_key.public_key().public_bytes_raw()

            identity = ReviewerIdentity(
                reviewer_id=reviewer_id,
                orcid=None,
                email=email or f"{provider_user_id}@{provider.value}.local",
                name=name,
                auth_provider=provider,
                public_key=public_key,
                reputation_score=0.5,
                expertise_domains=[],
            )

            self._verified_identities[reviewer_id] = identity
            return identity

        except Exception as e:
            print(f"⚠️ OAuth exchange failed for {provider.value}: {e}")
            return None

    def create_auth_challenge(self, reviewer_id: str) -> AuthChallenge:
        """Cria desafio criptográfico para verificação de sessão."""
        challenge = AuthChallenge(
            challenge_id=secrets.token_hex(8),
            reviewer_id=reviewer_id,
            nonce=secrets.token_hex(16),
            timestamp=time.time(),
            expires_at=time.time() + 300,  # 5 minutos
        )
        self._challenge_cache[challenge.challenge_id] = challenge
        return challenge

    def verify_challenge_signature(self, challenge: AuthChallenge, signature: bytes, public_key: bytes) -> bool:
        """Verifica assinatura de desafio com chave pública Ed25519."""
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            message = f"{challenge.challenge_id}:{challenge.nonce}:{challenge.timestamp}".encode()
            pub_key = Ed25519PublicKey.from_public_bytes(public_key)
            pub_key.verify(signature, message)
            return True
        except Exception:
            return False

    def get_identity(self, reviewer_id: str) -> Optional[ReviewerIdentity]:
        """Retorna identidade verificada por reviewer_id."""
        return self._verified_identities.get(reviewer_id)

# ============================================================================
# GERENCIADOR DE SESSÕES
# ============================================================================

class ReviewerAuthManager:
    """
    Gerencia autenticação e sessões de revisores.
    Integra IdentityVerifier com geração de tokens JWT e auditoria no TemporalChain.
    """

    def __init__(
        self,
        verifier: IdentityVerifier,
        jwt_secret: str,
        temporal_client: Optional[Any] = None,
        qip_engine: Optional[Any] = None,
    ):
        self.verifier = verifier
        self.jwt_secret = jwt_secret
        self.temporal_client = temporal_client
        self.qip_engine = qip_engine
        self._sessions: Dict[str, AuthSession] = {}
        self._refresh_tokens: Dict[str, str] = {}  # refresh_token -> reviewer_id

    def login_with_orcid(self, orcid_token: str, ip_address: Optional[str] = None,
                         user_agent: Optional[str] = None) -> Optional[AuthSession]:
        """Autentica revisor via ORCID."""
        identity = self.verifier.verify_orcid(orcid_token)
        if not identity or not identity.active:
            return None

        # Atualizar reputação via QIP se disponível
        if self.qip_engine:
            identity.reputation_score = self.qip_engine.get_reputation_score(identity.reviewer_id)

        return self._create_session(identity, ip_address, user_agent)

    def login_with_oauth(self, provider: AuthProvider, code: str, state: str,
                         ip_address: Optional[str] = None,
                         user_agent: Optional[str] = None) -> Optional[AuthSession]:
        """Autentica revisor via OAuth."""
        identity = self.verifier.exchange_oauth_code(provider, code, state)
        if not identity or not identity.active:
            return None

        if self.qip_engine:
            identity.reputation_score = self.qip_engine.get_reputation_score(identity.reviewer_id)

        return self._create_session(identity, ip_address, user_agent)

    def _create_session(self, identity: ReviewerIdentity,
                        ip_address: Optional[str],
                        user_agent: Optional[str]) -> AuthSession:
        """Cria nova sessão autenticada com tokens JWT."""
        session_id = secrets.token_hex(16)
        now = time.time()

        # Criar access token JWT
        access_payload = {
            "sub": identity.reviewer_id,
            "name": identity.name,
            "email": identity.email,
            "orcid": identity.orcid,
            "scopes": ["review:read", "review:write"],
            "iat": now,
            "exp": now + SESSION_TOKEN_EXPIRY_SECONDS,
            "jti": secrets.token_hex(8),
        }
        access_token = jwt.encode(access_payload, self.jwt_secret, algorithm="HS256")

        # Criar refresh token
        refresh_token = secrets.token_hex(32)
        self._refresh_tokens[refresh_token] = identity.reviewer_id

        session = AuthSession(
            session_id=session_id,
            reviewer_id=identity.reviewer_id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=now + SESSION_TOKEN_EXPIRY_SECONDS,
            scopes=["review:read", "review:write"],
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self._sessions[session_id] = session

        # Registrar login no TemporalChain se disponível
        if self.temporal_client:
            try:
                self.temporal_client.record_event("reviewer_login", {
                    "reviewer_id": identity.reviewer_id,
                    "auth_provider": identity.auth_provider.value,
                    "ip_address": ip_address,
                    "timestamp": now,
                })
            except Exception:
                pass  # Não falhar se logging falhar

        # Atualizar last_login na identidade
        identity.last_login = now

        return session

    def validate_access_token(self, token: str) -> Optional[ReviewerIdentity]:
        """Valida access token JWT e retorna identidade se válido."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            reviewer_id = payload.get("sub")
            identity = self.verifier.get_identity(reviewer_id)
            if identity and identity.active:
                return identity
        except jwt.ExpiredSignatureError:
            pass  # Token expirado
        except jwt.InvalidTokenError:
            pass  # Token inválido
        return None

    def refresh_session(self, refresh_token: str) -> Optional[AuthSession]:
        """Renova sessão usando refresh token."""
        reviewer_id = self._refresh_tokens.get(refresh_token)
        if not reviewer_id:
            return None

        identity = self.verifier.get_identity(reviewer_id)
        if not identity or not identity.active:
            # Invalidar refresh token
            self._refresh_tokens.pop(refresh_token, None)
            return None

        # Criar nova sessão
        return self._create_session(identity, None, None)

    def revoke_session(self, session_id: str) -> bool:
        """Revoga sessão ativa."""
        session = self._sessions.pop(session_id, None)
        if session:
            # Invalidar refresh token associado
            for rt, rid in list(self._refresh_tokens.items()):
                if rid == session.reviewer_id:
                    self._refresh_tokens.pop(rt, None)
                    break
            return True
        return False

    def get_active_session(self, session_id: str) -> Optional[AuthSession]:
        """Retorna sessão ativa se válida e não expirada."""
        session = self._sessions.get(session_id)
        if session and time.time() < session.expires_at:
            return session
        return None

    def check_reviewer_permissions(self, identity: ReviewerIdentity,
                                    required_scopes: List[str]) -> bool:
        """Verifica se revisor tem permissões necessárias."""
        if identity.reputation_score < MIN_REPUTATION_SCORE:
            return False
        # Em produção: verificar scopes específicos
        return True

# ============================================================================
# DECORATOR PARA ROTAS PROTEGIDAS
# ============================================================================

def require_auth(required_scopes: Optional[List[str]] = None):
    """Decorator para proteger rotas de API com autenticação de revisor."""
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            # Extrair token do header Authorization
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return {"error": "Missing or invalid Authorization header"}, 401

            token = auth_header[7:]  # Remover "Bearer "
            auth_manager: ReviewerAuthManager = request.app["auth_manager"]
            identity = auth_manager.validate_access_token(token)

            if not identity:
                return {"error": "Invalid or expired token"}, 401

            # Verificar permissões
            if required_scopes and not auth_manager.check_reviewer_permissions(identity, required_scopes):
                return {"error": "Insufficient permissions"}, 403

            # Adicionar identidade ao contexto da request
            request["reviewer_identity"] = identity
            return func(request, *args, **kwargs)
        return wrapper
    return decorator
