using System;
using System.Collections.Generic;
using System.Linq;

namespace ArkheNode.Networking
{
    public class Node
    {
        public string Id { get; set; }
        public double X { get; set; }
        public double Y { get; set; }
    }

    public class SacredGeometryRouter
    {
        public SacredGeometryRouter(Dictionary<string, double> parameters)
        {
        }

        public Node SelectNextHop(Node current, List<Node> peers)
        {
            if (peers == null || peers.Count == 0)
            {
                throw new ArgumentException("No available peers for routing");
            }
            return peers.First();
        }
    }
}
