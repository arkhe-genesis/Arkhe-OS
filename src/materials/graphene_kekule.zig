// src/materials/graphene_kekule.zig
//! Ordem Kekulé em Grafeno - Qubits de Vale (Valley Qubits)
//! Baseado em Zhang et al., PRL 136, 156401 (2026)
//! DOI: 10.1103/ncq1-yzpd

const std = @import("std");
const qtl = @import("../quantum.zig");
const Complex = std.math.Complex;

/// Parâmetros do grafeno (PRL 136, 156401)
pub const GrapheneParams = struct {
    pub const LATTICE_CONST = 0.246e-9; // nm (constante de rede)
    pub const FERMI_VEL = 1.0e6;        // m/s (velocidade de Fermi)
    pub const VALLEY_DEGENERACY = 2;    // K e K'

    // Parâmetros da ordem Kekulé observada em STM
    pub const KEKULE_WAVELENGTH = 3 * LATTICE_CONST; // ~0.738 nm (super-célula √3×√3)
    pub const PHASE_WINDING_RATE = 2 * std.math.pi / 5.0e-9; // rad/nm (5nm característico do artigo)
    pub const KEKULE_GAP = 0.2; // eV typical
};

/// Representa um domínio Kekulé como COBIT topológico
pub const KekuleDomain = struct {
    center_pos: [2]f64,     // Posição (x,y) da fronteira de grão
    valley_phase: f64,      // Fase de vale acumulada (θ_K - θ_K')
    chirality: i2,          // +1 (dextro) ou -1 (levo) - quebra de simetria espacial
    bond_texture: [3]f64,   // Amplitudes dos três vetores de enlace (δ1, δ2, δ3)

    /// Calcula o operador de massa de Dirac a partir da ordem Kekulé
    /// m(x) = Δ₀ e^{iφ(x)} onde φ é o winding da fase
    pub fn diracMassOperator(self: KekuleDomain) Complex(f64) {
        const phase = self.valley_phase * @as(f64, @floatFromInt(self.chirality));
        return Complex(f64).init(
            GrapheneParams.KEKULE_GAP * @cos(phase),
            GrapheneParams.KEKULE_GAP * @sin(phase)
        );
    }

    /// Converte domínio Kekulé para COBIT de vale (2-level system: K vs K')
    pub fn toValleyCobit(self: KekuleDomain) qtl.COBIT {
        // O vale é codificado na fase do COBIT
        // |K⟩ = |0⟩, |K'⟩ = |1⟩ na base computacional
        const theta = self.valley_phase;

        return qtl.COBIT{
            .phase = theta,
            .amplitude_k = @cos(theta / 2.0),  // Coeficiente no vale K
            .amplitude_kp = @sin(theta / 2.0), // Coeficiente no vale K'
            .id = @as(u32, @intFromFloat(self.center_pos[0] * 1e9)), // ID baseado em posição
            .substrate = .GRAPHENE_KEKULE,
        };
    }
};

/// Scanner STM virtual para mapeamento de ordem Kekulé
pub const STMScanner = struct {
    bias_voltage: f64,      // mV (energia de tunelamento)
    current_setpoint: f64,  // pA

    /// Mapeia a textura de elos em uma fronteira de grão 1D
    /// Retorna array de domínios Kekulé detectados
    pub fn mapGrainBoundary(
        self: *STMScanner,
        allocator: std.mem.Allocator,
        x_range: [2]f64,
        y_range: [2]f64,
        resolution: f64, // nm/pixel
    ) ![]KekuleDomain {
        var domains = std.ArrayList(KekuleDomain).init(allocator);

        var x = x_range[0];
        while (x < x_range[1]) : (x += resolution) {
            var y = y_range[0];
            while (y < y_range[1]) : (y += resolution) {

                // Simulação da medida STM (dI/dV mapping)
                // Picos em ±Δ indicam gap Kekulé local
                const local_gap = self.measureLocalGap(x, y);

                if (local_gap > 0.1) { // Gap detectado (ordem Kekulé presente)
                    const phase = self.extractPhaseWinding(x, y);
                    const chirality = self.determineChirality(x, y);

                    try domains.append(KekuleDomain{
                        .center_pos = .{ x, y },
                        .valley_phase = phase,
                        .chirality = chirality,
                        .bond_texture = self.calculateBondTexture(x, y),
                    });
                }
            }
        }

        return domains.toOwnedSlice();
    }

    fn measureLocalGap(self: *STMScanner, x: f64, y: f64) f64 {
        // dI/dV espectroscopia - gap proporcional à ordem Kekulé local
        _ = self;
        // Implementação simplificada: gap máximo na fronteira
        return 0.2 * @exp(-(x * x + y * y) / 1e-16); // 0.2 eV típico
    }

    fn extractPhaseWinding(self: *STMScanner, x: f64, y: f64) f64 {
        // A fase espiral observada no artigo varia ao longo da fronteira
        // θ(x) = kx + φ0 (mod 2π)
        _ = y;
        const k = GrapheneParams.PHASE_WINDING_RATE;
        return k * x + self.bias_voltage * 0.01; // bias modula a fase
    }

    fn determineChirality(self: *STMScanner, x: f64, y: f64) i2 {
        // Determinação via análise de Fourier da textura de elos
        // Padrão Kekulé: três vetores de enlace com fases 0, 2π/3, 4π/3
        _ = self;
        _ = y;
        return if (x > 0) @as(i2, 1) else @as(i2, -1);
    }

    fn calculateBondTexture(self: *STMScanner, x: f64, y: f64) [3]f64 {
        // Retorna amplitudes moduladas para os três elos do grafeno
        const phase = self.extractPhaseWinding(x, y);
        return .{
            @cos(phase),
            @cos(phase + 2.0 * std.math.pi / 3.0),
            @cos(phase + 4.0 * std.math.pi / 3.0),
        };
    }
};

/// Operações quânticas em qubits de vale grafeno
pub const ValleyQubitOps = struct {
    /// Inicializa superposição de vales usando potencial periódico
    /// (Suprime ordem Kekulé para criar estado uniforme)
    pub fn initializeValleySuperposition(
        cobit: *qtl.COBIT,
        potential_period: f64, // nm (período do potencial de supressão)
    ) !void {
        // Aplica COH_TUNE_TAU via back-gate
        try cobit.applyPotential(.{
            .amplitude = 0.5, // eV
            .period = potential_period,
            .direction = .PERPENDICULAR_TO_BOUNDARY,
        });

        // Após suprimir Kekulé, o vale é bem definido
        cobit.phase = 0.0; // |K⟩ + |K'⟩ / √2
        cobit.coherence = 0.95;
    }

    /// Operação de troca de vale (Valley Exchange) via fronteira
    /// Análogo ao exchange coupling em spins, mas para vales
    pub fn valleyExchange(control: KekuleDomain, target: KekuleDomain) !f64 {
        // O coupling depende do overlap das funções de onda de fronteira
        const distance = std.math.sqrt(
            std.math.pow(f64, control.center_pos[0] - target.center_pos[0], 2) +
            std.math.pow(f64, control.center_pos[1] - target.center_pos[1], 2)
        );

        // Decaimento exponencial do exchange com distância
        const J0 = 1.0e-3; // eV (escala típica)
        const xi = 2.0e-9; // nm (comprimento de coerência de fase)

        return J0 * @exp(-distance / xi) *
               @cos(control.valley_phase - target.valley_phase);
    }
};
