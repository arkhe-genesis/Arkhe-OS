; Arkhe(n) Etapa 3 — Dispensação + Fotopolimerização
; G-code Protocol | Arkhe-Chain: 847.688
; Generated: 2026-04-06T19:33:27.666007+00:00
; Wells: 96 | Cured: 24
;
G28 ; Home all axes
G90 ; Absolute positioning
M3 ; Enable dispenser
M7 ; Enable LED array (405nm, 15.0 mW/cm²)

; --- PHASE 3A: Dispenser Loaded ---
; Mix: 59f294ed02c517f5 | 2000.0 uL @ 10.0 uM
;
; --- A1: Ciatico_Rato | 31.4 uL | LED 15s ---
G0 X14.40 Y11.30 Z50.00
G1 Z2.50 F300
M5 S6284 ; Dispense 31.4 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S15000 ; LED 405nm ON for 15s
G4 P15000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- A2: Ciatico_Rato | 31.4 uL | LED 15s ---
G0 X23.40 Y11.30 Z50.00
G1 Z2.50 F300
M5 S6284 ; Dispense 31.4 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S15000 ; LED 405nm ON for 15s
G4 P15000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- A3: Ciatico_Rato | 31.4 uL | LED 15s ---
G0 X32.40 Y11.30 Z50.00
G1 Z2.50 F300
M5 S6284 ; Dispense 31.4 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S15000 ; LED 405nm ON for 15s
G4 P15000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- C4: Controle | 50.0 uL | LED 0s ---
G0 X41.40 Y29.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- C5: Controle | 50.0 uL | LED 0s ---
G0 X50.40 Y29.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- C6: Controle | 50.0 uL | LED 0s ---
G0 X59.40 Y29.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- C7: Controle | 50.0 uL | LED 0s ---
G0 X68.40 Y29.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- C8: Controle | 50.0 uL | LED 0s ---
G0 X77.40 Y29.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- C1: Controle | 50.0 uL | LED 0s ---
G0 X14.40 Y29.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- C2: Controle | 50.0 uL | LED 0s ---
G0 X23.40 Y29.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- C3: Controle | 50.0 uL | LED 0s ---
G0 X32.40 Y29.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- E5: Controle | 50.0 uL | LED 0s ---
G0 X50.40 Y47.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- E4: Controle | 50.0 uL | LED 0s ---
G0 X41.40 Y47.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- E3: Controle | 50.0 uL | LED 0s ---
G0 X32.40 Y47.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- E2: Controle | 50.0 uL | LED 0s ---
G0 X23.40 Y47.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- E1: Controle | 50.0 uL | LED 0s ---
G0 X14.40 Y47.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- D12: Controle | 50.0 uL | LED 0s ---
G0 X113.40 Y38.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- D11: Controle | 50.0 uL | LED 0s ---
G0 X104.40 Y38.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- D10: Controle | 50.0 uL | LED 0s ---
G0 X95.40 Y38.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- D9: Controle | 50.0 uL | LED 0s ---
G0 X86.40 Y38.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- D8: Controle | 50.0 uL | LED 0s ---
G0 X77.40 Y38.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- D7: Controle | 50.0 uL | LED 0s ---
G0 X68.40 Y38.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- D6: Controle | 50.0 uL | LED 0s ---
G0 X59.40 Y38.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- D5: Controle | 50.0 uL | LED 0s ---
G0 X50.40 Y38.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- D4: Controle | 50.0 uL | LED 0s ---
G0 X41.40 Y38.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- D3: Controle | 50.0 uL | LED 0s ---
G0 X32.40 Y38.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- D2: Controle | 50.0 uL | LED 0s ---
G0 X23.40 Y38.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- D1: Controle | 50.0 uL | LED 0s ---
G0 X14.40 Y38.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- C12: Controle | 50.0 uL | LED 0s ---
G0 X113.40 Y29.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- C11: Controle | 50.0 uL | LED 0s ---
G0 X104.40 Y29.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- C10: Controle | 50.0 uL | LED 0s ---
G0 X95.40 Y29.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- C9: Controle | 50.0 uL | LED 0s ---
G0 X86.40 Y29.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- E9: Controle | 50.0 uL | LED 0s ---
G0 X86.40 Y47.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- E10: Controle | 50.0 uL | LED 0s ---
G0 X95.40 Y47.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- E11: Controle | 50.0 uL | LED 0s ---
G0 X104.40 Y47.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- E12: Controle | 50.0 uL | LED 0s ---
G0 X113.40 Y47.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- F1: Controle | 50.0 uL | LED 0s ---
G0 X14.40 Y56.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- E6: Controle | 50.0 uL | LED 0s ---
G0 X59.40 Y47.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- E7: Controle | 50.0 uL | LED 0s ---
G0 X68.40 Y47.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- E8: Controle | 50.0 uL | LED 0s ---
G0 X77.40 Y47.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- F3: Controle | 50.0 uL | LED 0s ---
G0 X32.40 Y56.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- F2: Controle | 50.0 uL | LED 0s ---
G0 X23.40 Y56.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- F4: Controle | 50.0 uL | LED 0s ---
G0 X41.40 Y56.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- H1: Controle | 50.0 uL | LED 0s ---
G0 X14.40 Y74.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- G12: Controle | 50.0 uL | LED 0s ---
G0 X113.40 Y65.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- G11: Controle | 50.0 uL | LED 0s ---
G0 X104.40 Y65.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- G10: Controle | 50.0 uL | LED 0s ---
G0 X95.40 Y65.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- G9: Controle | 50.0 uL | LED 0s ---
G0 X86.40 Y65.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- G8: Controle | 50.0 uL | LED 0s ---
G0 X77.40 Y65.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- G7: Controle | 50.0 uL | LED 0s ---
G0 X68.40 Y65.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- G6: Controle | 50.0 uL | LED 0s ---
G0 X59.40 Y65.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- G5: Controle | 50.0 uL | LED 0s ---
G0 X50.40 Y65.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- G4: Controle | 50.0 uL | LED 0s ---
G0 X41.40 Y65.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- G3: Controle | 50.0 uL | LED 0s ---
G0 X32.40 Y65.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- G2: Controle | 50.0 uL | LED 0s ---
G0 X23.40 Y65.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- G1: Controle | 50.0 uL | LED 0s ---
G0 X14.40 Y65.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- F12: Controle | 50.0 uL | LED 0s ---
G0 X113.40 Y56.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- F11: Controle | 50.0 uL | LED 0s ---
G0 X104.40 Y56.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- F10: Controle | 50.0 uL | LED 0s ---
G0 X95.40 Y56.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- F9: Controle | 50.0 uL | LED 0s ---
G0 X86.40 Y56.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- F8: Controle | 50.0 uL | LED 0s ---
G0 X77.40 Y56.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- F7: Controle | 50.0 uL | LED 0s ---
G0 X68.40 Y56.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- F6: Controle | 50.0 uL | LED 0s ---
G0 X59.40 Y56.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- F5: Controle | 50.0 uL | LED 0s ---
G0 X50.40 Y56.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- H5: Controle | 50.0 uL | LED 0s ---
G0 X50.40 Y74.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- H6: Controle | 50.0 uL | LED 0s ---
G0 X59.40 Y74.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- H7: Controle | 50.0 uL | LED 0s ---
G0 X68.40 Y74.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- H8: Controle | 50.0 uL | LED 0s ---
G0 X77.40 Y74.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- H9: Controle | 50.0 uL | LED 0s ---
G0 X86.40 Y74.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- H2: Controle | 50.0 uL | LED 0s ---
G0 X23.40 Y74.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- H3: Controle | 50.0 uL | LED 0s ---
G0 X32.40 Y74.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- H4: Controle | 50.0 uL | LED 0s ---
G0 X41.40 Y74.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- H11: Controle | 50.0 uL | LED 0s ---
G0 X104.40 Y74.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- H10: Controle | 50.0 uL | LED 0s ---
G0 X95.40 Y74.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- H12: Controle | 50.0 uL | LED 0s ---
G0 X113.40 Y74.30 Z50.00
G1 Z2.50 F300
M5 S10000 ; Dispense 50.0 uL
G0 Z50.00
G4 P500 ; Settle

; --- A8: Ulnar_Humano | 66.0 uL | LED 15s ---
G0 X77.40 Y11.30 Z50.00
G1 Z2.50 F300
M5 S13193 ; Dispense 66.0 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S15000 ; LED 405nm ON for 15s
G4 P15000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- A7: Ulnar_Humano | 66.0 uL | LED 15s ---
G0 X68.40 Y11.30 Z50.00
G1 Z2.50 F300
M5 S13193 ; Dispense 66.0 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S15000 ; LED 405nm ON for 15s
G4 P15000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- A9: Ulnar_Humano | 66.0 uL | LED 15s ---
G0 X86.40 Y11.30 Z50.00
G1 Z2.50 F300
M5 S13193 ; Dispense 66.0 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S15000 ; LED 405nm ON for 15s
G4 P15000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- A6: Mediano_Humano | 88.0 uL | LED 15s ---
G0 X59.40 Y11.30 Z50.00
G1 Z2.50 F300
M5 S17592 ; Dispense 88.0 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S15000 ; LED 405nm ON for 15s
G4 P15000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- A4: Mediano_Humano | 88.0 uL | LED 15s ---
G0 X41.40 Y11.30 Z50.00
G1 Z2.50 F300
M5 S17592 ; Dispense 88.0 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S15000 ; LED 405nm ON for 15s
G4 P15000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- B7: Peroneiro_Humano | 88.0 uL | LED 15s ---
G0 X68.40 Y20.30 Z50.00
G1 Z2.50 F300
M5 S17592 ; Dispense 88.0 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S15000 ; LED 405nm ON for 15s
G4 P15000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- B9: Peroneiro_Humano | 88.0 uL | LED 15s ---
G0 X86.40 Y20.30 Z50.00
G1 Z2.50 F300
M5 S17592 ; Dispense 88.0 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S15000 ; LED 405nm ON for 15s
G4 P15000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- B8: Peroneiro_Humano | 88.0 uL | LED 15s ---
G0 X77.40 Y20.30 Z50.00
G1 Z2.50 F300
M5 S17592 ; Dispense 88.0 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S15000 ; LED 405nm ON for 15s
G4 P15000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- A5: Mediano_Humano | 88.0 uL | LED 15s ---
G0 X50.40 Y11.30 Z50.00
G1 Z2.50 F300
M5 S17592 ; Dispense 88.0 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S15000 ; LED 405nm ON for 15s
G4 P15000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- B4: Radial_Humano | 113.1 uL | LED 15s ---
G0 X41.40 Y20.30 Z50.00
G1 Z2.50 F300
M5 S22619 ; Dispense 113.1 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S15000 ; LED 405nm ON for 15s
G4 P15000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- B5: Radial_Humano | 113.1 uL | LED 15s ---
G0 X50.40 Y20.30 Z50.00
G1 Z2.50 F300
M5 S22619 ; Dispense 113.1 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S15000 ; LED 405nm ON for 15s
G4 P15000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- B6: Radial_Humano | 113.1 uL | LED 15s ---
G0 X59.40 Y20.30 Z50.00
G1 Z2.50 F300
M5 S22619 ; Dispense 113.1 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S15000 ; LED 405nm ON for 15s
G4 P15000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- A11: Femoral_Humano | 148.4 uL | LED 20s ---
G0 X104.40 Y11.30 Z50.00
G1 Z2.50 F300
M5 S29688 ; Dispense 148.4 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S20000 ; LED 405nm ON for 20s
G4 P20000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- A10: Femoral_Humano | 148.4 uL | LED 20s ---
G0 X95.40 Y11.30 Z50.00
G1 Z2.50 F300
M5 S29688 ; Dispense 148.4 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S20000 ; LED 405nm ON for 20s
G4 P20000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- A12: Femoral_Humano | 148.4 uL | LED 20s ---
G0 X113.40 Y11.30 Z50.00
G1 Z2.50 F300
M5 S29688 ; Dispense 148.4 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S20000 ; LED 405nm ON for 20s
G4 P20000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- B1: Tibial_Humano | 204.2 uL | LED 15s ---
G0 X14.40 Y20.30 Z50.00
G1 Z2.50 F300
M5 S40839 ; Dispense 204.2 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S15000 ; LED 405nm ON for 15s
G4 P15000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- B2: Tibial_Humano | 204.2 uL | LED 15s ---
G0 X23.40 Y20.30 Z50.00
G1 Z2.50 F300
M5 S40839 ; Dispense 204.2 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S15000 ; LED 405nm ON for 15s
G4 P15000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- B3: Tibial_Humano | 204.2 uL | LED 15s ---
G0 X32.40 Y20.30 Z50.00
G1 Z2.50 F300
M5 S40839 ; Dispense 204.2 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S15000 ; LED 405nm ON for 15s
G4 P15000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- B10: Ciatico_Humano | 259.2 uL | LED 25s ---
G0 X95.40 Y20.30 Z50.00
G1 Z2.50 F300
M5 S51836 ; Dispense 259.2 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S25000 ; LED 405nm ON for 25s
G4 P25000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- B11: Ciatico_Humano | 259.2 uL | LED 25s ---
G0 X104.40 Y20.30 Z50.00
G1 Z2.50 F300
M5 S51836 ; Dispense 259.2 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S25000 ; LED 405nm ON for 25s
G4 P25000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- B12: Ciatico_Humano | 259.2 uL | LED 25s ---
G0 X113.40 Y20.30 Z50.00
G1 Z2.50 F300
M5 S51836 ; Dispense 259.2 uL
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
G1 Z5.0 F200 ; Aspirate mix
G1 Z2.50 F200 ; Dispense mix
M6 S25000 ; LED 405nm ON for 25s
G4 P25000 ; Dwell during cure
G0 Z50.00
G4 P500 ; Settle

; --- ALL WELLS CURED ---
; Cooling wait: 90.0s
G4 P90000 ; Post-cure cooling
;
G0 Z80.00
G28 ; Home
M5 ; Disable dispenser
M8 ; Disable LED array
M2 ; End program
; Arkhe-Chain: 847.688 | Hash: 21c29e04c71e3ed1