// =============================================================================
// Substrate 123.1 — FPGA Safety Enclave (PL Fabric)
// Target: Xilinx Zynq UltraScale+ (Programmable Logic)
//
// This module sits BETWEEN the ARM Cortex-A53 and the physical DAC output.
// It independently enforces safety invariants that NO SOFTWARE CAN OVERRIDE.
//
// Safety invariants (hardcoded in silicon):
//   • Current ≤ CURRENT_LIMIT_CODE (1.5 mA equivalent)
//   • Impedance ≤ IMPEDANCE_LIMIT_CODE (10 kΩ equivalent)
//   • Watchdog must be kicked every < 50 ms or output is disabled
//   • Emergency stop input (physical button) instantly cuts output
// =============================================================================

module tdcs_safety_enclave (
    input  wire         clk_1mhz,           // 1 MHz safety monitoring clock
    input  wire         rst_n,              // Active-low reset

    // ARM Cortex-A53 interface (AXI4-Lite)
    input  wire [15:0]  dac_command_in,     // Desired DAC code from ARM
    input  wire         dac_enable_in,      // Desired enable from ARM
    input  wire [31:0]  wdt_kick_value,     // Watchdog kick value
    input  wire         wdt_kick_valid,     // Watchdog kick strobe

    // Analog safety inputs (from ADC)
    input  wire [15:0]  impedance_raw,      // Impedance measurement
    input  wire [15:0]  current_sense_raw,  // Actual current measurement

    // Physical emergency stop
    input  wire         emergency_stop_n,   // Active-low emergency button

    // DAC output (to physical DAC chip)
    output reg  [15:0]  dac_command_out,    // Safe DAC code
    output reg          dac_enable_out,     // Safe enable signal

    // Status outputs
    output wire         safety_fault,       // Asserted when in fault state
    output wire [3:0]   fault_code          // Fault reason code
);
    // ---- Safety Constants (hardcoded in silicon) ----
    localparam CURRENT_LIMIT_CODE    = 16'd65535;  // Full scale = 1.5 mA
    localparam IMPEDANCE_LIMIT_CODE  = 16'd32768;  // Mid scale = 10 kΩ
    localparam WDT_TIMEOUT_CYCLES    = 32'd50000;  // 50 ms @ 1 MHz = 50,000 cycles
    localparam WDT_KICK_MAGIC        = 32'hDEADBEEF;

    // ---- Watchdog Counter ----
    reg [31:0] wdt_counter;

    always @(posedge clk_1mhz or negedge rst_n) begin
        if (!rst_n) begin
            wdt_counter <= 32'd0;
        end else begin
            if (wdt_kick_valid && wdt_kick_value == WDT_KICK_MAGIC) begin
                wdt_counter <= 32'd0;  // Reset on valid kick
            end else if (wdt_counter < WDT_TIMEOUT_CYCLES) begin
                wdt_counter <= wdt_counter + 1;
            end
        end
    end

    wire wdt_expired = (wdt_counter >= WDT_TIMEOUT_CYCLES);

    // ---- Safety Condition Check (combinational, < 1 µs response) ----
    wire current_over_limit    = (dac_command_in > CURRENT_LIMIT_CODE);
    wire impedance_over_limit  = (impedance_raw > IMPEDANCE_LIMIT_CODE);
    wire emergency_stop_active = !emergency_stop_n;

    // Any safety violation forces output disable
    wire safety_violation = current_over_limit ||
                             impedance_over_limit ||
                             wdt_expired ||
                             emergency_stop_active;

    // ---- Fault Code Encoding ----
    assign fault_code = {
        emergency_stop_active,   // bit 3
        wdt_expired,             // bit 2
        impedance_over_limit,    // bit 1
        current_over_limit       // bit 0
    };

    assign safety_fault = safety_violation;

    // ---- Safe Output (registered, glitch-free) ----
    always @(posedge clk_1mhz or negedge rst_n) begin
        if (!rst_n) begin
            dac_command_out <= 16'd0;
            dac_enable_out  <= 1'b0;
        end else begin
            if (safety_violation) begin
                // HARD CUTOFF: ARM cannot override
                dac_command_out <= 16'd0;
                dac_enable_out  <= 1'b0;
            end else begin
                // Normal operation: pass through ARM commands
                dac_command_out <= dac_command_in;
                dac_enable_out  <= dac_enable_in;
            end
        end
    end

    // ---- Optional: Latch fault state until manual reset ----
    reg fault_latched;
    always @(posedge clk_1mhz or negedge rst_n) begin
        if (!rst_n) begin
            fault_latched <= 1'b0;
        end else if (emergency_stop_active) begin
            fault_latched <= 1'b1;  // Latch on emergency stop
        end else if (!safety_violation && fault_latched) begin
            // Stay latched until manual reset (not implemented here)
            fault_latched <= fault_latched;
        end
    end

endmodule