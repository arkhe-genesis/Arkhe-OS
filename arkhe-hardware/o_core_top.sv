//=============================================================================
// ARKHE VEI v0.2 — O-Core Top-Level (v0.2)
// Correções aplicadas: #149-P1, #149-P5, #149-P6, #150-P1, #150-P2
//=============================================================================

module o_core_top #(
    parameter int NUM_RPAS = 128,
    parameter int NUM_NVS = 48,
    parameter int PHASE_WIDTH = 12,
    parameter int WIDTH = 16
) (
    input  logic               clk_sys,        // 100 MHz system clock
    input  logic               rst_n,

    // Telemetria externa (sensores)
    input  logic [15:0]        lambda_mesh_raw, // do interferômetro
    input  logic               gate_healthy,    // do monitor μ_c

    // Barramento de fases para os DACs LiNbO₃
    output logic [PHASE_WIDTH-1:0] dac_phases [NUM_RPAS],
    output logic               dac_update_strobe,

    // Interface com o IBMQ noise server (simplificada)
    input  logic [PHASE_WIDTH-1:0] ibmq_correction [NUM_RPAS],
    input  logic                   ibmq_valid,

    // Status e flags
    output logic               ramp_ok,
    output logic               self_model_flag,
    output logic [15:0]        lambda_2_estimate
);

    //-------------------------------------------------------------------------
    // Sinais internos entre módulos
    //-------------------------------------------------------------------------
    logic [PHASE_WIDTH-1:0]    corrected_phases [NUM_RPAS];
    logic                      pau_enable;
    logic                      pau_apply_correction;
    logic                      alert_decoherence;
    logic                      alert_gate_critical;
    logic                      ibmq_update_req;

    // Base phases (Golden Table, carregada da ROM)
    logic [PHASE_WIDTH-1:0]    base_phases [NUM_RPAS];

    // LCE: erros de predição (simulados ou reais)
    logic signed [WIDTH-1:0]   internal_pred_error [NUM_NVS];
    logic signed [WIDTH-1:0]   external_noise      [NUM_NVS];
    logic [15:0]               alpha_soc = 16'h003D; // 0.015 em Q4.12

    //-------------------------------------------------------------------------
    // Geração da Tabela Dourada (OAM l=1 ideal)
    //-------------------------------------------------------------------------
    generate
        for (genvar g = 0; g < NUM_RPAS; g++) begin : gen_golden
            assign base_phases[g] = g * (4096 / NUM_RPAS); // 12-bit wrap automático
        end
    endgenerate

    //-------------------------------------------------------------------------
    // Instanciação da PAU (Phase Arithmetic Unit)
    //-------------------------------------------------------------------------
    pau #(
        .N_EMITTERS(NUM_RPAS),
        .PHASE_WIDTH(PHASE_WIDTH)
    ) u_pau (
        .clk               (clk_sys),
        .rst_n             (rst_n),
        .base_phase        (base_phases),
        .ibmq_correction   (ibmq_correction),
        .chronos_phase     (12'h000),      // Futuro: virá do PSI‑Q
        .gate_healthy      (gate_healthy),
        .corrected_phase   (corrected_phases),
        .ramp_ok           (ramp_ok)
    );

    //-------------------------------------------------------------------------
    // Instanciação do Mesh Controller
    //-------------------------------------------------------------------------
    mesh_controller #(
        .CLK_FREQ_HZ(1_000_000) // 1 MHz WFP clock derivado do PLL
    ) u_mesh (
        .clk               (clk_wfp),      // clock 1 MHz gerado por PLL
        .rst_n             (rst_n),
        .lambda_mesh_raw   (lambda_mesh_raw),
        .lambda_min        (16'd46340),    // 0.7071 * 65535
        .lambda_target     (16'd62259),    // 0.95 * 65535
        .gate_healthy      (gate_healthy),
        .ibmq_update_req   (ibmq_update_req),
        .pau_enable        (pau_enable),
        .pau_apply_correction (pau_apply_correction),
        .dac_update_strobe (dac_update_strobe),
        .alert_decoherence (alert_decoherence),
        .alert_gate_critical (alert_gate_critical)
    );

    //-------------------------------------------------------------------------
    // PLL para gerar clock WFP de 1 MHz a partir do sys 100 MHz
    //-------------------------------------------------------------------------
    logic clk_wfp;
    logic [6:0] pll_counter;
    always_ff @(posedge clk_sys or negedge rst_n) begin
        if (!rst_n) begin
            clk_wfp <= 0;
            pll_counter <= 0;
        end else if (pll_counter == 49) begin
            pll_counter <= 0;
            clk_wfp <= ~clk_wfp;
        end else begin
            pll_counter <= pll_counter + 1;
        end
    end

    //-------------------------------------------------------------------------
    // LCE (Laplacian Coherence Engine) — versão simplificada
    //-------------------------------------------------------------------------
    lce_top #(
        .NUM_NVS(NUM_NVS),
        .WIDTH(WIDTH)
    ) u_lce (
        .clk               (clk_wfp),
        .rst_n             (rst_n),
        .enable_update     (pau_apply_correction && !alert_decoherence),
        .internal_pred_error(internal_pred_error),
        .external_noise    (external_noise),
        .alpha_soc         (alpha_soc),
        .lambda_2_estimate (lambda_2_estimate),
        .self_model_flag   (self_model_flag)
    );

    // Simulação: erros de predição ainda são zerados (futuro: interface com NV‑Diamond)
    assign internal_pred_error = '{default: '0};
    assign external_noise      = '{default: '0};

    //-------------------------------------------------------------------------
    // DAC Serializer
    //-------------------------------------------------------------------------
    dac_serializer #(
        .N_CHANNELS(NUM_RPAS),
        .DATA_WIDTH(PHASE_WIDTH)
    ) u_dac (
        .clk_sys         (clk_sys),
        .rst_n           (rst_n),
        .update_strobe   (dac_update_strobe),
        .phases          (corrected_phases),
        .dac_phases      (dac_phases)
    );

endmodule
