# =============================================================================
# analyze_performance.tcl
# Post‑Implementation Performance & Resource Analysis for Arkhe Pulse Sequencer
# Usage: vivado -mode batch -source analyze_performance.tcl
# =============================================================================

# ── Open the implemented design (assumes impl_1 already run) ────────────────
open_run impl_1

# ── Create output directory ──────────────────────────────────────────────────
set OUT_DIR "./build/reports/analysis"
file mkdir ${OUT_DIR}

# ── 1. Resource Utilization ─────────────────────────────────────────────────
report_utilization -file ${OUT_DIR}/utilization_detailed.rpt -hierarchical
puts "  [OK] Utilization report saved."

# ── 2. DSP & BRAM Breakdown ─────────────────────────────────────────────────
# DSP usage by module containing pulse generation & DRAG
set dsp_cells [get_cells -hier -filter {PRIMITIVE_TYPE =~ DSP48E*}]
set bram_cells [get_cells -hier -filter {PRIMITIVE_TYPE =~ RAMB36E1 || PRIMITIVE_TYPE =~ RAMB18E1}]

proc summarize_primitives {cells label outfile} {
    set fh [open $outfile w]
    puts $fh "==== $label ===="
    set total 0
    set mod_dict [dict create]
    foreach cell $cells {
        set parent [get_property PARENT $cell]
        set module [get_property NAME $parent]
        dict incr mod_dict $module
        incr total
    }
    puts $fh "Total $label instances: $total"
    puts $fh "Per‑module breakdown:"
    foreach {mod count} [lsort -stride 2 -index 0 $mod_dict] {
        puts $fh "  $mod: $count"
    }
    close $fh
}

summarize_primitives $dsp_cells "DSP48E1" ${OUT_DIR}/dsp_breakdown.rpt
summarize_primitives $bram_cells "BRAM (RAMB36/18)" ${OUT_DIR}/bram_breakdown.rpt
puts "  [OK] DSP/BRAM breakdown saved."

# ── 3. Timing Analysis ──────────────────────────────────────────────────────
report_timing_summary -file ${OUT_DIR}/timing_summary.rpt -max_paths 100 -delay_type min_max
report_clock_interaction -file ${OUT_DIR}/clock_interaction.rpt
report_clock_networks -file ${OUT_DIR}/clock_networks.rpt
puts "  [OK] Timing reports saved."

# ── 4. Power Estimation ─────────────────────────────────────────────────────
# Set activity file (optional, from simulation)
# set_power_activity -use_sim_file ./wave.saif
report_power -file ${OUT_DIR}/power.rpt -sort_by type
puts "  [OK] Power report saved."

# ── 5. Specific Architecture Analysis ────────────────────────────────────────
# Check DRAG engine loop latency
set drag_paths [get_timing_paths -from [get_cells -hier -filter {NAME =~ *gaussian_drag_core*/clk}] -to [get_cells -hier -filter {NAME =~ *gaussian_drag_core*/i_sample[*]}] -max_paths 10]
report_timing -from [get_cells -hier -filter {NAME =~ *gaussian_drag_core*/clk}] -to [get_cells -hier -filter {NAME =~ *gaussian_drag_core*/i_sample[*]}] -file ${OUT_DIR}/drag_timing.rpt

# Crosstalk checker combinational delay
report_timing -from [get_cells -hier -filter {NAME =~ *crosstalk_matrix*}] -to [get_cells -hier -filter {NAME =~ *checker*/*}] -file ${OUT_DIR}/xtalk_timing.rpt

# JESD204B TX latency (internal connection from sequencer to GTX)
report_timing -from [get_pins -hier -filter {NAME =~ *pulse_sequencer_fsm*/data_out[*]}] -to [get_pins -hier -filter {NAME =~ *jesd204b_tx_wrapper*/tx_data_in[*]}] -file ${OUT_DIR}/jesd_timing.rpt

puts "  [OK] Architectural timing reports saved."

# ── 6. Design Rule Checks ───────────────────────────────────────────────────
report_design_analysis -timing -file ${OUT_DIR}/design_analysis.rpt
report_methodology -file ${OUT_DIR}/methodology.rpt
report_drc -file ${OUT_DIR}/drc.rpt
puts "  [OK] DRC and methodology reports saved."

# ── 7. Performance Summary (custom) ──────────────────────────────────────────
set fh [open ${OUT_DIR}/performance_summary.txt w]
set clocks [get_clocks]
puts $fh "=============================="
puts $fh " ARKHE PULSE SEQUENCER PERFORMANCE SUMMARY"
puts $fh "=============================="
puts $fh "Part: [get_property PART [current_design]]"
puts $fh "Frequency targets:"
foreach clk $clocks {
    puts $fh "  [get_property NAME $clk]: [get_property PERIOD $clk] ns"
}

# Utilization summary
set util [report_utilization -return_string -no_header]
puts $fh "\nUtilization:"
puts $fh $util

# Worst Negative Slack
set wns [get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 -setup]]
puts $fh "\nWorst Setup Slack: $wns ns"
set whs [get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 -hold]]
puts $fh "Worst Hold Slack: $whs ns"

# Power total
set power [get_property TOTAL_POWER [get_power_results]]
puts $fh "\nTotal on‑chip power: $power W"

# Critical modules
set dsp_cnt [llength $dsp_cells]
set bram_cnt [llength $bram_cells]
puts $fh "\nDSP48E1 used: $dsp_cnt"
puts $fh "BRAM (36k+18k) used: $bram_cnt"

close $fh
puts "  [OK] Performance summary written to ${OUT_DIR}/performance_summary.txt"

# ── 8. Generate canonical seal ──────────────────────────────────────────────
set seal_cmd "sha256sum ${OUT_DIR}/*.rpt ${OUT_DIR}/*.txt > ${OUT_DIR}/seal.sha256"
exec bash -c $seal_cmd
puts "  [OK] SHA256 seals generated."

puts "\n*** Performance analysis complete. Reports in ${OUT_DIR} ***"