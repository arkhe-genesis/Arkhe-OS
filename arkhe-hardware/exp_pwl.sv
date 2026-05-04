// ============================================================================
// exp_pwl.sv
// Piecewise Linear approximation of exp(x) for x in [-8, 0].
// Input: x in Q8.8
// Output: y in Q16.16
// ============================================================================

`timescale 1ns / 1ps

module exp_pwl (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        in_valid,
    input  logic signed [15:0] x,
    output logic        out_valid,
    output logic [31:0] y
);

    // Simple PWL implementation for exp(x)
    // Segments for [-8, 0]
    // Segment 1: [-8, -4] -> very small
    // Segment 2: [-4, -2]
    // Segment 3: [-2, -1]
    // Segment 4: [-1, 0]

    logic signed [15:0] x_reg;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= '0;
            out_valid <= 0;
        end else begin
            out_valid <= in_valid;
            x_reg <= x;

            if (x_reg >= 0) y <= 32'h00010000; // 1.0
            else if (x_reg < -16'sh0800) y <= 32'h0; // < -8
            else begin
                // Simple linear approx: exp(x) approx 1 + x for x approx 0
                // For better accuracy, use more segments.
                // Using 1 + x + x^2/2 ...
                // Here we just do a multi-segment linear map.
                if (x_reg > -16'sh0100) y <= 32'h00010000 + ($signed(32'h00010000) * x_reg >>> 8);
                else if (x_reg > -16'sh0200) y <= 32'h00005E00 + ($signed(32'h0000A000) * (x_reg + 16'sh0100) >>> 8);
                else y <= 32'h00002000; // rough floor
            end
        end
    end

endmodule
