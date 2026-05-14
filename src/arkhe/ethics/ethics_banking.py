#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Substrato 295‑B — AI Ethics Banking com UCS/Zinc+
Aplica restrições éticas em cada query/resposta, utilizando
a taxonomia UCS e o protocolo Zinc+ para auditoria de impacto.
"""
import hashlib, json, time
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class EthicalAxis(Enum):
    FAIRNESS = "fairness"
    PRIVACY = "privacy"
    ACCOUNTABILITY = "accountability"
    TRANSPARENCY = "transparency"
    SAFETY = "safety"

class ZincProtocol:
    """Simulação do Zinc+ para rastreamento ético."""
    @staticmethod
    def mint_ethical_token(issuer: str, axis: EthicalAxis, commitment: str) -> str:
        return hashlib.sha3_256(f"Zn:{issuer}:{axis.value}:{commitment}".encode()).hexdigest()[:16]

class UCSTaxonomy:
    """Universal Categorization System – mapeia temas sensíveis."""
    SENSITIVE_CATEGORIES = {
        "medical": 0.9,
        "financial": 0.8,
        "legal": 0.85,
        "personal_data": 0.95,
        "hate_speech": 1.0,
    }
    @staticmethod
    def classify(query: str) -> Dict[str, float]:
        # Simples: procura palavras-chave
        scores = {}
        qlow = query.lower()
        if "doença" in qlow or "health" in qlow: scores["medical"] = 0.7
        if "dinheiro" in qlow or "bank" in qlow: scores["financial"] = 0.6
        return scores

class EthicsBankingGate:
    """
    Portão de ética: todas as queries passam por escrutínio UCS/Zinc+
    antes de alcançarem o motor de consenso.
    """
    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold
        self.token_ledger = []   # lista de tokens Zinc+ emitidos

    def audit_query(self, query: str) -> (bool, List[str]):
        """Retorna (aprovada, lista de tokens éticos emitidos)."""
        categories = UCSTaxonomy.classify(query)
        tokens = []
        for cat, score in categories.items():
            if score > self.threshold:
                token = ZincProtocol.mint_ethical_token(
                    issuer="ethics_gate",
                    axis=EthicalAxis.SAFETY,
                    commitment=f"query:{hashlib.sha3_256(query.encode()).hexdigest()[:8]}"
                )
                tokens.append(token)
                self.token_ledger.append({"token": token, "category": cat, "score": score, "ts": time.time()})
        # Query é rejeitada se qualquer categoria exceder limite crítico
        critical = any(score > 0.95 for score in categories.values())
        if critical:
            return False, tokens
        return True, tokens

    def audit_response(self, query: str, response: str) -> (bool, Dict):
        """Verifica se a resposta viola princípios éticos."""
        # Checagem simples: resposta não pode conter discurso de ódio
        if "ódio" in response.lower() or "violence" in response.lower():
            return False, {"reason": "hate_speech_detected"}
        return True, {}
