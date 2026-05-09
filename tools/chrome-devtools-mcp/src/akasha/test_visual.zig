// src/akasha/test_visual.zig
const std = @import("std");
const visual = @import("visual_renderer.zig");
const skin = @import("skin_registry.zig");

test "AKA_VISUAL: Phase to Chroma Translation" {
    const stream = visual.PhaseStream{
        .amplitude = 0.8,
        .frequency = 0.5, // 0.5 * 360 = 180 (Cyan)
        .tau = 0.98,      // Criticality high -> persistence = true
    };

    const intent = visual.VisualRenderer.translatePhaseToChroma(stream);

    try std.testing.expectEqual(@as(f64, 0.8), intent.intensity);
    try std.testing.expectEqual(@as(f64, 180.0), intent.hue);
    try std.testing.expectEqual(@as(f64, 0.98), intent.saturation);
    try std.testing.expect(intent.persistence);
}

test "AKA_VISUAL: Rendering and Mural Logic" {
    const allocator = std.testing.allocator;
    var registry = try skin.HabitatSkinRegistry.init(allocator, 10);
    defer registry.deinit(allocator);

    const intent = visual.ChromaIntent{
        .intensity = 1.0,
        .hue = 240.0, // Blue
        .saturation = 1.0,
        .persistence = true,
        .significance = 1.0,
    };

    // This will trigger log info for pixel 0 (WO3)
    try visual.VisualRenderer.applyChroma(intent, registry);
}
