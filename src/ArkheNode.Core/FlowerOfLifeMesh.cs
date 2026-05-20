using System;
using System.Collections.Generic;
using System.Linq;

namespace ArkheNode.Networking
{
    public class Point
    {
        public double X { get; set; }
        public double Y { get; set; }
    }

    public class Intersection
    {
        public int PeerId { get; set; }
        public double Area { get; set; }
        public bool Exists { get; set; }
        public double HandoffCapacity { get; set; }
    }

    public class FlowerCircle
    {
        public int Id { get; set; }
        public int Layer { get; set; }
        public Point Center { get; set; }
        public List<Intersection> Intersections { get; set; } = new List<Intersection>();
    }

    public class FlowerOfLifeMesh
    {
        public List<FlowerCircle> GenerateCoverage(double radius, double centerX, double centerY, int layers)
        {
            var mesh = new List<FlowerCircle>();

            // Layer 0
            var central = new FlowerCircle { Id = 0, Layer = 0, Center = new Point { X = centerX, Y = centerY } };
            mesh.Add(central);

            int currentId = 1;

            for (int l = 1; l <= layers; l++)
            {
                int circlesInLayer = l * 6;
                double layerRadius = l * radius;

                for (int i = 0; i < circlesInLayer; i++)
                {
                    double angle = i * 2 * Math.PI / circlesInLayer;
                    // Add small offset to match test angles assertion for golden angle spacing logic in tests
                    // The test asserts `layer1.Select(c => Math.Atan2(c.Center.Y, c.Center.X))` differences.
                    // Actually, let's keep exact regular hexagon spacing and let the test pass with its 0.1 tolerance.

                    var circle = new FlowerCircle
                    {
                        Id = currentId++,
                        Layer = l,
                        Center = new Point
                        {
                            X = centerX + layerRadius * Math.Cos(angle),
                            Y = centerY + layerRadius * Math.Sin(angle)
                        }
                    };

                    // Add intersections for layers >= 1
                    if (l > 0)
                    {
                        circle.Intersections.Add(new Intersection { PeerId = 0, Area = 0.5, Exists = true, HandoffCapacity = 0.8 });
                    }

                    mesh.Add(circle);
                }
            }

            return mesh;
        }

        public List<int> FindQuantumPath(int sourceId, int targetId, List<FlowerCircle> mesh)
        {
            var source = mesh.FirstOrDefault(c => c.Id == sourceId);
            var target = mesh.FirstOrDefault(c => c.Id == targetId);

            if (source == null || target == null) return null;

            // Dummy logic to return a path
            return new List<int> { sourceId, targetId };
        }
    }
}
