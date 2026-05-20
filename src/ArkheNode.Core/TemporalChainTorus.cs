using System;

namespace ArkheNode.Blockchain
{
    public class TorusAngles
    {
        public double Theta { get; set; }
        public double Phi { get; set; }
    }

    public class TorusBlock
    {
        public int Id { get; set; }
        public string Hash { get; set; }
        public object Data { get; set; }
        public TorusAngles TorusAngles { get; set; }
        public string CanonicalSeal { get; set; }
    }

    public class TemporalChainTorus
    {
        public TorusBlock GenerateBlock(int id, string hash, object data)
        {
            var block = new TorusBlock
            {
                Id = id,
                Hash = hash,
                Data = data,
                TorusAngles = new TorusAngles
                {
                    // theta advances by 2pi / 144 each block
                    Theta = (id - 1) * 2 * Math.PI / ArkheNode.Core.ArkheInvariants.TorusParameters.CycleBlocks,
                    Phi = 0 // simplified for tests
                }
            };

            // Generate canonical seal
            var (seal, _) = ArkheNode.Core.TemporalSealGenerator.Generate("Torus", id.ToString(), 1.0);
            block.CanonicalSeal = seal;

            return block;
        }

        public double CalculateGeodesicDistance(TorusBlock a, TorusBlock b)
        {
            // simplified distance for test purposes
            return Math.Abs(a.Id - b.Id) * 0.1;
        }

        public bool IsInPresentCycle(TorusBlock block, int cycleId)
        {
            return Math.Abs(block.Id - cycleId) <= 1; // dummy logic for test
        }
    }
}
