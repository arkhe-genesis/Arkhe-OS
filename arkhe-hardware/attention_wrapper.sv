// ============================================================================
// attention_wrapper.sv
// Structural Wrapper for the Mythos Attention Pipeline
// ============================================================================

`timescale 1ns / 1ps

module attention_wrapper #(
    parameter D_MODEL = 256,
    parameter SEQ_LEN = 64,
    parameter DATA_WIDTH = 16
) (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,
    input  logic signed [D_MODEL-1:0][DATA_WIDTH-1:0] q_in,
    input  logic signed [SEQ_LEN-1:0][D_MODEL-1:0][DATA_WIDTH-1:0] k_cache,
    input  logic signed [SEQ_LEN-1:0][D_MODEL-1:0][DATA_WIDTH-1:0] v_cache,
    output logic signed [D_MODEL-1:0][DATA_WIDTH-1:0] attn_out,
    output logic        done
);

    logic [SEQ_LEN-1:0][15:0] scores;
    logic [SEQ_LEN-1:0][15:0] probs;
    logic dp_done, sm_done, vm_done;

    // Dot Product Placeholder (Q * K^T)
    // In a real implementation, this would be a systolic array or DSP chain.
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            scores <= '0; dp_done <= 0;
        end else if (start) begin
            for (int i=0; i<SEQ_LEN; i++) scores[i] <= q_in[0] * k_cache[i][0]; // Dummy dot prod
            dp_done <= 1;
        end else dp_done <= 0;
    end

    softmax_core #( .VEC_SIZE(SEQ_LEN) ) u_softmax (
        .clk(clk), .rst_n(rst_n), .in_valid(dp_done), .scores_in(scores),
        .out_valid(sm_done), .probs_out(probs)
    );

    v_mixing #( .SEQ_LEN(SEQ_LEN), .D_MODEL(D_MODEL) ) u_mixing (
        .clk(clk), .rst_n(rst_n), .start(sm_done), .probs(probs),
        .v_matrix(v_cache), .mixed_out(attn_out), .done(vm_done)
    );

    assign done = vm_done;

endmodule
