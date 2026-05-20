using System;
using System.Collections.Generic;

namespace ArkheNode.Topology
{
    public class TopologyMapping
    {
        public string SolidName { get; set; }
        public string SolidSymbol { get; set; }
        public int RegionsMapped { get; set; }
        public List<string> Assignments { get; set; } = new List<string>();
        public List<object> EdgeConnections { get; set; } = new List<object>();
    }

    public class PlatonicTopologyManager
    {
        public TopologyMapping MapRegions(string shape, List<string> regions)
        {
            if (shape.ToLower() == "cube")
            {
                if (regions.Count > 8)
                {
                    throw new ArgumentException($"Cube has 8 vertices, but {regions.Count} regions provided");
                }
                return new TopologyMapping
                {
                    SolidName = "Cube",
                    SolidSymbol = "□",
                    RegionsMapped = regions.Count,
                    Assignments = new List<string>(regions),
                    EdgeConnections = new List<object>(new object[12])
                };
            }
            else if (shape.ToLower() == "dodecahedron")
            {
                return new TopologyMapping
                {
                    SolidName = "Dodecahedron",
                    SolidSymbol = "⬠",
                    RegionsMapped = regions.Count,
                    Assignments = new List<string>(regions)
                };
            }
            throw new ArgumentException("Unknown shape");
        }
    }
}
