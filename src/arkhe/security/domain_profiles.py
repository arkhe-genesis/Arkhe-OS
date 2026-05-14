#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
domain_profiles.py — Substrato 172-OMEGA: Perfis de Domínio para Atrator Adaptativo
Ajusta parâmetros do campo atratora baseado no tipo de tarefa criativa/técnica/educacional.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Optional

class DomainProfile(Enum):
    """Perfis de domínio para configuração adaptativa do atrator."""
    CREATIVE_WRITING = "creative"      # Ficção, poesia, brainstorming
    TECHNICAL_DOCS = "technical"        # Documentação, especificações, código
    EDUCATIONAL = "educational"         # Explicações, tutoriais, ensino
    SCIENTIFIC = "scientific"           # Pesquisa, análise de dados, hipóteses
    CONVERSATIONAL = "conversational"   # Diálogo, suporte, assistência
    DEFAULT = "default"                 # Perfil balanceado

@dataclass
class AttractorProfile:
    """Configuração de parâmetros do atrator por domínio."""
    profile: DomainProfile
    alpha: float = 1.5      # Peso do potencial atrator (coerência)
    beta: float = 0.4       # Peso da surpresa (diversidade)
    gamma: float = 0.3      # Peso da ressonância (contexto)
    temperature: float = 0.8  # Temperatura de amostragem
    min_coherence: float = 0.75  # Coerência mínima aceitável
    max_surprise: float = 2.5    # Limite de surpresa para evitar alucinações
    description: str = ""

# Catálogo de perfis pré-definidos
DOMAIN_PROFILES: Dict[DomainProfile, AttractorProfile] = {
    DomainProfile.CREATIVE_WRITING: AttractorProfile(
        profile=DomainProfile.CREATIVE_WRITING,
        alpha=2.0,   # Alta coerência narrativa
        beta=0.6,    # Mais surpresa para criatividade
        gamma=0.4,   # Ressonância moderada com contexto
        temperature=0.9,  # Amostragem mais diversa
        min_coherence=0.70,  # Flexível para criatividade
        max_surprise=3.0,    # Permitir mais inovação
        description="Otimizado para ficção, poesia e geração criativa"
    ),

    DomainProfile.TECHNICAL_DOCS: AttractorProfile(
        profile=DomainProfile.TECHNICAL_DOCS,
        alpha=1.0,   # Coerência técnica prioritária
        beta=0.2,    # Baixa surpresa para precisão
        gamma=0.6,   # Alta ressonância com contexto técnico
        temperature=0.6,  # Amostragem conservadora
        min_coherence=0.90,  # Alta precisão requerida
        max_surprise=1.5,    # Limitar inovação para evitar erros
        description="Otimizado para documentação técnica e especificações"
    ),

    DomainProfile.EDUCATIONAL: AttractorProfile(
        profile=DomainProfile.EDUCATIONAL,
        alpha=1.5,   # Balanceado
        beta=0.5,    # Surpresa moderada para engajamento
        gamma=0.5,   # Ressonância com nível do aluno
        temperature=0.8,  # Balanceado
        min_coherence=0.80,  # Clareza pedagógica
        max_surprise=2.0,    # Permitir analogias criativas
        description="Otimizado para explicações e conteúdo educacional"
    ),

    DomainProfile.SCIENTIFIC: AttractorProfile(
        profile=DomainProfile.SCIENTIFIC,
        alpha=1.8,   # Alta coerência lógica
        beta=0.3,    # Baixa surpresa para rigor
        gamma=0.7,   # Alta ressonância com literatura
        temperature=0.7,  # Conservador
        min_coherence=0.85,  # Rigor científico
        max_surprise=1.8,    # Hipóteses controladas
        description="Otimizado para pesquisa e análise científica"
    ),

    DomainProfile.CONVERSATIONAL: AttractorProfile(
        profile=DomainProfile.CONVERSATIONAL,
        alpha=1.2,   # Coerência conversacional
        beta=0.5,    # Surpresa para naturalidade
        gamma=0.6,   # Alta ressonância com histórico
        temperature=0.85,  # Natural
        min_coherence=0.75,  # Fluidez dialógica
        max_surprise=2.2,    # Permitir variações naturais
        description="Otimizado para diálogo e assistência interativa"
    ),

    DomainProfile.DEFAULT: AttractorProfile(
        profile=DomainProfile.DEFAULT,
        alpha=1.5,
        beta=0.4,
        gamma=0.3,
        temperature=0.8,
        min_coherence=0.75,
        max_surprise=2.0,
        description="Perfil balanceado para uso geral"
    ),
}

class DomainProfileDetector:
    """Detecta domínio da tarefa baseado em prompt e contexto."""

    # Palavras-chave indicativas por domínio (simplificado)
    DOMAIN_KEYWORDS = {
        DomainProfile.CREATIVE_WRITING: [
            "story", "poem", "fiction", "character", "plot", "imagine", "creative",
            "escreva uma história", "poema", "ficção", "personagem"
        ],
        DomainProfile.TECHNICAL_DOCS: [
            "specification", "api", "function", "parameter", "implement", "code",
            "documentação", "api", "função", "parâmetro", "implementar"
        ],
        DomainProfile.EDUCATIONAL: [
            "explain", "teach", "learn", "tutorial", "beginner", "understand",
            "explique", "ensinar", "aprender", "tutorial", "iniciante"
        ],
        DomainProfile.SCIENTIFIC: [
            "hypothesis", "experiment", "data", "analysis", "research", "study",
            "hipótese", "experimento", "dados", "análise", "pesquisa"
        ],
        DomainProfile.CONVERSATIONAL: [
            "hello", "help", "question", "answer", "chat", "discuss",
            "olá", "ajuda", "pergunta", "resposta", "conversar"
        ],
    }

    @classmethod
    def detect(cls, prompt: str, context: Optional[str] = None) -> DomainProfile:
        """Detecta domínio baseado em análise lexical simples."""
        text = (prompt + " " + (context or "")).lower()

        # Contar matches por domínio
        scores = {}
        for domain, keywords in cls.DOMAIN_KEYWORDS.items():
            scores[domain] = sum(1 for kw in keywords if kw in text)

        # Retornar domínio com maior score, ou default se empate
        if not scores or max(scores.values()) == 0:
            return DomainProfile.DEFAULT

        return max(scores, key=scores.get)

    @classmethod
    def get_profile(cls, domain: DomainProfile) -> AttractorProfile:
        """Retorna configuração de atrator para domínio."""
        return DOMAIN_PROFILES.get(domain, DOMAIN_PROFILES[DomainProfile.DEFAULT])
