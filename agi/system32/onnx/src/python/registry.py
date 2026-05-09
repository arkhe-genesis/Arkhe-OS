#!/usr/bin/env python3
"""ONNX Model Registry with cryptographic verification and hardware-aware loading."""
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import onnxruntime as ort
from .ledger import LedgerClient
from .crypto import verify_falcon_signature

@dataclass
class ONNXModelEntry:
    model_hash: str
    model_path: str
    publisher_seal: str
    phi_c_training: float
    datasets: List[str]
    license: str
    signature: str
    created_at: float = 0.0

    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()

class ONNXModelRegistry:
    def __init__(self, storage_dir: str = "/var/lib/arkhe/models", ledger_url: str = "http://localhost:8080"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.ledger = LedgerClient(ledger_url)
        self._registry_db: Dict[str, ONNXModelEntry] = {}
        self._load_registry()

    def _load_registry(self):
        db_path = self.storage_dir / "registry.json"
        if db_path.exists():
            data = json.loads(db_path.read_text())
            self._registry_db = {k: ONNXModelEntry(**v) for k, v in data.items()}

    def register_model(self, onnx_path: str, publisher_seal: str,
                       phi_c_training: float, datasets: List[str],
                       license_type: str, signature: str) -> str:
        model_path = Path(onnx_path)
        model_bytes = model_path.read_bytes()
        model_hash = hashlib.sha3_256(model_bytes).hexdigest()

        metadata = {
            "model_hash": model_hash,
            "publisher_seal": publisher_seal,
            "phi_c_training": phi_c_training,
            "datasets": datasets,
            "license": license_type
        }
        payload = json.dumps(metadata, sort_keys=True).encode()
        if not verify_falcon_signature(publisher_seal, signature, payload):
            raise ValueError("Invalid Falcon-1024 signature")

        dest_path = self.storage_dir / f"{model_hash}.onnx"
        if not dest_path.exists():
            model_path.rename(dest_path)

        entry = ONNXModelEntry(
            model_hash=model_hash, model_path=str(dest_path),
            publisher_seal=publisher_seal, phi_c_training=phi_c_training,
            datasets=datasets, license=license_type, signature=signature
        )
        self._registry_db[model_hash] = entry
        self.ledger.record("model_registered", asdict(entry))
        self._save_registry()
        return model_hash

    def load_session(self, model_hash: str, execution_providers: Optional[List[str]] = None) -> ort.InferenceSession:
        entry = self._registry_db.get(model_hash)
        if not entry:
            raise ValueError("Model not registered")

        current_hash = hashlib.sha3_256(Path(entry.model_path).read_bytes()).hexdigest()
        if current_hash != model_hash:
            raise RuntimeError("Model integrity compromised!")

        providers = execution_providers or ["CUDAExecutionProvider", "CPUExecutionProvider"]
        sess_opts = ort.SessionOptions()
        sess_opts.log_severity_level = 3
        return ort.InferenceSession(entry.model_path, sess_opts=sess_opts, providers=providers)

    def _save_registry(self):
        db_path = self.storage_dir / "registry.json"
        serializable = {k: asdict(v) for k, v in self._registry_db.items()}
        db_path.write_text(json.dumps(serializable, indent=2))
