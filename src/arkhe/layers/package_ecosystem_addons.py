import re
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from .package_ecosystem import ArkToml, ArtBlock, PackageRegistry, ConRAGAuditor, AuditReport, AuditLevel, ArkpCLI
from .governance import MythosGate  # Camada 6
from .multiverse import MultiverseRouter, ConvergenceProtocol
from .qip import QIPRoyaltyEngine

# ========== SEMANTIC VERSIONING ==========
class SemVer:
    PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$")
    def __init__(self, version_str: str):
        match = self.PATTERN.match(version_str.strip())
        if not match:
            raise ValueError(f"Invalid semver: {version_str}")
        self.major = int(match.group(1))
        self.minor = int(match.group(2))
        self.patch = int(match.group(3))
        self.pre = match.group(4)
        self.build = match.group(5)

    def __str__(self):
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre:
            base += f"-{self.pre}"
        if self.build:
            base += f"+{self.build}"
        return base

    def __lt__(self, other: 'SemVer'):
        # Compare major, minor, patch, then pre-release
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        # Pre-release: absence > presence, then lexical
        if self.pre == other.pre:
            return False
        if self.pre is None:
            return False  # self is greater
        if other.pre is None:
            return True
        return self.pre < other.pre

    def __eq__(self, other):
        return (self.major, self.minor, self.patch, self.pre) == (other.major, other.minor, other.patch, other.pre)
    def __le__(self, other): return self < other or self == other
    def __gt__(self, other): return not self <= other
    def __ge__(self, other): return not self < other

# ========== DEPENDENCY CACHE ==========
class DependencyCache:
    """Cache em disco para dependências, evitando re-downloads."""
    def __init__(self, cache_dir: Path = Path(".arkhe-cache/deps")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, name: str, version: SemVer) -> str:
        return f"{name}@{version}"

    def has(self, name: str, version: SemVer) -> bool:
        return (self.cache_dir / self._key(name, version)).exists()

    def get(self, name: str, version: SemVer) -> Optional[bytes]:
        path = self.cache_dir / self._key(name, version)
        if path.exists():
            return path.read_bytes()
        return None

    def store(self, name: str, version: SemVer, content: bytes):
        path = self.cache_dir / self._key(name, version)
        path.write_bytes(content)

    def resolve_latest(self, name: str, registry: PackageRegistry) -> Optional[SemVer]:
        """Procura a versão mais recente no registry e retorna o SemVer."""
        versions = []
        for key in registry.blocks:
            if key.startswith(f"{name}@"):
                ver_str = key.split("@", 1)[1]
                try:
                    versions.append(SemVer(ver_str))
                except ValueError:
                    continue
        return max(versions) if versions else None

class ArkpCLI_Enhanced(ArkpCLI):
    def __init__(self, registry, auditor, qip, cache_dir=".arkhe-cache", mythos_gate=None):
        super().__init__(registry, auditor, qip)
        self.cache = DependencyCache(Path(cache_dir))
        self.gate = mythos_gate or MythosGate(mode='planetary')

    def resolve_dependencies(self, manifest: ArkToml) -> Dict[str, bytes]:
        """Resolve todas as dependências usando cache local e registry."""
        resolved = {}
        for name, version_req in manifest.dependencies.items():
            # versão pode ser "^1.0" (prefixo caret), "~1.2.3", ou um número exato
            if version_req.startswith('^'):
                base = SemVer(version_req[1:] + (".0" if version_req.count(".") == 1 else ".0.0" if version_req.count(".") == 0 else ""))
                # compatível com mesma major, >= base

                latest_compatible = None
                for key in self.registry.blocks:
                    if key.startswith(f"{name}@"):
                        ver_str = key.split("@", 1)[1]
                        try:
                            v = SemVer(ver_str)
                            if v.major == base.major and v >= base:
                                if latest_compatible is None or v > latest_compatible:
                                    latest_compatible = v
                        except ValueError:
                            continue

                if latest_compatible:
                    version = latest_compatible

                else:
                    raise ValueError(f"No compatible version for {name} {version_req}")
            elif version_req.startswith('~'):
                base = SemVer(version_req[1:] + (".0" if version_req.count(".") == 1 else ".0.0" if version_req.count(".") == 0 else ""))

                latest_compatible = None
                for key in self.registry.blocks:
                    if key.startswith(f"{name}@"):
                        ver_str = key.split("@", 1)[1]
                        try:
                            v = SemVer(ver_str)
                            if v.major == base.major and v.minor == base.minor and v >= base:
                                if latest_compatible is None or v > latest_compatible:
                                    latest_compatible = v
                        except ValueError:
                            continue

                if latest_compatible:
                    version = latest_compatible

                else:
                    raise ValueError(f"No compatible version for {name} {version_req}")
            else:
                version = SemVer(version_req)

            # Tentar cache
            content = self.cache.get(name, version)
            if content is None:
                # Baixar do registry (simulado: gera conteúdo)
                content = f"package {name}@{version}".encode()
                self.cache.store(name, version, content)
            resolved[name] = content
        return resolved

    def build(self, prove=True, anchor=True):
        manifest = self.current_manifest
        if not manifest:
            return {"success": False, "error": "No manifest"}
        # Resolver deps com cache
        try:
            deps = self.resolve_dependencies(manifest)
        except Exception as e:
            return {"success": False, "error": str(e)}
        # ... continua com compilação (simulada)
        return super().build(prove, anchor)

    def publish(self, dry_run=False):
        """Publicação com Mythos Gate para decisões irreversíveis."""
        manifest = self.current_manifest
        if not manifest:
            return {"success": False, "error": "No manifest"}

        # 1. Auditoria ConRAG
        source_code = "simulated source"
        audit = self.auditor.audit(manifest, source_code)
        if not audit.passed and not dry_run:
            return {"success": False, "error": "Audit failed", "audit": audit}

        # 2. Mythos Gate avalia publicação (ex: pacote nuclear?)
        gate_decision = self.gate.evaluate_irreversible(
            f"publish {manifest.package_name}@{manifest.version}",
            context={"foresight_risk": self._compute_risk(manifest)}
        )
        if not gate_decision:
            return {"success": False, "error": "Mythos Gate rejected publication"}

        # 3. Publicação normal
        return super().publish(dry_run)

    def _compute_risk(self, manifest: ArkToml) -> float:
        """Risco baseado em palavras-chave e dependências."""
        risk = 0.05
        if any(kw in manifest.package_name for kw in ["nuclear", "bioweapon", "genesis"]):
            risk = 0.9
        elif "unsafe" in manifest.description.lower():
            risk = 0.6
        return risk

class PluggableAuditor(ConRAGAuditor):
    def __init__(self, level=AuditLevel.STANDARD):
        super().__init__(level)
        self.plugins: List[Callable] = []

    def register_plugin(self, plugin_fn):
        self.plugins.append(plugin_fn)

    def audit(self, manifest, source):
        base = super().audit(manifest, source)
        combined = AuditReport(passed=base.passed, score=base.score,
                               checks=dict(base.checks), issues=list(base.issues),
                               zk_proof=base.zk_proof, temporal_anchor=base.temporal_anchor)
        for plugin in self.plugins:
            plugin_report = plugin(manifest, source)
            combined.passed = combined.passed and plugin_report.passed
            combined.issues.extend(plugin_report.issues)
            combined.checks.update(plugin_report.checks)
        # Recalcular score
        if combined.checks:
            combined.score = sum(1 for v in combined.checks.values() if v) / len(combined.checks)
        return combined

# Exemplo de plugin: verifica presença de licença no manifesto
def license_audit_plugin(manifest: ArkToml, source: str) -> AuditReport:
    if manifest.license in ["MIT", "Apache-2.0", "BSD-3-Clause"]:
        return AuditReport(passed=True, score=1.0, checks={"license_ok": True})
    return AuditReport(passed=False, score=0.0, issues=["License not recognized"],
                       checks={"license_ok": False})


class CrossBranchPublisher:
    def __init__(self, registry: PackageRegistry, router: MultiverseRouter):
        self.registry = registry
        self.router = router

    def publish_across_branches(self, block: ArtBlock, target_branches: List[str]):
        """Publica o mesmo ArtBlock em múltiplas branches do multiverso."""
        results = {}
        for branch in target_branches:
            # Cada branch tem seu próprio registry isolado
            branch_registry = self.router.branches[branch].get('registry')
            if not branch_registry:
                results[branch] = False
                continue
            try:
                branch_registry.publish(block)
                # Roteia evento de publicação
                self.router.route(self.router.current_branch, branch, {"type": "artblock_published", "hash": block.package_hash})
                results[branch] = True
            except:
                results[branch] = False
        return results

import time, threading, random

class EcosystemMetrics:
    """Coleta métricas simuladas que, em produção, seriam expostas via eBPF."""
    def __init__(self, registry, qip, auditor):
        self.registry = registry
        self.qip = qip
        self.auditor = auditor
        self._running = False
        self._thread = None

    def start(self, interval=5):
        self._running = True
        self._thread = threading.Thread(target=self._collect, args=(interval,), daemon=True)
        self._thread.start()

    def _collect(self, interval):
        while self._running:
            # Simular métricas
            metrics = {
                "total_packages": len(self.registry.blocks),
                "qip_events": len(self.qip.influence_events),
                "avg_audit_score": 0.8 + random.random()*0.2,
                "timestamp": int(time.time())
            }
            # Em produção, escreve em mapa eBPF
            time.sleep(interval)

    def snapshot(self):
        return {
            "total_packages": len(self.registry.blocks),
            "total_qip_balance": sum(self.qip.balances.values()),
        }
