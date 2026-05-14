# =============================================================================
# arkhe_pulse_sequencer_top_vivado.tcl
# Vivado 2024.1+ Tcl script — Non‑Project Mode synthesis & implementation
# Target: Xilinx Zynq‑7000 (xc7z045ffg900‑2) + JESD204B DAC interface
# Arkhe Ω‑Temp v7.5.1 — Pulse Sequencer with DRAG & Crosstalk Guard
# =============================================================================

# ── User‑adjustable paths ───────────────────────────────────────────────────
set TOP_MODULE        "arkhe_pulse_sequencer_top"
set RTL_DIR           "./rtl"
set IP_DIR            "./ip"
set CONSTRAINTS_DIR   "./constraints"
set OUTPUT_DIR        "./build"
set PART              "xc7z045ffg900-2"
set BOARD_PART        "xilinx.com:zc706:part0:1.4"

# ── Create output directories ────────────────────────────────────────────────
file mkdir ${OUTPUT_DIR}
file mkdir ${OUTPUT_DIR}/reports
file mkdir ${OUTPUT_DIR}/bitstream

# ── Read source files ────────────────────────────────────────────────────────
# RTL sources (order independent for Vivado)
set rtl_files [list \
    ${RTL_DIR}/gaussian_drag_core.v \
    ${RTL_DIR}/crosstalk_checker.v \
    ${RTL_DIR}/jesd204b_tx_wrapper.v \
    ${RTL_DIR}/axi_stream_receiver.v \
    ${RTL_DIR}/phi_c_guard.v \
    ${RTL_DIR}/pulse_sequencer_fsm.v \
    ${RTL_DIR}/arkhe_pulse_sequencer_top.v \
]

foreach file $rtl_files {
    if {[file exists $file]} {
        read_verilog -sv $file
    } else {
        puts "WARNING: RTL file not found: $file"
    }
}

# XDC constraints
read_xdc ${CONSTRAINTS_DIR}/timing.xdc
read_xdc ${CONSTRAINTS_DIR}/pinout_jesd204b.xdc
read_xdc ${CONSTRAINTS_DIR}/physical.xdc

# Pre‑synthesized IP (JESD204B core, AXI DMA, etc.)
if {[file exists ${IP_DIR}/jesd204b_tx_core.xci]} {
    read_ip ${IP_DIR}/jesd204b_tx_core.xci
    generate_target all [get_ips jesd204b_tx_core]
}
if {[file exists ${IP_DIR}/axi_dma_14gsps.xci]} {
    read_ip ${IP_DIR}/axi_dma_14gsps.xci
    generate_target all [get_ips axi_dma_14gsps]
}

# ── Synthesis settings ───────────────────────────────────────────────────────
set_property top ${TOP_MODULE} [current_fileset]
set_property part ${PART} [current_project]
set_property board_part ${BOARD_PART} [current_project]

# Synthesis strategy: Performance_ExplorePostRoutePhysOpt
set_property strategy "Flow_PerformanceOptimized_high" [get_runs synth_1]
set_property STEPS.SYNTH_DESIGN.ARGS.FLATTEN_HIERARCHY "rebuilt" [get_runs synth_1]
set_property STEPS.SYNTH_DESIGN.ARGS.RETIMING true [get_runs synth_1]

# ── Run synthesis ────────────────────────────────────────────────────────────
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts "  ARKHE PULSE SEQUENCER SYNTHESIS — STARTING"
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
launch_runs synth_1 -jobs 8
wait_on_run synth_1
puts "  Synthesis completed."

# Quick timing/utilisation summary
open_run synth_1
report_utilization -file ${OUTPUT_DIR}/reports/utilization_synth.rpt
report_timing_summary -file ${OUTPUT_DIR}/reports/timing_synth.rpt

# ── Implementation settings ──────────────────────────────────────────────────
set_property strategy "Performance_ExtraTimingOpt" [get_runs impl_1]
set_property STEPS.OPT_DESIGN.ARGS.DIRECTIVE "Explore" [get_runs impl_1]
set_property STEPS.PLACE_DESIGN.ARGS.DIRECTIVE "ExtraTimingOpt" [get_runs impl_1]
set_property STEPS.PHYS_OPT_DESIGN.ARGS.DIRECTIVE "AggressiveExplore" [get_runs impl_1]
set_property STEPS.ROUTE_DESIGN.ARGS.DIRECTIVE "AggressiveTiming" [get_runs impl_1]

# ── Run implementation ───────────────────────────────────────────────────────
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts "  ARKHE PULSE SEQUENCER IMPLEMENTATION — STARTING"
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
launch_runs impl_1 -jobs 8
wait_on_run impl_1
puts "  Implementation completed."

# ── Post‑implementation reports ──────────────────────────────────────────────
open_run impl_1
report_utilization -file ${OUTPUT_DIR}/reports/utilization_impl.rpt
report_timing_summary -file ${OUTPUT_DIR}/reports/timing_impl.rpt -max_paths 100
report_clock_interaction -file ${OUTPUT_DIR}/reports/clock_interaction.rpt
report_design_analysis -timing -file ${OUTPUT_DIR}/reports/design_analysis.rpt

# ── Generate bitstream with compression ──────────────────────────────────────
set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]
set_property BITSTREAM.CONFIG.CONFIGRATE 66 [current_design]
set_property BITSTREAM.CONFIG.SPI_BUSWIDTH 4 [current_design]

write_bitstream -force ${OUTPUT_DIR}/bitstream/arkhe_pulse_sequencer_top.bit
write_debug_probes -force ${OUTPUT_DIR}/bitstream/arkhe_pulse_sequencer_top.ltx

# ── Dump final timing summary to stdout ──────────────────────────────────────
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts "  ARKHE PULSE SEQUENCER — FINAL TIMING SUMMARY"
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
report_timing_summary

# ── Compute canonical seal ───────────────────────────────────────────────────
set bit_hash [exec sha256sum ${OUTPUT_DIR}/bitstream/arkhe_pulse_sequencer_top.bit | cut -d ' ' -f1]
set timing_hash [exec sha256sum ${OUTPUT_DIR}/reports/timing_impl.rpt | cut -d ' ' -f1]
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts "  ARKHE SEAL (Bitstream SHA256):  ${bit_hash}"
puts "  ARKHE SEAL (Timing SHA256):     ${timing_hash}"
puts "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
puts "  Synthesis & Implementation complete."