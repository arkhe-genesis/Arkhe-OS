// ============================================================================
// mythos_core_top.sv
// Top-Level Integration of the Recurrent-Depth Transformer (Mythos Core)
// ============================================================================

`timescale 1ns / 1ps

module mythos_core_top #(
    parameter D_MODEL        = 256,
    parameter SEQ_LEN        = 64,
    parameter MLP_HIDDEN     = 1024,
    parameter DATA_WIDTH     = 16,
    parameter AXI_ADDR_WIDTH = 12,
    parameter AXI_DATA_WIDTH = 32
) (
    // Clock e Reset
    input  logic        clk,
    input  logic        rst_n,

    // AXI4-Lite Slave (Controle e Configuração)
    input  logic [AXI_ADDR_WIDTH-1:0] s_axi_awaddr,
    input  logic                      s_axi_awvalid,
    output logic                      s_axi_awready,
    input  logic [AXI_DATA_WIDTH-1:0] s_axi_wdata,
    input  logic                      s_axi_wvalid,
    output logic                      s_axi_wready,
    output logic [1:0]                s_axi_bresp,
    output logic                      s_axi_bvalid,
    input  logic                      s_axi_bready,
    input  logic [AXI_ADDR_WIDTH-1:0] s_axi_araddr,
    input  logic                      s_axi_arvalid,
    output logic                      s_axi_arready,
    output logic [AXI_DATA_WIDTH-1:0] s_axi_rdata,
    output logic [1:0]                s_axi_rresp,
    output logic                      s_axi_rvalid,
    input  logic                      s_axi_rready,

    // AXI4-Stream Slave (Embedding de Entrada 'e' / Cache Load)
    input  logic                     s_axis_tvalid,
    output logic                     s_axis_tready,
    input  logic [D_MODEL-1:0][DATA_WIDTH-1:0] s_axis_tdata,
    input  logic                     s_axis_tlast,

    // AXI4-Stream Master (Estado Latente 'h' de saída)
    output logic                     m_axis_tvalid,
    input  logic                     m_axis_tready,
    output logic [D_MODEL-1:0][DATA_WIDTH-1:0] m_axis_tdata,
    output logic                     m_axis_tlast,

    // Interrupção (Loop Concluído)
    output logic                     irq_done
);

    // -------------------------------------------------------------------------
    // Sinais Internos de Controle e Dados
    // -------------------------------------------------------------------------
    logic [31:0] ctrl_reg, loop_cfg_reg, status_reg, debug_reg, norm_reg;
    logic        core_start, core_done, cache_loaded;
    logic [31:0] loop_count, loop_iter;

    logic [D_MODEL-1:0][DATA_WIDTH-1:0] h_state, e_embedding, h_next;
    logic [D_MODEL-1:0][DATA_WIDTH-1:0] attention_out, mlp_out;

    // KV Cache
    logic [SEQ_LEN-1:0][D_MODEL-1:0][DATA_WIDTH-1:0] k_cache, v_cache;
    logic [5:0] cache_ptr;

    // -------------------------------------------------------------------------
    // Interface AXI4-Lite
    // -------------------------------------------------------------------------
    mythos_axi_ctrl #( .ADDR_WIDTH(AXI_ADDR_WIDTH) ) u_axi_ctrl (
        .clk(clk), .rst_n(rst_n),
        .s_axi_awaddr(s_axi_awaddr), .s_axi_awvalid(s_axi_awvalid), .s_axi_awready(s_axi_awready),
        .s_axi_wdata(s_axi_wdata), .s_axi_wvalid(s_axi_wvalid), .s_axi_wready(s_axi_wready),
        .s_axi_bresp(s_axi_bresp), .s_axi_bvalid(s_axi_bvalid), .s_axi_bready(s_axi_bready),
        .s_axi_araddr(s_axi_araddr), .s_axi_arvalid(s_axi_arvalid), .s_axi_arready(s_axi_arready),
        .s_axi_rdata(s_axi_rdata), .s_axi_rresp(s_axi_rresp), .s_axi_rvalid(s_axi_rvalid), .s_axi_rready(s_axi_rready),
        .ctrl_reg(ctrl_reg), .loop_cfg_reg(loop_cfg_reg), .status_reg(status_reg),
        .debug_reg(debug_reg), .norm_reg(norm_reg)
    );

    assign core_start = ctrl_reg[0];
    assign loop_count = loop_cfg_reg;
    assign status_reg = {30'b0, core_done, cache_loaded};
    assign irq_done   = core_done & ctrl_reg[2];
    assign debug_reg  = {24'b0, cache_ptr};

    // -------------------------------------------------------------------------
    // AXI4-Stream: Load Embedding 'e' and Populate KV Cache
    // -------------------------------------------------------------------------
    assign s_axis_tready = (state == IDLE);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cache_loaded <= 0; cache_ptr <= 0; e_embedding <= '0;
        end else if (s_axis_tvalid && s_axis_tready) begin
            e_embedding <= s_axis_tdata;
            k_cache[cache_ptr] <= s_axis_tdata;
            v_cache[cache_ptr] <= s_axis_tdata;
            if (s_axis_tlast) begin
                cache_loaded <= 1;
            end
            cache_ptr <= cache_ptr + 1;
        end
    end

    // -------------------------------------------------------------------------
    // Recurrent Loop FSM
    // -------------------------------------------------------------------------
    typedef enum {IDLE, ATTENTION, MLP_STAGE, NORM_CALC, UPDATE, DONE_STATE} state_t;
    state_t state, next_state;
    logic attn_start, attn_done, mlp_start, mlp_done;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE; loop_iter <= 0; h_state <= '0; core_done <= 0;
        end else begin
            state <= next_state;
            if (state == IDLE && core_start && cache_loaded) begin
                loop_iter <= 0; h_state <= e_embedding;
            end else if (state == UPDATE) begin
                h_state <= h_next; loop_iter <= loop_iter + 1;
            end
            core_done <= (state == DONE_STATE);
        end
    end

    always_comb begin
        next_state = state; attn_start = 0; mlp_start = 0;
        case (state)
            IDLE: if (core_start && cache_loaded) next_state = ATTENTION;
            ATTENTION: begin
                attn_start = 1; if (attn_done) next_state = MLP_STAGE;
            end
            MLP_STAGE: begin
                mlp_start = 1; if (mlp_done) next_state = NORM_CALC;
            end
            NORM_CALC: begin
                // In a real implementation, wait for pipelined norm tree
                next_state = UPDATE;
            end
            UPDATE: begin
                if (loop_iter == loop_count - 1) next_state = DONE_STATE;
                else next_state = ATTENTION;
            end
            DONE_STATE: if (!core_start) next_state = IDLE;
        endcase
    end

    attention_wrapper #( .D_MODEL(D_MODEL), .SEQ_LEN(SEQ_LEN) ) u_attn (
        .clk(clk), .rst_n(rst_n), .start(attn_start), .q_in(h_state),
        .k_cache(k_cache), .v_cache(v_cache), .attn_out(attention_out), .done(attn_done)
    );

    mlp_block #( .IN_DIM(D_MODEL), .OUT_DIM(D_MODEL) ) u_mlp (
        .clk(clk), .rst_n(rst_n), .start(mlp_start), .in_data(h_state),
        .out_data(mlp_out), .done(mlp_done)
    );

    // Pipelined Norm Adder Tree (Structural Placeholder)
    logic [31:0] norm_tree [0:D_MODEL*2-2];
    generate
        for (genvar i = 0; i < D_MODEL; i++) begin : gen_norm_sq
            always_ff @(posedge clk) norm_tree[i] <= h_state[i] * h_state[i];
        end
        for (genvar j = 0; j < D_MODEL-1; j++) begin : gen_norm_tree
            always_ff @(posedge clk) norm_tree[D_MODEL+j] <= norm_tree[2*j] + norm_tree[2*j+1];
        end
    endgenerate
    assign norm_reg = norm_tree[D_MODEL*2-2];

    generate
        for (genvar i = 0; i < D_MODEL; i++) begin : gen_res
            always_ff @(posedge clk) if (state == NORM_CALC) h_next[i] <= h_state[i] + attention_out[i] + mlp_out[i];
        end
    endgenerate

    assign m_axis_tvalid = (state == DONE_STATE);
    assign m_axis_tdata  = h_state;
    assign m_axis_tlast  = 1'b1;

endmodule
