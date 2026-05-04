#!/bin/bash
# scripts/run_convergence_study.sh

echo "🌀 ARKHE v∞.393.3 — Convergence Study: 24³ → 48³ → 96³"
echo "========================================================"

# Array de grades para processamento
GRIDS=("24_cube" "48_cube" "96_cube")

for grid in "${GRIDS[@]}"; do
  echo ""
  echo "[GRID] Processing $grid..."

  # Executar simulação com configuração específica
  python core/quantumgrok_simulation_multigrid.py \
    --config config/quantumgrok_convergence_study.yaml \
    --grid-name "$grid" \
    --output "results/quantumgrok_${grid}_run_$(date +%Y%m%d).h5" \
    --extract-observables scar_ipr,hall_currents,friedmann_params \
    --ml-reconstruction enabled \
    --compare-cosmology Planck_2018,DESI_2024

  # Validar conformidade P1-P5
  python scripts/validate_v393_p1p5.py "results/quantumgrok_${grid}_run_*.h5" || true

  # Extrair métricas de convergência
  python scripts/extract_convergence_metrics.py \
    --input "results/quantumgrok_${grid}_run_$(date +%Y%m%d).h5" \
    --output "results/convergence_${grid}.json"
done

# Análise final de convergência
echo ""
echo "[ANALYSIS] Computing convergence laws and systematic errors..."
python scripts/analyze_convergence_laws.py \
  --inputs results/convergence_24_cube.json results/convergence_48_cube.json results/convergence_96_cube.json \
  --output results/convergence_summary_v393.3.json \
  --plot-results

echo ""
echo "✅ Convergence study complete. Summary: results/convergence_summary_v393.3.json"
