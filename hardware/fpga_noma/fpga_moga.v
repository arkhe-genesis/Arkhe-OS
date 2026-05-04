// substrates/v170_living_crystal/fpga_moga.v
// Implementação FPGA do Multi-Objective Genetic Algorithm para NOMA 6G
// Target: Xilinx Zynq-7000 / Artix-7

`timescale 1ns / 1ps

module moga_power_allocator #(
    parameter NUM_DEVICES = 8,
    parameter NUM_SUBCHANNELS = 4,
    parameter POP_SIZE = 16,
    parameter DATA_WIDTH = 32,
    parameter GEN_MAX = 256
) (
    input wire clk,
    input wire rst_n,

    // Interface AXI4-Stream para canais
    input wire [DATA_WIDTH-1:0] s_axis_channel_tdata,
    input wire s_axis_channel_tvalid,
    output wire s_axis_channel_tready,

    // Interface AXI4-Stream para resultado
    output wire [DATA_WIDTH-1:0] m_axis_result_tdata,
    output wire m_axis_result_tvalid,
    input wire m_axis_result_tready,

    // Registros de controle
    input wire [31:0] max_power_sink,
    input wire [31:0] noise_variance,
    input wire [7:0] gen_max_input,

    // Status
    output wire done,
    output wire [7:0] best_score
);

    // Memória BRAM para canais
    reg [DATA_WIDTH-1:0] channel_mem [0:NUM_DEVICES*NUM_SUBCHANNELS-1];

    // Memória para população
    reg [DATA_WIDTH-1:0] population [0:POP_SIZE-1][0:NUM_DEVICES-1][0:NUM_SUBCHANNELS-1];
    reg [DATA_WIDTH-1:0] fitness_scores [0:POP_SIZE-1][0:2]; // (power, rate, violations)

    // Máquina de estados principal
    reg [7:0] gen_counter;
    reg [2:0] state;
    reg valid_out;
    reg [7:0] best_score_val;
    reg channels_loaded;
    reg calc_valid;
    reg crossover_done;
    reg mutation_done;

    localparam IDLE = 3'd0, LOAD_CHANNELS = 3'd1, INIT_POP = 3'd2,
               EVALUATE = 3'd3, SELECT = 3'd4, CROSSOVER = 3'd5,
               MUTATE = 3'd6, FINISH = 3'd7;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            gen_counter <= 0;
            state <= IDLE;
            valid_out <= 0;
            best_score_val <= 0;
        end else begin
            case (state)
                IDLE: begin
                    if (s_axis_channel_tvalid) begin
                        gen_counter <= 0;
                        state <= LOAD_CHANNELS;
                    end
                end

                LOAD_CHANNELS: begin
                    // Carregar canais da interface AXI4-Stream
                    if (channels_loaded) begin
                        state <= INIT_POP;
                    end
                end

                INIT_POP: begin
                    // Inicializar população com LFSR
                    state <= EVALUATE;
                end

                EVALUATE: begin
                    // Pipeline de avaliação de fitness
                    if (calc_valid) begin
                        state <= SELECT;
                    end
                end

                SELECT: begin
                    // Seleção por ranking não-dominado
                    state <= CROSSOVER;
                end

                CROSSOVER: begin
                    if (crossover_done) begin
                        state <= MUTATE;
                    end
                end

                MUTATE: begin
                    if (mutation_done) begin
                        if (gen_counter < gen_max_input - 1) begin
                            gen_counter <= gen_counter + 1;
                            state <= EVALUATE;
                        end else begin
                            state <= FINISH;
                        end
                    end
                end

                FINISH: begin
                    valid_out <= 1;
                    state <= IDLE;
                end
            endcase
        end
    end

    assign done = (state == FINISH);
    assign best_score = best_score_val;
    assign m_axis_result_tvalid = valid_out;
endmodule
