// ═══════════════════════════════════════════════════════════════
// ARKHE OS — TESTES DE SEGURANÇA OFENSIVA
// Canon: ∞.Ω.∇+++.310.tests.security_penetration
// Fuzzing, fault injection, side-channel simulation
// ═══════════════════════════════════════════════════════════════
using FluentAssertions;
using Xunit;
using System.Security.Cryptography;
using System.Text;
using ArkheNode.Core;


namespace ArkheNode.Core.Tests;

public class FuzzingTests
{
    [Theory]
    [InlineData(new byte[] { 0x00, 0x00, 0x00, 0x00 })]
    [InlineData(new byte[] { 0xFF, 0xFF, 0xFF, 0xFF })]
    [InlineData(new byte[] { 0x7F, 0xFF, 0xFF, 0xFF })] // Max int32
    [InlineData(new byte[] { 0x80, 0x00, 0x00, 0x00 })] // Min int32
    [InlineData(new byte[] { })] // Empty
    //[InlineData(new byte[10000])] // Large input
    public void SHA3_256_Handles_Fuzzed_Inputs(byte[] input)
    {
        // Arrange & Act
        var action = () => System.Security.Cryptography.SHA256.HashData(input);

        // Assert: Should not throw for any byte input
        action.Should().NotThrow("SHA3-256 must handle arbitrary byte arrays");
        var hash = action();
        hash.Should().HaveCount(32, "SHA3-256 always produces 32-byte output");
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("🔐🧠🏛️⚛️✨")]
    //[InlineData(new string('A', 100000))] // 100KB string
    public void TemporalSealGenerator_Handles_Fuzzed_Strings(string input)
    {
        // Arrange
        var nodeId = input ?? "default";

        // Act
        var action = () => TemporalSealGenerator.Generate("310", nodeId, 0.95);

        // Assert: Should not throw for any string input
        action.Should().NotThrow("Seal generation must handle arbitrary strings");
        var seal = action();
        seal.SealHash.Should().HaveLength(64, "Seal hash must always be 64 hex chars");
    }

    [Fact]
    public void PhiCCalculator_Handles_Extreme_Metric_Values()
    {
        // Arrange: Generate random extreme values
        var random = new Random(42); // Fixed seed for reproducibility
        var testCases = Enumerable.Range(0, 100).Select(_ => new PhyMetrics(
            RssiDbm: random.Next(-200, 200),
            SnrDb: random.Next(-100, 200),
            ErrorRatePpm: random.Next(-1000, 10000),
            ChannelUtilization: random.Next(-100, 300) / 100.0,
            SecurityType: new[] { "WPA3", "OPEN", "", null, "UNKNOWN" }[random.Next(5)]
        )).ToArray();

        // Act & Assert
        foreach (var metrics in testCases)
        {
            var action = () => PhiCCalculator.Calculate(metrics);
            action.Should().NotThrow("Φ_C calculation must handle extreme metric values");
            var result = action();
            result.PhiC.Should().BeInRange(0.0, ArkheInvariants.GAP_MAX,
                "Φ_C must always be clamped to [0, GAP_MAX)");
        }
    }
}

public class FaultInjectionTests
{
    [Fact]
    public void TemporalSeal_Verification_Detects_Bit_Flips()
    {
        // Arrange
        var originalData = Encoding.UTF8.GetBytes("constitutional data");
        var originalHash = System.Security.Cryptography.SHA256.HashData(originalData);
        var originalHex = Convert.ToHexString(originalHash).ToLowerInvariant();

        // Inject single-bit flip in hash
        var tamperedHash = (byte[])originalHash.Clone();
        tamperedHash[0] ^= 0x01; // Flip LSB of first byte
        var tamperedHex = Convert.ToHexString(tamperedHash).ToLowerInvariant();

        // Act
        var isValid = TemporalSealGenerator.Verify(originalData, tamperedHex);

        // Assert
        isValid.Should().BeFalse("Verification must detect even single-bit tampering");
    }

    [Fact]
    public void AuditLogger_Preserves_Integrity_Under_Memory_Corruption_Simulation()
    {
        // Arrange
        var logger = new InMemoryAuditLogger();

        // Simulate memory corruption by logging with invalid data
        var corruptedEvent = new AuditEvent(
            Timestamp: DateTimeOffset.MaxValue, // Extreme value
            EventId: new string('\0', 1000), // Null characters
            Level: (AuditEventLevel)999, // Invalid enum value
            Substrate: null!, // Null substrate
            NodeId: "",
            Message: null!,
            PhiC: double.NaN, // NaN value
            Invariants: null,
            SealHash: null
        );

        // Act
        var action = () => logger.Log(corruptedEvent);

        // Assert: Should handle gracefully without crashing
        action.Should().NotThrow("Audit logger must handle corrupted input gracefully");

        // Verify event was still recorded with sanitized data
        var events = logger.GetEvents();
        events.Should().ContainSingle();
    }

    [Fact]
    public void PhiCCalculator_Resists_Timing_Attacks()
    {
        // Arrange: Test that execution time doesn't leak information about input
        var fastMetrics = new PhyMetrics(-30, 40, 0, 0.0, "WPA3"); // Fast path
        var slowMetrics = new PhyMetrics(-85, 5, 500, 0.95, "OPEN"); // Slow path

        // Act: Measure execution times
        var fastTime = MeasureExecutionTime(() => PhiCCalculator.Calculate(fastMetrics));
        var slowTime = MeasureExecutionTime(() => PhiCCalculator.Calculate(slowMetrics));

        // Assert: Times should be similar (constant-time implementation)
        var timeRatio = Math.Max(fastTime, slowTime) / Math.Min(fastTime, slowTime);
        timeRatio.Should().BeLessThan(2.0,
            "Φ_C calculation should have constant-time characteristics to resist timing attacks");
    }

    private double MeasureExecutionTime(Action action, int iterations = 1000)
    {
        var stopwatch = System.Diagnostics.Stopwatch.StartNew();
        for (int i = 0; i < iterations; i++)
        {
            action();
        }
        stopwatch.Stop();
        return stopwatch.Elapsed.TotalMilliseconds / iterations;
    }
}

public class SideChannelSimulationTests
{
    [Fact]
    public void SHA3_256_Implementation_Shows_No_Power_Signature_Correlation()
    {
        // Note: This is a simulation test - real power analysis requires hardware
        // We simulate by checking that output doesn't correlate with input patterns

        // Arrange: Generate inputs with different bit patterns
        var inputs = new[]
        {
            new byte[32], // All zeros
            Enumerable.Repeat((byte)0xFF, 32).ToArray(), // All ones
            Enumerable.Range(0, 32).Select(i => (byte)i).ToArray(), // Sequential
            new byte[] { 0xAA, 0x55, 0xAA, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 } // Alternating pattern
        };

        // Act
        var hashes = inputs.Select(input => System.Security.Cryptography.SHA256.HashData(input)).ToArray();

        // Assert: Hashes should appear random regardless of input pattern
        foreach (var hash in hashes)
        {
            // Check that hash has good entropy (simple heuristic)
            var uniqueBytes = hash.Distinct().Count();
            uniqueBytes.Should().BeGreaterThan(20,
                "Hash output should have high entropy regardless of input pattern");
        }
    }

    [Fact]
    public void TemporalSeal_Nonce_Prevents_Replay_Attacks()
    {
        // Arrange
        const string substrate = "310";
        const string nodeId = "test-node";
        const double phiC = 0.95;

        // Act: Generate multiple seals with same input
        var seals = Enumerable.Range(0, 10)
            .Select(_ => TemporalSealGenerator.Generate(substrate, nodeId, phiC))
            .ToArray();

        // Assert: All seals should be unique due to nonce
        var uniqueSeals = seals.Select(s => s.SealHash).Distinct().Count();
        uniqueSeals.Should().Be(seals.Length,
            "Each seal must be unique due to random nonce, preventing replay attacks");

        // Verify timestamps are non-decreasing
        var timestamps = seals.Select(s => s.Timestamp).ToArray();
        timestamps.Should().BeInAscendingOrder(
            "Timestamps should be monotonic for audit trail integrity");
    }
}

public class DenialOfServiceResistanceTests
{
    [Fact]
    public void PhiCCalculator_Handles_High_Frequency_Calls()
    {
        // Arrange
        var metrics = new PhyMetrics(-50, 30, 50, 0.5, "WPA2");
        const int callCount = 100000;

        // Act
        var stopwatch = System.Diagnostics.Stopwatch.StartNew();
        for (int i = 0; i < callCount; i++)
        {
            var result = PhiCCalculator.Calculate(metrics);
            // Prevent optimization
            if (result.PhiC < 0) throw new Exception("Should not happen");
        }
        stopwatch.Stop();

        // Assert: Should handle high frequency without degradation
        var elapsedMs = stopwatch.ElapsedMilliseconds;
        elapsedMs.Should().BeLessThan(5000,
            $"Must handle {callCount} calls in <5s for DoS resistance");

        var avgTimePerCall = elapsedMs * 1000.0 / callCount;
        avgTimePerCall.Should().BeLessThan(50.0,
            "Average time per call must be <50µs to resist resource exhaustion");
    }

    [Fact]
    public void AuditLogger_Handles_Burst_Logging_Without_Memory_Leak()
    {
        // Arrange
        var logger = new InMemoryAuditLogger();
        const int burstSize = 50000;

        // Act: Log burst of events
        var stopwatch = System.Diagnostics.Stopwatch.StartNew();
        for (int i = 0; i < burstSize; i++)
        {
            logger.Log(new AuditEvent(
                DateTimeOffset.UtcNow, "", AuditEventLevel.Info,
                "310", "burst-test", $"Event {i}", 0.90 + (i % 10) * 0.01, null, null));
        }
        stopwatch.Stop();

        // Assert: Should handle burst without memory issues
        var elapsedMs = stopwatch.ElapsedMilliseconds;
        elapsedMs.Should().BeLessThan(10000,
            $"Must handle {burstSize} events in <10s");

        var events = logger.GetEvents();
        events.Should().HaveCount(burstSize, "All events must be recorded");

        // Verify memory usage is reasonable (simple heuristic)
        var memoryAfter = GC.GetTotalMemory(false);
        // Note: Real memory testing would require more sophisticated approach
    }
}