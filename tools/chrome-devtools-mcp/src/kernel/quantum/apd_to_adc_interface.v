// ============================================================================
// Module: apd_to_adc_interface.v
// ============================================================================

module apd_to_adc_interface (
    input   clk,
    input   reset_n,
    input   apd_analog_in,
    output  [11:0] adc_out,
    input   [2:0] pga_gain,
    input   en,
    output  data_valid,
    output  overflow
);
    parameter ADC_BITS = 12;
    reg [ADC_BITS-1:0] adc_value;
    reg data_valid_reg;
    reg overflow_flag;

    always @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            adc_value <= 0;
            data_valid_reg <= 0;
            overflow_flag <= 0;
        end else if (en) begin
            // Simplified conversion logic
            adc_value <= 12'h800; // Mock mid-scale
            data_valid_reg <= 1'b1;
        end else begin
            data_valid_reg <= 1'b0;
        end
    end

    assign adc_out = adc_value;
    assign data_valid = data_valid_reg;
    assign overflow = overflow_flag;

endmodule
