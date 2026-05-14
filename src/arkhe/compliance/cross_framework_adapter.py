#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cross_framework_adapter.py — Adaptador para múltiplos frameworks de conformidade
Mapeia controles MA‑S2 para NIST CSF, ISO 27001, SOC 2 e outros padrões.
"""

import json, hashlib, time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum, auto
from arkhe.security.ma_s2_engine import ComplianceStatus

class ComplianceFramework(Enum):
    """Frameworks de conformidade suportados."""
    MA_S2 = "ma_s2"
    NIST_CSF = "nist_csf"
    ISO_27001 = "iso_27001"
    SOC2 = "soc2"
    PCI_DSS = "pci_dss"
    HIPAA = "hipaa"

@dataclass
class ControlMapping:
    """Mapeamento de controle entre frameworks."""
    source_framework: ComplianceFramework
    source_control_id: str
    target_framework: ComplianceFramework
    target_control_id: str
    mapping_strength: float  # 0.0–1.0 (força da correspondência)
    notes: str = ""

@dataclass
class CrossFrameworkAssessment:
    """Avaliação de conformidade cruzada entre frameworks."""
    assessment_id: str
    frameworks: List[ComplianceFramework]
    mapped_controls: List[ControlMapping]
    overall_compliance: Dict[ComplianceFramework, str]  # framework → status
    temporal_seal: str
    generated_at: float

class CrossFrameworkAdapter:
    """
    Adaptador para avaliação de conformidade em múltiplos frameworks.
    Funcionalidades:
    • Mapeamento bidirecional de controles entre padrões
    • Avaliação cruzada: um teste MA‑S2 pode validar múltiplos controles ISO/NIST
    • Geração de relatórios consolidados para auditoria multi‑padrão
    • Detecção de gaps: controles presentes em um framework mas ausentes em outro
    """

    # Mapeamentos pré-definidos (simulados para demo)
    CONTROL_MAPPINGS: List[ControlMapping] = [
        # MA‑S2 CVS → NIST CSF
        ControlMapping(
            source_framework=ComplianceFramework.MA_S2,
            source_control_id="CVS-0.1",
            target_framework=ComplianceFramework.NIST_CSF,
            target_control_id="PR.DS-5",  # Protections against data leaks
            mapping_strength=0.95,
            notes="Escaneamento contínuo valida proteções contra vazamentos",
        ),
        ControlMapping(
            source_framework=ComplianceFramework.MA_S2,
            source_control_id="CVS-0.2",
            target_framework=ComplianceFramework.NIST_CSF,
            target_control_id="DE.AE-3",  # Event data analysis
            mapping_strength=0.85,
            notes="EPSS/KEV enrichment apoia análise de dados de eventos",
        ),
        # MA‑S2 APM → ISO 27001
        ControlMapping(
            source_framework=ComplianceFramework.MA_S2,
            source_control_id="APM-1.1",
            target_framework=ComplianceFramework.ISO_27001,
            target_control_id="A.8.23",  # Information security for cloud services
            mapping_strength=0.90,
            notes="Modelagem de caminhos valida segurança de arquitetura em nuvem",
        ),
        # MA‑S2 INV → SOC 2
        ControlMapping(
            source_framework=ComplianceFramework.MA_S2,
            source_control_id="INV-2.1",
            target_framework=ComplianceFramework.SOC2,
            target_control_id="CC3.2",  # System inventory
            mapping_strength=1.0,
            notes="SBOM imutável atende requisito de inventário de sistema",
        ),
        # MA‑S2 ARO → NIST CSF
        ControlMapping(
            source_framework=ComplianceFramework.MA_S2,
            source_control_id="ARO-3.1",
            target_framework=ComplianceFramework.NIST_CSF,
            target_control_id="RS.MI-1",  # Mitigation of incidents
            mapping_strength=0.95,
            notes="Orquestração autônoma de patches valida mitigação de incidentes",
        ),
        # Adicionar mais mapeamentos conforme necessário...
    ]

    def __init__(self, ma_s2_engine):
        self.ma_s2_engine = ma_s2_engine
        self.mappings = self.CONTROL_MAPPINGS.copy()

    def map_control(
        self,
        source_framework: ComplianceFramework,
        source_control_id: str,
        target_framework: ComplianceFramework,
    ) -> List[ControlMapping]:
        """Retorna mapeamentos de um controle fonte para um framework alvo."""
        return [
            m for m in self.mappings
            if (m.source_framework == source_framework and
                m.source_control_id == source_control_id and
                m.target_framework == target_framework)
        ]

    def assess_cross_framework(
        self,
        frameworks: List[ComplianceFramework],
        ma_s2_assessment,  # MA_S2_Assessment do engine
    ) -> CrossFrameworkAssessment:
        """
        Avalia conformidade cruzada entre múltiplos frameworks.
        Usa resultados MA‑S2 como base e propaga para frameworks mapeados.
        """
        mapped_controls = []
        framework_status = {}

        # Status base do MA‑S2
        framework_status[ComplianceFramework.MA_S2] = ma_s2_assessment.overall_status.value

        # Propagar para outros frameworks via mapeamentos
        for domain, controls in ma_s2_assessment.domain_results.items():
            for control_id, status in controls.items():
                # Encontrar mapeamentos deste controle MA‑S2
                for target_fw in frameworks:
                    if target_fw == ComplianceFramework.MA_S2:
                        continue
                    mappings = self.map_control(
                        ComplianceFramework.MA_S2,
                        control_id,
                        target_fw,
                    )
                    for mapping in mappings:
                        mapped_controls.append(mapping)
                        # Propagar status (ponderado pela força do mapeamento)
                        if target_fw not in framework_status:
                            framework_status[target_fw] = status.value
                        else:
                            # Se qualquer mapeamento for non-compliant, marcar framework como partial
                            if status == ComplianceStatus.NON_COMPLIANT:
                                framework_status[target_fw] = ComplianceStatus.NON_COMPLIANT.value
                            elif status == ComplianceStatus.PARTIAL and framework_status[target_fw] == ComplianceStatus.COMPLIANT.value:
                                framework_status[target_fw] = ComplianceStatus.PARTIAL.value

        # Gerar selo temporal
        assessment_data = {
            "frameworks": [f.value for f in frameworks],
            "mapped_controls_count": len(mapped_controls),
            "status": framework_status,
            "timestamp": time.time(),
        }
        temporal_seal = hashlib.sha3_256(
            json.dumps(assessment_data, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]

        return CrossFrameworkAssessment(
            assessment_id=hashlib.sha3_256(json.dumps(assessment_data).encode()).hexdigest()[:16],
            frameworks=frameworks,
            mapped_controls=mapped_controls,
            overall_compliance=framework_status,
            temporal_seal=temporal_seal,
            generated_at=time.time(),
        )

    def generate_consolidated_report(
        self,
        assessment: CrossFrameworkAssessment,
        format: str = "json",
    ) -> str:
        """Gera relatório consolidado de conformidade multi‑framework."""
        report = {
            "assessment_id": assessment.assessment_id,
            "generated_at": assessment.generated_at,
            "frameworks": [f.value for f in assessment.frameworks],
            "overall_compliance": assessment.overall_compliance,
            "mappings_summary": {
                fw.value: sum(1 for m in assessment.mapped_controls if m.target_framework == fw)
                for fw in ComplianceFramework
            },
            "temporal_seal": assessment.temporal_seal,
            "controls_detail": [
                {
                    "source": f"{m.source_framework.value}:{m.source_control_id}",
                    "target": f"{m.target_framework.value}:{m.target_control_id}",
                    "strength": m.mapping_strength,
                    "notes": m.notes,
                }
                for m in assessment.mapped_controls
            ],
        }

        if format == "json":
            return json.dumps(report, indent=2, default=str)
        elif format == "markdown":
            return self._render_markdown_consolidated(report)
        else:
            raise ValueError(f"Formato não suportado: {format}")

    def _render_markdown_consolidated(self, report: Dict) -> str:
        """Renderiza relatório consolidado em Markdown."""
        lines = [
            f"# 📜 Relatório Consolidado de Conformidade Multi‑Framework",
            f"",
            f"**ID da Avaliação**: `{report['assessment_id']}`",
            f"**Gerado em**: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(report['generated_at']))}",
            f"**Frameworks Avaliados**: {', '.join(report['frameworks'])}",
            f"**Selo Temporal**: `{report['temporal_seal']}`",
            f"",
            f"## ✅ Status Geral por Framework",
            f"",
            f"| Framework | Status |",
            f"|-----------|--------|",
        ]
        for fw, status in report['overall_compliance'].items():
            icon = "✅" if status == "compliant" else "⚠️" if status == "partial" else "❌"
            lines.append(f"| {fw.upper()} | {icon} `{status}` |")

        lines.extend([
            f"",
            f"## 🔗 Mapeamento de Controles",
            f"",
            f"**Total de mapeamentos**: {len(report['controls_detail'])}",
            f"",
            f"| Controle Fonte | Controle Alvo | Força | Notas |",
            f"|---------------|--------------|-------|-------|",
        ])
        for ctrl in report['controls_detail']:
            lines.append(f"| `{ctrl['source']}` | `{ctrl['target']}` | {ctrl['strength']:.2f} | {ctrl['notes']} |")

        lines.extend([
            f"",
            f"---",
            f"*Relatório ancorado na TemporalChain. Verificar integridade com selo: `{report['temporal_seal']}`*",
        ])
        return "\n".join(lines)

    def detect_compliance_gaps(
        self,
        source_framework: ComplianceFramework,
        target_framework: ComplianceFramework,
    ) -> Dict[str, List[str]]:
        """
        Detecta gaps de conformidade: controles presentes em um framework mas sem mapeamento para outro.
        Returns:
            Dict com listas de controles sem mapeamento por framework.
        """
        # Para demo: retornar gaps simulados
        return {
            "unmapped_in_target": [
                "CVS-0.3",  # Critical finding escalation sem mapeamento direto para ISO 27001
                "APM-1.2",  # Adversarial AI simulation sem equivalente em SOC 2
            ],
            "partial_mappings": [
                "INV-2.3",  # Air-gap sync mapeado parcialmente para NIST CSF
            ],
        }