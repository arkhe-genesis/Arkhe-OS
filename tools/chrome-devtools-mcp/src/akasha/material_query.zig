// src/akasha/material_query.zig
//! Protocolo AKA_QUERY_MATERIAL (0x1FF) — Identificação de Substâncias via Espectro

const std = @import("std");
const registry = @import("material_registry.zig");

pub const SpectralData = struct {
    wavelengths: []f64,
    intensities: []f64,
};

pub const QueryResult = struct {
    material_id: ?registry.MaterialID,
    match_score: f64,
};

pub const MaterialQuery = struct {
    allocator: std.mem.Allocator,

    pub fn init(allocator: std.mem.Allocator) MaterialQuery {
        return .{ .allocator = allocator };
    }

    /// Implementação simplificada do AKA_QUERY_MATERIAL
    pub fn queryMaterial(self: *MaterialQuery, coords: [2]f64) !QueryResult {
        // 1. Simulação do sensor (bias sweeping + read_photocurrent)
        _ = coords;
        const raw_spectrum = try self.simulateSensorReading();
        defer {
            self.allocator.free(raw_spectrum.wavelengths);
            self.allocator.free(raw_spectrum.intensities);
        }

        // 2. Reconstrução do espectro S(λ)
        // No hardware real, isso usaria PHASE_FFT + PHASE_UNWRAP
        const reconstructed = raw_spectrum;

        // 3. Comparação com a biblioteca do AKASHA
        return self.matchLibrary(reconstructed);
    }

    fn simulateSensorReading(self: *MaterialQuery) !SpectralData {
        // Simula a varredura de 400nm a 1700nm
        const steps = 130;
        var wavelengths = try self.allocator.alloc(f64, steps);
        var intensities = try self.allocator.alloc(f64, steps);

        for (0..steps) |i| {
            const lambda = 400.0 + @as(f64, @floatFromInt(i)) * 10.0;
            wavelengths[i] = lambda;
            // Simula ruído de fundo
            intensities[i] = 0.05;
        }

        return SpectralData{
            .wavelengths = wavelengths,
            .intensities = intensities,
        };
    }

    fn matchLibrary(self: *MaterialQuery, spectrum: SpectralData) QueryResult {
        _ = self;
        var best_id: ?registry.MaterialID = null;
        var best_score: f64 = 0.0;

        // Itera sobre materiais conhecidos (exemplo simplificado)
        const candidates = [_]registry.MaterialID{
            registry.Registry.SILICON,
            registry.Registry.CARBON,
            registry.Registry.OXYGEN,
            registry.Registry.WATER,
        };

        for (candidates) |id| {
            if (registry.Registry.getSignature(id)) |sig| {
                const score = calculateMatch(spectrum, sig);
                if (score > best_score) {
                    best_score = score;
                    best_id = id;
                }
            }
        }

        const threshold = 0.75;
        if (best_score >= threshold) {
            return QueryResult{ .material_id = best_id, .match_score = best_score };
        } else {
            return QueryResult{ .material_id = null, .match_score = best_score };
        }
    }

    fn calculateMatch(spectrum: SpectralData, sig: registry.MaterialSignature) f64 {
        var total_score: f64 = 0.0;
        for (sig.peaks) |peak| {
            // Encontra o ponto mais próximo no espectro medido
            for (spectrum.wavelengths, spectrum.intensities) |w, v| {
                if (@abs(w - peak.wavelength) < 10.0) {
                    // Score baseado na proximidade da intensidade
                    const diff = @abs(v - peak.intensity);
                    total_score += std.math.max(0.0, 1.0 - diff);
                }
            }
        }
        return if (sig.peaks.len > 0) total_score / @as(f64, @floatFromInt(sig.peaks.len)) else 0.0;
    }
};
