# mythos_core.xdc
# Basic timing constraints for Mythos Core

# Primary clock (100 MHz)
create_clock -period 10.000 -name clk [get_ports clk]

# Input/Output delays (conservative)
set_input_delay -clock clk -max 3.0 [get_ports {s_axi_*}]
set_input_delay -clock clk -min 0.5 [get_ports {s_axi_*}]
set_output_delay -clock clk -max 3.0 [get_ports {s_axi_*}]
set_output_delay -clock clk -min 0.5 [get_ports {s_axi_*}]

# False path on asynchronous reset
set_false_path -from [get_ports rst_n]
