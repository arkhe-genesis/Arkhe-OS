#!/usr/bin/env python3
"""
registry.py — Cliente do registry federado de pacotes via DHT.
Integra com Substrato 321 (Federation) e 344 (Φ-REP).
"""
import asyncio
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class PackageIndexEntry:
    """Entrada no índice de pacotes do registry."""
    name: str
    version: str
    hash_sha3_256: str
    signature: str
    maintainer_seal: str
    phi_rep: float
    coherence_score: Optional[float]
    ipfs_cid: str
    published_at: float
    downloads: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)

class SovereignRegistryClient:
    """Cliente para o registry federado de pacotes ARKHE OS."""

    DHT_PREFIX = "pkg:arkhe:"
    MIRROR_URL = "https://pypi.arkhe.onion/simple"

    def __init__(self, dht_client=None, phi_rep_oracle=None):
        self.dht = dht_client  # Substrate 321 DHT client
        self.phi_rep = phi_rep_oracle  # Substrate 344 Φ-REP oracle
        self._cache: Dict[str, PackageIndexEntry] = {}
        self._cache_ttl = 300  # 5 minutos

    def _dht_key(self, package_name: str, version: Optional[str] = None) -> str:
        """Gerar chave DHT para pacote."""
        if version:
            return f"{self.DHT_PREFIX}{package_name}=={version}"
        return f"{self.DHT_PREFIX}{package_name}"

    async def _query_dht(self, key: str) -> Optional[Dict]:
        """Consultar DHT por entrada de pacote."""
        if self.dht:
            result = await self.dht.retrieve(key)
            if result:
                return json.loads(result)
        return None

    def get_package_manifest(self, package_name: str,
                          version: Optional[str] = None) -> Optional[PackageIndexEntry]:
        """Obter manifesto de pacote do registry."""
        # Verificar cache primeiro
        cache_key = f"{package_name}=={version or 'latest'}"
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if time.time() - entry.published_at < self._cache_ttl:
                return entry

        # Query DHT
        key = self._dht_key(package_name, version)
        loop = asyncio.get_event_loop()
        data = loop.run_until_complete(self._query_dht(key))

        if not data:
            # Fallback: tentar mirror HTTP
            return self._fetch_from_mirror(package_name, version)

        entry = PackageIndexEntry(**data)
        self._cache[cache_key] = entry
        return entry

    def _fetch_from_mirror(self, package_name: str,
                          version: Optional[str] = None) -> Optional[PackageIndexEntry]:
        """Fallback: buscar do mirror HTTP .onion."""
        import requests
        try:
            # Simple API do PyPI
            url = f"{self.MIRROR_URL}/{package_name}/json"
            if version:
                url = f"{self.MIRROR_URL}/{package_name}/{version}/json"

            resp = requests.get(url, timeout=10, proxies={
                'http': 'socks5h://127.0.0.1:9050',
                'https': 'socks5h://127.0.0.1:9050'
            })
            resp.raise_for_status()
            data = resp.json()

            # Converter para PackageIndexEntry
            return PackageIndexEntry(
                name=data['name'],
                version=data['version'],
                hash_sha3_256=data['hash_sha3_256'],
                signature=data['signature'],
                maintainer_seal=data['maintainer_seal'],
                phi_rep=data.get('phi_rep', 0.5),
                coherence_score=data.get('coherence_score'),
                ipfs_cid=data['ipfs_cid'],
                published_at=data['published_at']
            )
        except Exception:
            return None

    def search(self, query: str, min_phi_rep: float = 0.7,
              limit: int = 20) -> List[PackageIndexEntry]:
        """Buscar pacotes no registry."""
        # Em produção: query DHT com filtro
        # Aqui: simular resultados
        results = []
        # (Implementação simplificada)
        return results[:limit]

    def get_maintainer_public_key(self, maintainer_seal: str) -> Optional[bytes]:
        """Obter chave pública de um mantenedor via KYM."""
        # Integração com Substrate 5006 (KYM)
        # Em produção: consultar ledger de identidades
        return None  # Placeholder

    def publish_package(self, entry: PackageIndexEntry,
                       signature: str, kym_proof: Optional[str] = None) -> bool:
        """Publicar novo pacote no registry."""
        # 1. Verificar KYM do mantenedor
        if kym_proof:
            from .kym_integration import verify_kym_proof
            if not verify_kym_proof(entry.maintainer_seal, kym_proof):
                return False

        # 2. Publicar na DHT
        key = self._dht_key(entry.name, entry.version)
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(
            self.dht.store(key, json.dumps(entry.to_dict()))
        ) if self.dht else False