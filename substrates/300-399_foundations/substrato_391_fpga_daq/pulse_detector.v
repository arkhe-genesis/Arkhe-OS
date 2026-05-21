// ═══════════════════════════════════════════════════════
// pulse_detector.v — Deteção de Pulso Cherenkov
// Método: Limiar simples + integração trapezoidal
// ═══════════════════════════════════════════════════════
module pulse_detector (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [11:0] adc_data,
    input  wire [11:0] threshold,
    output reg         pulse_out,
    output reg  [15:0] amplitude,
    output reg  [31:0] integral,
    output reg  [63:0] timestamp,
    output reg         detected
);
    reg [11:0] data_prev;
    reg        above_thresh;
    reg        pulse_active;
    reg [31:0] integral_acc;
    reg [15:0] peak_hold;
    reg [63:0] time_counter;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_prev    <= 0;
            above_thresh <= 0;
            pulse_active <= 0;
            integral_acc <= 0;
            peak_hold    <= 0;
            time_counter <= 0;
            pulse_out    <= 0;
            amplitude    <= 0;
            integral     <= 0;
            timestamp    <= 0;
            detected     <= 0;
        end else begin
            time_counter <= time_counter + 1;
            detected     <= 0;

            above_thresh <= (adc_data > threshold);

            if (above_thresh && !pulse_active) begin
                // Início do pulso
                pulse_active <= 1;
                integral_acc <= 0;
                peak_hold    <= adc_data;
                timestamp    <= time_counter;
            end else if (pulse_active) begin
                // Integração trapezoidal
                integral_acc <= integral_acc +
                               ((adc_data + data_prev) >> 1);
                if (adc_data > peak_hold)
                    peak_hold <= adc_data;

                if (!above_thresh) begin
                    // Fim do pulso
                    pulse_active <= 0;
                    amplitude    <= peak_hold;
                    integral     <= integral_acc;
                    detected     <= 1;
                end
            end

            data_prev <= adc_data;
            pulse_out <= pulse_active;
        end
    end
endmodule
