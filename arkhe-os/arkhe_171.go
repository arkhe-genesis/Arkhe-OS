package main

import (
	"fmt"
)

func InitSubstrate171() {
	fmt.Println("\n[SUBSTRATO 171] Protocolo de Roteamento por Coerência Distribuída")
	engine := NewCosmologyEngine("Default")

	engine.RegisterNode("NODE_A", "Alpha", ScalePlanetary, 0.95, 0.8)
	engine.RegisterNode("NODE_B", "Beta", ScalePlanetary, 0.90, 0.75)
	engine.RegisterNode("GATEWAY", "Gateway", ScaleStellar, 0.99, 0.9)

	nodeAAddr := NewCosmicAddress(ScalePlanetary, 0.95, 0.8, 0.0, 0.0, 0, "Alpha")
	nodeBAddr := NewCosmicAddress(ScalePlanetary, 0.90, 0.75, 0.0, 0.0, 0, "Beta")
	gatewayAddr := NewCosmicAddress(ScaleStellar, 0.99, 0.9, 0.0, 0.0, 0, "Gateway")

	routerA := NewCoherenceRouter(engine, "NODE_A", nodeAAddr)
	routerA.AddNeighbor(engine.Nodes["GATEWAY"])

	// Simulating routing table population from the field
	// Node A learns route to Node B via Gateway
	routerA.UpdateRoute(nodeBAddr.Network(16), 16, "GATEWAY", 0.92, 0.1, 0.5)

	// Direct route (hypothetical quantum tunnel)
	routerA.UpdateRoute(nodeBAddr, 256, "NODE_B", 0.98, 0.01, 0.1)

	packet := []byte("quantum_echo")
	fmt.Printf("Sending packet from A to B (%s)\n", nodeBAddr.String())
	err := routerA.RoutePacket(packet, nodeBAddr)
	if err != nil {
		fmt.Println(err)
	}

	fmt.Printf("Sending packet from A to unknown gateway (%s)\n", gatewayAddr.String())
	err = routerA.RoutePacket(packet, gatewayAddr)
	if err != nil {
		fmt.Println("Expected error:", err)
	}
}
