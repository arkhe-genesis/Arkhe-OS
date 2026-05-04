// ============================================================================
// tb_endian_integration.sv
// Verifica endianness do ROI token no m_axis_roi_tdata do wrapper
// ============================================================================
`timescale 1ns/1ps

module tb_endian_integration;

    logic clk_100mhz_p, clk_100mhz_n, rst_n_btn;
    logic s_axis_lidar_tvalid, s_axis_lidar_tready, s_axis_lidar_tlast;
    logic [127:0] s_axis_lidar_tdata;
    logic m_axis_roi_tvalid, m_axis_roi_tready, m_axis_roi_tlast;
    logic [63:0] m_axis_roi_tdata;
    logic [0:0] m_axis_roi_tid;
    logic o_irq_roi_frame_done;

    // Configuração
    logic [3:0] i_cfg_grid_shift = 4'd2;
    logic [15:0] i_cfg_red_threshold = 16'h80;
    logic [15:0] i_cfg_green_threshold = 16'h80;
    logic [15:0] i_cfg_blue_threshold = 16'h80;
    logic [127:0] i_ibmq_correction = 0;
    logic i_dac_ready = 1;

    // Outros sinais do wrapper (não usados no check de endianness)
    logic [31:0] o_lambda_mesh_raw;
    logic o_gate_healthy, o_pll_locked, o_dac_valid, o_lce_computation_done, o_lce_self_model_flag, o_nv_valid, o_mmcm_locked, o_vrp_fifo_overflow;
    logic [11:0] o_dac_data;
    logic [31:0] o_lce_lambda2_estimate, o_nv_lambda, o_vrp_frame_count, o_vrp_voxel_count;
    logic [127:0] o_nv_pred_error;

    tau_soc_wrapper_v1_2 dut (
        .clk_100mhz_p(clk_100mhz_p),
        .clk_100mhz_n(clk_100mhz_n),
        .rst_n_btn(rst_n_btn),
        .s_axis_lidar_tvalid(s_axis_lidar_tvalid),
        .s_axis_lidar_tready(s_axis_lidar_tready),
        .s_axis_lidar_tdata(s_axis_lidar_tdata),
        .s_axis_lidar_tlast(s_axis_lidar_tlast),
        .m_axis_roi_tvalid(m_axis_roi_tvalid),
        .m_axis_roi_tready(m_axis_roi_tready),
        .m_axis_roi_tdata(m_axis_roi_tdata),
        .m_axis_roi_tlast(m_axis_roi_tlast),
        .m_axis_roi_tid(m_axis_roi_tid),
        .o_irq_roi_frame_done(o_irq_roi_frame_done),
        .o_lambda_mesh_raw(o_lambda_mesh_raw),
        .o_gate_healthy(o_gate_healthy),
        .o_pll_locked(o_pll_locked),
        .o_dac_data(o_dac_data),
        .o_dac_valid(o_dac_valid),
        .o_lce_computation_done(o_lce_computation_done),
        .o_lce_lambda2_estimate(o_lce_lambda2_estimate),
        .o_lce_self_model_flag(o_lce_self_model_flag),
        .o_nv_pred_error(o_nv_pred_error),
        .o_nv_lambda(o_nv_lambda),
        .o_nv_valid(o_nv_valid),
        .i_cfg_grid_shift(i_cfg_grid_shift),
        .i_cfg_red_threshold(i_cfg_red_threshold),
        .i_cfg_green_threshold(i_cfg_green_threshold),
        .i_cfg_blue_threshold(i_cfg_blue_threshold),
        .i_ibmq_correction(i_ibmq_correction),
        .i_dac_ready(i_dac_ready),
        .o_vrp_frame_count(o_vrp_frame_count),
        .o_vrp_voxel_count(o_vrp_voxel_count),
        .o_vrp_fifo_overflow(o_vrp_fifo_overflow),
        .o_mmcm_locked(o_mmcm_locked)
    );

    // Clock diferencial
    initial begin
        clk_100mhz_p = 0; clk_100mhz_n = 1;
        forever begin
            #5; clk_100mhz_p = ~clk_100mhz_p; clk_100mhz_n = ~clk_100mhz_n;
        end
    end

    // Stimulus
    initial begin
        rst_n_btn = 0;
        s_axis_lidar_tvalid = 0;
        m_axis_roi_tready = 1;

        // Reset
        repeat(20) @(posedge clk_100mhz_p);
        rst_n_btn = 1;
        repeat(50) @(posedge clk_100mhz_p);

        // Enviar voxel com valores distintos para rastreamento de bytes
        // Layout 128-bit Picasso: [intensity(16), b(8), g(8), r(8), z(16), y(16), x(16)]
        s_axis_lidar_tdata = {
            16'hFF00,    // intensity
            8'h00,       // b
            8'h00,       // g
            8'hFF,       // r (red dominant -> ROI)
            16'h5678,    // z
            16'h1234,    // y
            16'hABCD     // x
        };
        s_axis_lidar_tvalid = 1;
        s_axis_lidar_tlast = 1;

        // Aguardar handshake
        @(posedge clk_100mhz_p);
        while (!s_axis_lidar_tready) @(posedge clk_100mhz_p);

        // Aguardar saída no AXI4-Stream Master
        @(posedge clk_100mhz_p);
        while (!m_axis_roi_tvalid) @(posedge clk_100mhz_p);

        // Verificar endianness no pacote de 64 bits
        $display("=== Verificação Endianness (m_axis_roi_tdata) ===");
        $display("Dado completo: 0x%016h", m_axis_roi_tdata);
        $display("Byte 0 (x[7:0])      = 0x%02h (esperado: 0xCD)", m_axis_roi_tdata[7:0]);
        $display("Byte 1 (x[15:8])     = 0x%02h (esperado: 0xAB)", m_axis_roi_tdata[15:8]);
        $display("Byte 2 (y[7:0])      = 0x%02h (esperado: 0x34)", m_axis_roi_tdata[23:16]);
        $display("Byte 3 (y[15:8])     = 0x%02h (esperado: 0x12)", m_axis_roi_tdata[31:24]);
        $display("Byte 4 (z[7:0])      = 0x%02h (esperado: 0x78)", m_axis_roi_tdata[39:32]);
        $display("Byte 5 (z[15:8])     = 0x%02h (esperado: 0x56)", m_axis_roi_tdata[47:40]);
        $display("Byte 6 (intensity)   = 0x%02h (esperado: 0xFF)", m_axis_roi_tdata[55:48]);
        $display("Byte 7 (flags)       = 0x%02h (esperado: 0x01 = red)", m_axis_roi_tdata[63:56]);

        // Assertions
        if (m_axis_roi_tdata[7:0]   !== 8'hCD) $error("FAIL byte0");
        if (m_axis_roi_tdata[15:8]  !== 8'hAB) $error("FAIL byte1");
        if (m_axis_roi_tdata[23:16] !== 8'h34) $error("FAIL byte2");
        if (m_axis_roi_tdata[31:24] !== 8'h12) $error("FAIL byte3");
        if (m_axis_roi_tdata[39:32] !== 8'h78) $error("FAIL byte4");
        if (m_axis_roi_tdata[47:40] !== 8'h56) $error("FAIL byte5");
        if (m_axis_roi_tdata[55:48] !== 8'hFF) $error("FAIL byte6");
        if (m_axis_roi_tdata[63:56] !== 8'h01) $error("FAIL byte7");

        $display("✅ Endianness validada no nível do wrapper.");
        $finish;
    end

endmodule
