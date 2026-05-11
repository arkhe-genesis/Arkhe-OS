#!/bin/bash
# =============================================================================
# run_calmodulin_sim.sh
# =============================================================================
# Master simulation script for Calmodulin Dimer Phase 1 — Arkhe(n) Synapse-κ
#
# Executes the full GROMACS pipeline for all 15 simulation systems:
#   3 states (apo, 2ca, 4ca) × 5 replicas × 100 ns
#
# Pipeline per system:
#   1. Energy minimization (steepest descent)
#   2. NVT equilibration (500 ps, 310 K)
#   3. NPT equilibration (1 ns, 310 K, 1 bar)
#   4. Production MD (100 ns)
#
# Arkhe-Chain timestamp: 847.621
# =============================================================================

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$BASE_DIR")"
RESULTS_DIR="$BASE_DIR/results"

GMX="${GMX:-gmx}"

# Calcium states
STATES=("apo" "2ca" "4ca")
N_REPLICAS=5

# Arkhe(n) constants
LAMBDA2_CRIT=0.847

# =============================================================================
# LOGGING
# =============================================================================

LOG_FILE="$RESULTS_DIR/simulation.log"
mkdir -p "$RESULTS_DIR"

log() {
    local level="$1"
    shift
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*"
    echo "$msg" | tee -a "$LOG_FILE"
}

info()  { log "INFO"  "$@"; }
warn()  { log "WARN"  "$@"; }
error() { log "ERROR" "$@"; }

log_header() {
    echo "" | tee -a "$LOG_FILE"
    echo "=================================================================" | tee -a "$LOG_FILE"
    echo "$*" | tee -a "$LOG_FILE"
    echo "=================================================================" | tee -a "$LOG_FILE"
}

# =============================================================================
# ARKHE-CHAIN REGISTRY
# =============================================================================

register_arkhe_chain() {
    local file="$1"
    local desc="$2"
    if [ -f "$file" ]; then
        local hash
        hash=$(sha256sum "$file" | cut -d' ' -f1)
        local size
        size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null)
        local timestamp
        timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
        echo "{\"file\":\"$file\",\"sha256\":\"$hash\",\"description\":\"$desc\","\
             "\"timestamp\":\"$timestamp\",\"arkhe_chain_ts\":\"847.621\","\
             "\"size_bytes\":$size}" >> "$RESULTS_DIR/arkhe_chain_registry.jsonl"
        info "Arkhe-Chain: registered $desc (${hash:0:16}...)"
    fi
}

# =============================================================================
# SIMULATION FUNCTIONS
# =============================================================================

run_minimization() {
    local work_dir="$1"
    info "Energy minimization: $work_dir"
    $GMX grompp -f "$BASE_DIR/minimization.mdp" -c "${work_dir}/solvated_ions.gro" -p "${work_dir}/topol.top" -o "${work_dir}/em.tpr" > "${work_dir}/em.grompp.log" 2>&1
    $GMX mdrun -deffnm "${work_dir}/em" -v > "${work_dir}/em.mdrun.log" 2>&1
}

run_nvt() {
    local work_dir="$1"
    info "NVT equilibration: $work_dir"
    $GMX grompp -f "$BASE_DIR/nvt.mdp" -c "${work_dir}/em.gro" -r "${work_dir}/em.gro" -p "${work_dir}/topol.top" -o "${work_dir}/nvt.tpr" > "${work_dir}/nvt.grompp.log" 2>&1
    $GMX mdrun -deffnm "${work_dir}/nvt" -v > "${work_dir}/nvt.mdrun.log" 2>&1
}

run_npt() {
    local work_dir="$1"
    info "NPT equilibration: $work_dir"
    $GMX grompp -f "$BASE_DIR/npt.mdp" -c "${work_dir}/nvt.gro" -r "${work_dir}/nvt.gro" -t "${work_dir}/nvt.cpt" -p "${work_dir}/topol.top" -o "${work_dir}/npt.tpr" > "${work_dir}/npt.grompp.log" 2>&1
    $GMX mdrun -deffnm "${work_dir}/npt" -v > "${work_dir}/npt.mdrun.log" 2>&1
}

run_production() {
    local work_dir="$1"
    info "Production MD (100 ns): $work_dir"
    $GMX grompp -f "$BASE_DIR/production.mdp" -c "${work_dir}/npt.gro" -t "${work_dir}/npt.cpt" -p "${work_dir}/topol.top" -o "${work_dir}/production.tpr" > "${work_dir}/prod.grompp.log" 2>&1
    # Use GPU if available
    $GMX mdrun -deffnm "${work_dir}/production" -ntomp 8 -nb gpu -v > "${work_dir}/prod.mdrun.log" 2>&1
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    log_header "ARKHE(n) — CALMODULIN PHASE 1 SIMULATION"
    info "States: ${STATES[*]}"
    info "Replicas: $N_REPLICAS per state"
    info "Production: 100 ns per system"
    info "λ₂-crit = $LAMBDA2_CRIT"
    info "Arkhe-Chain timestamp: 847.621"

    # Process all systems
    for state in "${STATES[@]}"; do
        for ((rep=0; rep<N_REPLICAS; rep++)); do
            work_dir="$PARENT_DIR/${state}_r${rep}"
            if [ -d "$work_dir" ]; then
                log_header "System: $state | Replica: $rep | Dir: $work_dir"
                run_minimization "$work_dir"
                run_nvt "$work_dir"
                run_npt "$work_dir"
                run_production "$work_dir"
                info "System $state_r$rep Complete."
            else
                warn "Directory $work_dir not found. Skipping."
            fi
        done
    done

    log_header "POST-SIMULATION ANALYSIS: Arkhe(n) Hydration Stress Module"
    info "Running calmodulin_hydration_stress.py..."
    python3 "$BASE_DIR/calmodulin_hydration_stress.py" >> "$LOG_FILE" 2>&1
    register_arkhe_chain "$RESULTS_DIR/hydration_stress_results.json" "Calmodulin Hydration Stress Results"
    register_arkhe_chain "$RESULTS_DIR/calmodulin_hydration_stress.png" "Calmodulin 6-Panel Stress Analysis Plot"

    info "Running hydration_phase_validation.py..."
    python3 "$BASE_DIR/hydration_phase_validation.py" >> "$LOG_FILE" 2>&1
    register_arkhe_chain "$RESULTS_DIR/hydration_phase_validation.png" "Hydration Phase Validation Plot"

    info "Generating formal PDF Report..."
    python3 "$BASE_DIR/generate_hydration_stress_pdf.py" >> "$LOG_FILE" 2>&1
    register_arkhe_chain "$RESULTS_DIR/Analise-Stress-Hidratacao-CaM.pdf" "Formal Hydration Stress Report (PDF)"

    echo "Simulation script and analysis execution complete."
}

main "$@"
