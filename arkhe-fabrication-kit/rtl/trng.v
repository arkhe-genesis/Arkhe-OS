module trng (
    input clk,
    input rst_n,
    output [31:0] entropy
);
    // Placeholder for True Random Number Generator
    reg [31:0] rand_reg;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) rand_reg <= 32'hACE1;
        else rand_reg <= {rand_reg[30:0], rand_reg[31] ^ rand_reg[21]};
    end
    assign entropy = rand_reg;
endmodule
