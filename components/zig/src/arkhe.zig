const std = @import("std");
const c = @cImport({
    @cInclude("arkhe.h");
});

pub const FinalityLevel = enum(u32) {
    pending = c.FINALITY_PENDING,
    l0 = c.FINALITY_L0,
    l1 = c.FINALITY_L1,
    l2 = c.FINALITY_L2,
};

pub fn kolmogorovGap(query: []const u8, source: []const u8, response: []const u8) f64 {
    return c.kolmogorov_gap(query.ptr, source.ptr, response.ptr);
}

pub fn gapToFinality(gap: f64) FinalityLevel {
    return @enumFromInt(c.gap_to_finality(gap));
}
