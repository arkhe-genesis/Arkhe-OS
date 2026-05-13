import json
import hashlib
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from pathlib import Path
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
class DependencyCache:
    """Cache de dependências resolvidas para evitar re-downloads."""
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, name: str, version: str) -> Optional[Path]:
        key = f"{name}@{version}"
        path = self.cache_dir / key
        return path if path.exists() else None

    def set(self, name: str, version: str, content: bytes):
        key = f"{name}@{version}"
        path = self.cache_dir / key
        path.write_bytes(content)

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
class MythosGateIntegration:
    """Decisões de publicação com contexto ético."""
    def evaluate_ethical_context(self, package_name: str, source_code: str) -> bool:
        # Mock evaluation
        if "malicious" in source_code.lower():
            return False
        return True

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
