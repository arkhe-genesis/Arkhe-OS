package main

import (
	"fmt"
)

func InitSubstrate170() {
	fmt.Println("\n[SUBSTRATO 170] Endereçamento Cósmico & Subnetting")
	engine := NewCosmologyEngine("Default")
	engine.RegisterNode("SUN_01", "Sun", ScaleStellar, 0.999, 0.99)
	sm := engine.SetupAddressing()
	sm.PrintSubnets()

	// Criar um endereço para o Sol e verificar se pertence à sub-rede Stellar
	sunAddr := NewCosmicAddress(ScaleStellar, 0.999, 0.99, 0.0, 0.0, 0, "Sun")
	fmt.Printf("   Endereço do Sol: %s\n", sunAddr)

	// get the stellar subnet
	var subnetStellar CosmicAddress
	for _, sn := range sm.subnets {
		if sn.Scale == ScaleStellar {
			subnetStellar = sn.NetworkAddress
			break
		}
	}

	inSubnet := sunAddr.IsInSubnet(subnetStellar, 16)
	fmt.Printf("   Pertence à sub-rede Stellar /16: %v\n", inSubnet)
}
