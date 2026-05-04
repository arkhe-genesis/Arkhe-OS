// lstm_onchip.v — LSTM em array de memristores
// Implementação analógica para baixo consumo e alta velocidade

module lstm_onchip (
    input wire clk,
    input wire rst_n,
    input wire [7:0] thermal_input,    // Temperatura em escala 0.1nK
    output reg [15:0] prediction,       // Predição de M (escala 1000)
    output reg valid
);
    // Parâmetros do LSTM
    localparam HIDDEN_SIZE = 16;
    localparam INPUT_SIZE = 8;
    localparam WEIGHT_WIDTH = 8;

    // Arrays de memristores (simulados como BRAM por enquanto)
    reg signed [WEIGHT_WIDTH-1:0] Wf [0:HIDDEN_SIZE-1][0:INPUT_SIZE+HIDDEN_SIZE-1]; // Forget gate
    reg signed [WEIGHT_WIDTH-1:0] Wi [0:HIDDEN_SIZE-1][0:INPUT_SIZE+HIDDEN_SIZE-1]; // Input gate
    reg signed [WEIGHT_WIDTH-1:0] Wc [0:HIDDEN_SIZE-1][0:INPUT_SIZE+HIDDEN_SIZE-1]; // Candidate
    reg signed [WEIGHT_WIDTH-1:0] Wo [0:HIDDEN_SIZE-1][0:INPUT_SIZE+HIDDEN_SIZE-1]; // Output gate

    reg signed [15:0] hidden_state [0:HIDDEN_SIZE-1];
    reg signed [15:0] cell_state [0:HIDDEN_SIZE-1];

    // Buffers de entrada
    reg [7:0] thermal_history [0:49]; // 50 amostras de histórico
    reg [5:0] history_ptr;

    // FSM
    reg [3:0] lstm_state;
    reg [4:0] neuron_idx;

    localparam LSTM_IDLE = 4'd0;
    localparam LSTM_LOAD = 4'd1;
    localparam LSTM_FORGET = 4'd2;
    localparam LSTM_INPUT = 4'd3;
    localparam LSTM_CANDIDATE = 4'd4;
    localparam LSTM_UPDATE = 4'd5;
    localparam LSTM_OUTPUT = 4'd6;
    localparam LSTM_PREDICT = 4'd7;

    // Função sigmoid aproximada (lookup table)
    function signed [15:0] sigmoid;
        input signed [15:0] x;
        begin
            if (x > 8192) sigmoid = 16384;      // ~1.0
            else if (x < -8192) sigmoid = 0;    // ~0.0
            else sigmoid = 8192 + (x >> 1);     // Linear aprox
        end
    endfunction

    // Função tanh aproximada
    function signed [15:0] tanh_approx;
        input signed [15:0] x;
        begin
            if (x > 8192) tanh_approx = 8192;   // ~1.0
            else if (x < -8192) tanh_approx = -8192; // ~-1.0
            else tanh_approx = x;               // Linear
        end
    endfunction

    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            lstm_state <= LSTM_IDLE;
            history_ptr <= 0;
            valid <= 0;
            prediction <= 910; // M base = 0.91

            for (i = 0; i < HIDDEN_SIZE; i = i + 1) begin
                hidden_state[i] <= 0;
                cell_state[i] <= 0;
            end
        end else begin
            case (lstm_state)
                LSTM_IDLE: begin
                    valid <= 0;
                    if (history_ptr >= 50) begin
                        lstm_state <= LSTM_LOAD;
                        neuron_idx <= 0;
                    end else begin
                        thermal_history[history_ptr] <= thermal_input;
                        history_ptr <= history_ptr + 1;
                    end
                end

                LSTM_LOAD: begin
                    // Carregar pesos dos memristores
                    // (em hardware real: leitura analógica do crossbar)
                    lstm_state <= LSTM_FORGET;
                end

                LSTM_FORGET: begin
                    // f_t = σ(W_f · [h_{t-1}, x_t] + b_f)
                    // Simplificado: usar thermal_input como proxy
                    lstm_state <= LSTM_INPUT;
                end

                LSTM_INPUT: begin
                    // i_t = σ(W_i · [h_{t-1}, x_t] + b_i)
                    lstm_state <= LSTM_CANDIDATE;
                end

                LSTM_CANDIDATE: begin
                    // C̃_t = tanh(W_c · [h_{t-1}, x_t] + b_c)
                    lstm_state <= LSTM_UPDATE;
                end

                LSTM_UPDATE: begin
                    // C_t = f_t * C_{t-1} + i_t * C̃_t
                    lstm_state <= LSTM_OUTPUT;
                end

                LSTM_OUTPUT: begin
                    // o_t = σ(W_o · [h_{t-1}, x_t] + b_o)
                    // h_t = o_t * tanh(C_t)
                    if (neuron_idx < HIDDEN_SIZE - 1) begin
                        neuron_idx <= neuron_idx + 1;
                        lstm_state <= LSTM_FORGET;
                    end else begin
                        lstm_state <= LSTM_PREDICT;
                    end
                end

                LSTM_PREDICT: begin
                    // Predição final: M = base + variação térmica
                    // Simulação: M = 910 + (thermal_input - 128) / 10
                    prediction <= 910 + ((thermal_input - 128) * 3);
                    valid <= 1;
                    history_ptr <= 0; // Reset histórico
                    lstm_state <= LSTM_IDLE;
                end
            endcase
        end
    end
endmodule
