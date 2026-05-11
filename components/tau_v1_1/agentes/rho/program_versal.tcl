# program_versal.tcl
open_hw_manager
connect_hw_server -url localhost:3121
open_hw_target
set_property PROGRAM.FILE {./output/tau_soc_final.pdi} [get_hw_devices versal_0]
program_hw_devices [get_hw_devices versal_0]
refresh_hw_device [get_hw_devices versal_0]
puts "PDI gravado. Versal bootando..."
