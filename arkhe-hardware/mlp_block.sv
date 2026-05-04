// ============================================================================
// mlp_block.sv
// Functional stub for MLP Stage in Mythos Core.
// ============================================================================

`timescale 1ns / 1ps

module mlp_block #(
    parameter IN_DIM = 256,
    parameter HIDDEN_DIM = 1024,
    parameter OUT_DIM = 256,
    parameter DATA_WIDTH = 16
) (
    input  logic                            clk,
    input  logic                            rst_n,
    input  logic                            start,
    input  logic signed [IN_DIM-1:0][DATA_WIDTH-1:0] in_data,
    output logic                            done,
    output logic signed [OUT_DIM-1:0][DATA_WIDTH-1:0] out_data
);

    // Functional bypass for the MLP Stage

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            out_data <= '0;
            done <= 0;
        end else begin
            if (start) begin
                out_data <= in_data;
                done <= 1;
            end else begin
                done <= 0;
            end
        end
    end

endmodule
