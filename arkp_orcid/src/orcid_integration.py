#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
orcid_integration.py — Integração Completa com a API ORCID
Permite enriquecer o perfil de reputação QIP com publicações,
histórico de empregos e qualificações do ORCID.
"""

import aiohttp
from typing import Dict, List, Optional
import json

class OrcidAPIClient:
    """Cliente para interagir com a API Pública do ORCID."""

    BASE_URL = "https://pub.orcid.org/v3.0"

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token

    async def get_profile(self, orcid_id: str) -> Dict:
        """Obtém o perfil completo (dados biográficos e atividades)."""
        headers = {"Accept": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.BASE_URL}/{orcid_id}", headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                return {"error": f"Failed to fetch profile: {response.status}"}

    async def get_works(self, orcid_id: str) -> List[Dict]:
        """Obtém lista de publicações (works) do pesquisador."""
        headers = {"Accept": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.BASE_URL}/{orcid_id}/works", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    works = []
                    for group in data.get("group", []):
                        work_summary = group.get("work-summary", [])
                        if work_summary:
                            works.append(work_summary[0])
                    return works
                return []

class ReputationEnricher:
    """Enriquece perfis de revisores ARKHE com dados do ORCID."""

    def __init__(self, orcid_client: OrcidAPIClient):
        self.orcid_client = orcid_client

    async def enrich_reviewer_profile(self, orcid_id: str) -> Dict:
        """Coleta dados do ORCID para influenciar o peso no QIP."""
        works = await self.orcid_client.get_works(orcid_id)

        # Lógica simplificada: +0.01 de peso por publicação relevante
        publication_bonus = min(0.2, len(works) * 0.01)

        return {
            "orcid": orcid_id,
            "publications_count": len(works),
            "reputation_bonus": publication_bonus,
            "works_summary": [w.get("title", {}).get("title", {}).get("value", "Unknown") for w in works[:5]]
        }
