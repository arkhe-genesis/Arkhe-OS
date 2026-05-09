//! Driver Heterostrutura Germanium/Grafeno (Van der Waals Stack)
//! Integração Bloco #172 (Ge-18) + Bloco #173 (Gr-Kekulé)

const std = @import("std");
const groove = @import("groove_ge18.zig");
const kekule = @import("graphene_kekule.zig");
const qtl = @import("../quantum.zig");

pub const HeteroStackConfig = struct {
    pub const TWIST_ANGLE = 1.1; // graus
    pub const INTERLAYER_DISTANCE = 0.34e-9; // nm
    pub const BARRIER_HEIGHT = 0.25; // eV
};

pub const GeGrInterface = struct {
    ge_driver: groove.GrooveDriver,
    gr_scanner: kekule.STMScanner,
    sheet_map: [8]kekule.KekuleDomain = undefined,

    pub fn init(self: *GeGrInterface, vault: *qtl.Vault) !void {
        std.log.info("Inicializando heterostrutura Ge/Gr...", .{});

        try self.ge_driver.init(vault);

        const domains = try self.gr_scanner.mapGrainBoundary(
            .{ -50e-9, 50e-9 },
            .{ -10e-9, 10e-9 },
            0.5e-9,
        );
        defer std.heap.page_allocator.free(domains);

        for (domains, 0..) |domain, i| {
            if (i >= 4) break;
            const sheet_id: usize = if (domain.chirality > 0) i * 2 else i * 2 + 1;
            if (sheet_id < 8) {
                self.sheet_map[sheet_id] = domain;
                std.log.info("Domínio Kekulé {} mapeado para SHEET_{}", .{ domain.chirality, sheet_id });
            }
        }
    }

    pub fn spinToValleyTeleport(
        self: *GeGrInterface,
        ge_qubit_idx: u8,
        target_sheet: u8,
    ) !qtl.COBIT {
        var spin_cobit = try self.ge_driver.getCobit(ge_qubit_idx);

        const barrier = HeteroStackConfig.BARRIER_HEIGHT;
        const tau = spin_cobit.coherence;
        const tunnel_prob = std.math.exp(-barrier / (tau * tau));

        if (tunnel_prob < 0.70) { // Relaxed for prototype
            return error.TunnelBarrierTooHigh;
        }

        const kek_domain = self.sheet_map[target_sheet];
        try self.gr_scanner.suppressKekuleOrder(kek_domain, 0.1);

        var valley_cobit = kek_domain.toValleyCobit();
        valley_cobit.phase = spin_cobit.phase;

        try qtl.AkashaLog(.{
            .event = .SPIN_VALLEY_TELEPORT,
            .source = .{ .substrate = .GERMANIUM, .qubit = ge_qubit_idx },
            .dest = .{ .substrate = .GRAPHENE_KEKULE, .sheet = target_sheet },
            .fidelity = tunnel_prob,
            .barrier_transparency = barrier,
        });

        return valley_cobit;
    }

    pub fn prepareHybridGHZ(self: *GeGrInterface) ![3]qtl.COBIT {
        try self.ge_driver.initializeAll();
        const q7 = try self.ge_driver.getCobit(7);
        _ = try self.ge_driver.getCobit(9);

        try self.ge_driver.applyCZ(7, 9);

        var valley_q = try self.spinToValleyTeleport(9, 5);
        var aux_valley = try self.spinToValleyTeleport(10, 5);

        const J_valley = try kekule.ValleyQubitOps.valleyExchange(
            self.sheet_map[5],
            self.sheet_map[5]
        );

        try kekule.ValleyQubitOps.applyValleyCZ(&valley_q, &aux_valley, J_valley);

        return .{ q7, valley_q, aux_valley };
    }
};
