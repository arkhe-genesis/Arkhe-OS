using System;
using Xunit;
using ArkheNode.Biology;

namespace ArkheNode.Biology.Tests
{
    public class BiofotonicaTests
    {
        [Fact]
        public void ProcessPhotons_IncreasesPhiC_Correctly()
        {
            var node = new BiofotonicaOntologica(0.500);
            node.ProcessPhotons(4620000); // Canonical dosage 60s Critical

            Assert.Equal(4620000, node.EmittedPhotons);
            // Delta PhiC = 4620000 * 8.8e-9 = 0.040656
            Assert.True(Math.Abs(node.PhiC - 0.540656) < 1e-6);
        }

        [Fact]
        public void IsGhostPreserved_ReturnsTrue_WhenAboveInvariant()
        {
            var node = new BiofotonicaOntologica(0.600);
            Assert.True(node.IsGhostPreserved());
        }

        [Fact]
        public void IsGhostPreserved_ReturnsFalse_WhenBelowInvariant()
        {
            var node = new BiofotonicaOntologica(0.400);
            Assert.False(node.IsGhostPreserved());
        }

        [Fact]
        public void IsLoopsealValid_ReturnsTrue_ForCanonicalValue()
        {
            var node = new BiofotonicaOntologica(0.600);
            // math.pi/9 scaled is roughly 349065850
            Assert.True(node.IsLoopsealValid(349065850));
            Assert.False(node.IsLoopsealValid(349000000));
        }

        [Fact]
        public void IsHealthy_ReturnsTrue_WhenGhostPreservedAndBelowSovereignGap()
        {
            var node = new BiofotonicaOntologica(0.600);
            Assert.True(node.IsHealthy());
        }
    }
}
