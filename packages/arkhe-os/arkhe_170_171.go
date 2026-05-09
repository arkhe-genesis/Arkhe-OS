package main

import (
	"fmt"
)

func RegisterSubstrates170and171() {
	fmt.Println("\n--- Substrates 170-171: Cosmic Network Addressing & Routing ---")

	fmt.Println("\n[SUBSTRATO 170] Endereçamento Cósmico & Subnetting")
	engine := NewCosmologyEngine("RoutingTest")

	sm := engine.SetupAddressing()
	sm.PrintSubnets()

	// Criar um endereço para o Sol e verificar se pertence à sub-rede Stellar
	sunAddr := NewCosmicAddress(ScaleStellar, 0.999, 0.99, 0.0, 0.0, 0, "Sun")
	fmt.Printf("   Endereço do Sol: %s\n", sunAddr)

	// Buscar a subnet Stellar correta iterando
	var subnetStellar CosmicAddress
	found := false
	for _, sn := range sm.subnets {
		if sn.Scale == ScaleStellar {
			subnetStellar = sn.NetworkAddress
			found = true
			break
		}
	}

	if found {
		inSubnet := sunAddr.IsInSubnet(subnetStellar, 16)
		fmt.Printf("   Pertence à sub-rede Stellar /16: %v\n", inSubnet)
	} else {
		fmt.Println("   Erro: Subnet Stellar não encontrada.")
	}

	fmt.Println("\n[SUBSTRATO 171] Roteamento por Coerência Distribuída")
	// registrar nós de exemplo
	sun := &CosmicNode{ID: "SUN_01", Name: "Sol", Scale: ScaleStellar, Coherence: 0.999, Resonance: 0.99, InformationContent: 1e40, Entropy: 1e35}
	earth := &CosmicNode{ID: "EARTH_01", Name: "Terra", Scale: ScalePlanetary, Coherence: 0.997, Resonance: 0.98, InformationContent: 1e30, Entropy: 1e25}
	mars := &CosmicNode{ID: "MARS_01", Name: "Marte", Scale: ScalePlanetary, Coherence: 0.995, Resonance: 0.97, InformationContent: 1e28, Entropy: 1e23}
	engine.RegisterNodeStruct(sun)
	engine.RegisterNodeStruct(earth)
	engine.RegisterNodeStruct(mars)
	// estabelecer canais entre eles (simulação)
	chSE, _ := engine.EstablishTeleportationChannel("SUN_01", "EARTH_01")
	chSM, _ := engine.EstablishTeleportationChannel("SUN_01", "MARS_01")
	// inicializar roteador no Sol
	engine.EnableCoherenceRouting()
	router := NewCoherenceRouter(engine, "SUN_01", sunAddr)
	// testar roteamento
	earthAddr := NewCosmicAddress(ScalePlanetary, 0.997, 0.98, 0, 0, 0, "Terra")

	err := router.RoutePacket([]byte("hello"), earthAddr)
	if err == nil {
		fmt.Printf("   Rota para Terra via CoherenceRouter sucesso.\n")
	} else {
		fmt.Printf("   Falha: %v\n", err)
	}
	_ = chSE
	_ = chSM
}
