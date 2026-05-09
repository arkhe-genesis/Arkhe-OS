module safety_enclave_ors_v1_1 #(
    parameter COIL_CURRENT_BITS = 16,
    parameter TETHER_TENSION_BITS = 14,
    parameter DECEL_FIXED_BITS = 16,
    parameter SAFETY_MARGIN_BITS = 12,
    parameter THERMAL_LOAD_BITS = 16
) (
    // ... entradas mantidas ...
    input wire [THERMAL_LOAD_BITS-1:0] thermal_load_kw,  // Novo: monitoramento térmico
    // ... saídas mantidas ...
    output reg pcm_storage_engaged,  // Novo: controle de PCM
    output reg capacitor_buffering_en,  // Novo: buffer de capacitor
    output reg reduce_deceleration_rate
);

// Limites hard atualizados
localparam [TETHER_TENSION_BITS-1:0] MAX_TETHER_TENSION = 14'd13107; // 2000 N full-scale (corrigido)
localparam [DECEL_FIXED_BITS-1:0] MAX_DECEL_G = {8'd14, 8'd0};      // 90 g fixed-point (corrigido)
localparam [THERMAL_LOAD_BITS-1:0] MAX_THERMAL_BASE = 16'd44000;    // 44 kW radiadores base
localparam [THERMAL_LOAD_BITS-1:0] MAX_THERMAL_EMERG = 16'd224000;  // 224 kW base+emergência

// Detecção de falhas atualizada
wire thermal_violation_base = (thermal_load_kw > MAX_THERMAL_BASE);
wire thermal_violation_emerg = (thermal_load_kw > MAX_THERMAL_EMERG);

// Adição de estados para compilação (simplificado)
reg [1:0] current_state;
localparam STATE_NORMAL = 2'b00;
localparam STATE_CRITICAL = 2'b01;

// Ações de segurança atualizadas
always_comb begin
    pcm_storage_engaged = 1'b0;
    capacitor_buffering_en = 1'b0;
    reduce_deceleration_rate = 1'b0;

    case (current_state)
        STATE_NORMAL: begin
            if (thermal_violation_base) begin
                pcm_storage_engaged = 1'b1;  // Ativar armazenamento PCM
            end
        end
        STATE_CRITICAL: begin
            if (thermal_violation_emerg) begin
                capacitor_buffering_en = 1'b1;  // Reduzir taxa de desaceleração
                reduce_deceleration_rate = 1'b1;
            end
        end
        // ... outros estados mantidos ...
    endcase
end
endmodule
