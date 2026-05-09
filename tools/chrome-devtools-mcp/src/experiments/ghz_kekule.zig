//! Preparação GHZ usando Fronteiras de Grão Kekulé
//! Baseado na simetria espiral de Zhang et al.

const std = @import("std");
const qtl = @import("../quantum.zig");
const groove = @import("../drivers/groove_ge18.zig");
const kekule = @import("../drivers/graphene_kekule.zig");

pub fn prepareGHZ_Kekule(
    driver: *groove.GrooveDriver,
    qubits: [3]u8,         // Q1, Q2, Q3 em arranjo triangular
    domains: []kekule.KekuleDomain
) !void {
    // 1. Inicializar superposição local em cada qubit (Valley Superposition)
    for (qubits) |q| {
        try kekule.ValleyQubitOps.initializeValleySuperposition(
            try driver.getCobit(q),
            3.0 * kekule.GrapheneParams.LATTICE_CONST // Período de supressão
        );
    }

    // 2. Criar o emaranhamento "Valley-Braded"
    // A ordem espiral Kekulé impõe um phase-lock natural
    try driver.applyMicrowave(qubits[0], .HADAMARD);

    // Valley Exchange controlado pela fronteira de grão
    _ = try kekule.ValleyQubitOps.valleyExchange(domains[0], domains[1]); // CNOT Q1->Q2
    _ = try kekule.ValleyQubitOps.valleyExchange(domains[1], domains[2]); // CNOT Q2->Q3

    // 3. Aplicar "Winding Correction" baseado na textura do elo
    for (domains, 0..) |dom, i| {
        if (i >= 3) break;
        const correction = std.math.atan2(dom.bond_texture[1], dom.bond_texture[0]);
        try driver.applyMicrowave(qubits[i], .PHASE, correction);
    }

    std.log.info("Estado GHZ Kekulé preparado. Fase topologicamente protegida.", .{});
}
