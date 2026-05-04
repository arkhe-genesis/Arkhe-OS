// ============================================================================
// softmax_core.sv
// Complete Softmax Normalization with Max-Subtraction, Exp-PWL, Adder Tree,
// and Reciprocal Multiplication.
// Domain: scores in Q8.8, outputs probabilities in Q0.16.
// ============================================================================

`timescale 1ns / 1ps

module softmax_core #(
    parameter VEC_SIZE    = 64,   // Number of scores to normalize
    parameter DATA_WIDTH  = 16,
    parameter FRAC_WIDTH  = 8
) (
    input  logic clk,
    input  logic rst_n,
    input  logic in_valid,
    input  logic [VEC_SIZE-1:0][DATA_WIDTH-1:0] scores_in, // Q8.8
    output logic out_valid,
    output logic [VEC_SIZE-1:0][15:0] probs_out            // Q0.16
);

    // -------------------------------------------------------------------------
    // Stage 0: Find Maximum Score
    // -------------------------------------------------------------------------
    logic [DATA_WIDTH-1:0] max_score;
    always_comb begin
        max_score = scores_in[0];
        for (int i = 1; i < VEC_SIZE; i++) begin
            if ($signed(scores_in[i]) > $signed(max_score))
                max_score = scores_in[i];
        end
    end

    // -------------------------------------------------------------------------
    // Stage 1: Subtract Max and Apply Exp-PWL (in parallel)
    // -------------------------------------------------------------------------
    logic [VEC_SIZE-1:0][DATA_WIDTH-1:0] shifted_scores;
    generate
        for (genvar i = 0; i < VEC_SIZE; i++) begin : gen_shift
            assign shifted_scores[i] = $signed(scores_in[i]) - $signed(max_score);
        end
    endgenerate

    // Array of exp_pwl instances
    logic [VEC_SIZE-1:0] exp_valid;
    logic [VEC_SIZE-1:0][31:0] exp_values; // Q16.16

    generate
        for (genvar i = 0; i < VEC_SIZE; i++) begin : gen_exp
            exp_pwl u_exp (
                .clk(clk), .rst_n(rst_n),
                .in_valid(in_valid),
                .x(shifted_scores[i]),
                .out_valid(exp_valid[i]),
                .y(exp_values[i])
            );
        end
    endgenerate

    // Synchronize valid (all exp units have same latency)
    logic exp_all_valid;
    assign exp_all_valid = exp_valid[0]; // All finish simultaneously

    // -------------------------------------------------------------------------
    // Stage 2: Adder Tree to compute Sum of Exponentials
    // -------------------------------------------------------------------------
    localparam TREE_STAGES = $clog2(VEC_SIZE);
    logic [TREE_STAGES:0][VEC_SIZE-1:0][31:0] tree_sum;
    logic [TREE_STAGES:0] tree_valid;

    assign tree_sum[0] = exp_values;
    assign tree_valid[0] = exp_all_valid;

    generate
        for (genvar stage = 0; stage < TREE_STAGES; stage++) begin : gen_tree
            localparam int stage_len = VEC_SIZE >> (stage + 1);
            for (genvar j = 0; j < stage_len; j++) begin : gen_add
                always_ff @(posedge clk) begin
                    if (!rst_n) begin
                        tree_sum[stage+1][j] <= '0;
                    end else if (tree_valid[stage]) begin
                        tree_sum[stage+1][j] <= tree_sum[stage][2*j] + tree_sum[stage][2*j+1];
                    end
                end
            end
            always_ff @(posedge clk) begin
                if (!rst_n) tree_valid[stage+1] <= 1'b0;
                else tree_valid[stage+1] <= tree_valid[stage];
            end
        end
    endgenerate

    logic [31:0] sum_total;
    assign sum_total = tree_sum[TREE_STAGES][0];

    // -------------------------------------------------------------------------
    // Stage 3: Reciprocal of Sum
    // -------------------------------------------------------------------------
    logic recip_valid;
    logic [15:0] inv_sum; // Q0.16
    reciprocal_lut u_recip (
        .clk(clk), .rst_n(rst_n),
        .in_valid(tree_valid[TREE_STAGES]),
        .din(sum_total),
        .out_valid(recip_valid),
        .dout(inv_sum)
    );

    // -------------------------------------------------------------------------
    // Stage 4: Multiply each exp by inverse sum (normalization)
    // -------------------------------------------------------------------------
    localparam RECIP_LATENCY = 3;
    logic [RECIP_LATENCY-1:0][VEC_SIZE-1:0][31:0] exp_delayed;
    logic [RECIP_LATENCY-1:0] valid_delayed;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            exp_delayed <= '{default: '0};
            valid_delayed <= '0;
        end else begin
            exp_delayed[0] <= exp_values;
            valid_delayed[0] <= exp_all_valid;
            for (int i = 1; i < RECIP_LATENCY; i++) begin
                exp_delayed[i] <= exp_delayed[i-1];
                valid_delayed[i] <= valid_delayed[i-1];
            end
        end
    end

    logic [VEC_SIZE-1:0][31:0] exp_aligned;
    logic aligned_valid;
    assign exp_aligned   = exp_delayed[RECIP_LATENCY-1];
    assign aligned_valid = valid_delayed[RECIP_LATENCY-1];

    logic [VEC_SIZE-1:0][31:0] probs_full;

    generate
        for (genvar i = 0; i < VEC_SIZE; i++) begin : gen_norm
            always_ff @(posedge clk) begin
                if (!rst_n) begin
                    probs_full[i] <= '0;
                end else if (aligned_valid && recip_valid) begin
                    probs_full[i] <= exp_aligned[i] * inv_sum;
                end
            end
        end
    endgenerate

    always_ff @(posedge clk) begin
        if (!rst_n) out_valid <= 1'b0;
        else out_valid <= aligned_valid && recip_valid;
    end

    generate
        for (genvar i = 0; i < VEC_SIZE; i++) begin : gen_trunc
            assign probs_out[i] = probs_full[i][31:16];
        end
    endgenerate

endmodule
