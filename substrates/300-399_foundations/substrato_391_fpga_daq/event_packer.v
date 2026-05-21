// ═══════════════════════════════════════════════════════
// event_packer.v — Empacota evento em 128 bits
// Formato: [63:0] timestamp, [79:64] amplitude,
//          [111:80] integral, [127:112] flags/type
// ═══════════════════════════════════════════════════════
module event_packer (
    input  wire         clk,
    input  wire         rst_n,
    input  wire         pulse_detected,
    input  wire [15:0]  amplitude,
    input  wire [31:0]  integral,
    input  wire [63:0]  timestamp,
    output reg  [127:0] event_data,
    output reg          event_valid,
    input  wire         event_ready
);
    reg event_pending;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            event_data   <= 0;
            event_valid  <= 0;
            event_pending <= 0;
        end else begin
            if (pulse_detected && !event_pending) begin
                event_data   <= {4'h1,           // type: 1 = Cherenkov pulse
                                 12'h0,           // reserved
                                 integral[31:0],
                                 amplitude[15:0],
                                 timestamp[63:0]};
                event_valid  <= 1;
                event_pending <= 1;
            end else if (event_valid && event_ready) begin
                event_valid  <= 0;
                event_pending <= 0;
            end
        end
    end
endmodule
