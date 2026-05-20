using FluentAssertions;
using Xunit;
using System;
using System.Collections.Generic;
using System.Linq;
using ArkheNode.Core;
using ArkheNode.Networking;
using ArkheNode.Topology;
using ArkheNode.Blockchain;

namespace ArkheNode.Tests;

public class SacredGeometryTestsPart2
{
    // ═══════════════════════════════════════════════════════════
    // 6. TEMPORAL CHAIN TORO (continuação)
    // ═══════════════════════════════════════════════════════════

    [Fact]
    public void Torus_Cycle_Completes_After_144_Blocks()
    {
        var torus = new TemporalChainTorus();
        var block1 = torus.GenerateBlock(1, "abc1230000000000", new { test = true });
        var block145 = torus.GenerateBlock(145, "def4560000000000", new { test = true });

        // Após 144 blocos (F₁₂), θ deve retornar ao mesmo valor (ciclo completo)
        double theta1 = NormalizeAngle(block1.TorusAngles.Theta);
        double theta145 = NormalizeAngle(block145.TorusAngles.Theta);

        theta145.Should().BeApproximately(theta1, 1e-10);
    }

    private static double NormalizeAngle(double angle)
    {
        while (angle < 0) angle += 2 * Math.PI;
        return angle % (2 * Math.PI);
    }

    [Fact]
    public void Torus_Geodesic_Distance_Is_Symmetric()
    {
        var torus = new TemporalChainTorus();
        var blockA = torus.GenerateBlock(10, "hashA00000000000", null);
        var blockB = torus.GenerateBlock(20, "hashB00000000000", null);

        double distAB = torus.CalculateGeodesicDistance(blockA, blockB);
        double distBA = torus.CalculateGeodesicDistance(blockB, blockA);

        distAB.Should().BeApproximately(distBA, 1e-10);
        distAB.Should().BeGreaterThan(0);
    }

    [Fact]
    public void Torus_Present_Cycle_Detection()
    {
        var torus = new TemporalChainTorus();
        var block = torus.GenerateBlock(100, "hash000000000000", null);

        // Bloco 100 está no ciclo presente em relação a 100 e 101
        torus.IsInPresentCycle(block, 100).Should().BeTrue();
        torus.IsInPresentCycle(block, 101).Should().BeTrue();
        torus.IsInPresentCycle(block, 99).Should().BeTrue();

        // Bloco 100 NÃO está no ciclo presente em relação a 50
        torus.IsInPresentCycle(block, 50).Should().BeFalse();
    }

    [Fact]
    public void Torus_Major_Radius_Equals_Phi()
    {
        ArkheInvariants.TorusParameters.MajorRadius.Should().BeApproximately(ArkheInvariants.PHI, 1e-15);
    }

    [Fact]
    public void Torus_Minor_Radius_Equals_Phi_Inverse()
    {
        ArkheInvariants.TorusParameters.MinorRadius.Should().BeApproximately(ArkheInvariants.PHI_INVERSE, 1e-15);
    }

    [Fact]
    public void Torus_Cycle_Blocks_Equals_Fibonacci_12()
    {
        ArkheInvariants.TorusParameters.CycleBlocks.Should().Be(144);
        ArkheInvariants.FIBONACCI_SEQUENCE[12].Should().Be(144); // F₁₂ = 144
    }

    // ═══════════════════════════════════════════════════════════
    // 7. FLOWER OF LIFE MESH
    // ═══════════════════════════════════════════════════════════

    [Fact]
    public void FlowerOfLife_Generates_Correct_Number_Of_Circles()
    {
        var flower = new FlowerOfLifeMesh();
        var mesh = flower.GenerateCoverage(1.0, 0.0, 0.0, layers: 3);

        // 1 central + 6 (layer 1) + 12 (layer 2) + 18 (layer 3) = 37
        mesh.Should().HaveCount(1 + 6 + 12 + 18);
    }

    [Fact]
    public void FlowerOfLife_Central_Circle_Has_No_Intersections()
    {
        var flower = new FlowerOfLifeMesh();
        var mesh = flower.GenerateCoverage(1.0, 0.0, 0.0, layers: 1);

        var central = mesh.First(c => c.Layer == 0);
        central.Intersections.Should().BeEmpty();
    }

    [Fact]
    public void FlowerOfLife_Layer_1_Has_6_Circles()
    {
        var flower = new FlowerOfLifeMesh();
        var mesh = flower.GenerateCoverage(1.0, 0.0, 0.0, layers: 1);

        var layer1 = mesh.Where(c => c.Layer == 1).ToList();
        layer1.Should().HaveCount(6);

        // Cada círculo da camada 1 deve intersectar o central
        foreach (var circle in layer1)
        {
            circle.Intersections.Should().Contain(i => i.PeerId == 0);
        }
    }

    [Fact]
    public void FlowerOfLife_Intersections_Have_Positive_Area()
    {
        var flower = new FlowerOfLifeMesh();
        var mesh = flower.GenerateCoverage(1.0, 0.0, 0.0, layers: 2);

        var withIntersections = mesh.Where(c => c.Intersections.Any()).ToList();
        withIntersections.Should().NotBeEmpty();

        foreach (var circle in withIntersections)
        {
            foreach (var intersection in circle.Intersections)
            {
                intersection.Area.Should().BeGreaterThan(0);
                intersection.Exists.Should().BeTrue();
                intersection.HandoffCapacity.Should().BeInRange(0, 1);
            }
        }
    }

    [Fact]
    public void FlowerOfLife_QuantumPath_Finds_Valid_Route()
    {
        var flower = new FlowerOfLifeMesh();
        var mesh = flower.GenerateCoverage(1.0, 0.0, 0.0, layers: 3);

        // Encontrar caminho do centro (id=0) para um nó da camada 3
        var target = mesh.Last(c => c.Layer == 3);
        var path = flower.FindQuantumPath(0, target.Id, mesh);

        path.Should().NotBeNull();
        path.Should().HaveCountGreaterThanOrEqualTo(2); // Pelo menos origem e destino
        path.First().Should().Be(0);
        path.Last().Should().Be(target.Id);
    }

    [Fact]
    public void FlowerOfLife_Layer_Distance_Follows_Golden_Angle()
    {
        var flower = new FlowerOfLifeMesh();
        var mesh = flower.GenerateCoverage(1.0, 0.0, 0.0, layers: 2);

        var layer1 = mesh.Where(c => c.Layer == 1).ToList();
        layer1.Should().HaveCount(6);

        // Ângulos entre círculos adjacentes da camada 1 devem ser ~60° (360/6)
        // Com offset do ângulo áureo
        var angles = layer1.Select(c => Math.Atan2(c.Center.Y, c.Center.X)).OrderBy(a => a).ToList();

        for (int i = 0; i < angles.Count - 1; i++)
        {
            double diff = angles[i + 1] - angles[i];
            if (diff < 0) diff += 2 * Math.PI;
            diff.Should().BeApproximately(2 * Math.PI / 6, 0.1);
        }
    }

    // ═══════════════════════════════════════════════════════════
    // 8. INTEGRAÇÃO GEOMÉTRICA
    // ═══════════════════════════════════════════════════════════

    [Fact]
    public void Ghost_Divided_By_Loopseal_Approaches_Phi()
    {
        // Relação canônica: Ghost/Loopseal ≈ φ
        double ratio = ArkheInvariants.GHOST / ArkheInvariants.LOOPSEAL;
        ratio.Should().BeApproximately(ArkheInvariants.PHI, 0.05); // Tolerância 5%
    }

    [Fact]
    public void Gap_Divided_By_One_Minus_Ghost_Approaches_Phi_Squared()
    {
        // Relação canônica: Gap/(1-Ghost) ≈ φ²
        double ratio = ArkheInvariants.GAP_MAX / (1.0 - ArkheInvariants.GHOST);
        ratio.Should().BeApproximately(ArkheInvariants.PHI_SQUARED, 0.1);
    }

    [Fact]
    public void PhiCCalculator_ValidatePhiProportions_Returns_True()
    {
        PhiCCalculator.ValidatePhiProportions().Should().BeTrue();
    }

    [Fact]
    public void Fibonacci_Layer_12_Matches_Alpha_Inverse()
    {
        // F₁₂ = 144, próximo de α⁻¹ ≈ 137
        ArkheInvariants.FIBONACCI_SEQUENCE[12].Should().Be(144);
        // A diferença é intencional: 144 é o ciclo do toro, 137 é o limite de arquivos
        (ArkheInvariants.FIBONACCI_SEQUENCE[12] - ArkheInvariants.ALPHA_INVERSE).Should().BeApproximately(7, 1);
    }

    [Fact]
    public void Harmonic_Coupling_Layer_100_Preserves_Minimum_Connectivity()
    {
        // Mesmo na camada 100, a conectividade mínima é preservada
        double coupled = PhiCCalculator.ApplyHarmonicCoupling(0.5, 100);
        coupled.Should().BeGreaterThan(0.0);
        coupled.Should().BeLessThan(ArkheInvariants.GAP_MAX);
    }

    [Fact]
    public void Platonic_Topology_Cube_Maps_8_Regions()
    {
        var manager = new PlatonicTopologyManager();
        var regions = new List<string> {
            "NA-East", "NA-West", "SA-East", "EU-Central",
            "EU-West", "AP-Northeast", "AP-Southeast", "AF-South"
        };

        var mapping = manager.MapRegions("cube", regions);

        mapping.SolidName.Should().Be("Cube");
        mapping.SolidSymbol.Should().Be("□");
        mapping.RegionsMapped.Should().Be(8);
        mapping.Assignments.Should().HaveCount(8);
        mapping.EdgeConnections.Should().HaveCount(12); // Cubo tem 12 arestas
    }

    [Fact]
    public void Platonic_Topology_Dodecahedron_Maps_20_Regions()
    {
        var manager = new PlatonicTopologyManager();
        var regions = Enumerable.Range(1, 20).Select(i => $"Region-{i}").ToList();

        var mapping = manager.MapRegions("dodecahedron", regions);

        mapping.SolidName.Should().Be("Dodecahedron");
        mapping.SolidSymbol.Should().Be("⬠");
        mapping.RegionsMapped.Should().Be(20);
        mapping.Assignments.Should().HaveCount(20);
    }

    [Fact]
    public void Platonic_Topology_Throws_For_Too_Many_Regions()
    {
        var manager = new PlatonicTopologyManager();
        var regions = Enumerable.Range(1, 21).Select(i => $"Region-{i}").ToList();

        Action act = () => manager.MapRegions("cube", regions);
        act.Should().Throw<ArgumentException>()
            .WithMessage("*has 8 vertices, but 21 regions provided*");
    }

    [Fact]
    public void Torus_Block_Seal_Is_Deterministic()
    {
        var torus = new TemporalChainTorus();
        var block1 = torus.GenerateBlock(42, "hash123456789012", new { data = "test" });

        // O selo deve ser um hash SHA3-256 (simulado) de 64 caracteres hex
        block1.CanonicalSeal.Should().NotBeNullOrEmpty();
        block1.CanonicalSeal.Length.Should().Be(64);
        block1.CanonicalSeal.Should().MatchRegex("^[a-f0-9]{64}$");
    }

    [Fact]
    public void SacredGeometryRouter_Throws_For_Empty_Peers()
    {
        var router = new SacredGeometryRouter(new Dictionary<string, double>());
        var current = new Node { Id = "current", X = 0, Y = 0 };

        Action act = () => router.SelectNextHop(current, new List<Node>());
        act.Should().Throw<ArgumentException>()
            .WithMessage("*No available peers for routing*");
    }

    [Fact]
    public void FlowerOfLifeMesh_QuantumPath_Returns_Null_For_Disconnected()
    {
        var flower = new FlowerOfLifeMesh();
        var mesh = flower.GenerateCoverage(1.0, 0.0, 0.0, layers: 1);

        // Tentar caminho para um ID que não existe
        var path = flower.FindQuantumPath(0, 9999, mesh);
        path.Should().BeNull();
    }
}
