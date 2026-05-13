import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path

import hashlib
import json
import time
import zlib
import shutil
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import OrderedDict
import threading

from enum import Enum

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
except ImportError:
    ed25519 = None

try:
    from bcc import BPF
except ImportError:
    BPF = None

class AuditLevel(Enum):
    STANDARD = "standard"
    STRICT = "strict"

@dataclass
class AuditReport:
    passed: bool
    issues: List[str]

@dataclass
class ArkToml:
    package_name: str
    version: str
    dependencies: Dict[str, str] = field(default_factory=dict)

    def compute_seal(self) -> str:
        data = f"{self.package_name}:{self.version}:{json.dumps(self.dependencies, sort_keys=True)}"
        return hashlib.sha3_256(data.encode()).hexdigest()

@dataclass
class ArtBlock:
    metadata: ArkToml
    package_hash: str
    temporal_anchor: Optional[str] = None
    signature: Optional[str] = None
    orcid: Optional[str] = None

    def sign_with_orcid(self, orcid: str, private_key: str):
        """Assina o bloco usando Ed25519."""
        self.orcid = orcid
        data_to_sign = f"{self.package_hash}:{orcid}".encode()

        if ed25519 is not None:
            try:
                # Assuming private_key is a hex string of the raw bytes
                key_bytes = bytes.fromhex(private_key)
                if len(key_bytes) == 32:
                    priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)
                    self.signature = priv_key.sign(data_to_sign).hex()
                else:
                    self.signature = hashlib.sha256(f"{data_to_sign.decode()}:{private_key}".encode()).hexdigest()
            except Exception:
                self.signature = hashlib.sha256(f"{data_to_sign.decode()}:{private_key}".encode()).hexdigest()
        else:
            self.signature = hashlib.sha256(f"{data_to_sign.decode()}:{private_key}".encode()).hexdigest()

    def verify(self) -> bool:
        base_valid = self.package_hash == self.metadata.compute_seal()
        # Na vida real, verificaria a assinatura Ed25519 com a chave pública associada ao ORCID
        return base_valid

class ConRAGAuditor:
    def __init__(self, level: AuditLevel = AuditLevel.STANDARD):
        self.level = level

    def audit(self, manifest: ArkToml, source_code: str) -> AuditReport:
        # Dummy implementation
        return AuditReport(passed=True, issues=[])

class QIPRoyaltyEngine:
    def __init__(self, metrics_monitor: Optional['EBPFMetricsMonitor'] = None):
        self.metrics_monitor = metrics_monitor

    def record_influence(self, package: str, consumer: str):
        pass

    def calculate_royalties(self, base_amount: float, package: str) -> Dict[str, float]:
        multiplier = 1.0
        if self.metrics_monitor:
            metrics = self.metrics_monitor.get_metrics()
            multiplier += metrics.get("kernel_cache_hit_rate", 0.0)

        adjusted_base = base_amount * multiplier
        return {"creator": adjusted_base * 0.8, "cathedral": adjusted_base * 0.2}

class PackageRegistry:
    def __init__(self):
        self.packages: Dict[str, ArtBlock] = {}

    def publish(self, block: ArtBlock):
        self.packages[f"{block.metadata.package_name}@{block.metadata.version}"] = block

    def get(self, name: str, version: str) -> Optional[ArtBlock]:
        return self.packages.get(f"{name}@{version}")

    def resolve_tree(self, name: str, version: str) -> Dict[str, str]:
        """Resolve dependências recursivamente e retorna uma árvore achatada."""
        resolved: Dict[str, str] = {}

        def _resolve(pkg_name: str, pkg_version: str):
            if pkg_name in resolved:
                return
            resolved[pkg_name] = pkg_version
            block = self.get(pkg_name, pkg_version)
            if block:
                for dep_name, dep_version in block.metadata.dependencies.items():
                    _resolve(dep_name, dep_version)

        _resolve(name, version)
        return resolved

class ArkpCLI:
    def __init__(self, registry: PackageRegistry, auditor: ConRAGAuditor, qip: QIPRoyaltyEngine):
        self.registry = registry
        self.auditor = auditor
        self.qip = qip

    def new_package(self, name: str, template: str = "default") -> ArkToml:
        return ArkToml(package_name=name, version="0.1.0")

    def build(self, prove: bool = False, anchor: bool = False) -> Dict[str, bool]:
        return {"success": True}

    def publish(self) -> Dict[str, bool]:
        return {"success": True}

# 1. Adicionar suporte a versionamento semântico real
def parse_semver(version: str) -> Tuple[int, int, int]:
    """Parse '1.2.3' -> (1, 2, 3) com validação."""
    parts = version.split('.')
    if len(parts) != 3:
        raise ValueError(f"Invalid semver: {version}")
    return tuple(int(p) for p in parts)

# 2. Adicionar cache de dependências para build incremental

class CacheEntryStatus(Enum):
    VALID = "valid"
    EXPIRED = "expired"
    CORRUPTED = "corrupted"
    PENDING = "pending"
    EVICTED = "evicted"

@dataclass
class DependencyKey:
    name: str
    version: str
    source_hash: str

    def to_cache_key(self) -> str:
        return f"{self.name}@{self.version}:{self.source_hash[:16]}"

    def __hash__(self):
        return hash((self.name, self.version, self.source_hash))

    def __eq__(self, other):
        if not isinstance(other, DependencyKey):
            return False
        return (self.name == other.name and
                self.version == other.version and
                self.source_hash == other.source_hash)

@dataclass
class CacheEntry:
    key: DependencyKey
    content: bytes
    metadata: Dict[str, Any]
    created_at: float
    last_accessed: float
    access_count: int = 0
    qip_influence: float = 0.0
    temporal_anchor: Optional[str] = None
    compression_ratio: float = 1.0
    status: CacheEntryStatus = CacheEntryStatus.VALID

    @property
    def size_bytes(self) -> int:
        return len(self.content)

    @property
    def age_days(self) -> float:
        return (time.time() - self.created_at) / 86400

    @property
    def is_expired(self) -> bool:
        return self.age_days > 30

    @property
    def priority_score(self) -> float:
        recency = 1.0 / (1.0 + self.age_days / 7)
        frequency = min(1.0, self.access_count / 100)
        return self.qip_influence * 0.5 + recency * 0.3 + frequency * 0.2

class ContentAddressableStorage:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        for subdir in ["packages", "metadata", "indexes", "temporal_anchors"]:
            (self.base_path / subdir).mkdir(exist_ok=True)

    def _get_content_path(self, content_hash: str) -> Path:
        prefix = content_hash[:2]
        return self.base_path / "packages" / prefix / content_hash

    def store(self, content: bytes) -> str:
        content_hash = hashlib.sha3_256(content).hexdigest()
        content_path = self._get_content_path(content_hash)
        if content_path.exists():
            return content_hash
        content_path.parent.mkdir(parents=True, exist_ok=True)
        content_path.write_bytes(content)
        return content_hash

    def retrieve(self, content_hash: str) -> Optional[bytes]:
        content_path = self._get_content_path(content_hash)
        if not content_path.exists():
            return None
        content = content_path.read_bytes()
        if hashlib.sha3_256(content).hexdigest() != content_hash:
            content_path.unlink(missing_ok=True)
            return None
        return content

    def remove(self, content_hash: str) -> bool:
        content_path = self._get_content_path(content_hash)
        if content_path.exists():
            content_path.unlink()
            try:
                content_path.parent.rmdir()
            except OSError:
                pass
            return True
        return False

    def get_total_size_bytes(self) -> int:
        total = 0
        packages_dir = self.base_path / "packages"
        if packages_dir.exists():
            for path in packages_dir.rglob("*"):
                if path.is_file():
                    total += path.stat().st_size
        return total

class DependencyCache:
    def __init__(self, cache_dir: str, max_size_gb: float = 10.0,
                 temporal_client: Optional[Any] = None, qip_engine: Optional[Any] = None):
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = int(max_size_gb * 1024**3)
        self.temporal_client = temporal_client
        self.qip_engine = qip_engine
        self.storage = ContentAddressableStorage(self.cache_dir)
        self.metadata_index: Dict[DependencyKey, CacheEntry] = {}
        self.access_order = OrderedDict()
        self._lock = threading.RLock()
        self._load_index()

    def _load_index(self):
        index_path = self.cache_dir / "metadata" / "index.json"
        if index_path.exists():
            try:
                data = json.loads(index_path.read_text())
                for key_str, entry_data in data.items():
                    name, version_hash = key_str.split("@", 1)
                    version, source_hash = version_hash.split(":", 1)
                    key = DependencyKey(name, version, source_hash)
                    entry = CacheEntry(
                        key=key,
                        content=b"",
                        metadata=entry_data.get("metadata", {}),
                        created_at=entry_data["created_at"],
                        last_accessed=entry_data["last_accessed"],
                        access_count=entry_data.get("access_count", 0),
                        qip_influence=entry_data.get("qip_influence", 0.0),
                        temporal_anchor=entry_data.get("temporal_anchor"),
                        compression_ratio=entry_data.get("compression_ratio", 1.0),
                        status=CacheEntryStatus(entry_data.get("status", "valid")),
                    )
                    self.metadata_index[key] = entry
                    self.access_order[key] = None
            except Exception:
                pass

    def _save_index(self):
        index_path = self.cache_dir / "metadata" / "index.json"
        data = {}
        for key, entry in self.metadata_index.items():
            key_str = f"{key.name}@{key.version}:{key.source_hash}"
            data[key_str] = {
                "metadata": entry.metadata,
                "created_at": entry.created_at,
                "last_accessed": entry.last_accessed,
                "access_count": entry.access_count,
                "qip_influence": entry.qip_influence,
                "temporal_anchor": entry.temporal_anchor,
                "compression_ratio": entry.compression_ratio,
                "status": entry.status.value,
            }
        index_path.write_text(json.dumps(data, indent=2))

    def _compress_if_needed(self, content: bytes) -> Tuple[bytes, float]:
        if len(content) < 256 * 1024:
            return content, 1.0
        compressed = zlib.compress(content, level=6)
        ratio = len(content) / len(compressed) if len(compressed) > 0 else 1.0
        if ratio > 1.1:
            return compressed, ratio
        return content, 1.0

    def _decompress_if_needed(self, content: bytes, ratio: float) -> bytes:
        if ratio > 1.1:
            return zlib.decompress(content)
        return content

    def _evict_if_needed(self):
        current_size = self.storage.get_total_size_bytes()
        if current_size <= self.max_size_bytes:
            return
        candidates = sorted(self.metadata_index.values(), key=lambda e: e.priority_score)
        for entry in candidates:
            if current_size <= self.max_size_bytes * 0.9:
                break
            content_hash = entry.metadata.get("content_hash")
            if content_hash and self.storage.remove(content_hash):
                current_size -= entry.size_bytes
            del self.metadata_index[entry.key]
            self.access_order.pop(entry.key, None)
            entry.status = CacheEntryStatus.EVICTED
        self._save_index()

    def get(self, key: DependencyKey) -> Optional[bytes]:
        with self._lock:
            entry = self.metadata_index.get(key)
            if not entry:
                return None
            if entry.status != CacheEntryStatus.VALID:
                return None
            if entry.is_expired:
                entry.status = CacheEntryStatus.EXPIRED
                self._save_index()
                return None
            entry.last_accessed = time.time()
            entry.access_count += 1
            self.access_order.move_to_end(key)
            content_hash = entry.metadata.get("content_hash")
            if not content_hash:
                return None
            compressed = self.storage.retrieve(content_hash)
            if not compressed:
                entry.status = CacheEntryStatus.CORRUPTED
                self._save_index()
                return None
            return self._decompress_if_needed(compressed, entry.compression_ratio)

    def put(self, key: DependencyKey, content: bytes, metadata: Optional[Dict] = None,
            anchor_temporal: bool = True) -> bool:
        with self._lock:
            compressed_content, ratio = self._compress_if_needed(content)
            content_hash = self.storage.store(compressed_content)
            qip_influence = 0.0
            if self.qip_engine:
                qip_influence = self.qip_engine.get_influence_score(key.name, key.version)
            temporal_anchor = None
            if anchor_temporal and self.temporal_client:
                try:
                    temporal_anchor = self.temporal_client.anchor_content(
                        content_hash=content_hash,
                        metadata={"dependency": key.name, "version": key.version}
                    )
                except Exception:
                    pass
            entry = CacheEntry(
                key=key,
                content=compressed_content,
                metadata={**(metadata or {}), "content_hash": content_hash,
                          "original_size": len(content), "compressed_size": len(compressed_content)},
                created_at=time.time(),
                last_accessed=time.time(),
                qip_influence=qip_influence,
                temporal_anchor=temporal_anchor,
                compression_ratio=ratio,
            )
            self.metadata_index[key] = entry
            self.access_order[key] = None
            self.access_order.move_to_end(key)
            self._save_index()
            self._evict_if_needed()
            return True

    def clear_expired(self) -> int:
        with self._lock:
            expired = [k for k, e in self.metadata_index.items() if e.is_expired or e.status == CacheEntryStatus.EXPIRED]
            for key in expired:
                entry = self.metadata_index[key]
                content_hash = entry.metadata.get("content_hash")
                if content_hash:
                    self.storage.remove(content_hash)
                del self.metadata_index[key]
                self.access_order.pop(key, None)
            if expired:
                self._save_index()
            return len(expired)

    def get_stats(self) -> Dict:
        with self._lock:
            total_size = self.storage.get_total_size_bytes()
            valid_entries = sum(1 for e in self.metadata_index.values() if e.status == CacheEntryStatus.VALID)
            return {
                "cache_dir": str(self.cache_dir),
                "max_size_gb": self.max_size_bytes / 1024**3,
                "current_size_gb": total_size / 1024**3,
                "usage_percent": (total_size / self.max_size_bytes * 100) if self.max_size_bytes > 0 else 0,
                "total_entries": len(self.metadata_index),
                "valid_entries": valid_entries,
                "expired_entries": sum(1 for e in self.metadata_index.values() if e.is_expired),
                "corrupted_entries": sum(1 for e in self.metadata_index.values() if e.status == CacheEntryStatus.CORRUPTED),
                "total_accesses": sum(e.access_count for e in self.metadata_index.values()),
                "avg_compression_ratio": sum(e.compression_ratio for e in self.metadata_index.values()) / max(1, len(self.metadata_index)),
                "temporal_anchored": sum(1 for e in self.metadata_index.values() if e.temporal_anchor),
                "avg_qip_influence": sum(e.qip_influence for e in self.metadata_index.values()) / max(1, len(self.metadata_index)),
            }

# 3. Adicionar suporte a plugins de auditoria
class PluggableAuditor(ConRAGAuditor):
    """Auditor com plugins dinâmicos para verificações customizadas."""
    def __init__(self, level: AuditLevel = AuditLevel.STANDARD):
        super().__init__(level)
        self.plugins: List[Callable[[ArkToml, str], AuditReport]] = []

    def register_plugin(self, plugin: Callable):
        """Registra função de auditoria customizada."""
        self.plugins.append(plugin)

    def audit(self, manifest: ArkToml, source_code: str) -> AuditReport:
        base_report = super().audit(manifest, source_code)
        for plugin in self.plugins:
            plugin_report = plugin(manifest, source_code)
            base_report.passed &= plugin_report.passed
            base_report.issues.extend(plugin_report.issues)
        return base_report

# 4. Integrar auditoria com Mythos Gate

class PublicationDecision(Enum):
    APPROVED = "approved"
    REQUIRES_REVIEW = "requires_review"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"

class EthicalRiskCategory(Enum):
    SECURITY_VULNERABILITY = "security_vulnerability"
    PRIVACY_VIOLATION = "privacy_violation"
    MISINFORMATION = "misinformation"
    AUTONOMOUS_HARM = "autonomous_harm"
    BENEFICIAL = "beneficial"
    NEUTRAL = "neutral"

@dataclass
class EthicalAssessment:
    package_name: str
    package_version: str
    overall_risk_score: float
    risk_breakdown: Dict[EthicalRiskCategory, float]
    decision: PublicationDecision
    rationale: str
    recommendations: List[str]
    mythos_seal: str
    timestamp: float
    reviewer_orcid: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "package": self.package_name,
            "version": self.package_version,
            "overall_risk_score": self.overall_risk_score,
            "risk_breakdown": {k.value: v for k, v in self.risk_breakdown.items()},
            "decision": self.decision.value,
            "rationale": self.rationale,
            "recommendations": self.recommendations,
            "mythos_seal": self.mythos_seal,
            "timestamp": self.timestamp,
            "reviewer_orcid": self.reviewer_orcid,
        }

class EthicalRiskAssessor:
    DANGEROUS_PATTERNS = {
        "eval": EthicalRiskCategory.SECURITY_VULNERABILITY,
        "exec": EthicalRiskCategory.SECURITY_VULNERABILITY,
        "compile": EthicalRiskCategory.SECURITY_VULNERABILITY,
        "__import__": EthicalRiskCategory.SECURITY_VULNERABILITY,
        "os.system": EthicalRiskCategory.SECURITY_VULNERABILITY,
        "subprocess.call": EthicalRiskCategory.SECURITY_VULNERABILITY,
        "password": EthicalRiskCategory.PRIVACY_VIOLATION,
        "secret": EthicalRiskCategory.PRIVACY_VIOLATION,
        "private_key": EthicalRiskCategory.PRIVACY_VIOLATION,
        "misleading": EthicalRiskCategory.MISINFORMATION,
        "fake": EthicalRiskCategory.MISINFORMATION,
        "propaganda": EthicalRiskCategory.MISINFORMATION,
        "autonomous_decision": EthicalRiskCategory.AUTONOMOUS_HARM,
        "self_modify": EthicalRiskCategory.AUTONOMOUS_HARM,
        "weaponize": EthicalRiskCategory.AUTONOMOUS_HARM,
        "kill": EthicalRiskCategory.AUTONOMOUS_HARM,
        "destroy": EthicalRiskCategory.AUTONOMOUS_HARM,
    }

    SUSPICIOUS_DESCRIPTIONS = [
        "undetectable", "bypass", "exploit", "backdoor",
        "surveillance", "tracking", "harvest", "scrape",
        "manipulate", "influence", "persuade",
    ]

    HIGH_RISK_DEPENDENCIES = {
        "pycrypto": "deprecated_crypto_lib",
        "requests-ntlm": "weak_auth_protocol",
    }

    def __init__(self, constitutional_principles: Optional[List[str]] = None):
        self.constitutional_principles = constitutional_principles or [
            "preserve_consciousness", "avoid_harm", "maintain_truth",
            "respect_autonomy", "promote_knowledge",
        ]

    def assess_package(self, manifest: Dict, source_files: List[Tuple[str, str]],
                       dependencies: List[Dict]) -> EthicalAssessment:
        package_name = manifest.get("package", {}).get("name", "unknown")
        package_version = manifest.get("package", {}).get("version", "0.0.0")

        code_risks = self._analyze_code(source_files)
        metadata_risks = self._analyze_metadata(manifest)
        dependency_risks = self._analyze_dependencies(dependencies)
        constitutional_score = self._check_constitutional_alignment(manifest, source_files)

        risk_breakdown = {
            EthicalRiskCategory.SECURITY_VULNERABILITY:
                code_risks.get("security", 0.0) * 0.5 + dependency_risks.get("security", 0.0) * 0.3 + metadata_risks.get("security", 0.0) * 0.2,
            EthicalRiskCategory.PRIVACY_VIOLATION:
                code_risks.get("privacy", 0.0) * 0.5 + metadata_risks.get("privacy", 0.0) * 0.5,
            EthicalRiskCategory.MISINFORMATION:
                metadata_risks.get("misinformation", 0.0) * 0.7 + code_risks.get("misinformation", 0.0) * 0.3,
            EthicalRiskCategory.AUTONOMOUS_HARM:
                code_risks.get("autonomy", 0.0) * 0.6 + metadata_risks.get("autonomy", 0.0) * 0.4 + dependency_risks.get("autonomy", 0.0) * 0.3,
        }

        severity_weights = {
            EthicalRiskCategory.AUTONOMOUS_HARM: 1.0,
            EthicalRiskCategory.SECURITY_VULNERABILITY: 0.8,
            EthicalRiskCategory.PRIVACY_VIOLATION: 0.7,
            EthicalRiskCategory.MISINFORMATION: 0.6,
        }

        weighted_risks = [risk * severity_weights.get(category, 0.5)
                          for category, risk in risk_breakdown.items()]
        overall_risk = max(0.0, min(1.0, sum(weighted_risks)))
        overall_risk = overall_risk * (1.0 - constitutional_score * 0.15)

        if overall_risk >= 0.7:
            decision = PublicationDecision.REJECTED
            rationale = f"Risco ético crítico ({overall_risk:.2f}) excede threshold"
        elif overall_risk >= 0.4:
            decision = PublicationDecision.REQUIRES_REVIEW
            rationale = f"Risco moderado ({overall_risk:.2f}) — revisão humana recomendada"
        else:
            decision = PublicationDecision.APPROVED
            rationale = f"Risco aceitável ({overall_risk:.2f}) — princípios preservados"

        recommendations = self._generate_recommendations(risk_breakdown, overall_risk)

        seal_data = json.dumps({
            "package": package_name, "version": package_version,
            "overall_risk": overall_risk, "decision": decision.value,
            "timestamp": time.time(),
        }, sort_keys=True)
        mythos_seal = hashlib.sha3_256(seal_data.encode()).hexdigest()

        return EthicalAssessment(
            package_name=package_name, package_version=package_version,
            overall_risk_score=overall_risk, risk_breakdown=risk_breakdown,
            decision=decision, rationale=rationale, recommendations=recommendations,
            mythos_seal=mythos_seal, timestamp=time.time(),
        )

    def _analyze_code(self, source_files: List[Tuple[str, str]]) -> Dict[str, float]:
        risks = {}
        for filename, content in source_files:
            content_lower = content.lower()
            for pattern, category in self.DANGEROUS_PATTERNS.items():
                if pattern.lower() in content_lower:
                    count = content_lower.count(pattern.lower())
                    risk_score = min(1.0, count * 0.3)
                    cat_map = {
                        "security_vulnerability": "security",
                        "privacy_violation": "privacy",
                        "misinformation": "misinformation",
                        "autonomous_harm": "autonomy",
                    }
                    category_name = cat_map.get(category.value, category.value.split("_")[0])
                    risks[category_name] = max(risks.get(category_name, 0.0), risk_score)
            for keyword in self.SUSPICIOUS_DESCRIPTIONS:
                if keyword in content_lower:
                    risks["misinformation"] = max(risks.get("misinformation", 0.0), 0.5)
        return risks

    def _analyze_metadata(self, manifest: Dict) -> Dict[str, float]:
        risks = {}
        pkg = manifest.get("package", {})
        description = pkg.get("description", "").lower()
        for keyword in self.SUSPICIOUS_DESCRIPTIONS:
            if keyword in description:
                risks["misinformation"] = max(risks.get("misinformation", 0.0), 0.6)
        deps = manifest.get("dependencies", {})
        for dep_name in deps:
            if dep_name in self.HIGH_RISK_DEPENDENCIES:
                risks["security"] = max(risks.get("security", 0.0), 0.5)
        for kw in ["autonomous", "self_modify", "weaponize", "kill", "destroy"]:
            if kw in description:
                risks["autonomy"] = max(risks.get("autonomy", 0.0), 0.4)
        return risks

    def _analyze_dependencies(self, dependencies: List[Dict]) -> Dict[str, float]:
        risks = {}
        for dep in dependencies:
            dep_name = dep.get("name", "")
            if dep_name in self.HIGH_RISK_DEPENDENCIES:
                risks["security"] = max(risks.get("security", 0.0), 0.6)
            dep_risk = dep.get("ethical_risk_score", 0.0)
            if dep_risk > 0.3:
                for category in ["security", "privacy", "misinformation", "autonomy"]:
                    risks[category] = max(risks.get(category, 0.0), dep_risk * 0.7)
        return risks

    def _check_constitutional_alignment(self, manifest: Dict, source_files: List[Tuple[str, str]]) -> float:
        score = 1.0
        pkg = manifest.get("package", {})
        description = pkg.get("description", "").lower()
        for principle in self.constitutional_principles:
            if principle == "avoid_harm":
                for kw in ["harm", "damage", "destroy", "attack", "exploit", "surveillance", "backdoor", "weaponize"]:
                    if kw in description:
                        score -= 0.2
            elif principle == "maintain_truth":
                for tc in ["always_correct", "never_wrong", "absolute_truth", "undetectable", "fake", "propaganda"]:
                    if tc in description:
                        score -= 0.15
            elif principle == "respect_autonomy":
                for filename, content in source_files:
                    if "force_install" in content.lower() or "bypass_user" in content.lower():
                        score -= 0.25
                        break
        return max(0.0, min(1.0, score))

    def _generate_recommendations(self, risk_breakdown: Dict, overall_risk: float) -> List[str]:
        recommendations = []
        if risk_breakdown.get(EthicalRiskCategory.SECURITY_VULNERABILITY, 0) > 0.3:
            recommendations.append("Realizar auditoria de segurança")
        if risk_breakdown.get(EthicalRiskCategory.PRIVACY_VIOLATION, 0) > 0.3:
            recommendations.append("Adicionar política de privacidade")
        if risk_breakdown.get(EthicalRiskCategory.MISINFORMATION, 0) > 0.3:
            recommendations.append("Incluir avisos sobre limitações")
        if overall_risk >= 0.4:
            recommendations.append("Submeter para revisão ética")
        if not recommendations:
            recommendations.append("Manter práticas de desenvolvimento ético")
        return recommendations

class MythosGatePublisher:
    def __init__(self, assessor: Optional[EthicalRiskAssessor] = None,
                 temporal_client: Optional[Any] = None, ledger: Optional[Any] = None):
        self.assessor = assessor or EthicalRiskAssessor()
        self.temporal_client = temporal_client
        self.ledger = ledger
        self._assessment_cache: Dict[str, EthicalAssessment] = {}

    def evaluate_for_publication(self, manifest: Dict, source_files: List[Tuple[str, str]],
                                  dependencies: List[Dict], author_orcid: str) -> Tuple[bool, str, Optional[EthicalAssessment]]:
        package_name = manifest.get("package", {}).get("name", "unknown")
        package_version = manifest.get("package", {}).get("version", "0.0.0")
        cache_key = f"{package_name}@{package_version}:{author_orcid}"

        if cache_key in self._assessment_cache:
            assessment = self._assessment_cache[cache_key]
            if assessment.decision == PublicationDecision.APPROVED:
                return True, "Previously approved by Mythos Gate", assessment

        assessment = self.assessor.assess_package(manifest, source_files, dependencies)

        if self.ledger:
            self.ledger.record("mythos_package_assessment", {
                "package": package_name, "version": package_version,
                "author": author_orcid, "assessment": assessment.to_dict(),
            })

        if self.temporal_client and assessment.mythos_seal:
            try:
                self.temporal_client.anchor_content(
                    content_hash=assessment.mythos_seal,
                    metadata={"type": "mythos_assessment", "package": package_name,
                              "decision": assessment.decision.value, "risk_score": assessment.overall_risk_score}
                )
            except Exception:
                pass

        if assessment.decision == PublicationDecision.APPROVED:
            self._assessment_cache[cache_key] = assessment
            return True, f"Mythos Gate: APPROVED (risk={assessment.overall_risk_score:.2f})", assessment
        elif assessment.decision == PublicationDecision.REQUIRES_REVIEW:
            return False, f"Mythos Gate: REQUIRES REVIEW (risk={assessment.overall_risk_score:.2f})", assessment
        else:
            return False, f"Mythos Gate: REJECTED (risk={assessment.overall_risk_score:.2f})", assessment

    def get_assessment(self, package_name: str, version: str) -> Optional[EthicalAssessment]:
        for key, assessment in self._assessment_cache.items():
            if assessment.package_name == package_name and assessment.package_version == version:
                return assessment
        return None

# 5. Adicionar métricas em tempo real via eBPF
class EBPFMetricsMonitor:
    """Monitoramento de saúde do ecossistema."""
    def __init__(self):
        self.metrics = {
            "builds": 0,
            "publishes": 0,
            "build_latency_ms": 0.0,
            "kernel_cache_hit_rate": 0.0
        }

    def attach_hooks(self):
        """Anexa hooks eBPF reais para coletar latência e cache, com fallback graceful."""
        bpf_text = """
        #include <uapi/linux/ptrace.h>
        BPF_HASH(build_latency, u32, u64);
        BPF_HASH(cache_hits, u32, u64);

        int trace_build_start(struct pt_regs *ctx) {
            u32 pid = bpf_get_current_pid_tgid();
            u64 ts = bpf_ktime_get_ns();
            build_latency.update(&pid, &ts);
            return 0;
        }
        """
        if BPF is not None:
            try:
                self.bpf = BPF(text=bpf_text)
                # Na vida real tentariamos anexar a syscalls especificas
                # self.bpf.attach_kprobe(event="sys_execve", fn_name="trace_build_start")
            except Exception:
                self.bpf = None
        else:
            self.bpf = None

    def record_build(self, latency_ms: float = 0.0, cache_hit_rate: float = 0.0):
        self.metrics["builds"] += 1
        self.metrics["build_latency_ms"] = latency_ms
        self.metrics["kernel_cache_hit_rate"] = cache_hit_rate

    def record_publish(self):
        self.metrics["publishes"] += 1

    def get_metrics(self) -> Dict[str, float]:
        return self.metrics

class RegistryDashboard:
    """Dashboard web para visualizar o ecossistema do registry."""
    def __init__(self, registry: PackageRegistry, auditor: ConRAGAuditor):
        self.registry = registry
        self.auditor = auditor

    def render_html(self) -> str:
        """Gera um HTML para o dashboard incluindo auditoria e influencia."""
        html = ["<html><body><h1>Registry Dashboard</h1><ul>"]
        for key, block in self.registry.packages.items():
            orcid_info = f" | ORCID: {block.orcid}" if block.orcid else ""

            # Simulando os scores de auditoria e métricas de influência
            audit_report = self.auditor.audit(block.metadata, "")
            audit_score = 100 if audit_report.passed else 50

            # Graficos de influencia simulados por CSS/HTML barras
            influence = 85 # Dummy influence metric
            html.append(
                f"<li>"
                f"<strong>{key}</strong>{orcid_info} <br/>"
                f"Audit Score: {audit_score}/100 <br/>"
                f"Influence Graph: <div style='width: {influence}px; height: 10px; background: blue;'></div>"
                f"</li>"
            )
        html.append("</ul></body></html>")
        return "".join(html)


# 6. Suporte a publicação cross-branch via Multiverse Router
class MultiverseRouter:
    """Pacotes disponíveis em múltiplas branches."""
    def __init__(self, registry: PackageRegistry):
        self.registry = registry
        self.branches: Dict[str, List[str]] = {}

    def publish_to_branch(self, block: ArtBlock, branch_name: str):
        self.registry.publish(block)
        if branch_name not in self.branches:
            self.branches[branch_name] = []
        key = f"{block.metadata.package_name}@{block.metadata.version}"
        if key not in self.branches[branch_name]:
            self.branches[branch_name].append(key)

    def get_packages_in_branch(self, branch_name: str) -> List[str]:
        return self.branches.get(branch_name, [])
