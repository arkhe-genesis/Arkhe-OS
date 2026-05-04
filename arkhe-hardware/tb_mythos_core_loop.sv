
// ============================================================================
// tb_mythos_core_loop.sv
// Testbench de Convergência Recorrente para o Mythos Core
// ============================================================================

`timescale 1ns / 1ps

module tb_mythos_core_loop;

    // -------------------------------------------------------------------------
    // Parâmetros de Configuração do Mythos Core
    // -------------------------------------------------------------------------
    localparam H_DIM = 16;               // Reduzido para simulação rápida
    localparam E_DIM = 16;
    localparam MLP_HIDDEN_DIM = 64;
    localparam DATA_WIDTH = 16;
    localparam FRAC_WIDTH = 8;

    localparam CLK_PERIOD = 10;           // 100 MHz
    localparam N_LOOPS = 20;              // Número de iterações para observar convergência

    // -------------------------------------------------------------------------
    // Sinais do DUT
    // -------------------------------------------------------------------------
    logic clk;
    logic rst_n;
    logic start;
    logic done;
    logic [31:0] loop_count;
    logic signed [H_DIM-1:0][DATA_WIDTH-1:0] h_in;
    logic signed [E_DIM-1:0][DATA_WIDTH-1:0] e_in;
    logic signed [H_DIM-1:0][DATA_WIDTH-1:0] h_out;
    logic valid;

    // Variáveis de monitoramento
    real h_norm_initial;
    real h_norm_current;
    int  loop_idx;

    // -------------------------------------------------------------------------
    // Instância do Mythos Core (DUT)
    // -------------------------------------------------------------------------
    mythos_core #(
        .H_DIM(H_DIM),
        .E_DIM(E_DIM),
        .MLP_HIDDEN_DIM(MLP_HIDDEN_DIM),
        .DATA_WIDTH(DATA_WIDTH),
        .FRAC_WIDTH(FRAC_WIDTH)
    ) u_mythos (
        .clk(clk),
        .rst_n(rst_n),
        .start(start),
        .done(done),
        .loop_count(loop_count),
        .h_in(h_in),
        .e_in(e_in),
        .h_out(h_out),
        .valid(valid)
    );

    // -------------------------------------------------------------------------
    // Geração de Clock
    // -------------------------------------------------------------------------
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    // -------------------------------------------------------------------------
    // Função para calcular a norma L2 do vetor h (em ponto flutuante para análise)
    // -------------------------------------------------------------------------
    function real compute_norm(input logic signed [H_DIM-1:0][DATA_WIDTH-1:0] vec);
        real sum = 0.0;
        real val;
        for (int i = 0; i < H_DIM; i++) begin
            val = $itor(vec[i]) / (2.0 ** FRAC_WIDTH);
            sum += val * val;
        end
        compute_norm = $sqrt(sum);
    endfunction

    // -------------------------------------------------------------------------
    // Processo Principal de Teste
    // -------------------------------------------------------------------------
    initial begin
        // Inicializa sinais
        rst_n = 0;
        start = 0;
        loop_count = N_LOOPS;
        h_in = '{default: '0};
        e_in = '{default: '0};

        // Libera reset
        repeat(5) @(posedge clk);
        rst_n = 1;
        repeat(5) @(posedge clk);

        // ---------------------------------------------------------------------
        // Estado Inicial: um vetor unitário
        // ---------------------------------------------------------------------
        for (int i = 0; i < H_DIM; i++) begin
            h_in[i] = (i == 0) ? 16'sh0100 : 16'sh0000; // [1.0, 0, 0, ...]
        end
        e_in[0] = 16'sh0080; // entrada constante 0.5

        // Calcula a norma inicial
        h_norm_initial = compute_norm(h_in);
        $display("[%0t] Estado Inicial: Norma = %f", $time, h_norm_initial);

        // ---------------------------------------------------------------------
        // Loop de Iterações Recorrentes
        // ---------------------------------------------------------------------
        for (loop_idx = 0; loop_idx < N_LOOPS; loop_idx++) begin
            // Dispara uma iteração
            start = 1'b1;
            @(posedge clk);
            start = 1'b0;

            // Aguarda a conclusão do ciclo
            @(posedge clk);
            while (!done) @(posedge clk);

            // Captura a saída e a realimenta como nova entrada
            h_in = h_out;

            // Calcula e exibe a norma para análise de convergência
            h_norm_current = compute_norm(h_out);
            $display("[%0t] Loop %0d: Norma = %f", $time, loop_idx, h_norm_current);

            // Aguarda um ciclo antes da próxima iteração
            @(posedge clk);
        end

        // ---------------------------------------------------------------------
        // Verificação de Convergência
        // ---------------------------------------------------------------------
        if (h_norm_current < 10.0 && h_norm_current > 0.0) begin
            $display("[%0t] TESTE PASS: Estado convergiu para uma norma estável (%f).", $time, h_norm_current);
        end else begin
            $display("[%0t] TESTE FAIL: Estado divergiu ou saturou (Norma = %f).", $time, h_norm_current);
        end

        $finish;
    end

    // -------------------------------------------------------------------------
    // Waveform Dumping
    // -------------------------------------------------------------------------
    initial begin
        $dumpfile("mythos_core_loop.vcd");
        $dumpvars(0, tb_mythos_core_loop);
    end

endmodule
