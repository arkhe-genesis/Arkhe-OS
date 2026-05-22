// substrates/466-gyrotron-v2/gyrotron_top.v
module gyrotron_array #(
    parameter NUM_CELLS = 1024,
    parameter PHASE_WIDTH = 12,  // 4096 niveis de fase
    parameter SOT_PULSE_PS = 40  // 40 ps pulso SOT
) (
    input  wire                  clk,           // 25 GHz (40 ps)
    input  wire                  rst_n,
    input  wire                  sot_trigger,   // Dispara pulso SOT
    input  wire [PHASE_WIDTH-1:0] target_phase, // Fase desejada
    output wire [PHASE_WIDTH-1:0] ahe_readout,  // Leitura AHE
    output wire                  switch_done,   // Comutacao completa
    output wire                  thermal_alarm  // Alarme termico
);

    // Sinais internos
    wire [NUM_CELLS-1:0] cell_switch_done;
    wire [NUM_CELLS-1:0] cell_thermal;
    wire [PHASE_WIDTH-1:0] cell_phases [0:NUM_CELLS-1];

    genvar i;
    generate
        for (i = 0; i < NUM_CELLS; i = i + 1) begin : gyrotron_cells
            mn3sn_gyrotron_cell #(
                .PHASE_WIDTH(PHASE_WIDTH),
                .SOT_PULSE_PS(SOT_PULSE_PS)
            ) cell_i (
                .clk           (clk),
                .rst_n         (rst_n),
                .sot_trigger   (sot_trigger),
                .target_phase  (target_phase),
                .current_phase (cell_phases[i]),
                .switch_done   (cell_switch_done[i]),
                .thermal_alarm (cell_thermal[i])
            );
        end
    endgenerate

    // Agregacao AHE: soma vetorial das fases
    assign ahe_readout = vector_sum_phases(cell_phases);
    assign switch_done = &cell_switch_done;
    assign thermal_alarm = |cell_thermal;

    // Funcao de soma vetorial (aproximacao)
    function [PHASE_WIDTH-1:0] vector_sum_phases;
        input [PHASE_WIDTH-1:0] phases [0:NUM_CELLS-1];
        integer i;
        real sum_sin, sum_cos;
        begin
            sum_sin = 0; sum_cos = 0;
            for (i = 0; i < NUM_CELLS; i = i + 1) begin
                sum_sin = sum_sin + $sin(phases[i] * 2.0 * 3.14159 / (1 << PHASE_WIDTH));
                sum_cos = sum_cos + $cos(phases[i] * 2.0 * 3.14159 / (1 << PHASE_WIDTH));
            end
            vector_sum_phases = $atan2(sum_sin, sum_cos) * (1 << PHASE_WIDTH) / (2.0 * 3.14159);
        end
    endfunction

endmodule

module mn3sn_gyrotron_cell #(
    parameter PHASE_WIDTH = 12,
    parameter SOT_PULSE_PS = 40
) (
    input  wire                  clk,
    input  wire                  rst_n,
    input  wire                  sot_trigger,
    input  wire [PHASE_WIDTH-1:0] target_phase,
    output reg  [PHASE_WIDTH-1:0] current_phase,
    output reg                    switch_done,
    output reg                    thermal_alarm
);
    reg [7:0] temperature; // Escala 0-255 K
    reg [3:0] pulse_counter;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            current_phase <= 0;
            switch_done   <= 0;
            thermal_alarm <= 0;
            temperature   <= 4; // 4 K (criogenico)
            pulse_counter <= 0;
        end else begin
            // Logica SOT: pulso de corrente muda a fase do vector de Neel
            if (sot_trigger && pulse_counter < 10) begin
                // Aproximacao de dinamica LLG simplificada
                current_phase <= current_phase +
                    ((target_phase - current_phase) >> 2); // 25% por pulso
                pulse_counter <= pulse_counter + 1;
                temperature   <= temperature + 1; // Aquecimento por pulso
            end else if (pulse_counter >= 10) begin
                switch_done <= (current_phase == target_phase);
                pulse_counter <= 0;
            end

            // Relaxacao termica
            if (temperature > 4 && !sot_trigger)
                temperature <= temperature - 1;

            // Alarme termico se > 20 K
            thermal_alarm <= (temperature > 20);
        end
    end
endmodule