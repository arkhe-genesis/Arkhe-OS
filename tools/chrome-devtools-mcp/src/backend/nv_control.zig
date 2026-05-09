// src/backend/nv_control.zig
//! BACKEND DE CONTROLE NV — ARKHÉ(N) PARA PULSOS FÍSICOS

const std = @import("std");
const arkhe = @import("../isa/opcodes.zig");

pub const PulseType = enum { Laser, MW, RF };

pub const Pulse = struct {
    ptype: PulseType,
    frequency: f64, // Hz
    amplitude: f64, // Normalized 0.0-1.0
    phase: f64,     // Radians
    duration: f64,  // Seconds
};

pub const PulseSequence = std.ArrayList(Pulse);

pub fn compileOpcode(allocator: std.mem.Allocator, opcode: arkhe.Opcode, params: []const f64) !PulseSequence {
    var seq = PulseSequence.init(allocator);
    errdefer seq.deinit();

    switch (opcode) {
        // Inicialização: Laser Green para polarizar o spin eletrônico
        .COH_INIT => {
            try seq.append(.{
                .ptype = .Laser,
                .frequency = 532e12, // 532 nm
                .amplitude = 1.0,
                .phase = 0.0,
                .duration = 3.0e-6, // 3 us
            });
        },

        // Entrelaçamento: Porta CNOT simulada com MW seletivo + RF
        .COH_ENTANGLE => {
            if (params.len < 2) return error.MissingParameters;
            // Pulso RF em Nuclear (Hadamard)
            try seq.append(.{
                .ptype = .RF,
                .frequency = params[0], // Freq Larmor do N-14
                .amplitude = 0.8,
                .phase = std.math.pi / 2.0,
                .duration = 10.0e-6,
            });
            // Pulso MW seletivo no Eletron (CNOT)
            try seq.append(.{
                .ptype = .MW,
                .frequency = params[1], // Freq de ressonância NV
                .amplitude = 0.5,
                .phase = 0.0,
                .duration = 1.0e-6,
            });
        },

        // Definição de Fase: Rotação Z virtual via ajuste de fase do MW
        .PHASE_SET => {
            if (params.len < 1) return error.MissingParameters;
            const target_phase = params[0];
            try seq.append(.{
                .ptype = .MW,
                .frequency = 2.87e9, // D freq
                .amplitude = 0.0, // Virtual gate
                .phase = target_phase,
                .duration = 0.0,
            });
        },

        // Medição: Leitura óptica
        .COH_MEASURE => {
            try seq.append(.{
                .ptype = .Laser,
                .frequency = 532e12,
                .amplitude = 1.0,
                .phase = 0.0,
                .duration = 300.0e-9, // 300 ns readout
            });
        },

        else => return error.UnsupportedOpcodeForNV,
    }

    return seq;
}

/// Função de envio para o gerador de pulsos (FPGA/AWG)
pub fn executePulseSequence(seq: PulseSequence, device: std.fs.File) !void {
    for (seq.items) |pulse| {
        // Serializa o pulso e envia para o hardware via SPI/Ethernet
        var buf: [256]u8 = undefined;
        const cmd = try std.fmt.bufPrint(&buf, "PULSE {s} {d} {d} {d} {d}\n", .{
            @tagName(pulse.ptype),
            pulse.frequency,
            pulse.amplitude,
            pulse.phase,
            pulse.duration,
        });
        try device.writeAll(cmd);
    }
}
