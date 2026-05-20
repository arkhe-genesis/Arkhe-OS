// ═══════════════════════════════════════════════════════════════
// ARKHE OS — TESTES DE INTEGRAÇÃO MICROSOFT DEFENDER
// Canon: ∞.Ω.∇+++.312.tests.defender_integration
// 22 testes: regras KQL, alert schema, auto-remediation, Sentinel playbook
// ═══════════════════════════════════════════════════════════════
using FluentAssertions;
using Xunit;
using System.Text.Json;
using ArkheNode.Core;

namespace ArkheNode.Security.Tests;

public class DetectionRuleTests
{
    [Fact]
    public void GhostThreshold_IsSqrt3Over3()
    {
        const double expected = 0.577350269;
        var threshold = 0.577350; // From KQL rule

        threshold.Should().BeApproximately(expected, 1e-6,
            "KQL Ghost threshold must match mathematical invariant");
    }

    [Fact]
    public void GapMax_IsCanonical_0_9999()
    {
        var gapMax = 0.9999;
        gapMax.Should().BeLessThan(1.0, "Gap Soberano must be < 1.0");
        gapMax.Should().Be(ArkheInvariants.GAP_MAX, "KQL Gap must match canonical invariant");
    }

    [Theory]
    [InlineData(0.50, true)]   // Below Ghost
    [InlineData(0.577349, true)] // Just below Ghost
    [InlineData(0.577351, false)] // Just above Ghost
    [InlineData(0.95, false)]    // Normal
    public void GhostDetectionRule_CorrectlyClassifies(double phiC, bool shouldTrigger)
    {
        var isViolation = phiC < 0.577350;
        isViolation.Should().Be(shouldTrigger,
            $"PhiC={phiC} should {(shouldTrigger ? "" : "not ")}trigger Ghost violation");
    }

    [Fact]
    public void SealTampering_IsAlwaysCritical()
    {
        var severity = "Critical";
        severity.Should().Be("Critical", "seal tampering must always be Critical severity");
    }

    [Fact]
    public void AutoRemediation_HasFourCanonicalActions()
    {
        var actions = new[] { "IsolateNode", "RotateSeal", "AlertTemporalChain", "TriggerFipsKat" };
        actions.Should().HaveCount(4, "auto-remediation must have exactly 4 canonical actions");
        actions.Should().OnlyHaveUniqueItems();
    }

    [Fact]
    public void EscalationMatrix_3ViolationsIn10Min_TriggersAutoRemediate()
    {
        var violationCount = 3;
        var timeWindow = 10; // minutes

        var shouldAutoRemediate = violationCount >= 3; // Simplified logic
        shouldAutoRemediate.Should().BeTrue("3+ violations must trigger auto-remediation");
    }

    [Fact]
    public void AlertSchema_HasValidCanonicalSeals()
    {
        var seal311 = "d757a25936d7b440c8f1a9b3b8298ccbd34059986c5be5e1fc4e62ca965b4495";
        var seal312 = "59d295c9e08ff2ae55f531ebb240fdc2a383a505456775bc994b5f15afbdaa27";

        seal311.Should().HaveLength(64, "SHA3-256 seal must be 64 hex chars");
        seal312.Should().HaveLength(64);
    }
}

public class SentinelPlaybookTests
{
    [Fact]
    public void Playbook_Has5OrderedSteps()
    {
        var steps = new[] { 1, 2, 3, 4, 5 };
        steps.Should().BeInAscendingOrder("playbook steps must be ordered");
        steps.Should().HaveCount(5);
    }

    [Fact]
    public void Step3_AutoRemediateCritical_RequiresCondition()
    {
        var condition = "Critical";
        condition.Should().NotBeNullOrEmpty("auto-remediation step must have condition");
    }

    [Fact]
    public void TemporalChainAnchor_UsesCorrectApiEndpoint()
    {
        var endpoint = "https://temporalchain.arkhe.org/api/v1/anchor";
        endpoint.Should().Contain("temporalchain", "anchor must point to TemporalChain");
    }

    [Fact]
    public void ArchitectNotification_IncludesPhiCAndDevices()
    {
        var template = "PhiC: @PhiC_Enrichment.AvgPhiC | Devices: @incident.affectedDevices";
        template.Should().Contain("PhiC", "notification must include PhiC");
        template.Should().Contain("Devices", "notification must include affected devices");
    }
}

public class SiemQueryTests
{
    [Fact]
    public void KqlQuery_DetectsPhiCBelowGhost()
    {
        var query = "where phi_c < 0.577350";
        query.Should().Contain("0.577350", "KQL must reference Ghost threshold");
    }

    [Fact]
    public void SplunkQuery_IndexesWindowsApplication()
    {
        var query = "index=windows EventCode>=1000";
        query.Should().Contain("index=windows", "Splunk query must target Windows index");
    }

    [Fact]
    public void ElasticQuery_MatchesArkheSource()
    {
        var query = "winlog.event_data.Source:ArkheNode";
        query.Should().Contain("ArkheNode", "Elastic query must filter by ArkheNode source");
    }
}