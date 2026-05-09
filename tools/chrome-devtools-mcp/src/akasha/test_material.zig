// src/akasha/test_material.zig
const std = @import("std");
const material_query = @import("material_query.zig");
const registry = @import("material_registry.zig");

test "AKA_QUERY_MATERIAL: Registry lookup" {
    const sig = registry.Registry.getSignature(registry.Registry.WATER);
    try std.testing.expect(sig != null);
    try std.testing.expectEqualStrings("Water (H2O)", sig.?.name);
    try std.testing.expect(sig.?.peaks.len == 3);
}

test "AKA_QUERY_MATERIAL: Identification Logic" {
    var query = material_query.MaterialQuery.init(std.testing.allocator);
    const result = try query.queryMaterial(.{ 0.0, 0.0 });

    // Como simulateSensorReading gera apenas ruído, esperamos score baixo e null id
    try std.testing.expect(result.material_id == null);
    try std.testing.expect(result.match_score < 0.5);
}
