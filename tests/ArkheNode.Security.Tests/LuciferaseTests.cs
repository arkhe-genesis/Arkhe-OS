using System;
using System.Linq;
using FluentAssertions;
using Xunit;
using ArkheNode.Biology;
using ArkheNode.Core;

namespace ArkheNode.Security.Tests;

public class LuciferaseTests
{
    [Fact]
    public void Rate_Zero_Without_Atp()
    {
        var node = new LuciferaseNode("test") { AtpConcMm = 0.0 };
        node.Rate().Should().Be(0.0);
    }

    [Fact]
    public void Rate_Zero_Without_Luciferin()
    {
        var node = new LuciferaseNode("test") { LuciferinConcMm = 0.0 };
        node.Rate().Should().Be(0.0);
    }

    [Fact]
    public void Rate_Positive_With_Substrates()
    {
        var node = new LuciferaseNode("test") { LuciferinConcMm = 1.0, AtpConcMm = 2.0 };
        node.Rate().Should().BeGreaterThan(0.0);
    }

    [Fact]
    public void EmitPulse_Generates_Seal()
    {
        var node = new LuciferaseNode("test");
        var pulse = node.EmitPulse();
        pulse.Seal.Should().NotBeNullOrEmpty();
        pulse.Seal.Should().HaveLength(64);
    }

    [Fact]
    public void GoldenPulse_Duration_Is_Correct()
    {
        var node = new LuciferaseNode("test");
        var pulse = node.EmitGoldenPulse();
        pulse.DurationMs.Should().BeApproximately(5.0 * ArkheInvariants.PHI, 0.01);
    }

    [Fact]
    public void QuantumYield_Is_Above_Ghost()
    {
        var node = new LuciferaseNode("test");
        node.QuantumYield.Should().BeGreaterThan(ArkheInvariants.GHOST);
    }
}
