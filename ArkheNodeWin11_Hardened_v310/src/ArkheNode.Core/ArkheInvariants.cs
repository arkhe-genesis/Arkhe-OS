using System;
using System.Collections.Generic;

namespace ArkheNode.Core;

public static class ArkheInvariants
{
    public static readonly double GHOST = Math.Sqrt(3) / 3;
    public static readonly double LOOPSEAL = Math.PI / 9;
    public static readonly double GAP_MAX = 0.9999;
    public static readonly double AUTOCIDE = Math.Sqrt(3) / 3;
    public static readonly double LOOPSEAL_RADIANS = Math.PI / 9.0;
}

public record PhyMetrics(
    double RssiDbm,
    double SnrDb,
    double ErrorRatePpm,
    double ChannelUtilization,
    string SecurityType
);

public record PhiCResult(
    double PhiC,
    bool IsConstitutional,
    double SignalFactor,
    double PerformanceFactor,
    double SecurityFactor,
    double MediumFactor,
    Dictionary<string, bool> Invariants
);

public static class PhiCCalculator
{
    public static PhiCResult Calculate(PhyMetrics metrics, bool fipsKatPassed = true)
    {
        var signalNorm = Math.Clamp((metrics.RssiDbm + 90) / 60, 0, 1);
        var snrNorm = Math.Clamp(metrics.SnrDb / 40, 0, 1);
        var signalFactor = 0.6 * signalNorm + 0.4 * snrNorm;

        var perfFactor = Math.Clamp(1.0 - (metrics.ErrorRatePpm / 1000.0), 0, 1);
        var mediumFactor = Math.Clamp(1.0 - metrics.ChannelUtilization, 0, 1);

        double securityFactor = 0.50;
        if (!string.IsNullOrEmpty(metrics.SecurityType))
        {
            if (metrics.SecurityType.Contains("WPA3") || metrics.SecurityType.Contains("AES") || metrics.SecurityType.Contains("Kyber") || metrics.SecurityType.Contains("Dilithium"))
                securityFactor = 1.0;
            else if (metrics.SecurityType.Contains("WPA2"))
                securityFactor = 0.85;
            else if (metrics.SecurityType.Contains("OPEN"))
                securityFactor = 0.20;
        }

        var phiC = 0.25 * signalFactor + 0.30 * perfFactor + 0.25 * securityFactor + 0.20 * mediumFactor;
        phiC = Math.Min(phiC, ArkheInvariants.GAP_MAX);

        var invariants = new Dictionary<string, bool>
        {
            ["ghost"] = phiC >= ArkheInvariants.GHOST,
            ["loopseal"] = phiC >= ArkheInvariants.LOOPSEAL,
            ["gap"] = phiC <= ArkheInvariants.GAP_MAX,
            ["fips_kat"] = fipsKatPassed
        };

        var isConstitutional = invariants["ghost"] && invariants["loopseal"] && invariants["gap"] && invariants["fips_kat"];

        return new PhiCResult(phiC, isConstitutional, signalFactor, perfFactor, securityFactor, mediumFactor, invariants);
    }
}

public record TemporalSeal(
    string SealHash,
    long Timestamp,
    string Substrate,
    string NodeId,
    double PhiC,
    string PreviousSealHash
);

public static class TemporalSealGenerator
{
    public static TemporalSeal Generate(
        string substrate,
        string nodeId,
        double phiC,
        string previousSealHash = "")
    {
        long timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();

        var payload = new
        {
            substrate,
            nodeId,
            phiC,
            timestamp,
            previousSealHash,
            nonce = System.Security.Cryptography.RandomNumberGenerator.GetInt32(int.MaxValue)
        };

        string json = System.Text.Json.JsonSerializer.Serialize(payload);
        byte[] hash = SHA3_256(System.Text.Encoding.UTF8.GetBytes(json));
        string sealHash = Convert.ToHexString(hash).ToLowerInvariant();

        return new TemporalSeal(sealHash, timestamp, substrate, nodeId, phiC, previousSealHash);
    }

    public static byte[] SHA3_256(byte[] data)
    {
        var digest = new Org.BouncyCastle.Crypto.Digests.Sha3Digest(256);
        digest.BlockUpdate(data, 0, data.Length);
        byte[] result = new byte[digest.GetDigestSize()];
        digest.DoFinal(result, 0);
        return result;
    }

    public static bool Verify(byte[] data, string expectedHexHash)
    {
        byte[] actualHash = SHA3_256(data);
        string actualHex = Convert.ToHexString(actualHash).ToLowerInvariant();
        return actualHex == expectedHexHash.ToLowerInvariant();
    }
}

public enum AuditEventLevel { Constitutional, Violation, Warning, Info, Autocide }

public record AuditEvent(
    DateTimeOffset Timestamp,
    string EventId,
    AuditEventLevel Level,
    string Substrate,
    string NodeId,
    string Message,
    double? PhiC,
    Dictionary<string, bool>? Invariants,
    string? SealHash
);

public interface IAuditLogger
{
    void Log(AuditEvent evt);
    IReadOnlyList<AuditEvent> GetEvents(DateTimeOffset? since = null);
    void Flush();
}

public class InMemoryAuditLogger : IAuditLogger
{
    private readonly List<AuditEvent> _events = new();
    private readonly object _lock = new();

    public void Log(AuditEvent evt)
    {
        lock (_lock)
        {
            var newEvt = evt with { EventId = evt.EventId == "" ? $"EVT-{DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()}-{System.Security.Cryptography.RandomNumberGenerator.GetInt32(10000):D4}" : evt.EventId };
            _events.Add(newEvt);
        }
    }

    public IReadOnlyList<AuditEvent> GetEvents(DateTimeOffset? since = null)
    {
        lock (_lock)
        {
            var query = _events.AsEnumerable();
            if (since.HasValue)
            {
                query = query.Where(e => e.Timestamp >= since.Value);
            }
            return query.OrderByDescending(e => e.Timestamp).ToList();
        }
    }

    public void Flush() { }
}
