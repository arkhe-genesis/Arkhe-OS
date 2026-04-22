//=============================================================================
// ARKHE-Q: Cryo-CMOS Control Circuit (v1.0)
// Implements ANEXO EA: Cryogenic Clepsydra Control Logic.
// "O GELO QUE TESTEMUNHA"
//=============================================================================

module cryo_clepsydra (
    input  logic        clk_1hz,          // Clock lento (1Hz) derivado de oscilador de quartzo a 4K
    input  logic        rst_n,            // Reset assíncrono ativo baixo
    input  logic [11:0] temp_adc,         // Leitura do termômetro de ruído Johnson
    input  logic        guardian_override, // Entrada manual para avançar fase

    output logic [11:0] heater_dac,       // Controle do aquecedor
    output logic        phase_complete,    // Sinal para o Rootstock: "patamar atingido"
    output logic [2:0]  current_phase      // Fase atual do ritual
);

    // Parâmetros de tempo mínimo por fase (em segundos)
    localparam int MIN_PHASE_TIME [0:6] = '{
        1800, // Fase I: 30 min
        3600, // Fase II: 60 min
        7200, // Fase III: 120 min
        5400, // Fase IV: 90 min
        7200, // Fase V: 120 min
        14400, // Fase VI: 240 min
        60    // Fase VII: 1 min (selo)
    };

    // Tabela de setpoints das 7 fases (em unidades ADC)
    localparam logic [11:0] SETPOINTS [0:6] = '{
        12'd2048, // 150K
        12'd1024, // 77K
        12'd1024, // 77K (estabilização)
        12'd512,  // 20K
        12'd128,  // 4.2K
        12'd128,  // 4.2K (estabilização)
        12'd128   // 4.2K (selo)
    };

    // Ciclos de estabilidade exigidos
    localparam int STABLE_CYCLES = 300; // 5 minutos de estabilidade

    // Registradores internos
    logic [2:0]  phase;
    logic [31:0] timer;
    logic [31:0] stable_counter;
    logic [11:0] dac_reg;

    assign current_phase = phase;
    assign heater_dac = dac_reg;

    always_ff @(posedge clk_1hz or negedge rst_n) begin
        if (!rst_n) begin
            phase <= 3'd0;
            timer <= '0;
            stable_counter <= '0;
            dac_reg <= 12'd1000; // Valor inicial seguro
            phase_complete <= 1'b0;
        end else begin
            // Controle PID Lento (apenas P nesta implementação simplificada)
            if (temp_adc < SETPOINTS[phase] - 12'd10) begin
                if (dac_reg < 12'hFFF) dac_reg <= dac_reg + 12'd1; // Aquece
            end else if (temp_adc > SETPOINTS[phase] + 12'd10) begin
                if (dac_reg > 12'd0) dac_reg <= dac_reg - 12'd1; // Esfria
            end

            // Verificação de Estabilidade (±0.5% approx)
            if (temp_adc > SETPOINTS[phase] - 12'd6 && temp_adc < SETPOINTS[phase] + 12'd6) begin
                stable_counter <= stable_counter + 1;
            end else begin
                stable_counter <= 0;
            end

            // Lógica de transição de fase
            timer <= timer + 1;
            if ((timer >= MIN_PHASE_TIME[phase] && stable_counter >= STABLE_CYCLES) || guardian_override) begin
                if (phase < 3'd6) begin
                    phase <= phase + 3'd1;
                    timer <= 0;
                    stable_counter <= 0;
                    phase_complete <= 1'b1;
                end else begin
                    // Ritual concluído
                    phase_complete <= 1'b1;
                end
            end else begin
                phase_complete <= 1'b0;
            end
        end
    end

endmodule
