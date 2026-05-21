`timescale 1ns / 1ps

module fpga_adc_spi (
    input  wire        clk,          // 100 MHz system clock
    input  wire        rst_n,        // Active-low reset
    input  wire        adc_sdo,      // SPI Data Out
    output wire        adc_sclk,     // SPI Clock
    output wire        adc_cs_n,     // SPI Chip Select
    output wire        adc_start,    // Start conversion trigger
    input  wire        adc_eoc,      // End of conversion

    output wire [15:0] adc_data_out, // Parallel ADC data
    output wire        valid_pulse,  // Valid data pulse

    // PCIe DMA interface (simplified)
    output wire [31:0] dma_addr,
    output wire [31:0] dma_data,
    output wire        dma_valid,
    output wire        dma_last
);

    // Parameters
    parameter SPI_CLK_DIV = 4; // 100MHz / 4 = 25MHz SPI clock
    parameter THRESHOLD_5SIGMA = 16'h0A00; // 5σ threshold (calibrated)

    // Internal signals
    reg [7:0] spi_clk_div_cnt;
    reg [7:0] bit_cnt;
    reg [15:0] shift_reg;
    reg        cs_n_int;
    reg        sclk_int;
    reg        valid_int;

    // Timestamp generator (1ns resolution, 32-bit)
    reg [31:0] timestamp_reg;

    // Event detection
    reg [15:0] pulse_amplitude;
    reg [15:0] pulse_integral;
    reg [7:0]  pulse_width;
    reg        event_detected;

    assign adc_cs_n = cs_n_int;
    assign adc_sclk = sclk_int;
    assign adc_start = (bit_cnt == 8'd0) && !cs_n_int;
    assign adc_data_out = shift_reg;
    assign valid_pulse = valid_int;

    // SPI Master State Machine
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            spi_clk_div_cnt <= 8'd0;
            bit_cnt <= 8'd0;
            cs_n_int <= 1'b1;
            sclk_int <= 1'b0;
            shift_reg <= 16'd0;
            valid_int <= 1'b0;
            timestamp_reg <= 32'd0;
        end else begin
            timestamp_reg <= timestamp_reg + 1;

            if (spi_clk_div_cnt == SPI_CLK_DIV/2 - 1) begin
                spi_clk_div_cnt <= 8'd0;
                sclk_int <= ~sclk_int;

                if (sclk_int && !cs_n_int && adc_eoc) begin
                    shift_reg <= {shift_reg[14:0], adc_sdo};
                    bit_cnt <= bit_cnt + 1;

                    if (bit_cnt == 8'd15) begin
                        valid_int <= 1'b1;
                        pulse_amplitude <= shift_reg;
                        pulse_integral <= pulse_integral + shift_reg;
                        pulse_width <= pulse_width + 1;
                    end
                end else if (!sclk_int) begin
                    valid_int <= 1'b0;
                end
            end else begin
                spi_clk_div_cnt <= spi_clk_div_cnt + 1;
            end

            // Start new conversion if ready
            if (!adc_eoc && !valid_int && pulse_width > 8'd10) begin
                cs_n_int <= 1'b0;
                bit_cnt <= 8'd0;
                pulse_width <= 8'd0;
                pulse_integral <= 16'd0;

                // Check threshold
                if (pulse_amplitude > THRESHOLD_5SIGMA) begin
                    event_detected <= 1'b1;
                end
            end else if (event_detected) begin
                event_detected <= 1'b0;
                cs_n_int <= 1'b1;
                // Trigger DMA write
            end
        end
    end

    // DMA Burst Logic (simplified for clarity)
    assign dma_valid = event_detected;
    assign dma_data = {timestamp_reg, pulse_amplitude, pulse_integral, pulse_width, 8'hA5};
    assign dma_addr = 32'h0000_0000 + (timestamp_reg << 4);
    assign dma_last = 1'b1;

endmodule
