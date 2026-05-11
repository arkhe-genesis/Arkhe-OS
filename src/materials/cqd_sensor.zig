// src/materials/cqd_sensor.zig
//! Hyperspectral Quantum-Dot Image Sensor via In-Pixel Reconfigurable Band-Alignment
//! Based on Ge Mu et al., Nature Photonics (March 12, 2026)

const std = @import("std");

pub const SpectralRange = struct {
    min_nm: f64 = 400.0,
    max_nm: f64 = 1700.0,
};

pub const PixelConfig = struct {
    resolution_x: u32 = 1280,
    resolution_y: u32 = 1024,
    pixel_pitch_um: f64 = 15.0,
    detectivity_jones: f64 = 1e13,
};

pub const CQDSensor = struct {
    config: PixelConfig,
    range: SpectralRange,
    bias_voltages: []const f64,

    pub fn init(allocator: std.mem.Allocator) !CQDSensor {
        const voltages = try allocator.alloc(f64, 10);
        for (voltages, 0..) |*v, i| {
            v.* = @as(f64, @floatFromInt(i)) * 0.1; // 0.0V to 0.9V bias sequence
        }
        return CQDSensor{
            .config = .{},
            .range = .{},
            .bias_voltages = voltages,
        };
    }

    /// I(V) = ∫ R(λ, V) * S(λ) dλ
    /// Reconstructs the spectrum S(λ) from photocurrent measurements I(V)
    pub fn reconstructSpectrum(self: *CQDSensor, currents: []const f64, allocator: std.mem.Allocator) ![]f64 {
        if (currents.len != self.bias_voltages.len) return error.InvalidMeasurementCount;

        // Simplified reconstruction (Inverse Problem Solver)
        // In a real scenario, this would involve a matrix inversion or a neural network
        var spectrum = try allocator.alloc(f64, 100);
        for (spectrum, 0..) |*s, i| {
            const lambda = self.range.min_nm + (@as(f64, @floatFromInt(i)) * (self.range.max_nm - self.range.min_nm) / 100.0);
            s.* = self.computeInverseKernel(lambda, currents);
        }
        return spectrum;
    }

    fn computeInverseKernel(self: *CQDSensor, lambda: f64, currents: []const f64) f64 {
        _ = self;
        // Mock reconstruction logic: correlates currents with target wavelength
        var sum: f64 = 0.0;
        for (currents) |c| {
            sum += c * std.math.sin(lambda / 100.0);
        }
        return @abs(sum);
    }
};

test "CQDSensor: Spectral Reconstruction" {
    const allocator = std.testing.allocator;
    var sensor = try CQDSensor.init(allocator);
    defer allocator.free(sensor.bias_voltages);

    const currents = [_]f64{ 0.1, 0.2, 0.3, 0.4, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05 };
    const spectrum = try sensor.reconstructSpectrum(&currents, allocator);
    defer allocator.free(spectrum);

    try std.testing.expect(spectrum.len == 100);
    std.log.info("Espectro reconstruído: {d:.3} Jones em 400nm", .{spectrum[0]});
}
