
// ============================================================================
// gelu_pwl.sv
// GELU Activation via Piecewise Linear Approximation (PWL)
// Interval: [-4.0, 4.0], 16 segments, Q8.8 fixed-point
// Latency: 2 cycles
// ============================================================================

`timescale 1ns / 1ps

module gelu_pwl #(
    parameter DATA_WIDTH = 16,
    parameter FRAC_WIDTH = 8,
    parameter SEG_BITS    = 4   // 2^4 = 16 segments
) (
    input  logic                     clk,
    input  logic                     rst_n,

    input  logic                     in_valid,
    input  logic signed [DATA_WIDTH-1:0] in_data,

    output logic                     out_valid,
    output logic signed [DATA_WIDTH-1:0] out_data
);

    // -------------------------------------------------------------------------
    // Tabela de Coeficientes (GELU em Q8.8)
    // Formato: {slope_m[15:0], intercept_b[15:0]} = 32 bits
    // -------------------------------------------------------------------------
    logic [31:0] pwl_rom [0:(1<<SEG_BITS)-1];

    initial begin
        // Segmentos pré-calculados para GELU
        pwl_rom[0] = {16'sh0000, 16'sh0000};
        pwl_rom[1] = {16'sh0005, 16'sh0001};
        pwl_rom[2] = {16'sh0012, 16'sh0003};
        pwl_rom[3] = {16'sh0026, 16'sh000a};
        pwl_rom[4] = {16'sh0042, 16'sh0017};
        pwl_rom[5] = {16'sh0064, 16'sh002c};
        pwl_rom[6] = {16'sh0086, 16'sh0046};
        pwl_rom[7] = {16'sh009e, 16'sh005e};
        pwl_rom[8] = {16'sh00a8, 16'sh0080};
        pwl_rom[9] = {16'sh00a4, 16'sh00a2};
        pwl_rom[10] = {16'sh0094, 16'sh00c2};
        pwl_rom[11] = {16'sh0080, 16'sh00e0};
        pwl_rom[12] = {16'sh006c, 16'sh00f8};
        pwl_rom[13] = {16'sh005c, 16'sh0108};
        pwl_rom[14] = {16'sh0050, 16'sh0112};
        pwl_rom[15] = {16'sh0048, 16'sh0118};
    end

    // -------------------------------------------------------------------------
    // Estágio 1: Cálculo do Índice e Lookup
    // -------------------------------------------------------------------------
    logic [SEG_BITS-1:0] seg_index;
    logic signed [DATA_WIDTH-1:0] x_reg;
    logic valid_s1;

    always_comb begin
        // Índice = (x + 4.0) / 0.5 -> (x + 1024) >> 7 em Q8.8
        seg_index = (in_data + 16'sh0400) >>> 7;
        if (in_data <= -16'sh0400) seg_index = 0;
        if (in_data >= 16'sh0400) seg_index = (1<<SEG_BITS)-1;
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            x_reg <= '0;
            valid_s1 <= 1'b0;
        end else begin
            valid_s1 <= in_valid;
            if (in_valid) x_reg <= in_data;
        end
    end

    logic [31:0] coeff;
    assign coeff = pwl_rom[seg_index]; // Combinacional lookup para economizar 1 ciclo

    // -------------------------------------------------------------------------
    // Estágio 2: MAC (m*x + b)
    // -------------------------------------------------------------------------
    logic signed [DATA_WIDTH-1:0] slope, intercept;
    assign slope = coeff[31:16];
    assign intercept = coeff[15:0];

    logic signed [2*DATA_WIDTH-1:0] mult_result;
    logic signed [DATA_WIDTH-1:0]   result_next;

    // Multiplicação combinacional para manter 2 ciclos de latência total
    // ou poderíamos adicionar um ciclo. O usuário quer 2 ciclos.
    // Stage 1: Lookup (already done)
    // Stage 2: Mult + Add

    assign mult_result = slope * x_reg;
    assign result_next = mult_result[FRAC_WIDTH +: DATA_WIDTH] + intercept;

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            out_data <= '0;
            out_valid <= 1'b0;
        end else begin
            out_valid <= valid_s1;
            if (valid_s1) begin
                out_data <= result_next;
            end
        end
    end

endmodule
