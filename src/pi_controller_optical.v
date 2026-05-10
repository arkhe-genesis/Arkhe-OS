// pi_controller_optical.v
// PI controller for optical homeostasis in ARKHE spectral sensor
// Target: Xilinx Artix-7 / Lattice ECP5

module pi_controller_optical #(
    parameter DATA_WIDTH = 32,      // Width for spectral error
    parameter GAIN_WIDTH = 16,      // Q1.15 fixed-point gains
    parameter KAPPA_WIDTH = 16,     // Q1.15 fixed-point κ output
    parameter KAPPA_MIN = 16'd1638, // 0.1 in Q1.15: 0.1 * 2^15
    parameter KAPPA_MAX = 16'd32768 // 2.0 in Q1.15: 2.0 * 2^15
) (
    input wire clk,
    input wire rst_n,

    // Spectral error input (from error calculator)
    input wire [DATA_WIDTH-1:0] spectral_error,
    input wire error_valid,

    // Configuration via SPI
    input wire [GAIN_WIDTH-1:0] gain_prop,  // γ₁ in Q1.15
    input wire [GAIN_WIDTH-1:0] gain_int,   // γ₂ in Q1.15
    input wire config_valid,

    // κ output (to actuator driver)
    output reg [KAPPA_WIDTH-1:0] kappa_output,
    output reg kappa_valid,

    // Status flags
    output reg error_overflow,
    output reg converged_flag
);

    // Internal registers
    reg [DATA_WIDTH-1:0] integral_error;
    reg [DATA_WIDTH+GAIN_WIDTH:0] kappa_internal;
    reg [15:0] convergence_counter;

    // Fixed-point multiplication: Q1.15 × Q1.15 → Q2.30 → round to Q1.15
    function [GAIN_WIDTH-1:0] fixed_mult;
        input [GAIN_WIDTH-1:0] a, b;
        reg [31:0] product;
    begin
        product = a * b;  // Q1.15 × Q1.15 = Q2.30
        fixed_mult = product[30:15];  // Round to Q1.15
    end
    endfunction

    // Saturation function for κ bounds
    function [KAPPA_WIDTH-1:0] saturate_kappa;
        input [DATA_WIDTH+GAIN_WIDTH:0] val;
    begin
        if (val > KAPPA_MAX)
            saturate_kappa = KAPPA_MAX;
        else if (val < KAPPA_MIN)
            saturate_kappa = KAPPA_MIN;
        else
            saturate_kappa = val[KAPPA_WIDTH-1:0];
    end
    endfunction

    // Main control logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            integral_error <= 0;
            kappa_output <= 16'd12288;  // Initial κ = 0.75 in Q1.15
            kappa_valid <= 0;
            convergence_counter <= 0;
            error_overflow <= 0;
            converged_flag <= 0;
        end else if (error_valid) begin
            // Integral term update with anti-windup
            if (integral_error + spectral_error > 32'h7FFFFFFF) begin
                integral_error <= 32'h7FFFFFFF;
                error_overflow <= 1;
            end else if (integral_error + spectral_error < 32'h80000000) begin
                integral_error <= 32'h80000000;
                error_overflow <= 1;
            end else begin
                integral_error <= integral_error + spectral_error;
                error_overflow <= 0;
            end

            // PI control law: κ_new = κ + γ₁·error + γ₂·integral
            // All in fixed-point Q1.15 arithmetic
            kappa_internal = {kappa_output, 16'd0} +  // Promote to wider for accumulation
                           {fixed_mult(gain_prop, spectral_error), 16'd0} +
                           fixed_mult(gain_int, integral_error[31:16]);  // Use upper 16 bits of integral

            // Saturate and output
            kappa_output <= saturate_kappa(kappa_internal);
            kappa_valid <= 1;

            // Convergence detection: small error for N consecutive cycles
            if (spectral_error < 16'd100) begin  // Threshold for "small" error
                convergence_counter <= convergence_counter + 1;
                if (convergence_counter > 16'd100) begin  // 100 cycles of small error
                    converged_flag <= 1;
                end
            end else begin
                convergence_counter <= 0;
                converged_flag <= 0;
            end
        end else begin
            kappa_valid <= 0;
        end
    end

    // Configuration update (synchronous)
    always @(posedge clk) begin
        if (config_valid) begin
            // Gains updated via SPI interface (external)
            // No internal storage needed if driven directly
        end
    end

endmodule
