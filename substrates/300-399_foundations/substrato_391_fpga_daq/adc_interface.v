// ═══════════════════════════════════════════════════════
// adc_interface.v — Deserializador LVDS para ADC 12‑bit
// ═══════════════════════════════════════════════════════
module adc_interface (
    input  wire        clk_p, clk_n,
    input  wire [11:0] data_p, data_n,
    input  wire        or_p, or_n,
    input  wire        rst_n,
    output reg         adc_clk,
    output reg  [11:0] adc_data,
    output reg         adc_or
);
    // BUFR para divisão do relógio e deserialização
    wire clk_bufr;
    BUFR #(.BUFR_DIVIDE("2")) u_bufr (
        .I   (clk_p),
        .O   (clk_bufr),
        .CE  (1'b1),
        .CLR (1'b0)
    );

    always @(posedge clk_bufr or negedge rst_n) begin
        if (!rst_n) begin
            adc_clk  <= 0;
            adc_data <= 0;
            adc_or   <= 0;
        end else begin
            adc_clk  <= clk_bufr;
            // Amostragem simples (IDDR recomendado em produção)
            adc_data <= {data_p[11] ^ data_n[11],
                         data_p[10] ^ data_n[10],
                         data_p[9]  ^ data_n[9],
                         data_p[8]  ^ data_n[8],
                         data_p[7]  ^ data_n[7],
                         data_p[6]  ^ data_n[6],
                         data_p[5]  ^ data_n[5],
                         data_p[4]  ^ data_n[4],
                         data_p[3]  ^ data_n[3],
                         data_p[2]  ^ data_n[2],
                         data_p[1]  ^ data_n[1],
                         data_p[0]  ^ data_n[0]};
            adc_or   <= or_p ^ or_n;
        end
    end
endmodule
