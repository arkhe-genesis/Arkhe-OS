//=============================================================================
// ARKHE VEI v0.2 — DAC Serializer (v0.2)
//=============================================================================

module dac_serializer #(
    parameter int N_CHANNELS = 128,
    parameter int DATA_WIDTH = 12
) (
    input  logic                   clk_sys,
    input  logic                   rst_n,
    input  logic                   update_strobe,
    input  logic [DATA_WIDTH-1:0]  phases [N_CHANNELS],

    output logic [DATA_WIDTH-1:0]  dac_phases [N_CHANNELS]
);

    // Buffer interno para garantir atomicidade no barramento LiNbO₃
    // Correção P9: Sincronização de strobe entre canais
    logic [DATA_WIDTH-1:0] shadow_register [N_CHANNELS];

    always_ff @(posedge clk_sys or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < N_CHANNELS; i++) begin
                shadow_register[i] <= '0;
                dac_phases[i]      <= '0;
            end
        end else begin
            // Captura assíncrona do strobe de atualização
            if (update_strobe) begin
                shadow_register <= phases;
            end

            // Saída síncrona estável (bypass de serialização nesta versão simplificada)
            // Em hardware real, haveria um Shift Register aqui para reduzir pinout
            dac_phases <= shadow_register;
        end
    end

endmodule
