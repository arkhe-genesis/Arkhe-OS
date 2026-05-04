# synth_mythos.tcl - Complete synthesis flow for Mythos Core
# Target: AMD Versal AI Core

set_part xcvc1902-vsva2197-2MP-e-S
set_property target_language Verilog [current_project]

set RTL_DIR ../arkhe-hardware

# Add all RTL sources from the consolidated directory
add_files -norecurse "$RTL_DIR/mythos_core_top.sv"
add_files -norecurse "$RTL_DIR/mythos_axi_ctrl.sv"
add_files -norecurse "$RTL_DIR/attention_wrapper.sv"
add_files -norecurse "$RTL_DIR/softmax_core.sv"
add_files -norecurse "$RTL_DIR/exp_pwl.sv"
add_files -norecurse "$RTL_DIR/reciprocal_lut.sv"
add_files -norecurse "$RTL_DIR/v_mixing.sv"
add_files -norecurse "$RTL_DIR/mlp_block.sv"
add_files -norecurse "$RTL_DIR/gelu_pwl.sv"
add_files -norecurse "$RTL_DIR/bram_16kx16.sv"

update_compile_order -fileset sources_1

# Add constraints
add_files -fileset constrs_1 -norecurse "$RTL_DIR/mythos_core.xdc"
set_property top mythos_core_top [current_fileset]

# Synthesis with performance optimization
synth_design -directive PerformanceOptimized -flatten_hierarchy rebuilt

# Generate reports
report_utilization -file utilization_synth.rpt
report_timing_summary -file timing_synth.rpt
report_design_analysis -file design_analysis.rpt

# Write checkpoint
write_checkpoint -force mythos_core_synth.dcp
puts "Synthesis complete. Check utilization_synth.rpt and timing_synth.rpt"
