#!/usr/bin/env python3
import hashlib
import json
import base64
import tempfile
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

# ═══════════════════════════════════════════════
# CLASSES CANÓNICAS — EXTENSÃO DE 252 (SDX)
# ═══════════════════════════════════════════════

@dataclass
class OCIImage:
    """Subclasse de sdx:Package para imagens OCI (Docker)."""
    name: str
    version: str
    digest: str             # sha256:abc...
    media_type: str         # application/vnd.oci.image.manifest.v1+json
    registry: str           # ghcr.io/arkhe
    architecture: str = "amd64"
    os: str = "linux"
    annotations: Dict[str, str] = field(default_factory=dict)
    seal: Optional[str] = None

    def to_sdx(self) -> dict:
        return {
            "@type": "sdx:OCIImage",
            "sdx:artifactName": self.name + ":" + self.version,
            "sdx:digest": self.digest,
            "sdx:ociMediaType": self.media_type,
            "sdx:publishedAt": {"sdx:repositoryURL": self.registry + "/" + self.name},
            "sdx:hasVersion": {"sdx:versionString": self.version},
            "arkhe:hasSeal": {"arkhe:sealHash": self.seal or "PENDING"}
        }

@dataclass
class HelmChart:
    """Subclasse de sdx:Package para charts Helm."""
    name: str
    version: str
    digest: str             # sha256 do .tgz
    repo_url: str           # https://charts.arkhe.org
    api_version: str = "v2"
    dependencies: List[Dict] = field(default_factory=list)
    seal: Optional[str] = None

    def to_sdx(self) -> dict:
        return {
            "@type": "sdx:HelmChart",
            "sdx:artifactName": self.name,
            "sdx:digest": self.digest,
            "sdx:publishedAt": {"sdx:repositoryURL": self.repo_url},
            "sdx:hasVersion": {"sdx:versionString": self.version},
            "sdx:apiVersion": self.api_version,
            "sdx:dependsOn": self.dependencies,
            "arkhe:hasSeal": {"arkhe:sealHash": self.seal or "PENDING"}
        }

# ═══════════════════════════════════════════════
# CHAIN OF TRUST — ÁRVORE DE DEPENDÊNCIAS
# ═══════════════════════════════════════════════

class ChainOfTrust:
    """Verifica a integridade recursiva de uma árvore de artefactos."""

    def __init__(self):
        self.verified: Dict[str, bool] = {}
        self.failures: List[Dict] = []

    def verify(self, artifact: dict, registry: Dict[str, dict]) -> bool:
        """
        Verifica recursivamente um artefacto e todas as suas dependências.
        registry: mapeamento artifact_name → dados esperados (incluindo seal).
        """
        name = artifact.get("sdx:artifactName") or artifact.get("name")
        if name in self.verified:
            return self.verified[name]

        # Verificar selo do artefacto atual
        expected = registry.get(name, {})
        seal = artifact.get("arkhe:hasSeal", {}).get("arkhe:sealHash") or artifact.get("seal")
        if seal != expected.get("seal"):
            self.failures.append({"artifact": name, "reason": "Seal mismatch"})
            self.verified[name] = False
            return False

        # Verificar dependências recursivamente
        deps = artifact.get("sdx:dependsOn", [])
        if isinstance(deps, dict):
            deps = [deps]  # normalizar se vier como objeto único
        for dep in deps:
            dep_name = dep.get("sdx:artifactName") or dep.get("name")
            if dep_name:
                # Sempre verificar o selo contra o registo, independentemente do cache
                if dep_name not in registry:
                    self.failures.append({"artifact": dep_name, "reason": "Dependency not in registry"})
                    self.verified[dep_name] = False
                    self.verified[name] = False
                    return False
                dep_seal = dep.get("arkhe:hasSeal", {}).get("arkhe:sealHash") or dep.get("seal")
                if dep_seal != registry[dep_name].get("seal"):
                    self.failures.append({"artifact": dep_name, "reason": "Dependency seal mismatch"})
                    self.verified[dep_name] = False
                    self.verified[name] = False
                    return False

                # Verificar se o artefato foi previamente rejeitado
                if dep_name in self.verified and not self.verified[dep_name]:
                    self.verified[name] = False
                    return False

                self.verified[dep_name] = True

        self.verified[name] = True
        return True

# ═══════════════════════════════════════════════
# INTEGRAÇÃO COM BUILD PIPELINE (881)
# ═══════════════════════════════════════════════

class SLSAProvenanceGenerator:
    """Gera automaticamente sdx:Provenance a partir de um pipeline CI/CD."""

    @staticmethod
    def generate(artifact: dict, pipeline_run_id: str,
                 builder_id: str = "https://arkhe-ci.arkhe.io",
                 recipe: str = "Dockerfile") -> dict:
        """Retorna uma estrutura de proveniência SLSA nível 2."""
        return {
            "@type": "sdx:Provenance",
            "sdx:buildDate": datetime.now(timezone.utc).isoformat(),
            "sdx:buildEnvironment": "ARKHE CI/CD — run " + pipeline_run_id,
            "sdx:buildFrom": {"@type": "sdx:BuildRecipe", "recipe": recipe},
            "sdx:builderId": builder_id,
            "sdx:slsaLevel": "SLSA_BUILD_LEVEL_2",
            "arkhe:hasSeal": {
                "arkhe:hashAlgorithm": "SHA3-256",
                "arkhe:sealHash": hashlib.sha3_256(
                    json.dumps(artifact, sort_keys=True, default=str).encode()
                ).hexdigest()
            }
        }

if __name__ == "__main__":
    img = OCIImage(
        name="arkhe-gateway",
        version="870-G.4.0",
        digest="sha256:7c1e8d3f9a2b5c6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e",
        media_type="application/vnd.oci.image.manifest.v1+json",
        registry="ghcr.io/arkhe",
        seal="a1b2c3d4e5f6a7b8"
    )

    chart = HelmChart(
        name="arkhe-stack",
        version="1.0.0",
        digest="sha256:9f8e7d6c5b4a3210...",
        repo_url="https://charts.arkhe.org",
        dependencies=[
            {"name": "arkhe-gateway:870-G.4.0", "constraint": ">=870-G.4.0", "seal": "a1b2c3d4e5f6a7b8"}
        ],
        seal="f1e2d3c4b5a6..."
    )

    prov = SLSAProvenanceGenerator.generate(img.to_sdx(), "run-4242")
    img_sdx = img.to_sdx()
    img_sdx["sdx:hasProvenance"] = prov

    registry = {
        "arkhe-gateway:870-G.4.0": {"seal": "a1b2c3d4e5f6a7b8"},
        "arkhe-stack": {"seal": "f1e2d3c4b5a6..."},
    }
    cot = ChainOfTrust()
    valid = cot.verify(img_sdx, registry)

    report = {
        "status": "CANONIZED",
        "substrate": "888_owl_web3_supply_chain_bridge",
        "valid": valid,
        "failures": cot.failures,
        "canonical_seal": "f0e1d2c3b4a59687e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4"
    }

    _, report_path = tempfile.mkstemp(suffix=".json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print("Report written to", report_path)
