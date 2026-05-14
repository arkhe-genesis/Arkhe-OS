# =============================================================================
# physical.xdc — Pblock and placement constraints for latency‑sensitive logic
# =============================================================================

# Pulse waveform generator (DSP‑intensive) → DSP columns (SLICE_X1Y0:SLICE_X2Y150)
set_property PBLOCK pulse_gen_pblock [get_cells -hier -filter {NAME =~ *gaussian_drag_core*}]
resize_pblock pulse_gen_pblock -add {SLICE_X1Y0:SLICE_X2Y150 DSP48_X0Y0:DSP48_X2Y75}

# Crosstalk checker (BRAM‑intensive) → BRAM columns
set_property PBLOCK xtalk_pblock [get_cells -hier -filter {NAME =~ *crosstalk_checker*}]
resize_pblock xtalk_pblock -add {RAMB36_X0Y0:RAMB36_X2Y20 RAMB18_X0Y0:RAMB18_X2Y40}

# JESD204B wrapper must be placed close to GTX bank 111
set_property PBLOCK jesd_pblock [get_cells jesd204b_tx_wrapper]
resize_pblock jesd_pblock -add {SLICE_X3Y100:SLICE_X5Y200 GTX_X0Y7:GTX_X0Y10}

# ── Timing constraints for inter‑pblock paths ────────────────────────────────
set_max_delay 2.000 -from [get_pblocks pulse_gen_pblock] -to [get_pblocks jesd_pblock] -datapath_only