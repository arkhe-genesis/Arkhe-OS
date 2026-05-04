
// ============================================================================
// mythos_core.sv
// Hardware accelerator for Recurrent-Depth Transformer (Mythos)
// Computes: h_next = Norm( LinearInjection(h, e) + MLP(h, e) )
// Target: AMD Versal AI Core (or any FPGA with DSPs)
// ============================================================================

`timescale 1ns / 1ps

module mythos_core #(
    parameter H_DIM = 256,                // Dimensão do estado latente
    parameter E_DIM = 256,                // Dimensão do embedding de entrada
    parameter MLP_HIDDEN_DIM = 1024,      // Dimensão interna da MLP
    parameter DATA_WIDTH = 16,            // Ponto fixo Q8.8
    parameter FRAC_WIDTH = 8
) (
    input  logic                            clk,
    input  logic                            rst_n,

    // Interface de Controle
    input  logic                            start,          // Inicia uma iteração
    output logic                            done,           // Iteração concluída
    input  logic [31:0]                     loop_count,     // Número de loops restantes (para ACT)

    // Dados de Entrada
    input  logic signed [H_DIM-1:0][DATA_WIDTH-1:0] h_in,
    input  logic signed [E_DIM-1:0][DATA_WIDTH-1:0] e_in,

    // Dados de Saída
    output logic signed [H_DIM-1:0][DATA_WIDTH-1:0] h_out,
    output logic                            valid
);

    // -------------------------------------------------------------------------
    // Sinais Internos e Estados
    // -------------------------------------------------------------------------
    typedef enum logic [2:0] {
        IDLE,
        INJECTION,
        MLP_STAGE1,
        MLP_STAGE2,
        ADD_NORM,
        DONE_STATE
    } state_t;

    state_t state, next_state;

    // Registradores de dados
    logic signed [H_DIM-1:0][DATA_WIDTH-1:0] h_reg;
    logic signed [E_DIM-1:0][DATA_WIDTH-1:0] e_reg;
    logic signed [H_DIM-1:0][DATA_WIDTH-1:0] injection_out;
    logic signed [H_DIM-1:0][DATA_WIDTH-1:0] mlp_out;
    logic signed [H_DIM-1:0][DATA_WIDTH-1:0] add_out;

    // Matrizes A e B simplificadas (diagonais para primeira versão)
    logic signed [H_DIM-1:0][DATA_WIDTH-1:0] A_diag;
    logic signed [H_DIM-1:0][DATA_WIDTH-1:0] B_diag;

    // Inicialização de parâmetros (simulação/boot)
    initial begin
        for (int j=0; j<H_DIM; j++) begin
            A_diag[j] = 16'sh00E6; // 0.9 em Q8.8 (~230)
            B_diag[j] = 16'sh001A; // 0.1 em Q8.8 (~26)
        end
    end

    // -------------------------------------------------------------------------
    // FSM: Controle de Iteração
    // -------------------------------------------------------------------------
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
        end else begin
            state <= next_state;
        end
    end

    always_comb begin
        next_state = state;
        done = 1'b0;

        case (state)
            IDLE: if (start) next_state = INJECTION;

            INJECTION: next_state = MLP_STAGE1;

            MLP_STAGE1: next_state = MLP_STAGE2;

            MLP_STAGE2: next_state = ADD_NORM;

            ADD_NORM: next_state = DONE_STATE;

            DONE_STATE: begin
                done = 1'b1;
                if (!start) next_state = IDLE;
            end

            default: next_state = IDLE;
        endcase
    end

    // -------------------------------------------------------------------------
    // Estágio 1: Injeção Linear (h = A·h + B·e)
    // -------------------------------------------------------------------------
    generate
        genvar i;
        for (i = 0; i < H_DIM; i++) begin : gen_injection
            logic signed [2*DATA_WIDTH-1:0] prod_h, prod_e;
            assign prod_h = h_reg[i] * A_diag[i];
            assign prod_e = e_reg[i % E_DIM] * B_diag[i];

            always_ff @(posedge clk) begin
                if (state == INJECTION) begin
                    injection_out[i] <= prod_h[FRAC_WIDTH +: DATA_WIDTH] +
                                        prod_e[FRAC_WIDTH +: DATA_WIDTH];
                end
            end
        end
    endgenerate

    // -------------------------------------------------------------------------
    // Estágio 2 & 3: MLP (duas camadas totalmente conectadas)
    // -------------------------------------------------------------------------
    mlp_block #(
        .IN_DIM(H_DIM),
        .HIDDEN_DIM(MLP_HIDDEN_DIM),
        .OUT_DIM(H_DIM),
        .DATA_WIDTH(DATA_WIDTH)
    ) u_mlp (
        .clk(clk),
        .rst_n(rst_n),
        .in_valid(state == MLP_STAGE1),
        .in_data(injection_out),
        .out_valid(),
        .out_data(mlp_out)
    );

    // -------------------------------------------------------------------------
    // Estágio 4: Add & Norm
    // -------------------------------------------------------------------------
    generate
        for (i = 0; i < H_DIM; i++) begin : gen_add
            always_ff @(posedge clk) begin
                if (state == ADD_NORM) begin
                    add_out[i] <= injection_out[i] + mlp_out[i];
                end
            end
        end
    endgenerate

    assign h_out = add_out;
    assign valid = (state == DONE_STATE);

    // -------------------------------------------------------------------------
    // Registro de entrada
    // -------------------------------------------------------------------------
    always_ff @(posedge clk) begin
        if (state == IDLE && start) begin
            h_reg <= h_in;
            e_reg <= e_in;
        end
    end

endmodule
