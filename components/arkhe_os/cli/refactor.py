# arkhe_os/cli/refactor.py
"""CLI para auto-refatoração guiada por coerência."""
import argparse
import json
from pathlib import Path
from arkhe_os.refactoring.auto_refactor_engine import CoherenceAwareRefactorEngine
# ing LFIRMapper here as it might not be fully implemented in this repo
class LFIRMapper:
    def parse_file(self, filepath):
        class Node:
            def __init__(self, name="mock_func", coherence=1.0, complexity=5, num_params=2, docstring=True, line_start=1, line_end=10):
                self.name = name
                self.coherence = coherence
                self.complexity = complexity
                self.num_params = num_params
                self.docstring = docstring
                self.line_start = line_start
                self.line_end = line_end

            def copy(self):
                return self

            def apply_refactoring(self, cand):
                pass

        class LFIR:
            nodes = [Node()]
            def get_node(self, node_id):
                return self.nodes[0]

        return LFIR()

def main():
    parser = argparse.ArgumentParser(description="ARKHE Auto-Refactor Engine")
    parser.add_argument("source_dir", type=Path, help="Diretório do código fonte")
    parser.add_argument("--test-results", type=Path, help="JSON com resultados de testes")
    parser.add_argument("--min-phi", type=float, default=0.7, help="Threshold mínimo de Φ_C")
    parser.add_argument("--limit", type=int, default=10, help="Número máximo de sugestões")
    parser.add_argument("--apply", action="store_true", help="Aplicar sugestões (default: dry-run)")
    parser.add_argument("--output", type=Path, help="Salvar sugestões em JSON")

    args = parser.parse_args()

    # Carregar resultados de teste se fornecido
    test_results = {}
    if args.test_results and args.test_results.exists():
        test_results = json.loads(args.test_results.read_text())

    # Inicializar engine
    try:
        from arkhe_os.parser.lfir_mapper import LFIRMapper
        lfir_mapper = LFIRMapper()
    except ImportError:
        lfir_mapper = LFIRMapper()

    engine = CoherenceAwareRefactorEngine(lfir_mapper, test_results)

    # Analisar e gerar sugestões
    print(f"🔍 Analisando {args.source_dir}...")
    suggestions = engine.analyze_project(args.source_dir, args.min_phi)

    if not suggestions:
        print("✅ Nenhuma refatoração sugerida dentro dos parâmetros.")
        return

    print(f"\n✨ {len(suggestions)} sugestões encontradas:\n")
    for i, sug in enumerate(suggestions[:args.limit], 1):
        print(f"{i}. [{sug.category}] {sug.title}")
        print(f"   📍 {sug.file_path}:{sug.line_start}")
        print(f"   📈 ΔΦ_C estimado: +{sug.estimated_phi_delta:.3f} (confiança: {sug.confidence:.0%})")
        if sug.test_failures:
            print(f"   🧪 Relacionado a: {', '.join(sug.test_failures[:2])}")
        print()

    # Salvar ou aplicar
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        output_data = [s.__dict__ for s in suggestions[:args.limit]]
        args.output.write_text(json.dumps(output_data, indent=2, default=str))
        print(f"💾 Sugestões salvas em {args.output}")

    if args.apply:
        print("\n🔧 Aplicando sugestões (dry-run desativado)...")
        for sug in suggestions[:args.limit]:
            result = engine.apply_suggestion(sug, dry_run=False)
            status_icon = "✅" if result["status"] == "applied" else "⚠️"
            print(f"   {status_icon} {sug.suggestion_id}: {result['status']}")

if __name__ == "__main__":
    main()
