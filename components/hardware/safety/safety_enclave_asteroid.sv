// Arquivo: hardware/safety/safety_enclave_asteroid.sv
module safety_enclave_asteroid #(
    parameter COIL_CURRENT_BITS = 16,
    parameter APPROACH_VELOCITY_BITS = 14,
    parameter CRYO_TEMP_BITS = 12,
    parameter THERMAL_MARGIN_BITS = 12
) (
    input wire clk_50mhz,  // Frequência reduzida para radiação
    input wire rst_n,

    // Entradas de monitoramento específicas para asteroides
    input wire [COIL_CURRENT_BITS-1:0] coil_current_dac,
    input wire [APPROACH_VELOCITY_BITS-1:0] approach_velocity_sensor,
    input wire [CRYO_TEMP_BITS-1:0] cryo_temp_K,
    input wire [THERMAL_MARGIN_BITS-1:0] thermal_margin_fixed,
    input wire radiation_level_flag,
    input wire micrometeoroid_impact_flag,

    // Saídas de controle de emergência
    output reg coil_current_override_en,
    output reg approach_abort_trigger,
    output reg cryo_system_safe_mode,
    output reg [63:0] fault_timestamp_ns
);

// Limites hard para ambiente de asteroides
localparam [COIL_CURRENT_BITS-1:0] MAX_COIL_CURRENT = 16'd40959;  // 10 kA full-scale
localparam [APPROACH_VELOCITY_BITS-1:0] MAX_APPROACH_VELOCITY = 14'd500; // 500 m/s max approach
localparam [CRYO_TEMP_BITS-1:0] MIN_CRYO_TEMP_K = 12'd368;  // 90 K mínimo para destilação
localparam [THERMAL_MARGIN_BITS-1:0] MIN_THERMAL_MARGIN = 12'd3072; // 0.90 fixed-point

// Detecção de falhas específicas para cinturão de asteroides
wire current_violation = (coil_current_dac > MAX_COIL_CURRENT);
wire velocity_violation = (approach_velocity_sensor > MAX_APPROACH_VELOCITY);
wire cryo_violation = (cryo_temp_K < MIN_CRYO_TEMP_K);
wire margin_violation = (thermal_margin_fixed < MIN_THERMAL_MARGIN);
wire radiation_critical = radiation_level_flag;
wire impact_critical = micrometeoroid_impact_flag;

// Codificação de severidade
wire any_emergency = current_violation | cryo_violation | margin_violation | impact_critical;
wire any_critical = velocity_violation | radiation_critical;

// Máquina de estados de segurança para asteroides
typedef enum logic [2:0] {
    STATE_NORMAL = 3'b000,
    STATE_WARNING = 3'b001,
    STATE_CRITICAL = 3'b010,
    STATE_EMERGENCY = 3'b100
} safety_state_t;

safety_state_t current_state, next_state;

always_comb begin
    next_state = current_state;
    case (current_state)
        STATE_NORMAL: begin
            if (any_emergency) next_state = STATE_EMERGENCY;
            else if (any_critical) next_state = STATE_CRITICAL;
        end
        STATE_CRITICAL: begin
            if (any_emergency) next_state = STATE_EMERGENCY;
            else if (!any_critical) next_state = STATE_NORMAL;
        end
        STATE_EMERGENCY: begin
            if (rst_n == 1'b0) next_state = STATE_NORMAL;
        end
        default: next_state = STATE_NORMAL;
    endcase
end

// Ações de segurança específicas para asteroides
always_comb begin
    coil_current_override_en = 1'b0;
    approach_abort_trigger = 1'b0;
    cryo_system_safe_mode = 1'b0;

    case (current_state)
        STATE_NORMAL: begin
            // Operação normal
        end
        STATE_CRITICAL: begin
            if (velocity_violation) begin
                approach_abort_trigger = 1'b1;  // Abortar aproximação iônica
            end
            if (radiation_critical) begin
                cryo_system_safe_mode = 1'b1;  // Proteger sistemas criogênicos
            end
        end
        STATE_EMERGENCY: begin
            // Emergência: corte imediato e proteção de sistemas críticos
            coil_current_override_en = 1'b1;
            approach_abort_trigger = 1'b1;
            cryo_system_safe_mode = 1'b1;
        end
    endcase
end

// Registro de timestamp de falha (nanossegundos)
reg [63:0] timestamp_counter;
always_ff @(posedge clk_50mhz) begin
    timestamp_counter <= timestamp_counter + 1;  // 20 ns resolution @ 50 MHz
end

always_ff @(posedge clk_50mhz or negedge rst_n) begin
    if (!rst_n) begin
        fault_timestamp_ns <= 64'b0;
    end else if (current_state == STATE_EMERGENCY && next_state != STATE_EMERGENCY) begin
        fault_timestamp_ns <= timestamp_counter;  // Capturar entrada em emergência
    end
end

endmodule
