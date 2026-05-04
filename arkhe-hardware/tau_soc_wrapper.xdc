# Clock principal diferencial 100 MHz
create_clock -period 10.000 -name clk_100mhz [get_ports clk_100mhz_p]

# Input delays (Picasso Lidar)
set_input_delay -clock clk_100mhz -max 2.5 [get_ports {s_axis_lidar_tdata[*] s_axis_lidar_tvalid s_axis_lidar_tlast}]
set_input_delay -clock clk_100mhz -min 0.5 [get_ports {s_axis_lidar_tdata[*] s_axis_lidar_tvalid s_axis_lidar_tlast}]

# Output delays (AXI-Stream para NoC)
set_output_delay -clock clk_100mhz -max 2.5 [get_ports {m_axis_roi_tdata[*] m_axis_roi_tvalid m_axis_roi_tlast m_axis_roi_tid}]
set_output_delay -clock clk_100mhz -min 0.5 [get_ports {m_axis_roi_tdata[*] m_axis_roi_tvalid m_axis_roi_tlast m_axis_roi_tid}]

# Backpressure input
set_input_delay -clock clk_100mhz -max 2.5 [get_ports m_axis_roi_tready]
set_input_delay -clock clk_100mhz -min 0.5 [get_ports m_axis_roi_tready]

# tready output (para o Lidar)
set_output_delay -clock clk_100mhz -max 2.5 [get_ports s_axis_lidar_tready]

# False path no reset assíncrono
set_false_path -from [get_ports rst_n_btn]

# Configurações quasi-estáticas
set_input_delay -clock clk_100mhz -max 5.0 [get_ports {i_cfg_*}]
