# Vivado synthesis script for OVT Quaternion Engine
create_project -in_memory -part xc7z020clg400-1
read_verilog ovt_artifacts/ovt_config.vh
read_verilog top_ovt.v
synth_design -top top_ovt -part xc7z020clg400-1
report_utilization -file ovt_utilization.txt
report_timing_summary -file ovt_timing.txt
puts "Synthesis Complete."
