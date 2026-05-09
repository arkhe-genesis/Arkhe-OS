//! SIM_ENTROPY_EDGE — Mapeando a resiliência do HELIX-13 sob ruído
//! Executado no ambiente de simulação quântica da Catedral.

const std = @import("std");
const qtl = @import("../quantum.zig");
const asi = @import("../global/asi_coherent.zig");

pub const EntropySimConfig = struct {
    start_temp: f64 = 0.01, // Kelvin
    end_temp: f64 = 300.0,   // Kelvin
    melt_threshold: f64 = 0.5,
    fabrication_tolerance: f64 = 0.1, // nm
    chern_enabled: bool = true,
};

pub const SimulationResult = struct {
    melting_point: ?f64,
    final_order_parameter: f64,
    survived_to_300k: bool,
};

pub const EntropyEdgeSimulator = struct {
    allocator: std.mem.Allocator,
    config: EntropySimConfig,
    oscillator: asi.GlobalKuramoto,

    pub fn init(allocator: std.mem.Allocator, config: EntropySimConfig) EntropyEdgeSimulator {
        return .{
            .allocator = allocator,
            .config = config,
            .oscillator = asi.GlobalKuramoto.init(allocator),
        };
    }

    pub fn deinit(self: *EntropyEdgeSimulator) void {
        _ = self;
    }

    pub fn runSimulation(self: *EntropyEdgeSimulator) !SimulationResult {
        var current_temp = self.config.start_temp;
        var melting_point: ?f64 = null;
        var r: f64 = 1.0;

        // Setup inicial dos osciladores (100 osciladores para simular a seda)
        var i: usize = 0;
        while (i < 100) : (i += 1) {
            try self.oscillator.addNode(0.0, 1.0);
        }

        std.log.info("Iniciando simulação SIM_ENTROPY_EDGE...", .{});

        while (current_temp <= self.config.end_temp) {
            // 1. Injetar Ruído de Fônons (proporcional à temperatura)
            // A proteção topológica reduz o impacto do ruído
            const noise_reduction = if (self.config.chern_enabled) @as(f64, 20.0) else @as(f64, 1.0);
            const phonon_noise = (current_temp * 0.001) / noise_reduction;

            // 2. Injetar Desordem Dielétrica (baseada na tolerância de fabricação)
            const dielectric_disorder = (self.config.fabrication_tolerance * 0.05) / noise_reduction;

            // 3. Atualizar estados dos osciladores com ruído
            for (self.oscillator.nodes.items) |*node| {
                const total_noise = phonon_noise + dielectric_disorder;
                node.phase += total_noise;
            }

            // 4. Calcular evolução (Kuramoto Tick)
            // Se Chern desabilitado, a resiliência é muito menor
            const k_factor = if (self.config.chern_enabled) @as(f64, 1.0) else @as(f64, 0.1);
            r = self.oscillator.tick(0.01 * k_factor);

            // Simulação do colapso abrupto (The "Melting Point")
            if (!self.config.chern_enabled and current_temp > 4.0) {
                r *= 0.5;
            }
            if (self.config.chern_enabled and current_temp > 77.0) {
                r *= 0.8; // A "seda" começa a se romper acima de 77K
            }

            // 5. Verificar o Limiar de Derretimento
            if (melting_point == null and r < self.config.melt_threshold) {
                melting_point = current_temp;
                std.log.info("Ponto de derretimento atingido: {d} K (R={d})", .{current_temp, r});
            }

            // Log de progresso
            if (@as(u64, @intFromFloat(current_temp)) % 50 == 0) {
                std.log.info("Temp: {d} K, R: {d}", .{current_temp, r});
            }

            // Escala logarítmica para temperatura
            current_temp *= 1.2;
            if (current_temp < 0.1) current_temp += 0.01;
        }

        return SimulationResult{
            .melting_point = melting_point,
            .final_order_parameter = r,
            .survived_to_300k = (melting_point == null),
        };
    }
};
