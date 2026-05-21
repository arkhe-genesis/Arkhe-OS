// ═══════════════════════════════════════════════════════
// ruview_rad_top.v — Top‑Level do DAQ para Fibra Ótica
// Plataforma: Xilinx Artix‑7 / Kintex‑7
// ═══════════════════════════════════════════════════════
`timescale 1ns / 1ps

module ruview_rad_top (
    // ADC Interface (LVDS)
    input  wire         adc_clk_p, adc_clk_n,    // 500 MHz DDR
    input  wire [11:0]  adc_data_p, adc_data_n,  // 12 canais LVDS
    input  wire         adc_or_p, adc_or_n,      // Over‑range

    // PCIe Interface
    input  wire         pcie_refclk_p, pcie_refclk_n, // 100 MHz
    output wire [3:0]   pcie_tx_p, pcie_tx_n,
    input  wire [3:0]   pcie_rx_p, pcie_rx_n,

    // Sistema
    input  wire         sys_clk_200_p, sys_clk_200_n,
    input  wire         rst_n,

    // Debug / Status
    output wire [3:0]   led,
    output wire         pulse_out  // Saída de monitoração de pulso
);

    // ── Sinais internos ──
    wire              adc_clk;
    wire [11:0]       adc_data;
    wire              adc_or;

    wire              pulse_detected;
    wire [15:0]       pulse_amplitude;
    wire [31:0]       pulse_integral;
    wire [63:0]       pulse_timestamp;

    wire [127:0]      event_data;
    wire              event_valid;
    wire              event_ready;

    // ── Instanciação dos submódulos ──

    // 1. Interface ADC
    adc_interface u_adc (
        .clk_p      (adc_clk_p),
        .clk_n      (adc_clk_n),
        .data_p     (adc_data_p),
        .data_n     (adc_data_n),
        .or_p       (adc_or_p),
        .or_n       (adc_or_n),
        .rst_n      (rst_n),
        .adc_clk    (adc_clk),
        .adc_data   (adc_data),
        .adc_or     (adc_or)
    );

    // 2. Detetor de Pulsos Cherenkov
    pulse_detector u_pulse (
        .clk           (adc_clk),
        .rst_n         (rst_n),
        .adc_data      (adc_data),
        .threshold     (12'd200),       // Limiar programável
        .pulse_out     (pulse_out),
        .amplitude     (pulse_amplitude),
        .integral      (pulse_integral),
        .timestamp     (pulse_timestamp),
        .detected      (pulse_detected)
    );

    // 3. Empacotador de Eventos
    event_packer u_packer (
        .clk           (adc_clk),
        .rst_n         (rst_n),
        .pulse_detected(pulse_detected),
        .amplitude     (pulse_amplitude),
        .integral      (pulse_integral),
        .timestamp     (pulse_timestamp),
        .event_data    (event_data),
        .event_valid   (event_valid),
        .event_ready   (event_ready)
    );

    // 4. FIFO de Eventos
    wire [127:0] fifo_dout;
    wire         fifo_empty;
    wire         fifo_full;

    event_fifo u_fifo (
        .clk      (adc_clk),
        .rst_n    (rst_n),
        .din      (event_data),
        .wr_en    (event_valid),
        .rd_en    (dma_rd_en),
        .dout     (fifo_dout),
        .empty    (fifo_empty),
        .full     (fifo_full)
    );

    // 5. Motor de DMA
    wire dma_rd_en;

    dma_engine u_dma (
        .clk           (adc_clk),
        .rst_n         (rst_n),
        .fifo_dout     (fifo_dout),
        .fifo_empty    (fifo_empty),
        .fifo_rd_en    (dma_rd_en),
        .pcie_tx_data  (tx_data),
        .pcie_tx_valid (tx_valid),
        .pcie_tx_ready (tx_ready)
    );

    // 6. PCIe Endpoint (Xilinx 7 Series Integrated Block)
    wire [127:0] tx_data;
    wire         tx_valid;
    wire         tx_ready;

    pcie_endpoint u_pcie (
        .refclk_p     (pcie_refclk_p),
        .refclk_n     (pcie_refclk_n),
        .rst_n        (rst_n),
        .tx_p         (pcie_tx_p),
        .tx_n         (pcie_tx_n),
        .rx_p         (pcie_rx_p),
        .rx_n         (pcie_rx_n),
        .user_tx_data (tx_data),
        .user_tx_valid(tx_valid),
        .user_tx_ready(tx_ready),
        .user_clk     (adc_clk)        // Domínio de relógio único simplificado
    );

    // ── Leds de status ──
    assign led[0] = pulse_detected;
    assign led[1] = ~fifo_empty;
    assign led[2] = fifo_full;
    assign led[3] = tx_valid;

endmodule
