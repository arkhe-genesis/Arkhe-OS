// src/materials/living_glass.zig
//! Vidro Vivo Eletrocrômico — A Pele da Catedral
//! Baseado em Jeong et al., Nanophotonics 2026, e70062

const std = @import("std");

pub const MaterialType = enum {
    CONDUCTING_POLYMER, // PANI, PEDOT:PSS
    METAL_OXIDE,        // WO3, V2O5
    PLASMONIC_METAL,    // Ag, Cu
};

pub const PixelState = struct {
    oxidation_level: f64, // 0.0 to 1.0
    intercalation_density: f64,
    metal_nucleation: f64,
    refractive_index: std.math.Complex(f64),
};

pub const ElectrochemicalPixel = struct {
    id: u32,
    material: MaterialType,
    state: PixelState,
    coherence: f64,

    pub fn init(id: u32, material: MaterialType) ElectrochemicalPixel {
        return .{
            .id = id,
            .material = material,
            .state = .{
                .oxidation_level = 0.0,
                .intercalation_density = 0.0,
                .metal_nucleation = 0.0,
                .refractive_index = std.math.Complex(f64).init(1.5, 0.0),
            },
            .coherence = 1.0,
        };
    }

    /// Modula τ (criticalidade) via dopagem eletroquímica
    pub fn tuneTau(self: *ElectrochemicalPixel, voltage: f64) void {
        // Simula mudança no estado de oxidação
        self.state.oxidation_level = std.math.clamp(voltage, 0.0, 1.0);
        // Atualiza parte imaginária do índice de refração (k - absorção)
        self.state.refractive_index.im = self.state.oxidation_level * 0.5;
    }

    /// Persiste estado via intercalação iônica (Não-Volátil)
    pub fn memWrite(self: *ElectrochemicalPixel, density: f64) void {
        self.state.intercalation_density = density;
        // Intercalação altera a parte real (n)
        self.state.refractive_index.re = 1.5 + density * 0.3;
    }

    /// Nucleação de nanopartículas para amplificação plasmônica
    pub fn synthesizeMetal(self: *ElectrochemicalPixel, amount: f64) void {
        self.state.metal_nucleation = amount;
        self.coherence *= (1.0 + amount * 0.2); // Amplifica sinal
    }
};

pub const GTResonator = struct {
    pub const OXIDATION_TIME_MS = 34.0;
    pub const REDUCTION_TIME_MS = 171.0;

    /// Calcula o atraso de fase baseado na dinâmica iônica
    pub fn predictPhase(target_phase: f64, current_phase: f64) f64 {
        const delta = target_phase - current_phase;
        const time = if (delta > 0) OXIDATION_TIME_MS else REDUCTION_TIME_MS;
        // Firmware compensa o atraso difusivo
        return target_phase + (delta / time) * 10.0;
    }
};
