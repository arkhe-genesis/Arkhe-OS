// src/akasha/material_registry.zig
//! Biblioteca de Assinaturas Espectrais da Catedral (AKASHA_MATERIAL_SPECTRA)

const std = @import("std");

pub const MaterialID = u32;

pub const MaterialSignature = struct {
    id: MaterialID,
    name: []const u8,
    // Representação simplificada: Picos principais (comprimento de onda em nm, intensidade)
    peaks: []const SpectralPeak,
};

pub const SpectralPeak = struct {
    wavelength: f64,
    intensity: f64,
    width: f64,
};

pub const Registry = struct {
    pub const SILICON: MaterialID = 0x01;
    pub const CARBON: MaterialID = 0x02;
    pub const OXYGEN: MaterialID = 0x03;
    pub const WATER: MaterialID = 0x04;
    pub const TOXIN_X: MaterialID = 0x99;

    pub fn getSignature(id: MaterialID) ?MaterialSignature {
        return switch (id) {
            SILICON => .{
                .id = SILICON,
                .name = "Silicon",
                .peaks = &.{
                    .{ .wavelength = 1100.0, .intensity = 0.9, .width = 50.0 },
                },
            },
            CARBON => .{
                .id = CARBON,
                .name = "Carbon (Graphene)",
                .peaks = &.{
                    .{ .wavelength = 270.0, .intensity = 0.8, .width = 20.0 }, // UV, but let's say it has a NIR signature too
                    .{ .wavelength = 1550.0, .intensity = 0.4, .width = 100.0 },
                },
            },
            OXYGEN => .{
                .id = OXYGEN,
                .name = "Molecular Oxygen",
                .peaks = &.{
                    .{ .wavelength = 762.0, .intensity = 1.0, .width = 5.0 },
                },
            },
            WATER => .{
                .id = WATER,
                .name = "Water (H2O)",
                .peaks = &.{
                    .{ .wavelength = 970.0, .intensity = 0.6, .width = 40.0 },
                    .{ .wavelength = 1200.0, .intensity = 0.7, .width = 50.0 },
                    .{ .wavelength = 1450.0, .intensity = 0.9, .width = 60.0 },
                },
            },
            else => null,
        };
    }
};
