# scripts/log_pipeline.py — Ingestão de logs NGINX para o Audit Ledger
"""
Pipeline que lê logs JSON do NGINX e os injeta no Audit Ledger (Substrato 333).
"""
import json
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime

class CathedralLogIngester:
    """Ingestor de logs do NGINX para o Audit Ledger."""

    def __init__(self, log_path: str = "/var/log/nginx/access.log",
                 ledger_endpoint: str = "http://localhost:9090/api/v1/audit"):
        self.log_path = Path(log_path)
        self.ledger_endpoint = ledger_endpoint
        self.last_position = 0

    async def ingest_new_entries(self):
        """Lê novas entradas do log e envia ao Ledger."""
        if not self.log_path.exists():
            return

        with open(self.log_path, 'r') as f:
            f.seek(self.last_position)
            new_lines = f.readlines()
            self.last_position = f.tell()

        for line in new_lines:
            line = line.strip()
            if not line:
                continue

            try:
                entry = json.loads(line)
                audit_event = self._transform_to_audit_event(entry)
                await self._send_to_ledger(audit_event)
            except json.JSONDecodeError:
                continue

    def _transform_to_audit_event(self, log_entry: dict) -> dict:
        """Transforma log JSON em evento de auditoria canônico."""
        return {
            "event_type": "HTTP_REQUEST",
            "timestamp": log_entry.get("time"),
            "source_ip": log_entry.get("remote_addr"),
            "method": log_entry.get("method"),
            "path": log_entry.get("uri"),
            "status_code": log_entry.get("status"),
            "phi_rep": log_entry.get("phi_rep", "N/A"),
            "kym_seal": log_entry.get("kym_seal", "N/A"),
            "user_agent": log_entry.get("user_agent"),
            "request_time_ms": float(log_entry.get("request_time", 0)) * 1000,
            "canon_hash": self._compute_canon_hash(log_entry)
        }

    def _compute_canon_hash(self, entry: dict) -> str:
        """Hash canônico do evento para verificação de integridade."""
        import hashlib
        payload = f"{entry.get('time')}|{entry.get('remote_addr')}|{entry.get('request')}"
        return hashlib.sha256(payload.encode()).hexdigest()[:32]

    async def _send_to_ledger(self, event: dict):
        """Envia evento ao Audit Ledger via aiohttp."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.ledger_endpoint, json=event) as response:
                    if response.status != 200:
                        print(f"Error sending log to ledger: {response.status}")
        except Exception as e:
            print(f"Failed to send event: {e}")
