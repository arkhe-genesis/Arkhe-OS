# =============================================================================
# pinout_jesd204b.xdc — Zynq‑7000 (XC7Z045‑FFG900) to JESD204B DAC
# Target: AD9174 dual 16‑bit DAC, 4 lanes, 14 Gbps, JESD204B subclass 1
# =============================================================================

# ── JESD204B GTX transceivers (Bank 111, 4 lanes) ────────────────────────────
# Lane 0 (GTX_X0Y7)
set_property PACKAGE_PIN  AD9  [get_ports jesd_tx0_p]   ;# MGTTXP0_111
set_property PACKAGE_PIN  AD10 [get_ports jesd_tx0_n]   ;# MGTTXN0_111

# Lane 1 (GTX_X0Y8)
set_property PACKAGE_PIN  AF9  [get_ports jesd_tx1_p]   ;# MGTTXP1_111
set_property PACKAGE_PIN  AF10 [get_ports jesd_tx1_n]   ;# MGTTXN1_111

# Lane 2 (GTX_X0Y9)
set_property PACKAGE_PIN  AH9  [get_ports jesd_tx2_p]   ;# MGTTXP2_111
set_property PACKAGE_PIN  AH10 [get_ports jesd_tx2_n]   ;# MGTTXN2_111

# Lane 3 (GTX_X0Y10)
set_property PACKAGE_PIN  AJ9  [get_ports jesd_tx3_p]   ;# MGTTXP3_111
set_property PACKAGE_PIN  AJ10 [get_ports jesd_tx3_n]   ;# MGTTXN3_111

# Reference clock for GTX (156.25 MHz for 14 Gbps line rate)
set_property PACKAGE_PIN  AD11 [get_ports jesd_refclk_p]   ;# MGTREFCLKP0_111
set_property PACKAGE_PIN  AD12 [get_ports jesd_refclk_n]   ;# MGTREFCLKN0_111

# ── JESD204B SYSREF (Subclass 1 deterministic latency) ───────────────────────
set_property PACKAGE_PIN  AG15 [get_ports jesd_sysref_p]   ;# IO_L22N_T3_34
set_property PACKAGE_PIN  AH15 [get_ports jesd_sysref_n]   ;# IO_L22P_T3_34

# ── DAC SPI configuration bus (slow, no timing constraint) ───────────────────
set_property PACKAGE_PIN  AK19 [get_ports dac_spi_cs_n]    ;# IO_L12P_T1_34
set_property PACKAGE_PIN  AJ17 [get_ports dac_spi_sclk]    ;# IO_L12N_T1_34
set_property PACKAGE_PIN  AJ18 [get_ports dac_spi_mosi]    ;# IO_L13P_T2_34
set_property PACKAGE_PIN  AK18 [get_ports dac_spi_miso]    ;# IO_L13N_T2_34

# ── System clock 280 MHz differential (SYS_CLK) ──────────────────────────────
set_property PACKAGE_PIN  G15  [get_ports sys_clk_280_p]   ;# IO_L12P_T1_34 (example)
set_property PACKAGE_PIN  G14  [get_ports sys_clk_280_n]   ;# IO_L12N_T1_34

# ── Reset & GPIO ─────────────────────────────────────────────────────────────
set_property PACKAGE_PIN  C19  [get_ports pl_reset_n]      ;# IO_L1P_T0_34
set_property PACKAGE_PIN  B19  [get_ports heartbeat_led]   ;# IO_L1N_T0_34

# ── I/O Standard for high‑speed pins ─────────────────────────────────────────
set_property IOSTANDARD  LVDS     [get_ports jesd_sysref_p]
set_property IOSTANDARD  LVDS     [get_ports sys_clk_280_p]
set_property IOSTANDARD  LVCMOS33 [get_ports dac_spi_*]
set_property IOSTANDARD  LVCMOS33 [get_ports pl_reset_n]
set_property IOSTANDARD  LVCMOS33 [get_ports heartbeat_led]