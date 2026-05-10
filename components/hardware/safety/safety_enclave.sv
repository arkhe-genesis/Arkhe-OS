module safety_enclave (
    input wire clk,
    input wire rst_n,
    input wire [15:0] coil_current,
    input wire [15:0] acceleration,
    input wire [15:0] mercy_gap,

    output reg emergency_abort_trigger,
    output reg coil_override_en,
    output reg [15:0] coil_override_value
);
    // Limites hard (síntese, não podem ser alterados por software)
    localparam MAX_COIL_CURRENT = 16'd65535;   // 15 kA full-scale
    localparam MAX_ACCELERATION_G = {8'd46, 8'd0}; // 300 g fixed-point
    localparam MERCY_GAP_FLOOR = {8'd0, 8'd10};    // 0.04 fixed-point

    // Detecção de falhas (combinacional)
    wire current_violation = (coil_current > MAX_COIL_CURRENT);
    wire accel_violation = (acceleration > MAX_ACCELERATION_G);
    wire mercy_violation = (mercy_gap < MERCY_GAP_FLOOR);

    // Estado
    typedef enum logic [1:0] {
        STATE_NORMAL = 2'b00,
        STATE_EMERGENCY = 2'b01
    } state_t;

    state_t current_state, next_state;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            current_state <= STATE_NORMAL;
        end else begin
            current_state <= next_state;
        end
    end

    // Máquina de estados de segurança
    always_comb begin
        next_state = current_state;
        emergency_abort_trigger = 1'b0;
        coil_override_en = 1'b0;
        coil_override_value = 16'd0;

        case (current_state)
            STATE_NORMAL: begin
                if (current_violation | accel_violation | mercy_violation)
                    next_state = STATE_EMERGENCY;
            end
            STATE_EMERGENCY: begin
                // Corte imediato: zero coils, zero torção, trigger abort
                emergency_abort_trigger = 1'b1;
                coil_override_en = 1'b1;
                coil_override_value = 16'd0;
                // ... permanece em emergência até reset externo ...
            end
        endcase
    end
endmodule
