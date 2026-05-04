// ============================================================================
// mythos_axi_ctrl.sv
// AXI4-Lite Slave for Mythos Core Control Registers
// ============================================================================

`timescale 1ns / 1ps

module mythos_axi_ctrl #(
    parameter ADDR_WIDTH = 12,
    parameter DATA_WIDTH = 32
) (
    input  logic                   clk,
    input  logic                   rst_n,

    // AXI4-Lite Slave Interface
    input  logic [ADDR_WIDTH-1:0]  s_axi_awaddr,
    input  logic                   s_axi_awvalid,
    output logic                   s_axi_awready,
    input  logic [DATA_WIDTH-1:0]  s_axi_wdata,
    input  logic                   s_axi_wvalid,
    output logic                   s_axi_wready,
    output logic [1:0]             s_axi_bresp,
    output logic                   s_axi_bvalid,
    input  logic                   s_axi_bready,
    input  logic [ADDR_WIDTH-1:0]  s_axi_araddr,
    input  logic                   s_axi_arvalid,
    output logic                   s_axi_arready,
    output logic [DATA_WIDTH-1:0]  s_axi_rdata,
    output logic [1:0]             s_axi_rresp,
    output logic                   s_axi_rvalid,
    input  logic                   s_axi_rready,

    // Register Outputs
    output logic [31:0]            ctrl_reg,
    output logic [31:0]            loop_cfg_reg,
    input  logic [31:0]            status_reg,
    input  logic [31:0]            debug_reg,
    input  logic [31:0]            norm_reg
);

    // Register Map (Aligned with Driver)
    // 0x00: Control
    // 0x04: Loop Config
    // 0x08: Status (Read-Only)
    // 0x10: Debug  (Read-Only)
    // 0x14: Norm   (Read-Only)

    logic [31:0] regs [0:1]; // Only 0x00 and 0x04 are writable
    logic aw_en;

    assign ctrl_reg     = regs[0];
    assign loop_cfg_reg = regs[1];

    // AXI-Lite Write
    assign s_axi_awready = ~s_axi_bvalid && s_axi_awvalid && s_axi_wvalid && aw_en;
    assign s_axi_wready  = s_axi_awready;
    assign s_axi_bresp   = 2'b00;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            regs[0] <= 32'h0;
            regs[1] <= 32'h1;
            s_axi_bvalid <= 0;
            aw_en <= 1;
        end else begin
            if (s_axi_awvalid && s_axi_wvalid && aw_en) begin
                if (s_axi_awaddr[4:2] < 2) begin
                    regs[s_axi_awaddr[4:2]] <= s_axi_wdata;
                end
                s_axi_bvalid <= 1;
                aw_en <= 0;
            end
            if (s_axi_bready && s_axi_bvalid) begin
                s_axi_bvalid <= 0;
                aw_en <= 1;
            end
            // Auto-clear start bit
            if (regs[0][0]) regs[0][0] <= 1'b0;
        end
    end

    // AXI-Lite Read
    assign s_axi_arready = ~s_axi_rvalid && s_axi_arvalid;
    assign s_axi_rresp   = 2'b00;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axi_rvalid <= 0;
            s_axi_rdata  <= 0;
        end else begin
            if (s_axi_arvalid && !s_axi_rvalid) begin
                s_axi_rvalid <= 1;
                case (s_axi_araddr[4:2])
                    3'b000: s_axi_rdata <= regs[0];
                    3'b001: s_axi_rdata <= regs[1];
                    3'b010: s_axi_rdata <= status_reg;
                    3'b100: s_axi_rdata <= debug_reg;
                    3'b101: s_axi_rdata <= norm_reg;
                    default: s_axi_rdata <= 32'hDEADBEEF;
                endcase
            end else if (s_axi_rready && s_axi_rvalid) begin
                s_axi_rvalid <= 0;
            end
        end
    end

endmodule
