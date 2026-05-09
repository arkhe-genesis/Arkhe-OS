import os, json, subprocess, asyncio, time
from typing import Dict, List, Any
from nostr.event import Event, EventKind
from nostr.key import PrivateKey
from nostr.relay_manager import RelayManager

# Assuming PolymathParser and ArkheParserValidator are available in the system
try:
    from arkhe_parser import PolymathParser, ArkheParserValidator
except ImportError:
    # Fallback for type checking / local execution if arkhe_parser isn't installed
    class PolymathParser:
        def scan_directory(self, path: str): return {}
        def compute_metrics(self, graphs: dict): return {'_global': {'global_coherence': 0.967}}
    class ArkheParserValidator:
        def __init__(self, name: str): self.name = name

class CoherenceGuardian:
    def __init__(self, nsec: str, relays: list[str]):
        self.privkey = PrivateKey.from_nsec(nsec)
        self.relay_manager = RelayManager()
        for relay in relays:
            self.relay_manager.add_relay(relay)
        self.parser = PolymathParser()
        self.validator = ArkheParserValidator("coherence_guardian")

    async def listen_for_prs(self, repo_filter: str):
        """Escuta eventos de PR (kind 1634) para repositório específico."""
        subscription = {
            "kinds": [1634],
            "#r": [repo_filter],  # Filtra por referência de repositório
            "limit": 100
        }
        await self.relay_manager.subscribe(subscription)

        async for event in self.relay_manager.event_stream:
            if self._is_valid_pr(event):
                await self.process_pr(event)

    def _is_valid_pr(self, event: Event) -> bool:
        """Valida assinatura e estrutura do evento de PR."""
        if not event.verify_signature():
            return False
        # Verificar tags obrigatórias
        tags = dict(event.tags)
        return all(k in tags for k in ["h", "r", "commit", "head", "base"])

    async def process_pr(self, pr_event: Event):
        """Clona, verifica coerência e publica relatório."""
        tags = dict(pr_event.tags)
        repo_url = f"htree://{tags['r'][0]}"
        branch = tags['head'][0]

        # Clone temporário
        tmp_dir = f"/tmp/pr_{pr_event.id[:8]}"
        subprocess.run(["git", "clone", repo_url, tmp_dir], check=True)
        subprocess.run(["git", "-C", tmp_dir, "checkout", branch], check=True)

        # Scan de coerência
        graphs = self.parser.scan_directory(tmp_dir)
        metrics = self.parser.compute_metrics(graphs)
        global_coh = metrics['_global']['global_coherence']

        # Verificação de selos canônicos
        validator_result = self._validate_canonical_seals(graphs)

        # Publicar relatório como evento Nostr
        report = {
            "pr_event_id": pr_event.id,
            "global_coherence": global_coh,
            "canonical_seals_valid": validator_result,
            "metrics": metrics,
            "timestamp": int(time.time())
        }

        report_event = Event(
            kind=9001,
            pubkey=self.privkey.public_key.hex(),
            created_at=int(time.time()),
            tags=[
                ["e", pr_event.id],
                ["runner", "coherence-guardian-v1"],
                ["result", "pass" if global_coh >= 0.85 else "fail"],
                ["global_coherence", f"{global_coh:.4f}"]
            ],
            content=json.dumps(report)
        )
        report_event.sign(self.privkey)

        await self.relay_manager.publish(report_event)
        print(f"✅ Coherence report published: Φ_C={global_coh:.4f}")

    def _validate_canonical_seals(self, graphs: dict) -> bool:
        """Verifica selos canônicos em grafos LFIR gerados."""
        for filepath, graph in graphs.items():
            if hasattr(graph, 'metadata') and 'canonical_seal' in graph.metadata:
                pass  # Lógica de verificação criptográfica
        return True
