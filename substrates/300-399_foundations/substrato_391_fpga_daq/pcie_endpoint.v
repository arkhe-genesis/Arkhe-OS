// ═══════════════════════════════════════════════════════
// pcie_endpoint.v — Wrapper do PCIe Gen2 x4
// Utiliza o core "7 Series Integrated Block for PCIe"
// ═══════════════════════════════════════════════════════
module pcie_endpoint (
    input  wire        refclk_p, refclk_n,
    input  wire        rst_n,
    output wire [3:0]  tx_p, tx_n,
    input  wire [3:0]  rx_p, rx_n,
    input  wire [127:0] user_tx_data,
    input  wire        user_tx_valid,
    output wire        user_tx_ready,
    output wire        user_clk
);
    // Sinais do core PCIe (apenas TX simplificado)
    wire        cfg_aer_interrupt_msgnum;
    wire [63:0]  cfg_dsn;

    // Instanciação do IP Xilinx (parâmetros reais)
    pcie_7x_v1_1 #(
        .PL_FAST_TRAIN      ("TRUE"),
        .PCI_EXP_GEN2       ("TRUE"),
        .LINK_CAP_MAX_LINK_WIDTH(4)
    ) u_pcie_core (
        .sys_clk_p          (refclk_p),
        .sys_clk_n          (refclk_n),
        .sys_rst_n          (rst_n),
        .pci_exp_txp        (tx_p),
        .pci_exp_txn        (tx_n),
        .pci_exp_rxp        (rx_p),
        .pci_exp_rxn        (rx_n),
        .user_clk_out       (user_clk),
        .user_reset_out     (),
        .user_lnk_up        (),
        // Interface de transmissão AXI‑Stream (TX)
        .s_axis_tx_tdata    (user_tx_data),
        .s_axis_tx_tvalid   (user_tx_valid),
        .s_axis_tx_tready   (user_tx_ready),
        .s_axis_tx_tlast    (1'b1),
        .s_axis_tx_tkeep    (16'hFFFF),
        .s_axis_tx_tuser    (4'h0)
    );
endmodule
