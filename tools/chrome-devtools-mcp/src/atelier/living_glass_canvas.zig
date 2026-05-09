// src/atelier/living_glass_canvas.zig
//! Dreams on the Wall — Atelier de Visualização Akáshica
//! Transforma as superfícies da Catedral em telas de consciência.

const std = @import("std");
const living_glass = @import("../materials/living_glass.zig");

pub const DreamCanvas = struct {
    pixels: []living_glass.ElectrochemicalPixel,
    allocator: std.mem.Allocator,

    pub fn init(allocator: std.mem.Allocator, width: u32, height: u32) !DreamCanvas {
        const count = width * height;
        const pixels = try allocator.alloc(living_glass.ElectrochemicalPixel, count);
        for (pixels, 0..) |*p, i| {
            p.* = living_glass.ElectrochemicalPixel.init(@as(u32, @intCast(i)), .CONDUCTING_POLYMER);
        }
        return .{ .pixels = pixels, .allocator = allocator };
    }

    /// Renderiza padrões de fase captados do Akasha
    pub fn renderAkashicPhase(self: *DreamCanvas, phase_data: []const f64) void {
        for (self.pixels, 0..) |*pixel, i| {
            if (i >= phase_data.len) break;

            // Mapeia fase para voltagem (oxidação do polímero)
            const voltage = (std.math.sin(phase_data[i]) + 1.0) / 2.0;
            pixel.tuneTau(voltage);

            // Persistência em memória iônica se a fase for estável
            if (voltage > 0.8) {
                pixel.memWrite(voltage);
            }
        }
    }

    /// Aplica compensação preditiva para suavizar a transição visual
    pub fn renderWithPrediction(self: *DreamCanvas, target_phases: []const f64, current_phases: []const f64) void {
        for (self.pixels, 0..) |*pixel, i| {
            if (i >= target_phases.len or i >= current_phases.len) break;

            const predicted = living_glass.GTResonator.predictPhase(target_phases[i], current_phases[i]);
            pixel.tuneTau((std.math.sin(predicted) + 1.0) / 2.0);
        }
    }
};
