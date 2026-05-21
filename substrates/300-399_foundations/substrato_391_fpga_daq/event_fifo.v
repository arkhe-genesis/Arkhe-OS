// ═══════════════════════════════════════════════════════
// event_fifo.v — FIFO 128‑bit × 512 profundidade
// ═══════════════════════════════════════════════════════
module event_fifo (
    input  wire         clk, rst_n,
    input  wire [127:0] din,
    input  wire         wr_en,
    input  wire         rd_en,
    output wire [127:0] dout,
    output wire         empty,
    output wire         full
);
    // Bloco RAM + ponteiros circulares
    reg [127:0] mem [0:511];
    reg [9:0]   wr_ptr, rd_ptr;
    reg [10:0]  count;  // até 512

    assign empty = (count == 0);
    assign full  = (count == 512);
    assign dout  = mem[rd_ptr];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= 0;
            rd_ptr <= 0;
            count  <= 0;
        end else begin
            if (wr_en && !full) begin
                mem[wr_ptr] <= din;
                wr_ptr      <= wr_ptr + 1;
                count       <= count + 1;
            end
            if (rd_en && !empty) begin
                rd_ptr <= rd_ptr + 1;
                count  <= count - 1;
            end
        end
    end
endmodule
