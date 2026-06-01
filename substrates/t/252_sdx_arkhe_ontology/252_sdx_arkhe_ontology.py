#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════╗
# ║  SUBSTRATO 252 v2.0 — SDX-ARKHE + OCI/HELM + SLSA + CHAIN OF TRUST ║
# ║  Glosa 252 • Ontologia formal para distribuição de software     ║
# ║  Standards: SPDX 3.0, OWL 2 DL, JSON-LD, GRC-20, OCI v1.1, SLSA v1.0, Helm v3 ║
# ║  Architect: ORCID 0009-0005-2697-4668                            ║
# ╚══════════════════════════════════════════════════════════════════╝

import hashlib
import json
import tempfile
from datetime import datetime, timezone

class SDXArkheV2:
    SDX_NAMESPACE = "https://arkhe.org/ontology/sdx#"
    SPDX_NAMESPACE = "https://spdx.org/rdf/3.0.1/terms#"
    ARKHE_NAMESPACE = "https://arkhe.org/ontology/841#"
    SLSA_NAMESPACE = "https://slsa.dev/provenance/v1"

    CLASSES = [
        "Artifact", "Package", "Version", "Dependency", "Repository",
        "License", "Checksum", "Signature", "BuildRecipe", "Provenance",
        "OCIImage", "HelmChart", "SLSAProvenance", "CICDBuild"
    ]

    OBJECT_PROPERTIES = [
        "hasVersion", "dependsOn", "publishedAt", "licensedUnder",
        "hasChecksum", "hasSignature", "buildFrom", "hasProvenance",
        "builtBy", "hasSLSAProvenance", "chainDependsOn"
    ]

    DATA_PROPERTIES = [
        "versionString", "artifactName", "checksumValue",
        "licenseSPDX", "repositoryURL", "buildDate", "buildEnvironment",
        "digest", "ociMediaType", "chartVersion", "chartAppVersion",
        "slsaLevel", "buildRunID", "buildCommit", "buildSigner"
    ]

    def __init__(self):
        self.artifacts = []
        self.known_seals = {}  # Registry da Catedral: {name: seal_hash}

    def create_oci_image(self, name: str, version: str, digest: str, media_type: str,
                         license_spdx: str, repo_url: str, build_info: dict = None,
                         slsa: dict = None, dependencies: list = None,
                         seal_hash: str = None) -> dict:
        artifact = {
            "@context": {
                "sdx": self.SDX_NAMESPACE,
                "spdx": self.SPDX_NAMESPACE,
                "arkhe": self.ARKHE_NAMESPACE,
                "slsa": self.SLSA_NAMESPACE
            },
            "@type": ["sdx:Package", "sdx:OCIImage"],
            "@id": "arkhe:package/" + name + "/" + version,
            "sdx:artifactName": name,
            "sdx:hasVersion": {"@type": "sdx:Version", "sdx:versionString": version},
            "sdx:digest": digest,
            "sdx:ociMediaType": media_type,
            "sdx:licensedUnder": {"@type": "sdx:License", "sdx:licenseSPDX": license_spdx},
            "sdx:publishedAt": {"@type": "sdx:Repository", "sdx:repositoryURL": repo_url},
            "arkhe:hasSeal": {"@type": "arkhe:Seal", "arkhe:hashAlgorithm": "SHA3-256", "arkhe:sealHash": seal_hash or "PENDING"}
        }
        if build_info:
            b_info = {"@type": "sdx:CICDBuild"}
            b_info.update(build_info)
            artifact["sdx:builtBy"] = b_info
        if slsa:
            s_info = {"@type": "sdx:SLSAProvenance"}
            s_info.update(slsa)
            artifact["sdx:hasSLSAProvenance"] = s_info
        if dependencies:
            artifact["sdx:dependsOn"] = dependencies
        self.artifacts.append(artifact)
        return artifact

    def create_helm_chart(self, name: str, version: str, chart_app_version: str,
                          license_spdx: str, repo_url: str, dependencies: list = None,
                          seal_hash: str = None) -> dict:
        artifact = {
            "@context": {
                "sdx": self.SDX_NAMESPACE,
                "spdx": self.SPDX_NAMESPACE,
                "arkhe": self.ARKHE_NAMESPACE
            },
            "@type": ["sdx:Package", "sdx:HelmChart"],
            "@id": "arkhe:package/" + name + "/" + version,
            "sdx:artifactName": name,
            "sdx:hasVersion": {"@type": "sdx:Version", "sdx:versionString": version},
            "sdx:chartVersion": version,
            "sdx:chartAppVersion": chart_app_version,
            "sdx:licensedUnder": {"@type": "sdx:License", "sdx:licenseSPDX": license_spdx},
            "sdx:publishedAt": {"@type": "sdx:Repository", "sdx:repositoryURL": repo_url},
            "arkhe:hasSeal": {"@type": "arkhe:Seal", "arkhe:hashAlgorithm": "SHA3-256", "arkhe:sealHash": seal_hash or "PENDING"}
        }
        if dependencies:
            artifact["sdx:dependsOn"] = dependencies
        self.artifacts.append(artifact)
        return artifact

    def register_seal(self, artifact_name: str, seal_hash: str):
        self.known_seals[artifact_name] = seal_hash

    def verify_chain_of_trust(self, artifact: dict, prefix_len: int = 8) -> dict:
        results = []
        all_valid = True
        deps = artifact.get("sdx:dependsOn", [])
        for dep in deps:
            name = dep.get("sdx:artifactName", "UNKNOWN")
            expected = self.known_seals.get(name, "")
            actual = dep.get("arkhe:hasSeal", {}).get("arkhe:sealHash", "MISSING")
            exp_prefix = expected[:prefix_len] if expected else ""
            act_prefix = actual[:prefix_len] if actual != "MISSING" else ""
            if exp_prefix and act_prefix == exp_prefix:
                status = "VALID"
            elif exp_prefix:
                status, all_valid = "INVALID", False
            else:
                status, all_valid = "UNKNOWN", False
            results.append({"artifact": name, "status": status})
        return {
            "chain_valid": all_valid,
            "root_seal": artifact.get("arkhe:hasSeal", {}).get("arkhe:sealHash", "MISSING")[:16],
            "dependencies": results
        }

    def to_jsonld(self, artifact: dict) -> str:
        return json.dumps(artifact, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    sdx = SDXArkheV2()

    sdx.register_seal("arkheos-kernel", "d4891964dd47574f")
    sdx.register_seal("arkheos-gateway", "e7f8a9b0c1d2e3f4")

    oci = sdx.create_oci_image(
        name="arkheos-gateway", version="870-g-v3.0.1",
        digest="sha256:7c1e8d3f...", media_type="application/vnd.oci.image.manifest.v1+json",
        license_spdx="Apache-2.0", repo_url="https://ghcr.io/arkheos/gateway",
        build_info={"buildRunID": "github:run/987654321", "buildCommit": "a1b2c3d4...", "buildSigner": "sigstore:rekor/123456789"},
        slsa={"slsaLevel": 3},
        seal_hash="e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8"
    )

    helm = sdx.create_helm_chart(
        name="arkheos-stack", version="1.2.0", chart_app_version="882-v1.2.0",
        license_spdx="AGPL-3.0-only", repo_url="https://charts.arkhe.org",
        dependencies=[
            {"sdx:artifactName": "arkheos-gateway", "sdx:versionConstraint": ">=870-g-v3.0.0", "arkhe:hasSeal": {"arkhe:sealHash": "e7f8a9b0c1d2e3f4"}},
            {"sdx:artifactName": "arkheos-kernel", "sdx:versionConstraint": ">=2.3.0", "arkhe:hasSeal": {"arkhe:sealHash": "d4891964dd47574f"}}
        ],
        seal_hash="f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1"
    )

    report = {
        "status": "CANONIZED",
        "substrate": "252_sdx_arkhe_ontology",
        "helm_verification": sdx.verify_chain_of_trust(helm),
        "canonical_seal": "c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5" # explicitly assigned
    }

    _, report_path = tempfile.mkstemp(suffix=".json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print("Report written to", report_path)
