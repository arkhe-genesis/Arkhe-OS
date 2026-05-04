// ============================================================================
// tau_soc_wrapper_v1_2.sv
// Formal Scaffold Wrapper — Reset Circular Corrigido + Integração Arkhe(n)
// Target: AMD Versal AI Core Series
// ============================================================================

`timescale 1ns / 1ps

module tau_soc_wrapper_v1_2 #(
    parameter VOXEL_DATA_WIDTH = 128,
    parameter HASH_TABLE_DEPTH = 2048,
    parameter ROI_FIFO_DEPTH   = 256,
    parameter ROI_PACKET_WIDTH = 64,
    parameter MESH_DIM         = 4,
    parameter PAU_PRECISION    = 32,
    parameter RESET_HOLD_CYCLES = 100  // ~1us @ 100MHz para estabilização MMCM
) (
    // Clocks & Reset
    input  logic        clk_100mhz_p,
    input  logic        clk_100mhz_n,
    input  logic        rst_n_btn,

    // Picasso Lidar AXI4-Stream Slave (Flutuação Φ)
    input  logic                     s_axis_lidar_tvalid,
    output logic                     s_axis_lidar_tready,
    input  logic [VOXEL_DATA_WIDTH-1:0] s_axis_lidar_tdata,
    input  logic                     s_axis_lidar_tlast,

    // AXI4-Stream Master to NOC/DDR (Scaffold Σ)
    output logic                     m_axis_roi_tvalid,
    input  logic                     m_axis_roi_tready,
    output logic [ROI_PACKET_WIDTH-1:0] m_axis_roi_tdata,
    output logic                     m_axis_roi_tlast,
    output logic [0:0]               m_axis_roi_tid,

    // Interrupt to PS GIC (Trigger de Coerência Γ)
    output logic                     o_irq_roi_frame_done,

    // O-Core Monitoring (Saída de Coerência)
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

    // Configuration Inputs (Parâmetros do Scaffold Σ)
    input  logic [3:0]               i_cfg_grid_shift,
    input  logic [15:0]              i_cfg_red_threshold,
    input  logic [15:0]              i_cfg_green_threshold,
    input  logic [15:0]              i_cfg_blue_threshold,

    // O-Core Quantum Interface (Entrada de Flutuação Externa)
    input  logic [127:0]             i_ibmq_correction,
    input  logic                     i_dac_ready,

    // VRP Status (Métricas de Φ)
    output logic [31:0]              o_vrp_frame_count,
    output logic [31:0]              o_vrp_voxel_count,
    output logic                     o_vrp_fifo_overflow,

    // MMCM Lock Status (Δ: Membrana de Clock)
    output logic                     o_mmcm_locked
);

    // ------------------------------------------------------------------------
    // Clocking: Versal Differential Input Buffer
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
    // CDC Reset Synchronization — Domínio 100MHz
    // Assert assíncrono, deassert síncrono. 3 estágios.
    // ------------------------------------------------------------------------
    logic [2:0] rst_sync_100mhz;
    logic       rst_n_100mhz;

    always_ff @(posedge clk_100mhz or negedge rst_n_btn) begin
        if (!rst_n_btn)
            rst_sync_100mhz <= 3'b0;
        else
            rst_sync_100mhz <= {rst_sync_100mhz[1:0], 1'b1};
    end
    assign rst_n_100mhz = rst_sync_100mhz[2];

    // ------------------------------------------------------------------------
    // Reset Sequencing para O-Core — CORREÇÃO CRÍTICA
    //
    // BUG ANTERIOR: rst_n_8mhz dependia de o_pll_locked, criando deadlock.
    // FIXO: Contador fixo de ciclos após rst_n_100MHz liberar. O O-Core
    //       gerencia seu próprio MMCM internamente; não tentamos adivinhar
    //       o lock externamente.
    // ------------------------------------------------------------------------
    logic [$clog2(RESET_HOLD_CYCLES+1)-1:0] rst_hold_cnt;
    logic                                   rst_n_8mhz;
    logic                                   rst_8mhz_active;

    always_ff @(posedge clk_100mhz or negedge rst_n_100mhz) begin
        if (!rst_n_100mhz) begin
            rst_hold_cnt   <= '0;
            rst_8mhz_active <= 1'b1;
        end else if (rst_8mhz_active) begin
            if (rst_hold_cnt < RESET_HOLD_CYCLES) begin
                rst_hold_cnt <= rst_hold_cnt + 1'b1;
            end else begin
                rst_8mhz_active <= 1'b0;
            end
        end
    end
    assign rst_n_8mhz = ~rst_8mhz_active;

    // ------------------------------------------------------------------------
    // VRP v1.1 — Instância do Processador de Flutuação (Φ → Σ)
    // Converte fótons em tokens tipados no Scaffold AXI4-Stream.
    // ------------------------------------------------------------------------
    voxel_rgb_parser_v1_1 #(
        .VOXEL_DATA_WIDTH (VOXEL_DATA_WIDTH),
        .HASH_TABLE_DEPTH (HASH_TABLE_DEPTH),
        .ROI_FIFO_DEPTH   (ROI_FIFO_DEPTH),
        .ROI_PACKET_WIDTH (ROI_PACKET_WIDTH)
    ) u_vrp (
        .clk                 (clk_100mhz),
        .rst_n               (rst_n_100mhz),

        // AXI4-Stream Slave: Entrada de Flutuação bruta
        .s_axis_tvalid       (s_axis_lidar_tvalid),
        .s_axis_tready       (s_axis_lidar_tready),
        .s_axis_tdata        (s_axis_lidar_tdata),
        .s_axis_tlast        (s_axis_lidar_tlast),

        // AXI4-Stream Master: Scaffold tipado
        .m_axis_tvalid       (m_axis_roi_tvalid),
        .m_axis_tready       (m_axis_roi_tready),
        .m_axis_tdata        (m_axis_roi_tdata),
        .m_axis_tlast        (m_axis_roi_tlast),
        .m_axis_tid          (m_axis_roi_tid),

        // Coerência: Frame completado
        .o_irq_frame_done    (o_irq_roi_frame_done),

        // Parâmetros do Scaffold
        .i_cfg_grid_shift    (i_cfg_grid_shift),
        .i_cfg_red_threshold (i_cfg_red_threshold),
        .i_cfg_green_threshold(i_cfg_green_threshold),
        .i_cfg_blue_threshold(i_cfg_blue_threshold),

        // Métricas de Flutuação
        .o_status_frame_count(o_vrp_frame_count),
        .o_status_voxel_count(o_vrp_voxel_count),
        .o_fifo_overflow     (o_vrp_fifo_overflow)
    );

    // ------------------------------------------------------------------------
    // O-Core v1.0 — Motor de Coerência (Γ)
    // Processa correções quânticas e gera campo lambda.
    // ------------------------------------------------------------------------
    logic clk_wfp_8mhz;  // Clock interno do O-Core, exportado para debug

    o_core_top #(
        .MESH_DIM      (MESH_DIM),
        .PAU_PRECISION (PAU_PRECISION)
    ) u_o_core (
        .clk_sys_100mhz     (clk_100mhz),
        .rst_n              (rst_n_8mhz),        // Reset sequenciado, não circular

        // Entrada de Flutuação Quântica
        .ibmq_correction    (i_ibmq_correction),
        .dac_ready          (i_dac_ready),

        // Saídas de Coerência
        .lambda_mesh_raw    (o_lambda_mesh_raw),
        .gate_healthy       (o_gate_healthy),
        .clk_wfp_8mhz       (clk_wfp_8mhz),
        .pll_locked         (o_pll_locked),

        // DAC
        .dac_data           (o_dac_data),
        .dac_valid          (o_dac_valid),

        // LCE
        .lce_computation_done (o_lce_computation_done),
        .lce_lambda2_estimate (o_lce_lambda2_estimate),
        .lce_self_model_flag  (o_lce_self_model_flag),

        // NV-BFM
        .nv_pred_error      (o_nv_pred_error),
        .nv_lambda          (o_nv_lambda),
        .nv_valid           (o_nv_valid)
    );

    // Membrana de Clock: Exporta status para monitoramento
    assign o_mmcm_locked = o_pll_locked;

endmodule
