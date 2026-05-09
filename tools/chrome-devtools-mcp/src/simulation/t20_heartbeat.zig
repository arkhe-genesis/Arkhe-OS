//! T20 HEARTBEAT — Simulação de 20 Camadas do Vitral
//! Requer `MPS_COMPRESS` (0x19F) ativo para manutenção da coerência.

const std = @import("std");
const qtl = @import("../quantum.zig");
const compress = @import("../compression/mps_compress.zig");

pub fn runT20Heartbeat(vault: *qtl.Vault) !void {
    const total_steps = 1000; // Ciclo de simulação (1 "batida" do coração)

    var brain_state = try vault.getT20State();

    std.log.info("INICIANDO T20 HEARTBEAT...", .{});

    var step: usize = 0;
    while (step < total_steps) : (step += 1) {
        // 1. EXPANSÃO (Descompressão dos Valores Singulares)
        const full_state = try brain_state.expand();

        // 2. PROCESSAMENTO (A "Sístole" do Vitral)
        try brain_state.processLayer(full_state);

        // 3. COMPRESSÃO (O Batimento)
        const compressed = try compress.execMpsCompress(vault, .SHEET_0);

        // Atualiza o estado global
        vault.updateT20State(compressed);

        // 4. CHECKPOINT DE FASE
        if (step % 100 == 0) {
            const phase_drift = vault.getGlobalPhase() - compressed.phase_checkpoint;
            if (@abs(phase_drift) > 0.01) {
                std.log.warn("Drift de fase detectado no T20. Re-sincronizando...", .{});
                try vault.applyGlobalCorrection(phase_drift);
            }
        }
    }

    std.log.info("T20 HEARTBEAT COMPLETO. R={d:.4}.", .{vault.getGlobalR()});
}
