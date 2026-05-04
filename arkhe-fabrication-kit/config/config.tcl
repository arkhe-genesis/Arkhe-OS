set ::env(DESIGN_NAME) "arkhe_soc"
set ::env(VERILOG_FILES) [glob $::env(DESIGN_DIR)/rtl/*.v]
set ::env(CLOCK_PORT) "clk"
set ::env(CLOCK_PERIOD) "10.0"  ;# 100 MHz

# Restrições Arkhe
set ::env(SYNTH_STRATEGY) "AREA 0"
set ::env(FP_CORE_UTIL) "40"     ;# Espaço para expansão futura (copas)
set ::env(PL_TARGET_DENSITY) "0.55"

# Macros: acelerador Clifford (bloco duro)
set ::env(EXTRA_LEFS) [glob $::env(DESIGN_DIR)/macros/clifford_hard.lef]
set ::env(EXTRA_LIBS) [glob $::env(DESIGN_DIR)/macros/clifford_hard.lib]

# Testes Arkhe obrigatórios
set ::env(RUN_DRC) "1"
set ::env(RUN_LVS) "1"
set ::env(RUN_ANTENNA) "1"

# Injeção de ruído térmico no clock (simulado)
set ::env(CLOCK_TREE_SYNTH) "0"
