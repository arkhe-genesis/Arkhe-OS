//=============================================================================
// ARKHE VEI v0.2 — Laplacian Coherence Engine (LCE)
//=============================================================================

module lce_top #(
    parameter int NUM_NVS = 48,
    parameter int WIDTH = 16
) (
    input  logic              clk,
    input  logic              rst_n,
    input  logic              enable_update,
    input  logic signed [WIDTH-1:0] internal_pred_error [NUM_NVS],
    input  logic signed [WIDTH-1:0] external_noise      [NUM_NVS],
    input  logic [15:0]       alpha_soc,
    output logic [15:0]       lambda_2_estimate,
    output logic              self_model_flag
);

    // Registradores internos
    logic [31:0] total_error_q;
    logic [11:0] cycle_count;
    logic [15:0] l2_reg;

    // Correção #150-P1, #150-P2: Inicialização e tratamento de loops
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            total_error_q     <= '0;
            cycle_count       <= '0;
            l2_reg            <= 16'h0300; // ~0.1875 (Checklist: < 0.2)
            self_model_flag   <= 1'b0;
            lambda_2_estimate <= 16'h0300;
        end else if (enable_update) begin
            // Acúmulo de erro escalar (Laplaciana simplificada)
            // Em hardware real, isso seria uma rede sistólica ou árvore de redução
            automatic logic [31:0] batch_error = 0;
            for (int i = 0; i < NUM_NVS; i++) begin
                logic signed [WIDTH:0] diff;
                diff = internal_pred_error[i] - external_noise[i];
                batch_error += (diff[WIDTH]) ? -diff : diff;
            end
            total_error_q <= batch_error;

            // Aproximação de λ₂: dλ/dt = α * (Target - Error)
            // Se erro < threshold, λ₂ sobe.
            // Threshold escalado por alpha_soc (0.015 em Q4.12)
            if (batch_error < (16'h1000 >> 2)) begin // Threshold arbitrário
                if (l2_reg < 16'hF000) // teto 0.9375
                    l2_reg <= l2_reg + alpha_soc[7:0]; // Incremento lento
            end else begin
                if (l2_reg > 16'h0200)
                    l2_reg <= l2_reg - 16'h0010;
            end

            // Saídas
            lambda_2_estimate <= l2_reg;

            // Despertar do Auto-modelo (Checklist: < 2000 ciclos)
            if (cycle_count < 2047) begin
                cycle_count <= cycle_count + 1;
            end

            if (cycle_count > 1500 && l2_reg > 16'h8000) begin
                self_model_flag <= 1'b1;
            end else begin
                self_model_flag <= 1'b0;
            end
        end
    end

endmodule
