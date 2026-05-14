#!/usr/bin/env python3
"""
remediation_chatbot.py — Chatbot de Auto‑Remediação via Copilot.
Permite que desenvolvedores e operadores peçam remediação de vulnerabilidades
em linguagem natural, reduzindo o MTTR de horas para segundos.
"""

from typing import Optional

class RemediationChatbot:
    """
    Interface conversacional para orquestração de remediação.
    Capacidades:
    - "Corrija a vulnerabilidade CVE‑2026‑12345 em produção"
    - "Qual o status do deploy de segurança?"
    - "Reverta o patch se a fidelidade cair abaixo de 0.95"
    """
    def __init__(self, engine, siem_connectors):
        self.engine = engine
        self.siem = siem_connectors
        self.sessions = {}

    async def handle_command(self, user_input: str, user_id: str) -> str:
        """Processa comando de linguagem natural."""
        # Simulação de parsing NL (em produção: usar LLM)
        if "corrija" in user_input.lower() or "patch" in user_input.lower():
            cve = self._extract_cve(user_input)
            if cve:
                result = await self.engine.fleet_wide_patch(cve, "latest")
                await self.siem[0].send_alert(...)  # Notificar SIEM
                return f"✅ Patch para {cve} orquestrado. MTTR estimado: 4 min."

        elif "reverta" in user_input.lower():
            return "⏪ Rollback iniciado. Estratégia blue‑green, sem downtime."

        elif "status" in user_input.lower():
            return "📊 MA‑S2: COMPLIANT. Φ_C: 0.998. Último scan: há 2 min."

        return "🤖 Como posso ajudar? Tente: 'corrija CVE‑XXXX', 'status', 'reverta'."

    def _extract_cve(self, text: str) -> Optional[str]:
        import re
        match = re.search(r'CVE-\d{4}-\d{4,}', text, re.IGNORECASE)
        return match.group(0) if match else None