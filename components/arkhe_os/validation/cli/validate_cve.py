#!/usr/bin/env python3
"""
CLI para validação experimental do ARKHE OS.
"""
import argparse
import json
from pathlib import Path
from arkhe_os.validation.experimental_harness import ExperimentalValidationHarness

def main():
    parser = argparse.ArgumentParser(
        description="ARKHE OS Experimental Validation Harness (Substrato 284)"
    )
    parser.add_argument(
        "experiment_type",
        choices=["susceptibility", "raman", "neutron", "epr"],
        help="Tipo de experimento a validar"
    )
    parser.add_argument(
        "data_file",
        type=Path,
        help="Arquivo de dados experimentais"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Caminho para salvar relatório JSON (padrão: stdout)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="Threshold mínimo de coerência para considerar predição como passou (padrão: 0.8)"
    )
    parser.add_argument(
        "--sign",
        action="store_true",
        help="Gerar prova CoSNARK para o relatório"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Exibir detalhes da validação"
    )

    args = parser.parse_args()

    # Inicializar harness
    harness = ExperimentalValidationHarness(
        coherence_threshold=args.threshold
    )

    # Executar validação
    print(f"🔬 Validando {args.experiment_type} com dados de '{args.data_file}'...")
    report = harness.validate_experiment(
        experiment_type=args.experiment_type,
        data_file=args.data_file,
        config={"verbose": args.verbose}
    )

    # Exibir resultados
    print(f"\n📊 Resultados da Validação (Substrato {report.substrate_id}):")
    print(f"   Coerência global: {report.global_coherence:.4f}")
    print(f"   Todas predições passaram: {'✅' if report.all_passed else '❌'}")
    print(f"   Mercy gap válido: {'✅' if any(r.mercy_gap_valid for r in report.cve_results) else '⚠️'}")
    print()

    for cve_result in report.cve_results:
        status = "✅" if cve_result.passed else "❌"
        print(f"   {status} {cve_result.cve_id} — {cve_result.metric_name}:")
        print(f"      Predito: {cve_result.predicted_value:.4f} ± {cve_result.predicted_error:.4f}")
        print(f"      Observado: {cve_result.observed_value:.4f} ± {cve_result.observed_error:.4f}")
        print(f"      Φ_C = {cve_result.coherence:.4f}")

    if report.warnings:
        print(f"\n   ⚠️  Avisos: {report.warnings}")

    # Prova CoSNARK
    if args.sign:
        if report.cosnark_proof:
            print(f"\n🔐 Prova CoSNARK gerada: {report.cosnark_proof['proof_hex'][:32]}...")
        else:
            print(f"\n⚠️  Prova CoSNARK não gerada (veja avisos)")

    # Salvar relatório
    if args.output:
        output_data = {
            "report_id": report.report_id,
            "substrate_id": report.substrate_id,
            "experiment_type": report.experiment_type,
            "data_source": str(report.data_source),
            "timestamp": report.timestamp,
            "cve_results": [
                {
                    "cve_id": r.cve_id,
                    "metric": r.metric_name,
                    "predicted": {"value": r.predicted_value, "error": r.predicted_error},
                    "observed": {"value": r.observed_value, "error": r.observed_error},
                    "coherence": r.coherence,
                    "passed": r.passed,
                    "mercy_gap_valid": r.mercy_gap_valid
                }
                for r in report.cve_results
            ],
            "global_coherence": report.global_coherence,
            "all_passed": report.all_passed,
            "cosnark_proof": report.cosnark_proof,
            "warnings": report.warnings
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2, default=str)
        print(f"\n💾 Relatório salvo em: {args.output}")
    else:
        # Imprimir JSON resumido no stdout
        print("\n" + json.dumps({
            "global_coherence": report.global_coherence,
            "all_passed": report.all_passed,
            "cosnark_proof_id": report.cosnark_proof.get("proof_hex", "N/A")[:32] if report.cosnark_proof else None
        }))

if __name__ == "__main__":
    main()