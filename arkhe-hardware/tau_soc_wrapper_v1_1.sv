// ============================================================================
// tau_soc_wrapper_v1_1.sv
// Complete Wrapper with Reset Synchronization and VRP v1.1 Instance
// ============================================================================

`timescale 1ns / 1ps

module tau_soc_wrapper_v1_1 #(
    parameter VOXEL_DATA_WIDTH = 128,
    parameter HASH_TABLE_DEPTH = 2048,
    parameter ROI_FIFO_DEPTH   = 256,
    parameter ROI_PACKET_WIDTH = 64,
    parameter MESH_DIM         = 4,
    parameter PAU_PRECISION    = 32
) (
    // Clocks & Reset
    input  logic        clk_100mhz_p,
    input  logic        clk_100mhz_n,
    input  logic        rst_n_btn,

    // Picasso Lidar AXI4-Stream Slave
    input  logic                     s_axis_lidar_tvalid,
    output logic                     s_axis_lidar_tready,
    input  logic [VOXEL_DATA_WIDTH-1:0] s_axis_lidar_tdata,
    input  logic                     s_axis_lidar_tlast,

    // AXI4-Stream Master to NOC/DDR
    output logic                     m_axis_roi_tvalid,
    input  logic                     m_axis_roi_tready,
    output logic [ROI_PACKET_WIDTH-1:0] m_axis_roi_tdata,
    output logic                     m_axis_roi_tlast,
    output logic [0:0]               m_axis_roi_tid,

    // Interrupt to PS
    output logic                     o_irq_roi_frame_done,

    // O-Core Monitoring
    output logic [31:0]              o_lambda_mesh_raw,
    output logic                     o_gate_healthy,
    output logic                     o_pll_locked,
    output logic [11:0]              o_dac_data,
    output logic                     o_dac_valid,
    output logic                     o_lce_computation_done,
    output logic [31:0]              o_lce_lambda2_estimate,
    output logic                     o_lce_self_model_flag,
    output logic [127:0]             o_nv_pred_error,
    output logic [31:0]              o_nv_lambda,
    output logic                     o_nv_valid,

    // Configuration
    input  logic [3:0]               i_cfg_grid_shift,
    input  logic [15:0]              i_cfg_red_threshold,
    input  logic [15:0]              i_cfg_green_threshold,
    input  logic [15:0]              i_cfg_blue_threshold,

    // O-Core Quantum Interface
    input  logic [127:0]             i_ibmq_correction,
    input  logic                     i_dac_ready,

    // VRP Status
    output logic [31:0]              o_vrp_frame_count,
    output logic [31:0]              o_vrp_voxel_count,
    output logic                     o_vrp_fifo_overflow,

    // MMCM lock status (exported)
    output logic                     o_mmcm_locked
);

    // ------------------------------------------------------------------------
    // Clock Buffer (Versal IBUFDS)
    // ------------------------------------------------------------------------
    logic clk_100mhz;

    IBUFDS #(
        .DIFF_TERM    ("TRUE"),
        .IBUF_LOW_PWR ("FALSE")
    ) u_ibufds_clk (
        .I  (clk_100mhz_p),
        .IB (clk_100mhz_n),
        .O  (clk_100mhz)
    );

    // ------------------------------------------------------------------------
    // Reset Synchronizer for 100MHz Domain (3-stage)
    // ------------------------------------------------------------------------
    logic [2:0] rst_sync_100mhz;
    logic       rst_n_100mhz;

    always_ff @(posedge clk_100mhz or negedge rst_n_btn) begin
        if (!rst_n_btn) rst_sync_100mhz <= 3'b0;
        else            rst_sync_100mhz <= {rst_sync_100mhz[1:0], 1'b1};
    end
    assign rst_n_100mhz = rst_sync_100mhz[2];

    // ------------------------------------------------------------------------
    // VRP v1.1 Instance
    // ------------------------------------------------------------------------
    voxel_rgb_parser_v1_1 #(
        .VOXEL_DATA_WIDTH (VOXEL_DATA_WIDTH),
        .HASH_TABLE_DEPTH (HASH_TABLE_DEPTH),
        .ROI_FIFO_DEPTH   (ROI_FIFO_DEPTH),
        .ROI_PACKET_WIDTH (ROI_PACKET_WIDTH)
    ) u_vrp (
        .clk                 (clk_100mhz),
        .rst_n               (rst_n_100mhz),

        .s_axis_tvalid       (s_axis_lidar_tvalid),
        .s_axis_tready       (s_axis_lidar_tready),
        .s_axis_tdata        (s_axis_lidar_tdata),
        .s_axis_tlast        (s_axis_lidar_tlast),

        .m_axis_tvalid       (m_axis_roi_tvalid),
        .m_axis_tready       (m_axis_roi_tready),
        .m_axis_tdata        (m_axis_roi_tdata),
        .m_axis_tlast        (m_axis_roi_tlast),
        .m_axis_tid          (m_axis_roi_tid),

        .o_irq_frame_done    (o_irq_roi_frame_done),

        .i_cfg_grid_shift    (i_cfg_grid_shift),
        .i_cfg_red_threshold (i_cfg_red_threshold),
        .i_cfg_green_threshold(i_cfg_green_threshold),
        .i_cfg_blue_threshold(i_cfg_blue_threshold),

        .o_status_frame_count(o_vrp_frame_count),
        .o_status_voxel_count(o_vrp_voxel_count),
        .o_fifo_overflow     (o_vrp_fifo_overflow)
    );

    // ------------------------------------------------------------------------
    // Reset Sequencer for O-Core (8MHz domain)
    // Since O-Core MMCM generates 8MHz, we generate a synchronous reset
    // that releases only after PLL lock and a few 100MHz cycles.
    // ------------------------------------------------------------------------
    logic [2:0] rst_sync_8mhz_seq;
    logic       rst_n_8mhz;

    always_ff @(posedge clk_100mhz or negedge rst_n_100mhz) begin
        if (!rst_n_100mhz) begin
            rst_sync_8mhz_seq <= 3'b0;
        end else begin
            // Wait for O-Core PLL to lock before releasing reset
            if (o_pll_locked) begin
                rst_sync_8mhz_seq <= {rst_sync_8mhz_seq[1:0], 1'b1};
            end else begin
                rst_sync_8mhz_seq <= 3'b0;
            end
        end
    end
    assign rst_n_8mhz = rst_sync_8mhz_seq[2];

    // ------------------------------------------------------------------------
    // O-Core v1.0 Instance
    // ------------------------------------------------------------------------
    o_core_top #(
        .MESH_DIM      (MESH_DIM),
        .PAU_PRECISION (PAU_PRECISION)
    ) u_o_core (
        .clk_sys_100mhz     (clk_100mhz),
        .rst_n              (rst_n_8mhz),     // Safe, sequenced reset

        .ibmq_correction    (i_ibmq_correction),
        .dac_ready          (i_dac_ready),

        .lambda_mesh_raw    (o_lambda_mesh_raw),
        .gate_healthy       (o_gate_healthy),
        .clk_wfp_8mhz       (),
        .pll_locked         (o_pll_locked),

        .dac_data           (o_dac_data),
        .dac_valid          (o_dac_valid),

        .lce_computation_done (o_lce_computation_done),
        .lce_lambda2_estimate (o_lce_lambda2_estimate),
        .lce_self_model_flag  (o_lce_self_model_flag),

        .nv_pred_error      (o_nv_pred_error),
        .nv_lambda          (o_nv_lambda),
        .nv_valid           (o_nv_valid)
    );

    // ------------------------------------------------------------------------
    // Export MMCM lock status
    // ------------------------------------------------------------------------
    assign o_mmcm_locked = o_pll_locked;

endmodule
