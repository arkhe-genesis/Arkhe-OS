import hashlib
import json
import os
import time
import re
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from enum import Enum, auto
from pathlib import Path

# ============================================================
# SEMVER — Versionamento Semântico Real (Rust/npm compatible)
# ============================================================

@dataclass
class SemVer:
    """Versionamento semântico: MAJOR.MINOR.PATCH[-prerelease][+build]"""
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None

    @classmethod
    def parse(cls, version: str) -> "SemVer":
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?(?:\+([a-zA-Z0-9.-]+))?$'
        m = re.match(pattern, version.strip())
        if not m:
            raise ValueError(f"Invalid semver: {version}")
        major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
        prerelease = m.group(4)
        build = m.group(5)
        return cls(major, minor, patch, prerelease, build)

    def __str__(self) -> str:
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            s += f"-{self.prerelease}"
        if self.build:
            s += f"+{self.build}"
        return s

    def __lt__(self, other: "SemVer") -> bool:
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        if self.prerelease is None and other.prerelease is not None:
            return False  # release > prerelease
        if self.prerelease is not None and other.prerelease is None:
            return True
        if self.prerelease and other.prerelease:
            return self._compare_prerelease(self.prerelease, other.prerelease) < 0
        return False

    def __le__(self, other: "SemVer") -> bool:
        return self == other or self < other

    def __gt__(self, other: "SemVer") -> bool:
        return not self <= other

    def __ge__(self, other: "SemVer") -> bool:
        return not self < other

    def __eq__(self, other) -> bool:
        if not isinstance(other, SemVer):
            return False
        return (self.major, self.minor, self.patch, self.prerelease) == \
               (other.major, other.minor, other.patch, other.prerelease)

    def __hash__(self):
        return hash((self.major, self.minor, self.patch, self.prerelease))

    def _compare_prerelease(self, a: str, b: str) -> int:
        pa = a.split('.')
        pb = b.split('.')
        for x, y in zip(pa, pb):
            nx, ny = x.isdigit(), y.isdigit()
            if nx and ny:
                xi, yi = int(x), int(y)
                if xi != yi:
                    return -1 if xi < yi else 1
            elif nx:
                return -1  # numeric < alphanumeric
            elif ny:
                return 1
            else:
                if x != y:
                    return -1 if x < y else 1
        return len(pa) - len(pb)

    def is_compatible_with(self, other: "SemVer") -> bool:
        """Verifica se OTHER é compatível com SELF (a versão requisitada).
        Para 1.x.y: mesmo MAJOR, other >= self.
        Para 0.x.y: mesmo MAJOR e MINOR, other >= self."""
        if self.major == 0:
            return self.major == other.major and self.minor == other.minor and other >= self
        return self.major == other.major and other >= self

    def bump_major(self) -> "SemVer":
        return SemVer(self.major + 1, 0, 0)

    def bump_minor(self) -> "SemVer":
        return SemVer(self.major, self.minor + 1, 0)

    def bump_patch(self) -> "SemVer":
        return SemVer(self.major, self.minor, self.patch + 1)

# ============================================================
# DEPENDENCY CACHE — Cache de dependências para builds incrementais
# ============================================================

class DependencyCache:
    """Cache de dependências resolvidas para builds incrementais"""

    def __init__(self, cache_dir: str = "/tmp/arkhe_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _cache_path(self, name: str, version: str) -> Path:
        key = hashlib.sha3_256(f"{name}@{version}".encode()).hexdigest()[:16]
        return self.cache_dir / key

    def get(self, name: str, version: str) -> Optional[bytes]:
        path = self._cache_path(name, version)
        if path.exists():
            self.hits += 1
            return path.read_bytes()
        self.misses += 1
        return None

    def set(self, name: str, version: str, content: bytes) -> Path:
        path = self._cache_path(name, version)
        path.write_bytes(content)
        return path

    def invalidate(self, name: str, version: str) -> bool:
        path = self._cache_path(name, version)
        if path.exists():
            path.unlink()
            self.evictions += 1
            return True
        return False

    def resolve(self, name: str, version_req: str, registry: Dict[str, List[str]]) -> Optional[Tuple[str, bytes]]:
        """Resolve versão compatível e retorna do cache ou registry"""
        available = registry.get(name, [])
        req = SemVer.parse(version_req) if version_req[0].isdigit() else None

        best_version = None
        for v in available:
            try:
                sv = SemVer.parse(v)
                if req and req.is_compatible_with(sv):
                    if best_version is None or sv > best_version:
                        best_version = sv
            except ValueError:
                continue

        if best_version is None:
            return None

        vstr = str(best_version)
        cached = self.get(name, vstr)
        if cached:
            return (vstr, cached)

        # Simula download do registry
        content = f"DOWNLOADED:{name}@{vstr}".encode()
        self.set(name, vstr, content)
        return (vstr, content)

    def get_stats(self) -> Dict:
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": hit_rate,
            "cache_dir": str(self.cache_dir),
        }

# ============================================================
# MYTHOS GATE AUDITOR — Decisões de publicação com contexto ético
# ============================================================

class MythosGateAuditor:
    """Integra ConRAG com Mythos Gate para decisões complexas de publicação"""

    MODES = {'planetary': 0.9, 'colony': 0.8, 'deep_space': 0.7}

    def __init__(self, mode: str = 'planetary'):
        self.threshold = self.MODES.get(mode, 0.9)
        self.decision_log: List[Dict] = []

    def evaluate_publication(self, manifest: Dict, code: str, audit_scores: Dict) -> Dict:
        """Avalia se a publicação deve ser permitida dado contexto ético"""

        # Risco combinado: audit_score inverso + complexidade do código + impacto potencial
        audit_risk = 1.0 - (sum(audit_scores.values()) / len(audit_scores) if audit_scores else 0.5)
        complexity = min(1.0, len(code) / 10000)
        impact = manifest.get("impact_score", 0.3)

        risk = (audit_risk * 0.4 + complexity * 0.3 + impact * 0.3)

        # Verificar conteúdo letal
        lethal = ["weaponize", "kill", "destroy", "annihilate", "exploit", "surveillance_mass"]
        for word in lethal:
            if word in code.lower():
                risk = 1.0
                break

        approved = risk < self.threshold
        requires_human = risk >= 0.5

        decision = {
            "approved": approved,
            "risk": risk,
            "threshold": self.threshold,
            "requires_human_review": requires_human,
            "mode": [k for k, v in self.MODES.items() if v == self.threshold][0] if self.threshold in self.MODES.values() else "custom",
            "factors": {"audit_risk": audit_risk, "complexity": complexity, "impact": impact},
            "timestamp_ns": int(time.time() * 1e9),
        }
        self.decision_log.append(decision)
        return decision

    def get_stats(self) -> Dict:
        if not self.decision_log:
            return {"total": 0, "approved": 0, "rejected": 0, "human_review": 0}
        total = len(self.decision_log)
        approved = sum(1 for d in self.decision_log if d["approved"])
        human = sum(1 for d in self.decision_log if d["requires_human_review"])
        return {
            "total": total,
            "approved": approved,
            "rejected": total - approved,
            "human_review": human,
            "approval_rate": approved / total,
        }

# ============================================================
# PLUGGABLE AUDITOR — Plugins de auditoria customizáveis
# ============================================================

@dataclass
class AuditReport:
    passed: bool
    score: float
    issues: List[str]
    plugin_name: str

class PluggableAuditor:
    """Auditor com plugins dinâmicos para verificações customizadas"""

    def __init__(self):
        self.plugins: List[Tuple[str, Callable[[Dict, str], AuditReport]]] = []
        self.base_checks = {
            "beaver_bias": 0.85,
            "rlcr_robustness": 0.75,
            "constitutional": 0.90,
            "explainability": 0.70,
            "hallucination": 0.75,
        }

    def register_plugin(self, name: str, plugin: Callable[[Dict, str], AuditReport]):
        self.plugins.append((name, plugin))

    def audit(self, manifest: Dict, code: str) -> Dict:
        scores = {}
        issues = []

        # Base checks
        scores["beaver_bias"] = 0.88 if "fairness" in str(manifest).lower() or "bias" in code.lower() else 0.90
        scores["rlcr_robustness"] = 0.90 if "try" in code or "catch" in code else 0.80
        scores["constitutional"] = 0.95 if not any(w in code.lower() for w in ["weaponize", "kill", "destroy"]) else 0.0
        scores["explainability"] = 0.85 if "#" in code or "///" in code else 0.75
        scores["hallucination"] = 0.92 if "assert" in code or "prove" in code.lower() else 0.80

        violations = [k for k, v in scores.items() if v < self.base_checks[k]]

        # Plugin checks
        plugin_results = []
        for pname, plugin in self.plugins:
            report = plugin(manifest, code)
            plugin_results.append({"name": pname, "passed": report.passed, "score": report.score, "issues": report.issues})
            if not report.passed:
                violations.append(f"plugin:{pname}")
                issues.extend(report.issues)

        all_scores = list(scores.values()) + [r["score"] for r in plugin_results]
        overall = sum(all_scores) / len(all_scores) if all_scores else 0.0
        passed = len(violations) == 0

        return {
            "passed": passed,
            "scores": scores,
            "overall": overall,
            "violations": violations,
            "plugin_results": plugin_results,
            "issues": issues,
        }

# ============================================================
# EBPF METRICS — Monitoramento de saúde do ecossistema (simulado)
# ============================================================

class eBPFMetrics:
    """Métricas em tempo real do ecossistema (simulação de eBPF probes)"""

    def __init__(self):
        self.metrics: Dict[str, List[float]] = {
            "build_latency_ms": [],
            "publish_rate": [],
            "audit_pass_rate": [],
            "cache_hit_rate": [],
            "dependency_resolution_time_ms": [],
            "memory_usage_mb": [],
        }
        self.alerts: List[Dict] = []
        self.thresholds = {
            "build_latency_ms": 5000,
            "audit_pass_rate": 0.70,
            "cache_hit_rate": 0.50,
        }

    def record(self, metric: str, value: float):
        if metric in self.metrics:
            self.metrics[metric].append(value)
            # Keep last 1000 samples
            if len(self.metrics[metric]) > 1000:
                self.metrics[metric] = self.metrics[metric][-1000:]
        self._check_alert(metric, value)

    def _check_alert(self, metric: str, value: float):
        threshold = self.thresholds.get(metric)
        if threshold is None:
            return
        if metric == "audit_pass_rate" or metric == "cache_hit_rate":
            if value < threshold:
                self.alerts.append({
                    "metric": metric,
                    "value": value,
                    "threshold": threshold,
                    "severity": "warning" if value > threshold * 0.8 else "critical",
                    "timestamp_ns": int(time.time() * 1e9),
                })
        else:
            if value > threshold:
                self.alerts.append({
                    "metric": metric,
                    "value": value,
                    "threshold": threshold,
                    "severity": "warning",
                    "timestamp_ns": int(time.time() * 1e9),
                })

    def get_summary(self) -> Dict:
        summary = {}
        for metric, values in self.metrics.items():
            if values:
                summary[metric] = {
                    "count": len(values),
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "last": values[-1],
                }
        return summary

    def get_alerts(self, severity: Optional[str] = None) -> List[Dict]:
        if severity:
            return [a for a in self.alerts if a["severity"] == severity]
        return self.alerts[-10:]  # last 10

    def health_score(self) -> float:
        """Score de saúde do ecossistema (0-1)"""
        scores = []
        if self.metrics["audit_pass_rate"]:
            scores.append(self.metrics["audit_pass_rate"][-1])
        if self.metrics["cache_hit_rate"]:
            scores.append(self.metrics["cache_hit_rate"][-1])
        if self.metrics["build_latency_ms"]:
            # Lower is better, normalize
            lat = self.metrics["build_latency_ms"][-1]
            scores.append(max(0, 1 - lat / 10000))
        return sum(scores) / len(scores) if scores else 1.0

# ============================================================
# CROSS-BRANCH PUBLISHER — Publicação via Multiverse Router
# ============================================================

class CrossBranchPublisher:
    """Publica pacotes em múltiplas branches do multiverso"""

    def __init__(self):
        self.branches: Dict[str, Dict[str, Any]] = {}  # branch -> {packages}
        self.publications: List[Dict] = []

    def register_branch(self, branch_id: str, coherence: float, parent: Optional[str] = None):
        self.branches[branch_id] = {
            "coherence": coherence,
            "parent": parent,
            "packages": {},
        }

    def publish(self, package_name: str, version: str, artifact: bytes,
                target_branches: List[str], source_branch: str = "main") -> Dict:
        """Publica pacote em múltiplas branches com verificação de coerência"""
        results = {}

        for branch in target_branches:
            if branch not in self.branches:
                results[branch] = {"error": "branch_not_found"}
                continue

            # Verificar divergência
            src_coh = self.branches[source_branch]["coherence"] if source_branch in self.branches else 1.0
            dst_coh = self.branches[branch]["coherence"]
            divergence = abs(src_coh - dst_coh)

            if divergence > 0.30:
                results[branch] = {"error": "divergence_too_high", "diff": divergence}
                continue

            # Publicar
            pkg_id = f"{package_name}@{version}"
            self.branches[branch]["packages"][pkg_id] = {
                "artifact_hash": hashlib.sha3_256(artifact).hexdigest()[:16],
                "source_branch": source_branch,
                "coherence_at_publish": dst_coh,
                "timestamp_ns": int(time.time() * 1e9),
            }

            pub_record = {
                "package": package_name,
                "version": version,
                "branch": branch,
                "divergence": divergence,
                "success": True,
            }
            self.publications.append(pub_record)
            results[branch] = pub_record

        return results

    def get_package(self, package_name: str, version: str, branch: str) -> Optional[Dict]:
        pkg_id = f"{package_name}@{version}"
        return self.branches.get(branch, {}).get("packages", {}).get(pkg_id)

    def list_branches(self) -> List[str]:
        return list(self.branches.keys())

    def get_publication_stats(self) -> Dict:
        total = len(self.publications)
        success = sum(1 for p in self.publications if p.get("success"))
        return {
            "total_publications": total,
            "successful": success,
            "failed": total - success,
            "branches": len(self.branches),
        }

# ============================================================
# TESTES CANÔNICOS
# ============================================================

if __name__ == "__main__":
    results = []
    def test(name, fn):
        try:
            fn()
            results.append((name, "PASS", None))
            print(f"  OK {name}")
        except Exception as e:
            import traceback; traceback.print_exc()

            results.append((name, "FAIL", str(e)))
            print(f"  FAIL {name}: {e}")

    print("\n=== ARKHE v5.3.1 — CAMADA 4 EXTENDIDA ===\n")

    # ---------- SEMVER ----------

    def t1():
        v = SemVer.parse("1.2.3")
        assert v.major == 1 and v.minor == 2 and v.patch == 3
        assert str(v) == "1.2.3"
    test("SemVer basic", t1)

    def t2():
        v = SemVer.parse("2.0.0-alpha.1+build.123")
        assert v.major == 2 and v.prerelease == "alpha.1" and v.build == "build.123"
    test("SemVer prerelease+build", t2)

    def t3():
        v1 = SemVer.parse("1.0.0")
        v2 = SemVer.parse("1.0.1")
        v3 = SemVer.parse("1.1.0")
        v4 = SemVer.parse("2.0.0")
        assert v1 < v2 < v3 < v4
        assert v4 > v3 > v2 > v1
        assert v1 == SemVer.parse("1.0.0")
    test("SemVer ordering", t3)

    def t4():
        v1 = SemVer.parse("1.0.0-alpha")
        v2 = SemVer.parse("1.0.0")
        assert v1 < v2  # prerelease < release
    test("SemVer prerelease < release", t4)

    def t5():
        v1 = SemVer.parse("1.2.3")
        v2 = SemVer.parse("1.3.0")
        v3 = SemVer.parse("2.0.0")
        assert v1.is_compatible_with(v2)
        assert not v1.is_compatible_with(v3)
        assert not v1.is_compatible_with(SemVer.parse("1.2.2"))
    test("SemVer compatibility", t5)

    def t6():
        v = SemVer.parse("1.2.3")
        assert str(v.bump_patch()) == "1.2.4"
        assert str(v.bump_minor()) == "1.3.0"
        assert str(v.bump_major()) == "2.0.0"
    test("SemVer bump", t6)

    # ---------- DEPENDENCY CACHE ----------

    def t7():
        cache = DependencyCache("/tmp/arkhe_test_cache")
        cache.set("numpy", "1.24.0", b"numpy_content")
        assert cache.get("numpy", "1.24.0") == b"numpy_content"
    test("Cache basic", t7)

    def t8():
        cache = DependencyCache("/tmp/arkhe_test_cache2")
        assert cache.get("missing", "1.0.0") is None
        assert cache.get_stats()["misses"] == 1
        assert cache.get_stats()["hits"] == 0
    test("Cache miss", t8)

    def t9():
        cache = DependencyCache("/tmp/arkhe_test_cache3")
        cache.set("pkg", "1.0.0", b"content")
        cache.invalidate("pkg", "1.0.0")
        assert cache.get("pkg", "1.0.0") is None
        assert cache.get_stats()["evictions"] == 1
    test("Cache invalidate", t9)

    def t10():
        cache = DependencyCache("/tmp/arkhe_test_cache4")
        registry = {
            "arkhe-core": ["1.0.0", "1.1.0", "1.2.0", "2.0.0"],
        }
        result = cache.resolve("arkhe-core", "1.1.0", registry)
        assert result is not None
        version, content = result
        assert version == "1.2.0"  # best compatible
        # Second call should hit cache
        result2 = cache.resolve("arkhe-core", "1.1.0", registry)
        assert result2[0] == "1.2.0"
        assert cache.get_stats()["hit_rate"] > 0
    test("Cache resolve semver", t10)

    def t11():
        cache = DependencyCache("/tmp/arkhe_test_cache5")
        registry = {"pkg": ["2.0.0", "3.0.0"]}
        result = cache.resolve("pkg", "1.0.0", registry)
        assert result is None  # no compatible version
    test("Cache resolve fail", t11)

    # ---------- MYTHOS GATE AUDITOR ----------

    def t12():
        mg = MythosGateAuditor(mode="planetary")
        r = mg.evaluate_publication(
            {"impact_score": 0.2},
            "def safe(): return 42",
            {"beaver": 0.9, "rlcr": 0.9, "constitutional": 0.95}
        )
        assert r["approved"]
        assert not r["requires_human_review"]
        assert r["risk"] < 0.3
    test("Mythos approve safe", t12)

    def t13():
        mg = MythosGateAuditor(mode="deep_space")
        r = mg.evaluate_publication(
            {"impact_score": 0.8},
            "def weaponize(): return missile",
            {"beaver": 0.9, "rlcr": 0.9, "constitutional": 0.95}
        )
        assert not r["approved"]
        assert r["risk"] == 1.0
    test("Mythos block lethal", t13)

    def t14():
        mg = MythosGateAuditor(mode="colony")
        # High complexity code + low audit scores + high impact = high risk
        code = "def complex_ai():\n" + "\n".join([f"    x{i} = compute_{i}()" for i in range(500)])
        r = mg.evaluate_publication(
            {"impact_score": 1.0},
            code,
            {"beaver": 0.3, "rlcr": 0.3, "constitutional": 0.3}
        )
        assert not r["approved"]  # high risk
        assert r["requires_human_review"]
    test("Mythos human review", t14)

    def t15():
        mg = MythosGateAuditor(mode="planetary")
        mg.evaluate_publication({}, "safe", {"a": 0.9})
        mg.evaluate_publication({}, "weaponize", {"a": 0.9})
        stats = mg.get_stats()
        assert stats["total"] == 2
        assert stats["approved"] == 1
        assert stats["rejected"] == 1
    test("Mythos stats", t15)

    # ---------- PLUGGABLE AUDITOR ----------

    def t16():
        pa = PluggableAuditor()
        r = pa.audit({"name": "x"}, "def main(): return 42")
        assert r["passed"]
        assert r["overall"] >= 0.80
        assert len(r["plugin_results"]) == 0
    test("Pluggable base pass", t16)

    def t17():
        pa = PluggableAuditor()
        def my_plugin(manifest, code):
            if "unsafe" in code.lower():
                return AuditReport(False, 0.0, ["unsafe detected"], "safety_check")
            return AuditReport(True, 1.0, [], "safety_check")
        pa.register_plugin("safety_check", my_plugin)
        r = pa.audit({"name": "x"}, "unsafe_call()")
        assert not r["passed"]
        assert "plugin:safety_check" in r["violations"]
    test("Pluggable plugin block", t17)

    def t18():
        pa = PluggableAuditor()
        def plugin1(m, c):
            return AuditReport(True, 0.95, [], "p1")
        def plugin2(m, c):
            return AuditReport(True, 0.90, [], "p2")
        pa.register_plugin("p1", plugin1)
        pa.register_plugin("p2", plugin2)
        r = pa.audit({"name": "x"}, "def main(): return 42")
        assert r["passed"]
        assert len(r["plugin_results"]) == 2
        assert r["overall"] >= 0.85
    test("Pluggable multi plugin", t18)

    # ---------- EBPF METRICS ----------

    def t19():
        m = eBPFMetrics()
        m.record("build_latency_ms", 100)
        m.record("audit_pass_rate", 0.95)
        summary = m.get_summary()
        assert summary["build_latency_ms"]["mean"] == 100
        assert summary["audit_pass_rate"]["mean"] == 0.95
    test("eBPF record", t19)

    def t20():
        m = eBPFMetrics()
        m.record("audit_pass_rate", 0.50)
        alerts = m.get_alerts("critical")
        assert len(alerts) >= 1
        assert alerts[0]["metric"] == "audit_pass_rate"
    test("eBPF alert", t20)

    def t21():
        m = eBPFMetrics()
        m.record("audit_pass_rate", 0.90)
        m.record("cache_hit_rate", 0.85)
        m.record("build_latency_ms", 500)
        score = m.health_score()
        assert 0 <= score <= 1
        assert score > 0.7
    test("eBPF health score", t21)

    # ---------- CROSS-BRANCH PUBLISHER ----------

    def t22():
        cb = CrossBranchPublisher()
        cb.register_branch("main", 1.0)
        cb.register_branch("alpha", 0.98)
        cb.register_branch("beta", 0.50)

        results = cb.publish("my-pkg", "1.0.0", b"artifact", ["main", "alpha", "beta"])
        assert results["main"]["success"]
        assert results["alpha"]["success"]
        assert "error" in results["beta"]  # divergence too high
        assert results["beta"]["error"] == "divergence_too_high"
    test("Cross-branch publish", t22)

    def t23():
        cb = CrossBranchPublisher()
        cb.register_branch("main", 1.0)
        cb.register_branch("stable", 0.99)
        cb.publish("pkg", "1.0.0", b"data", ["main", "stable"])

        pkg = cb.get_package("pkg", "1.0.0", "stable")
        assert pkg is not None
        assert pkg["source_branch"] == "main"
    test("Cross-branch get", t23)

    def t24():
        cb = CrossBranchPublisher()
        cb.register_branch("b1", 0.95)
        cb.register_branch("b2", 0.96)
        cb.publish("x", "1.0.0", b"a", ["b1", "b2"])
        stats = cb.get_publication_stats()
        assert stats["total_publications"] == 2
        assert stats["successful"] == 2
    test("Cross-branch stats", t24)

    # ---------- INTEGRATION ----------

    def t25():
        # Pipeline completo: SemVer + Cache + Mythos + Pluggable + eBPF + Cross-Branch

        import shutil
        import os
        if os.path.exists("/tmp/arkhe_integration"):
            shutil.rmtree("/tmp/arkhe_integration")

        # 1. Versionamento
        v = SemVer.parse("2.1.0")

        # 2. Cache
        cache = DependencyCache("/tmp/arkhe_integration")
        registry = {"arkhe-core": ["1.0.0", "1.1.0", "2.0.0", "2.1.0"]}
        resolved = cache.resolve("arkhe-core", str(v), registry)
        assert resolved[0] == "2.1.0"
        # Simula uma segunda resolução para gerar cache hit
        cache.resolve("arkhe-core", str(v), registry)


        # 3. Auditoria com plugin
        pa = PluggableAuditor()
        def license_plugin(manifest, code):
            if manifest.get("license") != "ARKHE-1.0":
                return AuditReport(False, 0.0, ["invalid_license"], "license_check")
            return AuditReport(True, 1.0, [], "license_check")
        pa.register_plugin("license_check", license_plugin)

        manifest = {"name": "my-pkg", "version": "2.1.0", "license": "ARKHE-1.0"}
        audit = pa.audit(manifest, "def main(): return 42")
        assert audit["passed"]

        # 4. Mythos Gate
        mg = MythosGateAuditor(mode="planetary")
        mythos = mg.evaluate_publication(manifest, "def main(): return 42", audit["scores"])
        assert mythos["approved"]

        # 5. eBPF metrics
        metrics = eBPFMetrics()
        metrics.record("audit_pass_rate", audit["overall"])
        metrics.record("cache_hit_rate", cache.get_stats()["hit_rate"])
        assert metrics.health_score() > 0.5

        # 6. Cross-branch publish
        cb = CrossBranchPublisher()
        cb.register_branch("main", 1.0)
        cb.register_branch("stable", 0.99)
        pub = cb.publish("my-pkg", "2.1.0", b"artifact", ["main", "stable"])
        assert pub["main"]["success"]
        assert pub["stable"]["success"]

        print(f"    Pipeline v{str(v)} published to {len(pub)} branches")
        print(f"    Health score: {metrics.health_score():.2f}")
        print(f"    Cache hit rate: {cache.get_stats()['hit_rate']:.2f}")
    test("Integration v5.3.1 full", t25)

    print("\n" + "="*55)
    p = sum(1 for r in results if r[1] == "PASS")
    f = sum(1 for r in results if r[1] == "FAIL")
    print(f"Total: {len(results)} | PASS: {p} | FAIL: {f}")
    if f == 0:
        print("ALL PASSED — Camada 4 v5.3.1 validada.")
        chain = json.dumps([{"t": r[0], "s": r[1]} for r in results], sort_keys=True, default=str)
        print(f"Test seal: {hashlib.sha3_256(chain.encode()).hexdigest()[:16]}")
        with open(__file__, 'rb') as f_obj:
            print(f"Substrate seal: {hashlib.sha3_256(f_obj.read()).hexdigest()[:16]}")
    else:
        for n, s, e in results:
            if s == "FAIL": print(f"  FAIL: {n}: {e}")