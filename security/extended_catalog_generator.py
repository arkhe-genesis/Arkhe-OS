#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extended_catalog_generator.py — Substrato 9026: Gerador de Catálogo de Segurança Expandido
Gera catálogo .cat unificado para driver Cathedral + substratos adicionais (MCP, Spark, blockchain).
"""

import os
import sys
import json
import hashlib
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURAÇÃO DE SUBSTRATOS
# ============================================================================

@dataclass
class SubstrateConfig:
    """Configuração de um substrato para inclusão no catálogo."""
    name: str
    substrate_id: str
    files: List[str]  # Caminhos relativos dos arquivos a catalogar
    hash_algorithm: str = "SHA3_256"
    required: bool = True
    description: str = ""
    dependencies: List[str] = field(default_factory=list)

# Configuração dos substratos a incluir no catálogo
SUBSTRATES = {
    "cathedral_core": SubstrateConfig(
        name="Cathedral Core Driver",
        substrate_id="9018",
        files=[
            "catedral.sys",
            "catedral.ini",
            "catedral.cat",
        ],
        description="Driver kernel principal da Catedral",
    ),
    "safe_core_mcp": SubstrateConfig(
        name="Safe Core MCP",
        substrate_id="9013",
        files=[
            "safe_core_mcp/server.py",
            "safe_core_mcp/tools/__init__.py",
            "safe_core_mcp/resources/__init__.py",
        ],
        description="Servidor MCP para capacidades de segurança",
        dependencies=["cathedral_core"],
    ),
    "arkhe_spark": SubstrateConfig(
        name="Arkhe Spark Integration",
        substrate_id="9014",
        files=[
            "arkhe_spark/__init__.py",
            "arkhe_spark/udfs.py",
            "arkhe_spark/config.py",
        ],
        description="Integração PySpark para processamento distribuído",
        dependencies=["cathedral_core"],
    ),
    "temporal_chain": SubstrateConfig(
        name="TemporalChain Core",
        substrate_id="9018",
        files=[
            "arkhe_timechain/core.py",
            "arkhe_timechain/storage/__init__.py",
            "arkhe_timechain/api/__init__.py",
        ],
        description="Cadeia temporal imutável para auditoria",
        dependencies=["cathedral_core"],
    ),
    "blockchain_anchoring": SubstrateConfig(
        name="Blockchain Anchoring Module",
        substrate_id="9027",
        files=[
            "blockchain/ipfs_adapter.py",
            "blockchain/arweave_adapter.py",
            "blockchain/ethereum_adapter.py",
        ],
        description="Adaptadores para ancoragem em blockchains públicas",
        dependencies=["temporal_chain"],
    ),
}

# ============================================================================
# GERADOR DE CATÁLOGO
# ============================================================================

class ExtendedCatalogGenerator:
    """Gera catálogo de segurança .cat para múltiplos substratos."""

    def __init__(self, base_path: str, output_path: str, config: Dict):
        self.base_path = Path(base_path)
        self.output_path = Path(output_path)
        self.config = config
        self.catalog_entries: List[Dict] = []

    def compute_file_hash(self, filepath: Path, algorithm: str = "SHA3_256") -> str:
        """Computa hash criptográfico de arquivo."""
        if algorithm == "SHA3_256":
            hasher = hashlib.sha3_256()
        elif algorithm == "SHA256":
            hasher = hashlib.sha256()
        else:
            raise ValueError(f"Algorithm not supported: {algorithm}")

        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)

        return hasher.hexdigest()

    def get_file_metadata(self, filepath: Path) -> Dict:
        """Obtém metadados de arquivo para catálogo."""
        stat = filepath.stat()
        return {
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        }

    def add_substrate(self, substrate: SubstrateConfig):
        """Adiciona todos os arquivos de um substrato ao catálogo."""
        logger.info(f"📦 Processing substrate: {substrate.name} ({substrate.substrate_id})")

        for rel_path in substrate.files:
            filepath = self.base_path / rel_path

            if not filepath.exists():
                if substrate.required:
                    logger.error(f"❌ Required file not found: {filepath}")
                    return False
                else:
                    logger.warning(f"⚠️  Optional file not found: {filepath}")
                    continue

            # Calcular hashes
            hashes = {}
            for algo in ["SHA3_256", "SHA256"]:
                try:
                    hashes[algo] = self.compute_file_hash(filepath, algo)
                except Exception as e:
                    logger.error(f"❌ Error hashing {filepath}: {e}")
                    return False

            # Obter metadados
            metadata = self.get_file_metadata(filepath)

            # Criar entrada do catálogo
            entry = {
                "FileName": filepath.name,
                "FilePath": str(filepath.relative_to(self.base_path)),
                "FileSize": metadata["size"],
                "FileDate": metadata["modified"],
                "FileHashes": [
                    {"Algorithm": algo, "Hash": h} for algo, h in hashes.items()
                ],
                "FileAttributes": {
                    "SubstrateID": substrate.substrate_id,
                    "SubstrateName": substrate.name,
                    "Description": substrate.description,
                    "Required": substrate.required,
                },
                "Dependencies": substrate.dependencies,
            }

            self.catalog_entries.append(entry)
            logger.info(f"   ✅ Added: {filepath.name} ({hashes['SHA3_256'][:16]}...)")

        return True

    def generate_catalog_xml(self) -> str:
        """Gera XML do catálogo no formato Windows Catalog."""
        root = ET.Element("CatalogFile", {
            "xmlns": "http://schemas.microsoft.com/windows/catalog/2021",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        })

        # Metadados do catálogo
        metadata = ET.SubElement(root, "CatalogMetadata")
        ET.SubElement(metadata, "CatalogId").text = "ARKHE-EXTENDED-CORE"
        ET.SubElement(metadata, "CatalogVersion").text = "2.0.0.0"
        ET.SubElement(metadata, "CatalogDate").text = datetime.utcnow().isoformat() + "Z"
        ET.SubElement(metadata, "CatalogDescription").text = "Extended Security Catalog for Arkhe Cathedral Ecosystem"
        ET.SubElement(metadata, "CatalogPublisher").text = "ARKHE Observatory"

        # Algoritmos suportados
        algorithms = ET.SubElement(metadata, "SupportedHashAlgorithms")
        for algo in ["SHA3_256", "SHA256"]:
            ET.SubElement(algorithms, "Algorithm").text = algo

        # Políticas de validação
        validation = ET.SubElement(metadata, "ValidationPolicy")
        ET.SubElement(validation, "RequireSecureBoot").text = "true"
        ET.SubElement(validation, "AllowTestSigning").text = "true" if self.config.get("dev_mode") else "false"
        ET.SubElement(validation, "MinWindowsBuild").text = "19041"

        # Entradas do catálogo
        entries = ET.SubElement(root, "CatalogEntries")
        for entry in self.catalog_entries:
            catalog_entry = ET.SubElement(entries, "CatalogEntry")

            for key, value in entry.items():
                if key == "FileHashes":
                    hashes_elem = ET.SubElement(catalog_entry, key)
                    for h in value:
                        hash_elem = ET.SubElement(hashes_elem, "Hash", {"Algorithm": h["Algorithm"]})
                        hash_elem.text = h["Hash"]
                elif key == "FileAttributes":
                    attrs_elem = ET.SubElement(catalog_entry, key)
                    for attr_name, attr_value in value.items():
                        ET.SubElement(attrs_elem, "Attribute", {"Name": attr_name}).text = str(attr_value)
                elif key == "Dependencies":
                    if value:
                        deps_elem = ET.SubElement(catalog_entry, key)
                        for dep in value:
                            ET.SubElement(deps_elem, "Dependency").text = dep
                elif isinstance(value, (str, int, float)):
                    ET.SubElement(catalog_entry, key).text = str(value)

        # Regras de integridade em runtime
        integrity_rules = ET.SubElement(root, "IntegrityRules")

        # Regra: Verificar hash do driver ao carregar
        rule = ET.SubElement(integrity_rules, "IntegrityRule", {"Id": "DriverHashCheck"})
        ET.SubElement(rule, "TargetFile").text = "catedral.sys"
        ET.SubElement(rule, "CheckType").text = "OnLoad"
        ET.SubElement(rule, "HashAlgorithm").text = "SHA3_256"
        # Hash esperado será preenchido pelo signtool
        ET.SubElement(rule, "ExpectedHash").text = "PENDING_SIGNATURE"
        ET.SubElement(rule, "ActionOnMismatch").text = "PreventLoad"
        ET.SubElement(rule, "LogEvent").text = "true"

        # Regra: Monitorar alterações em substratos críticos
        for substrate_id in ["9018", "9013", "9014"]:
            rule = ET.SubElement(integrity_rules, "IntegrityRule",
                               {"Id": f"SubstrateWatch_{substrate_id}"})
            ET.SubElement(rule, "TargetSubstrate").text = substrate_id
            ET.SubElement(rule, "CheckType").text = "Continuous"
            ET.SubElement(rule, "ActionOnChange").text = "AlertAndVerify"

        # Assinatura do catálogo (placeholder)
        signature = ET.SubElement(root, "CatalogSignature")
        ET.SubElement(signature, "SignatureAlgorithm").text = "SHA3_256withRSA"
        # Certificado e hash serão preenchidos pelo signtool

        # Converter para string
        ET.indent(root, space="  ", level=0)
        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def generate(self) -> bool:
        """Gera catálogo completo."""
        logger.info("🔐 Starting extended catalog generation...")

        # Processar todos os substratos
        for substrate_key, substrate in SUBSTRATES.items():
            if not self.add_substrate(substrate):
                logger.error(f"❌ Failed to process substrate: {substrate_key}")
                return False

        # Gerar XML do catálogo
        catalog_xml = self.generate_catalog_xml()

        # Salvar arquivo .cat
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(catalog_xml)

        logger.info(f"✅ Catalog generated: {self.output_path}")
        logger.info(f"   • Total entries: {len(self.catalog_entries)}")
        logger.info(f"   • Substrates included: {len(SUBSTRATES)}")

        return True

    def sign_catalog(self, cert_path: Optional[str] = None,
                    hsm_config: Optional[Dict] = None) -> bool:
        """Assina o catálogo gerado usando signtool ou HSM."""
        if not self.output_path.exists():
            logger.error("❌ Catalog file not found")
            return False

        # Comando signtool para assinatura
        cmd = ["signtool", "sign", "/v"]

        if hsm_config:
            # Assinatura via HSM
            cmd.extend([
                "/csp", hsm_config.get("csp_name", "ARKHE PKCS#11 Provider"),
                "/kc", hsm_config.get("key_container", "arkhe-cathedral-production"),
            ])
        elif cert_path:
            # Assinatura via certificado arquivo
            cmd.extend(["/f", cert_path])
            if self.config.get("cert_password"):
                cmd.extend(["/p", self.config["cert_password"]])
        else:
            # Test signing (desenvolvimento)
            cmd.append("/t")
            cmd.append("http://timestamp.digicert.com")

        cmd.extend([
            "/fd", "SHA3_256",
            "/td", "SHA3_256",
            "/tr", "http://timestamp.digicert.com",
            "/d", "ARKHE Extended Security Catalog",
            "/du", "https://arkhe.org",
            str(self.output_path),
        ])

        logger.info(f"🔐 Signing catalog: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"✅ Catalog signed successfully")
            if result.stdout:
                logger.debug(f"signtool output: {result.stdout[:500]}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ signtool failed: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error("❌ signtool not found. Install Windows SDK.")
            return False

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate extended security catalog for Arkhe substrates")
    parser.add_argument("--base-path", required=True, help="Base path for substrate files")
    parser.add_argument("--output", required=True, help="Output path for .cat file")
    parser.add_argument("--config", help="Path to JSON config file")
    parser.add_argument("--sign", action="store_true", help="Sign catalog after generation")
    parser.add_argument("--cert", help="Path to signing certificate")
    parser.add_argument("--dev", action="store_true", help="Development mode (allow test signing)")

    args = parser.parse_args()

    # Carregar configuração
    config = {"dev_mode": args.dev}
    if args.config and Path(args.config).exists():
        with open(args.config) as f:
            config.update(json.load(f))

    # Gerar catálogo
    generator = ExtendedCatalogGenerator(args.base_path, args.output, config)

    if not generator.generate():
        sys.exit(1)

    # Assinar se solicitado
    if args.sign:
        hsm_config = config.get("hsm") if config.get("hsm_enabled") else None
        if not generator.sign_catalog(cert_path=args.cert, hsm_config=hsm_config):
            logger.warning("⚠️  Catalog generation succeeded but signing failed")
            # Não falhar o script inteiro se assinatura falhar em modo dev
            if not args.dev:
                sys.exit(2)

    print(f"\n✅ Extended catalog generated: {args.output}")
    print(f"📋 To verify: Test-FileCatalog -Path <dir> -CatalogFilePath {args.output}")

if __name__ == "__main__":
    main()
