#!/usr/bin/env python3
"""
ARKHE OS Compliance Framework Registry
Expande suporte para ANPD, CCPA, PIPL com mapeamento automático de controles.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum, auto
import re
import hashlib

class RegulatoryFramework(Enum):
    """Frameworks regulatórios suportados."""
    ANATEL = "anatel"
    FCC = "fcc"
    BACEN = "bacen"
    GDPR = "gdpr"
    LGPD = "lgpd"
    ANPD = "anpd"              # Brasil - Proteção de Dados (nova)
    CCPA = "ccpa"              # Califórnia - Privacy
    PIPL = "pipl"              # China - Personal Information Protection
    NIAP_EAL4 = "niap_eal4"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"

@dataclass
class ControlMapping:
    """Mapeamento de controle regulatório para código."""
    control_id: str                    # Ex: "LGPD-Art.46", "CCPA-1798.100"
    framework: RegulatoryFramework
    description: str
    code_patterns: List[str]           # Regex patterns para detectar implementação
    validation_fn: Optional[Callable]  # Função de validação customizada
    severity: str = "medium"           # critical, high, medium, low
    auto_remediation: bool = False     # Se pode ser corrigido automaticamente

class ComplianceFrameworkRegistry:
    """
    Registro central de frameworks com mapeamento automático de controles.
    """

    # Mapeamentos pré-definidos para novos frameworks
    NEW_FRAMEWORK_MAPPINGS: Dict[RegulatoryFramework, List[ControlMapping]] = {
        RegulatoryFramework.ANPD: [
            ControlMapping(
                control_id="ANPD-Resolução-CDN-001",
                framework=RegulatoryFramework.ANPD,
                description="Criptografia de dados pessoais em trânsito",
                code_patterns=[
                    r"tls\.SSLContext",
                    r"aiohttp\.ClientSession.*verify=True",
                    r"requests\.get.*verify=True",
                ],
                validation_fn=lambda code: "ssl" in code.lower() or "tls" in code.lower(),
                severity="critical"
            ),
            ControlMapping(
                control_id="ANPD-Art.46-I",
                framework=RegulatoryFramework.ANPD,
                description="Registro de operações com dados pessoais",
                code_patterns=[
                    r"temporal\.anchor_event",
                    r"audit\.log\(",
                    r"logger\.(info|audit)\(.*data.*personal",
                ],
                validation_fn=lambda code: "anchor_event" in code or "audit" in code.lower(),
                severity="high",
                auto_remediation=True
            ),
        ],
        RegulatoryFramework.CCPA: [
            ControlMapping(
                control_id="CCPA-1798.100",
                framework=RegulatoryFramework.CCPA,
                description="Direito de acesso a dados pessoais",
                code_patterns=[
                    r"def get_personal_data\(",
                    r"export_user_data",
                    r"data_subject_request",
                ],
                validation_fn=lambda code: "personal_data" in code or "data_subject" in code,
                severity="high"
            ),
            ControlMapping(
                control_id="CCPA-1798.105",
                framework=RegulatoryFramework.CCPA,
                description="Direito de exclusão (right to delete)",
                code_patterns=[
                    r"def delete_user_data\(",
                    r"right_to_delete",
                    r"gdpr_delete|ccpa_delete",
                ],
                validation_fn=lambda code: "delete" in code.lower() and ("user" in code or "data" in code),
                severity="critical",
                auto_remediation=True
            ),
        ],
        RegulatoryFramework.PIPL: [
            ControlMapping(
                control_id="PIPL-Art.13",
                framework=RegulatoryFramework.PIPL,
                description="Consentimento para processamento de dados",
                code_patterns=[
                    r"consent\.check\(",
                    r"user_consent",
                    r"data_processing_consent",
                ],
                validation_fn=lambda code: "consent" in code.lower(),
                severity="critical"
            ),
            ControlMapping(
                control_id="PIPL-Art.38",
                framework=RegulatoryFramework.PIPL,
                description="Transferência transfronteiriça de dados",
                code_patterns=[
                    r"cross_border_transfer",
                    r"data_localization",
                    r"pipl\.transfer_check",
                ],
                validation_fn=lambda code: "transfer" in code.lower() or "localization" in code,
                severity="high"
            ),
        ],
    }

    def __init__(self):
        self._mappings: Dict[RegulatoryFramework, Dict[str, ControlMapping]] = {}
        self._load_predefined_mappings()

    def _load_predefined_mappings(self):
        """Carrega mapeamentos pré-definidos para todos os frameworks."""
        for framework, mappings in self.NEW_FRAMEWORK_MAPPINGS.items():
            self._mappings[framework] = {m.control_id: m for m in mappings}

    def auto_map_code_to_controls(self, code: str, frameworks: List[RegulatoryFramework]) -> Dict[str, List[ControlMapping]]:
        """
        Mapeia automaticamente trechos de código para controles regulatórios.

        Args:
            code: Trecho de código a analisar
            frameworks: Lista de frameworks para verificar

        Returns:
            Dict mapeando framework → lista de controles aplicáveis
        """
        results = {}

        for framework in frameworks:
            if framework not in self._mappings:
                continue

            matched_controls = []
            for control in self._mappings[framework].values():
                matched = False
                # Verificar patterns de regex
                for pattern in control.code_patterns:
                    if re.search(pattern, code, re.IGNORECASE):
                        matched_controls.append(control)
                        matched = True
                        break
                # Verificar função de validação customizada
                if not matched and control.validation_fn and control.validation_fn(code):
                    if control not in matched_controls:
                        matched_controls.append(control)

            if matched_controls:
                results[framework] = matched_controls

        return results

    def generate_compliance_report(self, codebase_path: str, frameworks: List[RegulatoryFramework]) -> Dict:
        """
        Gera relatório de conformidade para um codebase.

        Returns:
            Dict com métricas de conformidade por framework
        """
        import os
        from pathlib import Path

        report = {}

        for root, dirs, files in os.walk(codebase_path):
            # Ignorar diretórios de dependências
            dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', '__pycache__', '.venv'}]

            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.go', '.rs')):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            code = f.read()

                        mapped = self.auto_map_code_to_controls(code, frameworks)

                        for framework, controls in mapped.items():
                            if framework not in report:
                                report[framework] = {
                                    "total_controls": len(self._mappings.get(framework, {})),
                                    "implemented_controls": {},
                                    "coverage": 0.0
                                }

                            for control in controls:
                                if control.control_id not in report[framework]["implemented_controls"]:
                                    report[framework]["implemented_controls"][control.control_id] = {
                                        "description": control.description,
                                        "severity": control.severity,
                                        "files": [],
                                        "auto_remediation": control.auto_remediation
                                    }
                                report[framework]["implemented_controls"][control.control_id]["files"].append(str(file_path))

                    except Exception as e:
                        # Logar erro mas continuar processamento
                        pass

        # Calcular cobertura percentual
        for framework in report:
            total = report[framework]["total_controls"]
            implemented = len(report[framework]["implemented_controls"])
            report[framework]["coverage"] = (implemented / total * 100) if total > 0 else 0

        return report
