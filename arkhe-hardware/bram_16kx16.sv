// ============================================================================
// bram_16kx16.sv
// Weight and State storage for Mythos Core
// ============================================================================
`timescale 1ns / 1ps
module bram_16kx16 (
    input  logic        clk,
    input  logic        we,
    input  logic [13:0] addr,
    input  logic [15:0] din,
    output logic [15:0] dout
);
    logic [15:0] ram [0:16383];
    always_ff @(posedge clk) begin
        if (we) ram[addr] <= din;
        dout <= ram[addr];
    end
endmodule
