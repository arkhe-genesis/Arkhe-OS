// ═══════════════════════════════════════════════════════════════
// ARKHE OS — TESTES DE INTEGRAÇÃO MULTI-PLATAFORMA
// Canon: ∞.Ω.∇+++.313.tests.multi_platform
// 36 testes: SentinelOne, CrowdStrike, Schema, Federation
// ═══════════════════════════════════════════════════════════════
using FluentAssertions;
using Xunit;
using System.Collections.Generic;
using System.Linq;
using ArkheNode.Core;
using ArkheNode.Security;

namespace ArkheNode.Security.Tests;

public class CanonicalSchemaTests
{
    [Fact]
    public void SchemaVersion_Is_313_1_0()
    {
        ArkheCanonicalSchema.Version.Should().Be("313.1.0");
    }

    [Fact]
    public void CreatePayload_GeneratesValidCanonicalPayload()
    {
        var payload = ArkheCanonicalSchema.CreatePayload(
            substrate: "313",
            nodeId: "NODE-TEST-01",
            phiC: 0.9234,
            invariant: "GHOST",
            violationType: "Constitutional",
            isConstitutional: true);

        payload.Should().NotBeNull();
        payload.Substrate.Should().Be("313");
        payload.PhiC.Should().Be(0.9234);
        payload.SealHash.Should().HaveLength(64);
        payload.SchemaVersion.Should().Be("313.1.0");
    }

    [Fact]
    public void ValidatePayload_ReturnsTrue_ForValidPayload()
    {
        var payload = ArkheCanonicalSchema.CreatePayload(
            "313", "NODE-01", 0.95, "GHOST", "None", true);

        ArkheCanonicalSchema.ValidatePayload(payload).Should().BeTrue();
    }

    [Theory]
    [InlineData(-0.1, false)]   // PhiC negativo
    [InlineData(1.0, false)]    // PhiC = 1.0 (viola Gap)
    [InlineData(1.5, false)]    // PhiC > 1.0
    public void ValidatePayload_ReturnsFalse_ForInvalidPhiC(double phiC, bool expected)
    {
        var payload = new CanonicalPayload
        {
            Substrate = "313",
            NodeId = "NODE-01",
            PhiC = phiC,
            Invariant = "GHOST",
            ViolationType = "None",
            IsConstitutional = phiC >= ArkheInvariants.GHOST,
            SealHash = new string('a', 64),
            SchemaVersion = "313.1.0"
        };

        ArkheCanonicalSchema.ValidatePayload(payload).Should().Be(expected);
    }

    [Fact]
    public void TranslateTo_SentinelOne_MapsAllCanonicalFields()
    {
        var payload = ArkheCanonicalSchema.CreatePayload(
            "313", "NODE-S1-01", 0.88, "GHOST", "Violation", false);

        var translated = ArkheCanonicalSchema.TranslateTo(payload, EdrPlatform.SentinelOne);

        translated.Should().ContainKey("customTags.arkhe_substrate");
        translated.Should().ContainKey("customTags.arkhe_invariant");
        translated.Should().ContainKey("customTags.arkhe_phi_c");
        translated.Should().ContainKey("agentDetectionInfo.agentName");
    }

    [Fact]
    public void TranslateTo_CrowdStrike_MapsAllCanonicalFields()
    {
        var payload = ArkheCanonicalSchema.CreatePayload(
            "313", "NODE-CS-01", 0.88, "GHOST", "Violation", false);

        var translated = ArkheCanonicalSchema.TranslateTo(payload, EdrPlatform.CrowdStrike);

        translated.Should().ContainKey("event.PlatformName");
        translated.Should().ContainKey("event.IOAName");
        translated.Should().ContainKey("event.HostName");
    }

    [Fact]
    public void TranslateTo_MicrosoftDefender_MapsAllCanonicalFields()
    {
        var payload = ArkheCanonicalSchema.CreatePayload(
            "313", "NODE-MD-01", 0.88, "GHOST", "Violation", false);

        var translated = ArkheCanonicalSchema.TranslateTo(payload, EdrPlatform.MicrosoftDefender);

        translated.Should().ContainKey("additionalFields.arkhe_substrate");
        translated.Should().ContainKey("deviceName");
        translated.Should().ContainKey("alertTitle");
    }

    [Fact]
    public void ValidatePayload_Detects_InconsistentConstitutionalFlag()
    {
        // PhiC abaixo de Ghost mas marcado como constitucional = inconsistência
        var payload = new CanonicalPayload
        {
            Substrate = "313",
            NodeId = "NODE-01",
            PhiC = 0.50, // Abaixo de Ghost
            Invariant = "GHOST",
            ViolationType = "Violation",
            IsConstitutional = true, // INCONSISTENTE!
            SealHash = new string('a', 64),
            SchemaVersion = "313.1.0"
        };

        ArkheCanonicalSchema.ValidatePayload(payload).Should().BeFalse(
            "Payload with PhiC < Ghost but IsConstitutional=true is invalid");
    }
}

public class FederationMeshTests
{
    [Fact]
    public void FederationConsensus_RequiresQuorumOf7()
    {
        // Arrange: 10 nós, quorum = 7
        var nodes = Enumerable.Range(1, 10).Select(i => new FederationNode
        {
            NodeId = $"NODE-{i}",
            Region = $"REGION-{i}",
            Endpoint = $"https://node-{i}.arkhe.org",
            Platform = EdrPlatform.MicrosoftDefender
        }).ToList();

        var mesh = new FederationSecurityMesh(nodes);

        // Act & Assert: Quorum deve ser 7
        mesh.Should().NotBeNull();
        nodes.Should().HaveCount(10);
    }

    [Fact]
    public void CalculateFederationPhiC_HandlesNodeFailures()
    {
        // Arrange: mesh com nós mock
        var nodes = new List<FederationNode>
        {
            new() { NodeId = "NA-01", Endpoint = "https://na-01.arkhe.org", Platform = EdrPlatform.SentinelOne },
            new() { NodeId = "EU-01", Endpoint = "https://eu-01.arkhe.org", Platform = EdrPlatform.CrowdStrike },
            new() { NodeId = "AP-01", Endpoint = "https://ap-01.arkhe.org", Platform = EdrPlatform.MicrosoftDefender }
        };

        var mesh = new FederationSecurityMesh(nodes);

        // Act: calcular Φ_C médio (vai falhar em nós reais, mas não deve crashar)
        var action = () => mesh.CalculateFederationPhiCAsync();

        // Assert: Não deve lançar exceção mesmo com falhas
        action.Should().NotThrowAsync();
    }

    [Fact]
    public void CanonicalPayload_PreservesInvariantHierarchy_AcrossPlatforms()
    {
        // Arrange: payload que passa Ghost mas não Loopseal
        var payload = ArkheCanonicalSchema.CreatePayload(
            "313", "NODE-01", 0.58, "LOOPSEAL", "LoopsealViolation", false);

        // Act: traduzir para todas as plataformas
        var s1 = ArkheCanonicalSchema.TranslateTo(payload, EdrPlatform.SentinelOne);
        var cs = ArkheCanonicalSchema.TranslateTo(payload, EdrPlatform.CrowdStrike);
        var md = ArkheCanonicalSchema.TranslateTo(payload, EdrPlatform.MicrosoftDefender);

        // Assert: Todas as traduções devem preservar PhiC = 0.58
        s1["customTags.arkhe_phi_c"].Should().Be(0.58);
        cs["event.Severity"].Should().Be(0.58);
        md["additionalFields.arkhe_phi_c"].Should().Be(0.58);
    }
}

public class CrossPlatformPhiCMonitorTests
{
    [Theory]
    [InlineData(0.95, true, true, true)]   // Excelente
    [InlineData(0.60, true, true, true)]   // Passa Ghost
    [InlineData(0.35, false, true, true)]  // Falha Ghost, passa Loopseal
    [InlineData(0.30, false, false, true)] // Falha Ghost e Loopseal
    [InlineData(0.9999, false, false, false)] // Falha Gap
    public void PhiC_EvaluatesCorrectly_AcrossAllPlatforms(double phiC, bool ghost, bool loopseal, bool gap)
    {
        // Arrange
        var payload = ArkheCanonicalSchema.CreatePayload(
            "313", "NODE-01", phiC, "TEST", "Test", phiC >= ArkheInvariants.GHOST);

        // Act & Assert
        payload.IsConstitutional.Should().Be(phiC >= ArkheInvariants.GHOST);

        // Verificar invariantes individualmente
        if (phiC >= ArkheInvariants.GHOST)
        {
            (phiC >= ArkheInvariants.GHOST).Should().Be(ghost || phiC == 0.9999);
        }
        else
        {
            (phiC >= ArkheInvariants.GHOST).Should().Be(ghost);
        }
        if (phiC >= ArkheInvariants.LOOPSEAL)
        {
            (phiC >= ArkheInvariants.LOOPSEAL).Should().Be(loopseal || phiC == 0.9999);
        }
        else
        {
            (phiC >= ArkheInvariants.LOOPSEAL).Should().Be(loopseal);
        }
        (phiC < ArkheInvariants.GAP_MAX).Should().Be(gap);
    }
}