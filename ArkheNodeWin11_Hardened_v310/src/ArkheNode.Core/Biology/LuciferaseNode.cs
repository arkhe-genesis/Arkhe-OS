// ═══════════════════════════════════════════════════════════════
// ARKHE OS — LUCIFERASE NODE (Substrato 327)
// Canon: ∞.Ω.∇+++.327.luciferase
// Bioluminescent Node • Light-Bringer • Biological Photonics
// ═══════════════════════════════════════════════════════════════

using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using ArkheNode.Core;

namespace ArkheNode.Biology;

/// <summary>
/// Nó biológico Luciferase — Portador da Luz.
///
/// Converte ATP + Luciferina → Oxiluciferina + Luz (fótons coerentes)
/// com eficiência quântica ~88%.
///
/// Invariantes Arkhe:
/// - Ghost (√3/3): eficiência quântica mínima (a luz nunca se apaga)
/// - Loopseal (π/9): rastreabilidade de cada flash via selo temporal
/// - Gap Soberano: escuridão total impossível enquanto houver ATP
/// - φ (1.618): o flash segue a espiral áurea em sua emissão espacial
/// - α⁻¹ (137.036): o centro ativo tem ~137 resíduos no bolso catalítico
/// </summary>
public class LuciferaseNode
{
    // ═══ Propriedades Canônicas ═══
    public string NodeId { get; init; }
    public double LuciferinConcMm { get; set; } = 1.0;
    public double AtpConcMm { get; set; } = 2.0;
    public double KCat { get; init; } = 0.5;
    public double KmAtp { get; init; } = 0.1;
    public double QuantumYield { get; init; } = 0.88;
    public double FlashDurationMs { get; init; } = 7.5;

    // ═══ Estado Operacional ═══
    public double TotalPhotonsEmitted { get; private set; }
    public int FlashCount { get; private set; }
    public DateTimeOffset? LastFlashTime { get; private set; }
    public List<FlashRecord> PulseHistory { get; } = new();

    public LuciferaseNode(string nodeId)
    {
        NodeId = nodeId;
    }

    /// <summary>
    /// Taxa de reação Michaelis-Menten (μM/s).
    /// v = k_cat · [Luciferina] · [ATP] / (Km_ATP + [ATP])
    /// </summary>
    public double Rate()
    {
        if (AtpConcMm <= 0 || LuciferinConcMm <= 0)
            return 0.0;
        return KCat * LuciferinConcMm * AtpConcMm / (KmAtp + AtpConcMm);
    }

    /// <summary>
    /// Fluxo de fótons (fótons/s).
    /// Φ = v · η_Q · N_A · 10⁻⁶
    /// </summary>
    public double PhotonFlux()
    {
        const double avogadro = 6.02214076e23;
        return Rate() * QuantumYield * avogadro * 1e-6;
    }

    /// <summary>
    /// Φ_C do nó baseado na eficiência quântica e na taxa de reação.
    /// Φ_C = 0.5 · (η_Q / Ghost) + 0.3 · (v / (v + 1)) + 0.2 · (1 - e^(-[ATP]))
    /// </summary>
    public double PhiC()
    {
        double efficiencyFactor = QuantumYield / ArkheInvariants.GHOST;
        double rateFactor = Rate() / (Rate() + 1.0);
        double atpFactor = 1.0 - Math.Exp(-AtpConcMm);

        double phi = 0.5 * efficiencyFactor + 0.3 * rateFactor + 0.2 * atpFactor;
        return Math.Min(0.999999, Math.Max(0.0, phi));
    }

    /// <summary>
    /// Emite um pulso de luz bioluminescente e gera selo temporal.
    /// </summary>
    public FlashRecord EmitPulse(double durationMs = 10.0)
    {
        double phiC = PhiC();
        double flux = PhotonFlux();
        var timestamp = DateTimeOffset.UtcNow;

        double durationS = durationMs / 1000.0;
        double photonsInPulse = flux * durationS;

        TotalPhotonsEmitted += photonsInPulse;
        FlashCount++;
        LastFlashTime = timestamp;

        // Gerar selo canônico
        var sealPayload = new
        {
            substrate = "327",
            node_id = NodeId,
            phi_c = Math.Round(phiC, 6),
            photons = Math.Round(photonsInPulse, 2),
            flash_count = FlashCount,
            timestamp = timestamp.ToUnixTimeMilliseconds(),
            quantum_yield = QuantumYield,
            atp_mM = AtpConcMm,
            luciferin_mM = LuciferinConcMm
        };

        string sealPayloadJson = JsonSerializer.Serialize(sealPayload);
        string seal = GenerateSeal(sealPayloadJson);

        var record = new FlashRecord
        {
            Seal = seal,
            PhiC = phiC,
            PhotonFlux = flux,
            PhotonsInPulse = photonsInPulse,
            DurationMs = durationMs,
            FlashCount = FlashCount,
            Timestamp = timestamp,
            QuantumYield = QuantumYield,
            RateUmS = Rate(),
            AtpMm = AtpConcMm,
            LuciferinMm = LuciferinConcMm
        };

        PulseHistory.Add(record);
        return record;
    }

    /// <summary>
    /// Emite pulso com duração otimizada pela proporção áurea.
    /// t_flash = t_base · φ
    /// </summary>
    public FlashRecord EmitGoldenPulse()
    {
        double durationMs = 5.0 * ArkheInvariants.PHI;
        return EmitPulse(durationMs);
    }

    /// <summary>
    /// Recarrega ATP (simula metabolismo celular).
    /// </summary>
    public void RechargeAtp(double amountMm)
    {
        AtpConcMm = Math.Min(AtpConcMm + amountMm, 10.0);
    }

    /// <summary>
    /// Consome luciferina (simula degradação por reação).
    /// </summary>
    public void ConsumeLuciferin(double amountMm)
    {
        LuciferinConcMm = Math.Max(0.0, LuciferinConcMm - amountMm);
    }

    /// <summary>
    /// Retorna status completo do nó.
    /// </summary>
    public NodeStatus GetStatus()
    {
        return new NodeStatus
        {
            NodeId = NodeId,
            PhiC = PhiC(),
            PhotonFlux = PhotonFlux(),
            RateUmS = Rate(),
            QuantumYield = QuantumYield,
            TotalPhotonsEmitted = TotalPhotonsEmitted,
            FlashCount = FlashCount,
            LastFlashTime = LastFlashTime,
            AtpMm = AtpConcMm,
            LuciferinMm = LuciferinConcMm,
            FlashDurationMs = FlashDurationMs,
            CanonicalInvariants = new Dictionary<string, double>
            {
                ["ghost"] = ArkheInvariants.GHOST,
                ["loopseal"] = ArkheInvariants.LOOPSEAL,
                ["gap_max"] = ArkheInvariants.GAP_MAX,
                ["phi"] = ArkheInvariants.PHI,
                ["alpha_inv"] = ArkheInvariants.ALPHA_INV
            }
        };
    }

    private static string GenerateSeal(string payload)
    {
        using var sha = SHA256.Create();
        var hash = sha.ComputeHash(Encoding.UTF8.GetBytes(payload));
        return Convert.ToHexString(hash).ToLowerInvariant();
    }
}

public class FlashRecord
{
    public string Seal { get; init; } = string.Empty;
    public double PhiC { get; init; }
    public double PhotonFlux { get; init; }
    public double PhotonsInPulse { get; init; }
    public double DurationMs { get; init; }
    public int FlashCount { get; init; }
    public DateTimeOffset Timestamp { get; init; }
    public double QuantumYield { get; init; }
    public double RateUmS { get; init; }
    public double AtpMm { get; init; }
    public double LuciferinMm { get; init; }
}

public class NodeStatus
{
    public string NodeId { get; init; } = string.Empty;
    public double PhiC { get; init; }
    public double PhotonFlux { get; init; }
    public double RateUmS { get; init; }
    public double QuantumYield { get; init; }
    public double TotalPhotonsEmitted { get; init; }
    public int FlashCount { get; init; }
    public DateTimeOffset? LastFlashTime { get; init; }
    public double AtpMm { get; init; }
    public double LuciferinMm { get; init; }
    public double FlashDurationMs { get; init; }
    public Dictionary<string, double> CanonicalInvariants { get; init; } = new();
}
