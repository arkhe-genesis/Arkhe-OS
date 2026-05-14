#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bioapi_client.py — Cliente para APIs de bancos genômicos (NCBI, JGI, UniProt)
Implementa conexão real com APIs públicas para coleta de dados genômicos.
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional

class BioAPIClient:
    """Cliente unificado para múltiplas APIs de biologia molecular."""

    ENDPOINTS = {
        "ncbi": {
            "base": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            "esearch": "/esearch.fcgi",
            "esummary": "/esummary.fcgi",
            "efetch": "/efetch.fcgi",
        },
        "jgi": {
            "base": "https://genome.jgi.doe.gov",
            "search": "/portal/ext/genome/search.jsf",
            "download": "/portal/ext/download/download.jsf",
        },
        "uniprot": {
            "base": "https://rest.uniprot.org",
            "search": "/uniprotkb/search",
            "retrieve": "/uniprotkb/",
        }
    }

    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def ncbi_search(self, database: str, term: str, retmax: int = 20) -> List[str]:
        """Busca IDs no NCBI Entrez."""
        url = f"{self.ENDPOINTS['ncbi']['base']}{self.ENDPOINTS['ncbi']['esearch']}"
        params = {
            "db": database,
            "term": term,
            "retmode": "json",
            "retmax": retmax,
            "api_key": self.api_keys.get("ncbi", "")
        }
        async with self.session.get(url, params=params) as resp:
            data = await resp.json()
            return data.get("esearchresult", {}).get("idlist", [])

    async def ncbi_fetch_summary(self, database: str, ids: List[str]) -> Dict:
        """Busca resumo de entradas no NCBI."""
        url = f"{self.ENDPOINTS['ncbi']['base']}{self.ENDPOINTS['ncbi']['esummary']}"
        params = {
            "db": database,
            "id": ",".join(ids),
            "retmode": "json",
            "api_key": self.api_keys.get("ncbi", "")
        }
        async with self.session.get(url, params=params) as resp:
            return await resp.json()

    async def uniprot_search(self, query: str, fields: List[str] = None) -> List[Dict]:
        """Busca proteínas no UniProt."""
        url = f"{self.ENDPOINTS['uniprot']['base']}{self.ENDPOINTS['uniprot']['search']}"
        params = {
            "query": query,
            "format": "json",
            "size": 20,
            "fields": ",".join(fields) if fields else "id,organism_name,gene_names,protein_name"
        }
        async with self.session.get(url, params=params) as resp:
            data = await resp.json()
            return data.get("results", [])

    # ... métodos adicionais para JGI, etc.
