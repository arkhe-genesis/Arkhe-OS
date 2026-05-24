// ═══════════════════════════════════════════════════════
// dma_engine.v — Leitura da FIFO e envio para PCIe
// ═══════════════════════════════════════════════════════
module dma_engine (
    input  wire         clk, rst_n,
    input  wire [127:0] fifo_dout,
    input  wire         fifo_empty,
    output reg          fifo_rd_en,
    output reg  [127:0] pcie_tx_data,
    output reg          pcie_tx_valid,
    input  wire         pcie_tx_ready
);
    reg [1:0] state;
    localparam IDLE = 2'b00, READ_FIFO = 2'b01, SEND = 2'b10;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state        <= IDLE;
            fifo_rd_en   <= 0;
            pcie_tx_data <= 0;
            pcie_tx_valid <= 0;
        end else begin
            case (state)
                IDLE: begin
                    fifo_rd_en   <= 0;
                    pcie_tx_valid <= 0;
                    if (!fifo_empty) begin
                        state      <= READ_FIFO;
                        fifo_rd_en <= 1;
                    end
                end
                READ_FIFO: begin
                    fifo_rd_en   <= 0;
                    pcie_tx_data <= fifo_dout;
                    pcie_tx_valid <= 1;
                    state        <= SEND;
                end
                SEND: begin
                    if (pcie_tx_ready) begin
                        pcie_tx_valid <= 0;
                        state         <= IDLE;
                    end
                end
            endcase
        end
    end
endmodule
