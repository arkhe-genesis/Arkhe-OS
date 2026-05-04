//=============================================================================
// ARKHE VEI v0.2 — Phase Arithmetic Unit (PAU)
//=============================================================================

module pau #(
    parameter int N_EMITTERS = 128,
    parameter int PHASE_WIDTH = 12
) (
    input  logic                   clk,
    input  logic                   rst_n,

    input  logic [PHASE_WIDTH-1:0] base_phase [N_EMITTERS],
    input  logic [PHASE_WIDTH-1:0] ibmq_correction [N_EMITTERS],
    input  logic [PHASE_WIDTH-1:0] chronos_phase,
    input  logic                   gate_healthy,

    output logic [PHASE_WIDTH-1:0] corrected_phase [N_EMITTERS],
    output logic                   ramp_ok
);

    // Registradores para pipeline e sincronização (Correção P5: Timing)
    logic [PHASE_WIDTH-1:0] base_q [N_EMITTERS];
    logic [PHASE_WIDTH-1:0] ibmq_q [N_EMITTERS];
    logic [PHASE_WIDTH-1:0] chronos_q;
    logic                   healthy_q;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            chronos_q <= '0;
            healthy_q <= 1'b0;
            ramp_ok   <= 1'b0;
            for (int i = 0; i < N_EMITTERS; i++) begin
                base_q[i] <= '0;
                ibmq_q[i] <= '0;
                corrected_phase[i] <= '0;
            end
        end else begin
            // Estágio 1: Captura de entradas
            base_q    <= base_phase;
            ibmq_q    <= ibmq_correction;
            chronos_q <= chronos_phase;
            healthy_q <= gate_healthy;

            // Estágio 2: Aritmética de fase (Correção P1: Inteiros)
            for (int i = 0; i < N_EMITTERS; i++) begin
                if (healthy_q) begin
                    // Soma modular automática pelo tamanho do vetor logic
                    corrected_phase[i] <= base_q[i] + ibmq_q[i] + chronos_q;
                end else begin
                    // Fallback para Tabela Dourada se o gate estiver instável
                    corrected_phase[i] <= base_q[i];
                end
            end

            // Status de rampa (simplificado: segue a saúde do gate com 1 ciclo de atraso)
            ramp_ok <= healthy_q;
        end
    end

endmodule
