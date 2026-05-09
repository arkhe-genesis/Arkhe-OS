// o_core_top.sv - Functional Stub matching tau_soc_wrapper expectations
module o_core_top #(
    parameter int MESH_DIM = 4,
    parameter int PAU_PRECISION = 32
) (
    input  logic               clk_sys_100mhz,
    input  logic               rst_n,

    // Quantum Interface
    input  logic [127:0]       ibmq_correction,
    input  logic               dac_ready,

    // Coherence Outputs
    output logic [31:0]        lambda_mesh_raw,
    output logic               gate_healthy,
    output logic               clk_wfp_8mhz,
    output logic               pll_locked,

    // DAC Interface
    output logic [11:0]        dac_data,
    output logic               dac_valid,

    // LCE Outputs
    output logic               lce_computation_done,
    output logic [31:0]        lce_lambda2_estimate,
    output logic               lce_self_model_flag,

    // NV-BFM Outputs
    output logic [127:0]       nv_pred_error,
    output logic [31:0]        nv_lambda,
    output logic               nv_valid
);

    // Clock generation (8MHz)
    logic clk_8mhz = 0;
    logic [3:0] counter = 0;
    always @(posedge clk_sys_100mhz) begin
        if (counter == 5) begin // ~8.33MHz
            counter <= 0;
            clk_8mhz <= ~clk_8mhz;
        end else begin
            counter <= counter + 1;
        end
    end
    assign clk_wfp_8mhz = clk_8mhz;

    always_ff @(posedge clk_sys_100mhz or negedge rst_n) begin
        if (!rst_n) begin
            pll_locked <= 1'b0;
            lambda_mesh_raw <= 32'h0;
            gate_healthy <= 1'b0;
            dac_data <= 12'h0;
            dac_valid <= 1'b0;
            lce_computation_done <= 1'b0;
            lce_lambda2_estimate <= 32'h0;
            lce_self_model_flag <= 1'b0;
            nv_pred_error <= 128'h0;
            nv_lambda <= 32'h0;
            nv_valid <= 1'b0;
        end else begin
            pll_locked <= 1'b1;
            lambda_mesh_raw <= 32'h99999999;
            gate_healthy <= 1'b1;
            dac_data <= 12'hABC;
            dac_valid <= 1'b1;
            lce_computation_done <= 1'b1;
            lce_lambda2_estimate <= 32'h55555555;
            lce_self_model_flag <= 1'b1;
            nv_valid <= 1'b1;
        end
    end

endmodule
