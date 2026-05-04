// ============================================================================
// reciprocal_lut.sv
// Structural approximation of 1/x using a small LUT.
// Input: Q16.16 (unsigned)
// Output: Q0.16
// ============================================================================

`timescale 1ns / 1ps

module reciprocal_lut (
    input  logic        clk,
    input  logic        rst_n,
    input  logic        in_valid,
    input  logic [31:0] din,
    output logic        out_valid,
    output logic [15:0] dout
);

    // Normalize input to find MSB
    logic [4:0] msb_pos;
    logic [31:0] normalized;

    // Very simple 4-entry LUT for the 2 bits after MSB
    logic [15:0] lut [0:3];
    initial begin
        lut[0] = 16'hFFFF; // 1/1.0
        lut[1] = 16'hCCCC; // 1/1.25
        lut[2] = 16'hAAAA; // 1/1.5
        lut[3] = 16'h9249; // 1/1.75
    end

    logic [2:0] valid_pipe;
    logic [1:0] lut_idx;
    logic [4:0] shift_amt;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            valid_pipe <= '0;
            dout <= '0;
        end else begin
            valid_pipe <= {valid_pipe[1:0], in_valid};

            // Cycle 1: Find MSB (simplified priority encoder)
            msb_pos <= 0;
            for (int i=0; i<32; i++) if (din[i]) msb_pos <= i;

            // Cycle 2: Index LUT and calculate shift
            // normalized = din >> (msb_pos - 1)
            lut_idx <= (msb_pos >= 2) ? din[msb_pos-1 -: 2] : 2'b00;
            shift_amt <= (msb_pos >= 16) ? (msb_pos - 16) : (16 - msb_pos);

            // Cycle 3: Final shift
            if (msb_pos >= 16) dout <= lut[lut_idx] >> shift_amt;
            else dout <= lut[lut_idx] << shift_amt;

            if (din == 0) dout <= 16'hFFFF;
        end
    end

    assign out_valid = valid_pipe[2];

endmodule
