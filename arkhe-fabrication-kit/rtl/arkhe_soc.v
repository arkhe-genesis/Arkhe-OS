module arkhe_soc (
    input clk,
    input rst_n,
    input [15:0] data_in,
    output [15:0] data_out,
    output hesitate
);
    // Placeholder for Arkhe SoC Top Level
    clifford_core u_clifford (
        .clk(clk),
        .rst_n(rst_n),
        .data_in(data_in),
        .data_out(data_out)
    );

    trng u_trng (
        .clk(clk),
        .rst_n(rst_n),
        .entropy()
    );

    assign hesitate = 1'b0; // To be implemented with 8-buffer path
endmodule
