# synth.tcl — Síntese do ARKHE‑SoC para Sky130
yosys -import

read_verilog -sv rtl/clifford_core.v
read_verilog -sv rtl/arkhe_soc.v
read_verilog -sv rtl/trng.v

hierarchy -top arkhe_soc
synth -top arkhe_soc -flatten

dfflibmap -liberty $::env(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib

# Otimizações específicas Arkhe:
# - Garantir que o caminho de HESITATE nunca seja otimizado para fora
# - Preservar a entropia do TRNG

opt -full
abc -liberty $::env(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib \
    -script +strash; scorr; ifraig; retime; strash; dch; map; buffer

# O Makefile cuidará da escrita do netlist
stat
