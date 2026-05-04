// ============================================================================
// v_mixing.sv
// Value Mixing Stage for Mythos Attention
// Computes: mixed_out = sum(probs[i] * v_matrix[i])
// ============================================================================

`timescale 1ns / 1ps

module v_mixing #(
    parameter SEQ_LEN = 64,
    parameter D_MODEL = 64,
    parameter DATA_WIDTH = 16
) (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        start,
    input  logic [SEQ_LEN-1:0][15:0] probs, // Q0.16
    input  logic signed [SEQ_LEN-1:0][D_MODEL-1:0][DATA_WIDTH-1:0] v_matrix, // Q8.8
    output logic signed [D_MODEL-1:0][DATA_WIDTH-1:0] mixed_out, // Q8.8
    output logic        done
);

    typedef enum {IDLE, COMPUTE, DONE_STATE} state_t;
    state_t state;
    logic [$clog2(SEQ_LEN):0] idx;
    logic signed [D_MODEL-1:0][39:0] accum; // 40-bit to avoid overflow

    genvar d;
    generate
        for (d = 0; d < D_MODEL; d++) begin : gen_mixing
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    accum[d] <= '0;
                    mixed_out[d] <= '0;
                end else begin
                    if (state == IDLE && start) begin
                        accum[d] <= '0;
                    end else if (state == COMPUTE) begin
                        // Q0.16 * Q8.8 = Q8.24
                        accum[d] <= accum[d] + (probs[idx] * v_matrix[idx][d]);
                    end else if (state == DONE_STATE) begin
                        // Q8.24 -> Q8.8: Rounding (add bit 15)
                        mixed_out[d] <= accum[d][31:16] + accum[d][15];
                    end
                end
            end
        end
    endgenerate

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            idx <= 0;
            done <= 0;
        end else begin
            case (state)
                IDLE: begin
                    done <= 0;
                    if (start) begin
                        state <= COMPUTE;
                        idx <= 0;
                    end
                end
                COMPUTE: begin
                    if (idx == SEQ_LEN - 1) begin
                        state <= DONE_STATE;
                    end else begin
                        idx <= idx + 1;
                    end
                end
                DONE_STATE: begin
                    done <= 1;
                    state <= IDLE;
                end
            endcase
        end
    end

endmodule
