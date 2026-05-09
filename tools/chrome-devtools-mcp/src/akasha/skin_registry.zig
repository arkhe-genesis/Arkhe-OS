// src/akasha/skin_registry.zig
//! Registro de Superfície da Catedral (Pele Eletrocrômica)

const std = @import("std");

pub const MaterialType = enum {
    WO3,  // Trióxido de Tungstênio (Bistável, alta persistência)
    PANI, // Polianilina (Rápida resposta)
    VIOLOGEN, // Resposta de cor profunda
};

pub const SkinPixel = struct {
    addr: u64,
    material: MaterialType,
    pos: [3]f64, // (x, y, z) coordenadas no habitat
};

pub const HabitatSkinRegistry = struct {
    pixels: []SkinPixel,

    pub fn init(allocator: std.mem.Allocator, num_pixels: u64) !HabitatSkinRegistry {
        var pixels = try allocator.alloc(SkinPixel, num_pixels);
        for (pixels, 0..) |*p, i| {
            p.* = .{
                .addr = i,
                .material = if (i % 10 == 0) .WO3 else .PANI,
                .pos = .{ @as(f64, @floatFromInt(i % 100)), @as(f64, @floatFromInt(i / 100)), 0.0 },
            };
        }
        return HabitatSkinRegistry{ .pixels = pixels };
    }

    pub fn deinit(self: *HabitatSkinRegistry, allocator: std.mem.Allocator) void {
        allocator.free(self.pixels);
    }
};
