# arkhe_os/validation/experimental_harness/harness.py
"""
Substrato 284: Experimental Validation Harness
Orquestra a ingestão de dados experimentais, cálculo de coerência e geração de provas.
"""
import json
import time
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .ingestors.susceptibility import SusceptibilityIngestor
from .ingestors.raman import RamanIngestor
from .ingestors.neutron import NeutronIngestor
from .ingestors.epr import EPRIngestor
from .predictors.cve_283 import CV283Predictor
from .coherence.calculator import CoherenceCalculator
from .cosnark.signer import CoSNARKValidatorSigner
from .report.generator import ReportGenerator

@dataclass
class ValidationResult:
    """Resultado da validação de um único CVE."""
    cve_id: str
    metric_name: str
    predicted_value: float
    predicted_error: float
    observed_value: float
    observed_error: float
    coherence: float           # Φ_C para esta predição
    mercy_gap_valid: bool      # se a diferença está dentro do gap aceitável
    passed: bool               # se a coerência atende o threshold

@dataclass
class ValidationReport:
    """Relatório completo de validação experimental."""
    report_id: str
    substrate_id: int          # 283
    experiment_type: str
    data_source: str
    timestamp: float
    cve_results: List[ValidationResult]
    global_coherence: float
    all_passed: bool
    cosnark_proof: Optional[Dict] = None
    warnings: List[str] = field(default_factory=list)

class ExperimentalValidationHarness:
    """Orquestrador principal do harness de validação experimental."""

    def __init__(
        self,
        substrate_id: int = 283,
        coherence_threshold: float = 0.8,
        mercy_gap: tuple = (0.04, 0.10)
    ):
        self.substrate_id = substrate_id
        self.coherence_threshold = coherence_threshold
        self.mercy_gap = mercy_gap

        # Ingestores
        self.ingestors = {
            'susceptibility': SusceptibilityIngestor(),
            'raman': RamanIngestor(),
            'neutron': NeutronIngestor(),
            'epr': EPRIngestor(),
        }

        # Preditor
        self.predictor = CV283Predictor()

        # Calculadora de coerência
        self.coherence_calc = CoherenceCalculator(mercy_gap=mercy_gap)

        # Assinador CoSNARK
        self.signer = CoSNARKValidatorSigner()

        # Gerador de relatório
        self.report_gen = ReportGenerator()

    def validate_experiment(
        self,
        experiment_type: str,
        data_file: Path,
        config: Optional[Dict] = None
    ) -> ValidationReport:
        """
        Executa validação completa para um tipo de experimento.

        Args:
            experiment_type: um de 'susceptibility', 'raman', 'neutron', 'epr'
            data_file: caminho para o arquivo de dados
            config: parâmetros específicos do experimento (campos, temperatura, etc.)

        Returns:
            ValidationReport com resultados e prova CoSNARK
        """
        # 1. Ingestão dos dados
        if experiment_type not in self.ingestors:
            raise ValueError(f"Tipo de experimento não suportado: {experiment_type}")

        ingestor = self.ingestors[experiment_type]
        observed_data = ingestor.ingest(data_file, config)

        # 2. Obter predições Ψ_ToE
        predictions = self.predictor.predict_all(experiment_type, observed_data, config)

        # 3. Calcular coerência para cada CVE
        cve_results = []
        for pred in predictions:
            obs = observed_data.get(pred.cve_id)
            if obs is None:
                cve_results.append(ValidationResult(
                    cve_id=pred.cve_id,
                    metric_name=pred.metric_name,
                    predicted_value=pred.value,
                    predicted_error=pred.error,
                    observed_value=float('nan'),
                    observed_error=0.0,
                    coherence=0.0,
                    mercy_gap_valid=False,
                    passed=False
                ))
                continue

            coherence, mercy_valid = self.coherence_calc.compute(
                observed=obs['value'],
                observed_err=obs['error'],
                predicted=pred.value,
                predicted_err=pred.error
            )

            cve_results.append(ValidationResult(
                cve_id=pred.cve_id,
                metric_name=pred.metric_name,
                predicted_value=pred.value,
                predicted_error=pred.error,
                observed_value=obs['value'],
                observed_error=obs['error'],
                coherence=coherence,
                mercy_gap_valid=mercy_valid,
                passed=coherence >= self.coherence_threshold
            ))

        # 4. Coerência global
        valid_coherences = [r.coherence for r in cve_results if not np.isnan(r.observed_value)]
        global_coh = np.mean(valid_coherences) if valid_coherences else 0.0
        all_passed = all(r.passed for r in cve_results if not np.isnan(r.observed_value))

        # 5. Gerar relatório
        report = ValidationReport(
            report_id=f"valid-{self.substrate_id}-{int(time.time())}",
            substrate_id=self.substrate_id,
            experiment_type=experiment_type,
            data_source=str(data_file),
            timestamp=time.time(),
            cve_results=cve_results,
            global_coherence=round(global_coh, 4),
            all_passed=all_passed,
            warnings=[]
        )

        # 6. Assinar com CoSNARK
        try:
            proof = self.signer.sign_report(report)
            report.cosnark_proof = proof
        except Exception as e:
            report.warnings.append(f"Falha ao gerar prova CoSNARK: {e}")

        return report
