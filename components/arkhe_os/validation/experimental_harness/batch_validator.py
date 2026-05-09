"""Validação em lote para meta-análises de múltiplos experimentos."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pandas as pd
from .harness import ExperimentalValidationHarness

class BatchValidationHarness(ExperimentalValidationHarness):
    """Extensão para validação em lote de múltiplos arquivos experimentais."""

    def validate_batch(
        self,
        experiment_type: str,
        data_dir: Path,
        file_pattern: str = "*.csv",
        max_workers: int = 4,
        config: dict = None
    ) -> pd.DataFrame:
        """
        Executa validação em paralelo para múltiplos arquivos.

        Returns:
            DataFrame com resultados agregados por arquivo e CVE
        """
        files = list(data_dir.glob(file_pattern))
        results = []

        def _validate_single(file_path: Path) -> dict:
            try:
                report = self.validate_experiment(
                    experiment_type=experiment_type,
                    data_file=file_path,
                    config=config
                )
                return {
                    "file": str(file_path),
                    "report_id": report.report_id,
                    "global_coherence": report.global_coherence,
                    "all_passed": report.all_passed,
                    "cve_count": len(report.cve_results),
                    "passed_count": sum(1 for r in report.cve_results if r.passed),
                    "cosnark_valid": report.cosnark_proof is not None,
                    "timestamp": report.timestamp
                }
            except Exception as e:
                return {
                    "file": str(file_path),
                    "error": str(e),
                    "global_coherence": 0.0,
                    "all_passed": False
                }

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_validate_single, f): f for f in files}
            for future in as_completed(futures):
                results.append(future.result())

        return pd.DataFrame(results)

    def generate_meta_report(self, batch_results: pd.DataFrame) -> dict:
        """Gera relatório de meta-análise sobre múltiplos experimentos."""
        valid = batch_results[batch_results["global_coherence"] > 0]

        return {
            "total_experiments": len(batch_results),
            "successful_validations": len(valid),
            "success_rate": len(valid) / len(batch_results) if len(batch_results) > 0 else 0.0,
            "mean_coherence": valid["global_coherence"].mean(),
            "std_coherence": valid["global_coherence"].std(),
            "min_coherence": valid["global_coherence"].min(),
            "max_coherence": valid["global_coherence"].max(),
            "all_passed_rate": valid["all_passed"].mean(),
            "cosnark_coverage": valid["cosnark_valid"].mean(),
            "recommendation": self._generate_recommendation(valid)
        }

    def _generate_recommendation(self, valid: pd.DataFrame) -> str:
        """Gera recomendação baseada na distribuição de coerências."""
        if len(valid) == 0:
            return "Nenhuma validação bem-sucedida. Verificar ingestão de dados."

        mean_coh = valid["global_coherence"].mean()
        std_coh = valid["global_coherence"].std()

        if mean_coh >= 0.9 and std_coh <= 0.05:
            return "✅ Alta coerência consistente: predições Ψ_ToE validadas com confiança."
        elif mean_coh >= 0.8:
            return "⚠️ Coerência aceitável, mas com variabilidade: investigar outliers."
        elif mean_coh >= 0.6:
            return "❗ Coerência marginal: revisar modelos teóricos ou incertezas experimentais."
        else:
            return "❌ Baixa coerência: discrepância significativa entre teoria e experimento."
