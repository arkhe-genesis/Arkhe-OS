const std = @import("std");
const arkhe = @import("arkhe.zig");

pub fn main() void {
    const gap = arkhe.kolmogorovGap("query", "source", "response");
    std.debug.print("gap: {d}\n", .{gap});
}
