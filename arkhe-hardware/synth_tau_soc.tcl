# ============================================================================
# synth_tau_soc.tcl
# Síntese TAU SoC v1.2 — Vivado 2023.2/2024.1
# Target: AMD Versal AI Core Series (xcvc1902-vsva2197-2MP-e-S)
# ============================================================================

set project_name "tau_soc_final"
set top_module   "tau_soc_wrapper_v1_2"
set part_name    "xcvc1902-vsva2197-2MP-e-S"
set rtl_dir      "."
set xdc_dir      "."
set out_dir      "./output"

file mkdir $out_dir

create_project -force $project_name ./$project_name -part $part_name
set_property target_language Verilog [current_project]
set_property simulator_language Mixed [current_project]

# ----------------------------------------------------------------------------
# Fontes RTL
# ----------------------------------------------------------------------------
add_files -norecurse [list \
    $rtl_dir/voxel_rgb_parser_v1_1.sv \
    $rtl_dir/o_core_top.sv \
    $rtl_dir/o_core_top_v1_0.sv \
    $rtl_dir/tau_soc_wrapper_v1_2.sv \
]

update_compile_order -fileset sources_1
set_property top $top_module [current_fileset]

# ----------------------------------------------------------------------------
# Constraints
# ----------------------------------------------------------------------------
add_files -fileset constrs_1 -norecurse $xdc_dir/tau_soc_wrapper.xdc

# ----------------------------------------------------------------------------
# Configurações de Síntese
# ----------------------------------------------------------------------------
set_property strategy "Flow_PerfOptimized_high" [get_runs synth_1]
set_property STEPS.SYNTH_DESIGN.ARGS.RETIMING true [get_runs synth_1]
set_property STEPS.SYNTH_DESIGN.ARGS.FANOUT_LIMIT 32 [get_runs synth_1]

# ----------------------------------------------------------------------------
# Executar Síntese
# ----------------------------------------------------------------------------
puts "ARKHE > Iniciando síntese de $top_module para $part_name..."
# launch_runs synth_1 -jobs 8
# wait_on_run synth_1

# ----------------------------------------------------------------------------
# Relatórios Pós-Síntese (Simulado no script, requer execução real)
# ----------------------------------------------------------------------------
# open_run synth_1
# report_utilization -hierarchical -file $out_dir/utilization_synth.rpt
# report_timing_summary -file $out_dir/timing_synth.rpt

puts "ARKHE > Script de síntese preparado para $top_module."
