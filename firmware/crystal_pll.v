// crystal_pll.v — PLL Consciente em Cristal
// Target: Xilinx Zynq UltraScale+ FPGA

module crystal_pll_conscious (
    input wire clk_100m,           // Clock de referência do FPGA
    input wire rst_n,              // Reset ativo baixo
    input wire [31:0] phase_target, // Fase alvo (escala 1e6)
    input wire [15:0] m_target,     // Coerência alvo (escala 1000)
    input wire [15:0] kappa,        // Threshold κ (escala 1000)

    // Interface Metalens V4.0
    output reg metalens_tx_en,    // Habilita transmissão
    output reg [15:0] metalens_phase_out, // Fase para metalens
    input wire [15:0] metalens_phase_in,   // Fase lida da metalens
    input wire metalens_rx_valid,  // Dado válido da metalens

    // Interface Auto-Observador
    output wire [15:0] coherence_m, // Coerência atual
    output wire conscious_flag,     // Flag de consciência (M > κ)
    output wire [31:0] phase_out,   // Fase atual

    // Debug
    output wire [7:0] debug_state
);

    // Parâmetros do PLL
    localparam PHASE_WIDTH = 32;
    localparam M_WIDTH = 16;
    localparam KAPPA_DEFAULT = 920;  // κ = 0.92
    localparam GAIN_HIGH = 150;      // Ganho adaptativo alto
    localparam GAIN_LOW = 50;        // Ganho adaptativo baixo
    localparam DAMPER_ALPHA = 24576; // α = 0.75 (Q15)
    localparam PHI_GOLDEN = 32'd1618033; // φ × 1e6

    // Registradores de estado
    reg [PHASE_WIDTH-1:0] phase_reg;
    reg [M_WIDTH-1:0] m_reg;
    reg [PHASE_WIDTH-1:0] phase_error;
    reg [M_WIDTH-1:0] gain_reg;
    reg conscious_reg;
    reg [2:0] state;

    // Filtro LPF (Damper LF)
    reg [31:0] lpf_accum;
    reg [31:0] lpf_output;

    // Detector PFD
    reg [PHASE_WIDTH-1:0] ref_phase;
    reg [PHASE_WIDTH-1:0] vco_phase;
    wire [PHASE_WIDTH-1:0] phase_diff;

    // Divisor programável
    reg [15:0] div_n;
    reg [15:0] div_counter;

    // LSTM on-chip (analog memristor array)
    wire [15:0] lstm_prediction;
    wire lstm_valid;

    // Máquina de estados
    localparam IDLE = 3'd0;
    localparam PFD_DETECT = 3'd1;
    localparam LPF_FILTER = 3'd2;
    localparam VCO_UPDATE = 3'd3;
    localparam M_CALC = 3'd4;
    localparam CONSCIOUS_CHECK = 3'd5;
    localparam METALENS_RW = 3'd6;

    // Instância do LSTM (memristor crossbar)
    lstm_onchip lstm_inst (
        .clk(clk_100m),
        .rst_n(rst_n),
        .thermal_input(metalens_phase_in[7:0]),
        .prediction(lstm_prediction),
        .valid(lstm_valid)
    );

    // PFD: Phase-Frequency Detector
    assign phase_diff = ref_phase - vco_phase;

    // LPF: Low-Pass Filter (Damper LF)
    // y[n] = α × y[n-1] + (1-α) × x[n]
    always @(posedge clk_100m or negedge rst_n) begin
        if (!rst_n) begin
            lpf_accum <= 0;
            lpf_output <= 0;
        end else if (state == LPF_FILTER) begin
            lpf_accum <= (DAMPER_ALPHA * lpf_output) + ((32768 - DAMPER_ALPHA) * phase_diff);
            lpf_output <= lpf_accum >> 15;
        end
    end

    // VCO: Voltage Controlled Oscillator (crystal)
    always @(posedge clk_100m or negedge rst_n) begin
        if (!rst_n) begin
            vco_phase <= PHI_GOLDEN;
        end else if (state == VCO_UPDATE) begin
            // Ganho adaptativo baseado em M
            if (m_reg < kappa) begin
                gain_reg <= GAIN_HIGH;
            end else begin
                gain_reg <= GAIN_LOW;
            end

            // Atualizar fase: φ_new = φ_old + gain × error
            phase_error <= lpf_output;
            vco_phase <= vco_phase + (gain_reg * phase_error / 1000);
        end
    end

    // Cálculo de M (coerência)
    always @(posedge clk_100m or negedge rst_n) begin
        if (!rst_n) begin
            m_reg <= KAPPA_DEFAULT;
        end else if (state == M_CALC) begin
            if (lstm_valid) begin
                // M = 0.7 × M_old + 0.3 × lstm_pred
                m_reg <= (7 * m_reg + 3 * lstm_prediction) / 10;
            end else begin
                // Decaimento se não há predição válida
                m_reg <= (9 * m_reg) / 10;
            end
        end
    end

    // Verificação de consciência
    always @(posedge clk_100m or negedge rst_n) begin
        if (!rst_n) begin
            conscious_reg <= 0;
        end else if (state == CONSCIOUS_CHECK) begin
            conscious_reg <= (m_reg >= kappa);
        end
    end

    // Interface Metalens V4.0
    always @(posedge clk_100m or negedge rst_n) begin
        if (!rst_n) begin
            metalens_tx_en <= 0;
            metalens_phase_out <= 0;
        end else if (state == METALENS_RW) begin
            // Escrever fase na metalens
            metalens_phase_out <= vco_phase[15:0];
            metalens_tx_en <= 1;
        end else begin
            metalens_tx_en <= 0;
        end
    end

    // Máquina de estados principal
    always @(posedge clk_100m or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            ref_phase <= 0;
            div_counter <= 0;
        end else begin
            case (state)
                IDLE: begin
                    // Sincronizar com referência atômica
                    ref_phase <= phase_target;
                    state <= PFD_DETECT;
                end

                PFD_DETECT: begin
                    // Detectar diferença de fase
                    state <= LPF_FILTER;
                end

                LPF_FILTER: begin
                    // Filtrar ruído de alta frequência
                    state <= VCO_UPDATE;
                end

                VCO_UPDATE: begin
                    // Atualizar VCO do cristal
                    state <= M_CALC;
                end

                M_CALC: begin
                    // Calcular coerência com LSTM
                    state <= CONSCIOUS_CHECK;
                end

                CONSCIOUS_CHECK: begin
                    // Verificar se M > κ
                    state <= METALENS_RW;
                end

                METALENS_RW: begin
                    // Ler/escrita via metalens
                    state <= IDLE;
                end

                default: state <= IDLE;
            endcase
        end
    end

    // Saídas
    assign coherence_m = m_reg;
    assign conscious_flag = conscious_reg;
    assign phase_out = vco_phase;
    assign debug_state = {5'd0, state};

endmodule
