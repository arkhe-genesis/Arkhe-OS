"""
Ledger distribuído para audit trail imutável com verificação criptográfica.
Implementa append-only log com hashes encadeados e provas de integridade.
"""
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

@dataclass
class AuditEntry:
    """Entrada individual no audit ledger."""
    entry_id: str
    timestamp: str
    event_type: str
    deployment_id: Optional[str]
    actor: str  # Quem realizou a ação
    metadata: Dict[str, Any]
    previous_hash: str  # Hash da entrada anterior para encadeamento
    signature: Optional[str] = None  # Assinatura digital para não-repúdio

    def compute_hash(self) -> str:
        """Computa hash criptográfico da entrada."""
        data = {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "deployment_id": self.deployment_id,
            "actor": self.actor,
            "metadata": json.dumps(self.metadata, sort_keys=True),
            "previous_hash": self.previous_hash,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

    def to_dict(self) -> Dict:
        """Serializa para dicionário (para armazenamento)."""
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "deployment_id": self.deployment_id,
            "actor": self.actor,
            "metadata": self.metadata,
            "previous_hash": self.previous_hash,
            "hash": self.compute_hash(),
            "signature": self.signature,
        }

class AuditLedger:
    """Ledger imutável para logs de auditoria regulatória."""

    def __init__(self, ledger_path: str, signing_key: Optional[str] = None):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.mkdir(parents=True, exist_ok=True)
        self.signing_key = signing_key  # Para assinaturas digitais (opcional)
        self._current_hash = self._load_or_initialize_ledger()
        self._entry_counter = 0

    def _load_or_initialize_ledger(self) -> str:
        """Carrega ledger existente ou inicializa novo com genesis block."""
        ledger_file = self.ledger_path / "audit_ledger.jsonl"

        if ledger_file.exists():
            # Carregar último hash do ledger existente
            with open(ledger_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_entry = json.loads(lines[-1])
                    return last_entry["hash"]

        # Inicializar com genesis block
        genesis = AuditEntry(
            entry_id="genesis",
            timestamp=datetime.now().isoformat(),
            event_type="LEDGER_INITIALIZED",
            deployment_id=None,
            actor="system",
            metadata={"version": "1.0", "purpose": "regulatory_audit_trail"},
            previous_hash="0" * 64,  # Hash zero para genesis
        )
        self._append_entry(genesis)
        return genesis.compute_hash()

    async def log_event(self, event_type: str, deployment_id: Optional[str],
                       metadata: Dict[str, Any], actor: str = "system") -> str:
        """
        Registra evento no audit ledger de forma imutável.

        Returns:
            entry_id: Identificador único da entrada registrada
        """
        self._entry_counter += 1
        entry_id = f"{event_type}_{deployment_id or 'global'}_{self._entry_counter}"

        entry = AuditEntry(
            entry_id=entry_id,
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            deployment_id=deployment_id,
            actor=actor,
            metadata=metadata,
            previous_hash=self._current_hash,
        )

        # Assinar entrada se chave disponível (para não-repúdio)
        if self.signing_key:
            entry.signature = self._sign_entry(entry)

        # Calcular hash e atualizar estado
        entry_hash = entry.compute_hash()
        self._current_hash = entry_hash

        # Persistir entrada
        self._append_entry(entry)

        return entry_id

    def _append_entry(self, entry: AuditEntry):
        """Anexa entrada ao arquivo de ledger (append-only)."""
        ledger_file = self.ledger_path / "audit_ledger.jsonl"
        with open(ledger_file, 'a') as f:
            f.write(json.dumps(entry.to_dict()) + '\n')

    def _sign_entry(self, entry: AuditEntry) -> str:
        """Assina entrada com chave privada para não-repúdio."""
        # Em produção: usar ECDSA ou esquema PQC
        # Aqui: stub para demonstração
        message = entry.compute_hash().encode()
        return f"sig_{hashlib.sha256(message + self.signing_key.encode()).hexdigest()[:32]}"

    def verify_integrity(self) -> tuple[bool, Optional[str]]:
        """
        Verifica integridade completa do ledger (hash chain validation).

        Returns:
            (valid, error_message): True se ledger íntegro, False com descrição do erro
        """
        ledger_file = self.ledger_path / "audit_ledger.jsonl"
        if not ledger_file.exists():
            return False, "Ledger file not found"

        with open(ledger_file, 'r') as f:
            lines = f.readlines()

        if not lines:
            return False, "Ledger is empty"

        prev_hash = "0" * 64  # Genesis expected previous hash

        for i, line in enumerate(lines):
            try:
                entry_data = json.loads(line)
                entry = AuditEntry(
                    entry_id=entry_data["entry_id"],
                    timestamp=entry_data["timestamp"],
                    event_type=entry_data["event_type"],
                    deployment_id=entry_data["deployment_id"],
                    actor=entry_data["actor"],
                    metadata=entry_data["metadata"],
                    previous_hash=entry_data["previous_hash"],
                    signature=entry_data.get("signature"),
                )

                # Verificar hash da entrada
                computed_hash = entry.compute_hash()
                if computed_hash != entry_data.get("hash"):
                    return False, f"Hash mismatch at entry {i}: {entry.entry_id}"

                # Verificar encadeamento
                if entry.previous_hash != prev_hash:
                    return False, f"Chain broken at entry {i}: expected {prev_hash}, got {entry.previous_hash}"

                # Verificar assinatura se presente
                if entry.signature and self.signing_key:
                    if not self._verify_signature(entry):
                        return False, f"Signature verification failed at entry {i}"

                prev_hash = computed_hash

            except json.JSONDecodeError as e:
                return False, f"Invalid JSON at line {i}: {str(e)}"
            except KeyError as e:
                return False, f"Missing field at entry {i}: {str(e)}"

        return True, None

    def _verify_signature(self, entry: AuditEntry) -> bool:
         # stub signature verification
         message = entry.compute_hash().encode()
         expected_sig = f"sig_{hashlib.sha256(message + self.signing_key.encode()).hexdigest()[:32]}"
         return entry.signature == expected_sig

    def query_events(self, event_type: Optional[str] = None,
                    deployment_id: Optional[str] = None,
                    time_range: Optional[tuple[str, str]] = None) -> List[Dict]:
        """Consulta eventos no ledger com filtros."""
        ledger_file = self.ledger_path / "audit_ledger.jsonl"
        results = []

        if not ledger_file.exists():
            return results

        with open(ledger_file, 'r') as f:
            for line in f:
                entry = json.loads(line)

                # Aplicar filtros
                if event_type and entry["event_type"] != event_type:
                    continue
                if deployment_id and entry["deployment_id"] != deployment_id:
                    continue
                if time_range:
                    entry_time = entry["timestamp"]
                    if not (time_range[0] <= entry_time <= time_range[1]):
                        continue

                results.append(entry)

        return results

    def generate_compliance_report(self, jurisdiction: str,
                                  time_range: tuple[str, str]) -> Dict:
        """Gera relatório de compliance para auditoria regulatória."""
        events = self.query_events(time_range=time_range)

        # Agrupar eventos por tipo e deployment
        report = {
            "jurisdiction": jurisdiction,
            "report_period": time_range,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_events": len(events),
                "by_type": {},
                "by_deployment": {},
            },
            "compliance_proofs": [],
            "integrity_verification": None,
        }

        # Contar eventos por tipo
        for event in events:
            etype = event["event_type"]
            report["summary"]["by_type"][etype] = report["summary"]["by_type"].get(etype, 0) + 1

            if event["deployment_id"]:
                dep = event["deployment_id"]
                report["summary"]["by_deployment"][dep] = report["summary"]["by_deployment"].get(dep, 0) + 1

            # Coletar proofs de compliance
            if "COMPLIANCE_PROOF" in etype:
                report["compliance_proofs"].append({
                    "deployment_id": event["deployment_id"],
                    "proof_hash": event["metadata"].get("proof_hash"),
                    "jurisdiction": event["metadata"].get("jurisdiction"),
                })

        # Verificar integridade do ledger
        valid, error = self.verify_integrity()
        report["integrity_verification"] = {
            "valid": valid,
            "error": error,
            "verified_at": datetime.now().isoformat(),
        }

        return report
