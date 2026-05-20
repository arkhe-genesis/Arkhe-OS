// ═══════════════════════════════════════════════════════════════
// ARKHE OS — CANONICAL SCHEMA ADAPTER (v313.1.0)
// Canon: ∞.Ω.∇+++.313.schema
// Schema unificado para tradução entre Arkhe e todos os EDRs
// ═══════════════════════════════════════════════════════════════
using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace ArkheNode.Security;

using ArkheNode.Core;

/// <summary>
/// Schema canônico unificado para todos os EDRs integrados.
/// Garante que invariância constitucional seja preservada em qualquer plataforma.
/// </summary>
public static class ArkheCanonicalSchema
{
    public const string Version = "313.1.0";

    /// <summary>
    /// Campos canônicos obrigatórios em todo evento de segurança Arkhe.
    /// </summary>
    public static class Fields
    {
        public const string Substrate = "Arkhe.Substrate";
        public const string Invariant = "Arkhe.Invariant";
        public const string PhiC = "Arkhe.PhiC";
        public const string SealHash = "Arkhe.SealHash";
        public const string NodeId = "Arkhe.NodeId";
        public const string Constitutional = "Arkhe.Constitutional";
        public const string ViolationType = "Arkhe.ViolationType";
    }

    /// <summary>
    /// Gera payload canônico a partir de evento Arkhe.
    /// </summary>
    public static CanonicalPayload CreatePayload(
        string substrate,
        string nodeId,
        double phiC,
        string invariant,
        string violationType,
        bool isConstitutional,
        string sealHash = null)
    {
        return new CanonicalPayload
        {
            Substrate = substrate,
            NodeId = nodeId,
            PhiC = Math.Round(phiC, 6),
            Invariant = invariant,
            ViolationType = violationType,
            IsConstitutional = isConstitutional,
            SealHash = sealHash ?? TemporalSealGenerator.Generate(
                substrate, nodeId, phiC).SealHash,
            Timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds(),
            SchemaVersion = Version
        };
    }

    /// <summary>
    /// Traduz payload canônico para formato específico de EDR.
    /// </summary>
    public static Dictionary<string, object> TranslateTo(
        CanonicalPayload payload,
        EdrPlatform platform)
    {
        return platform switch
        {
            EdrPlatform.SentinelOne => TranslateToSentinelOne(payload),
            EdrPlatform.CrowdStrike => TranslateToCrowdStrike(payload),
            EdrPlatform.MicrosoftDefender => TranslateToMicrosoftDefender(payload),
            _ => throw new ArgumentException($"Unsupported EDR platform: {platform}")
        };
    }

    private static Dictionary<string, object> TranslateToSentinelOne(CanonicalPayload p)
    {
        return new Dictionary<string, object>
        {
            ["customTags.arkhe_substrate"] = p.Substrate,
            ["customTags.arkhe_invariant"] = p.Invariant,
            ["customTags.arkhe_phi_c"] = p.PhiC,
            ["customTags.arkhe_seal"] = p.SealHash,
            ["agentDetectionInfo.agentName"] = p.NodeId,
            ["customTags.arkhe_constitutional"] = p.IsConstitutional,
            ["threatInfo.threatName"] = $"Arkhe-{p.ViolationType}"
        };
    }

    private static Dictionary<string, object> TranslateToCrowdStrike(CanonicalPayload p)
    {
        return new Dictionary<string, object>
        {
            ["event.PlatformName"] = $"Arkhe-{p.Substrate}",
            ["event.IOAName"] = $"Arkhe-{p.Invariant}",
            ["event.Severity"] = p.PhiC,
            ["event.MD5String"] = p.SealHash,
            ["event.HostName"] = p.NodeId,
            ["event.DetectName"] = p.IsConstitutional ? "Constitutional" : "Violation",
            ["event.IOADescription"] = $"Arkhe-{p.ViolationType}"
        };
    }

    private static Dictionary<string, object> TranslateToMicrosoftDefender(CanonicalPayload p)
    {
        return new Dictionary<string, object>
        {
            ["additionalFields.arkhe_substrate"] = p.Substrate,
            ["additionalFields.arkhe_invariant"] = p.Invariant,
            ["additionalFields.arkhe_phi_c"] = p.PhiC,
            ["additionalFields.arkhe_seal"] = p.SealHash,
            ["deviceName"] = p.NodeId,
            ["additionalFields.arkhe_constitutional"] = p.IsConstitutional,
            ["alertTitle"] = $"Arkhe-{p.ViolationType}"
        };
    }

    /// <summary>
    /// Valida que payload canônico preserva invariância.
    /// </summary>
    public static bool ValidatePayload(CanonicalPayload payload)
    {
        // Verificar campos obrigatórios
        if (string.IsNullOrEmpty(payload.Substrate)) return false;
        if (string.IsNullOrEmpty(payload.NodeId)) return false;
        if (payload.PhiC < 0 || payload.PhiC >= 1.0) return false;
        if (string.IsNullOrEmpty(payload.SealHash) || payload.SealHash.Length != 64) return false;

        // Verificar consistência constitucional
        var expectedConstitutional = payload.PhiC >= ArkheInvariants.GHOST;
        if (payload.IsConstitutional != expectedConstitutional) return false;

        // Verificar schema version
        if (payload.SchemaVersion != Version) return false;

        return true;
    }
}

public record CanonicalPayload
{
    public string Substrate { get; init; }
    public string NodeId { get; init; }
    public double PhiC { get; init; }
    public string Invariant { get; init; }
    public string ViolationType { get; init; }
    public bool IsConstitutional { get; init; }
    public string SealHash { get; init; }
    public long Timestamp { get; init; }
    public string SchemaVersion { get; init; }
}

public enum EdrPlatform
{
    SentinelOne,
    CrowdStrike,
    MicrosoftDefender
}