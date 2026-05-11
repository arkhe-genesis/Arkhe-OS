// examples/nv_sensing.zig
const std = @import("std");
const nv2arkhe = @import("../src/backends/nv2arkhe/main.zig");

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    // Bytecode Arkhé(N) para estimativa multiparâmetro
    // Formato: [Opcode, Reg, Imm_Low, Imm_High]
    const bytecode = [_]u8{
        0x01, 0x00, 0x00, 0x00, // COH_INIT
        0x0D, 0x01, 0x02, 0x00, // COH_ENTANGLE R1, R2
        0x07, 0x01, 0x0A, 0x00, // COH_BRAID R1, reps=10
        0x02, 0x01, 0x03, 0x00, // COH_MEASURE R1, R3
        0x73, 0x03, 0x04, 0x00, // ARKH_VERIFY R3, R4
    };

    var circuit = try nv2arkhe.compileToNV(allocator, &bytecode);
    defer circuit.deinit();

    std.debug.print("Circuito NV gerado: {d} pulsos, {d} repetições\n", .{ circuit.pulses.items.len, circuit.repetitions });
    for (circuit.pulses.items) |pulse| {
        std.debug.print("  {s}: {d:.1} ns, amp={d:.1} MHz, phase={d:.2} rad\n", .{
            @tagName(pulse.channel),
            pulse.duration,
            pulse.amplitude,
            pulse.phase,
        });
    }
}
