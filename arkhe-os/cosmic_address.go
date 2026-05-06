// cosmic_address.go — Substrato 170: Cosmic Network Addressing & Subnetting
package main

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"math"
)

// ─── Cosmic Address ─────────────────────────────────────

const CosmicAddressLen = 32 // 256 bits

type CosmicAddress [CosmicAddressLen]byte

// NewCosmicAddress constrói um endereço a partir dos componentes.
func NewCosmicAddress(scale CosmicScale, coherence, resonance float64, branchAngle float32, branchPhase float32, branchIndex uint32, nodeName string) CosmicAddress {
	var addr CosmicAddress
	// prefixo: 0xARK
	addr[0] = 0x04 // 0100
	addr[1] = 0x12 // 0001 0010
	addr[0] = 0x04 // 0100
	addr[1] = 0x12 // 0001 0010

	// escala e classe de coerência (1 byte)
	addr[2] = byte(scale)<<4 | byte(coherenceClass(coherence))

	// coerência comprimida (10 bytes float64)
	bits := math.Float64bits(coherence)
	for i := 0; i < 8; i++ {
		addr[3+i] = byte(bits >> (56 - 8*i))
	}
	// 2 bytes de ressonância comprimida
	res := uint16(resonance * 65535)
	addr[11] = byte(res >> 8)
	addr[12] = byte(res & 0xFF)

	// identificador de ramo (8 bytes)
	branchID := make([]byte, 8)
	binary.BigEndian.PutUint32(branchID[0:4], math.Float32bits(branchAngle))
	binary.BigEndian.PutUint16(branchID[4:6], uint16(branchPhase*1000))
	binary.BigEndian.PutUint16(branchID[6:8], uint16(branchIndex))
	copy(addr[13:21], branchID)

	// ID do nó (11 bytes = 88 bits, mas guardamos 11 bytes; completamos com zeros finais para 256 bits)
	nodeHash := sha256.Sum256([]byte(nodeName))
	copy(addr[21:32], nodeHash[:11])

	return addr
}

func coherenceClass(coherence float64) byte {
	switch {
	case coherence >= 0.999:
		return 5 // Singular
	case coherence >= 0.9:
		return 4 // Full
	case coherence >= 0.66:
		return 3 // Resonant
	case coherence >= 0.33:
		return 2 // Partial
	default:
		return 1 // Decoherent
	}
}

// String imprime o endereço no formato canônico.
func (ca CosmicAddress) String() string {
	// Extrair escala e ramo para legibilidade
	scale := CosmicScale(ca[2] >> 4)
	branchAngle := math.Float32frombits(binary.BigEndian.Uint32(ca[13:17]))
	branchPhase := float32(binary.BigEndian.Uint16(ca[17:19])) / 1000
	branchIndex := binary.BigEndian.Uint16(ca[19:21])
	// nodeID
	nodeID := hex.EncodeToString(ca[21:32])
	return fmt.Sprintf("ARK-%s:%.1f_φ%.3f#%d:%s", scale, branchAngle, branchPhase, branchIndex, nodeID[:16])
}

// Network retorna o endereço de rede (sub‑rede) dado um comprimento de prefixo.
func (ca CosmicAddress) Network(prefixLen int) CosmicAddress {
	var netAddr CosmicAddress
	copy(netAddr[:], ca[:])
	if prefixLen <= 0 {
		return netAddr
	}
	bits := prefixLen
	for i := 0; i < len(netAddr); i++ {
		if bits >= 8 {
			bits -= 8
		} else {
			mask := byte(0xFF << (8 - bits))
			netAddr[i] &= mask
			bits = 0
		}
	}
	return netAddr
}

// IsInSubnet verifica se o endereço pertence a uma sub‑rede de comprimento prefixLen cujo endereço base é subnetAddr.
func (ca CosmicAddress) IsInSubnet(subnetAddr CosmicAddress, prefixLen int) bool {
	if prefixLen <= 0 {
		return true
	}
	bytes := prefixLen / 8
	for i := 0; i < bytes; i++ {
		if ca[i] != subnetAddr[i] {
			return false
		}
	}
	remainingBits := prefixLen % 8
	if remainingBits > 0 {
		mask := byte(0xFF << (8 - remainingBits))
		if (ca[bytes] & mask) != (subnetAddr[bytes] & mask) {
			return false
		}
	}
	return true
}

// ─── Subnet Manager ──────────────────────────────────────

type CosmicSubnet struct {
	NetworkAddress CosmicAddress
	PrefixLen      int
	Scale          CosmicScale
	Description    string
	Nodes          []string // IDs dos nós registrados nesta sub‑rede
}

type CosmicSubnetManager struct {
	subnets map[string]*CosmicSubnet // key: "networkAddr/prefixLen"
	engine  *CosmologyEngine
}

func NewCosmicSubnetManager(engine *CosmologyEngine) *CosmicSubnetManager {
	return &CosmicSubnetManager{
		subnets: make(map[string]*CosmicSubnet),
		engine:  engine,
	}
}

func (sm *CosmicSubnetManager) AddSubnet(desc string, scale CosmicScale, prefixLen int) (*CosmicSubnet, error) {
	// Cria um endereço de rede representativo: tipo ARK + escala + zeros.
	var netAddr CosmicAddress
	netAddr[0] = 0x04
	netAddr[1] = 0x12
	netAddr[2] = byte(scale) << 4
	// os demais campos são zero para representar a rede
	subnet := &CosmicSubnet{
		NetworkAddress: netAddr,
		PrefixLen:      prefixLen,
		Scale:          scale,
		Description:    desc,
	}
	key := fmt.Sprintf("%s/%d", hex.EncodeToString(netAddr[:]), prefixLen)
	sm.subnets[key] = subnet
	return subnet, nil
}

// AssignNodeToBestSubnet aloca um nó na sub‑rede de escala correspondente.
func (sm *CosmicSubnetManager) AssignNode(nodeID string) {
	node, ok := sm.engine.Nodes[nodeID]
	if !ok {
		return
	}
	addr := NewCosmicAddress(node.Scale, node.Coherence, node.Resonance,
		0.0, 0.0, 0, node.Name) // ramo default
	// Encontrar a sub‑rede mais específica que casa com o endereço do nó
	var best *CosmicSubnet
	for _, sn := range sm.subnets {
		if addr.IsInSubnet(sn.NetworkAddress, sn.PrefixLen) && sn.Scale == node.Scale {
			if best == nil || sn.PrefixLen > best.PrefixLen {
				best = sn
			}
		}
	}
	if best != nil {
		best.Nodes = append(best.Nodes, nodeID)
	}
}

// PrintSubnets exibe todas as sub‑redes.
func (sm *CosmicSubnetManager) PrintSubnets() {
	fmt.Println("\n🌐 COSMIC SUBNETS:")
	for _, sn := range sm.subnets {
		fmt.Printf("   %-30s %s (prefix /%d) [%s] — %d nodes\n",
			sn.Description, sn.NetworkAddress.String()[:20]+"...", sn.PrefixLen, sn.Scale, len(sn.Nodes))
	}
}

// ─── Integration with Cosmology Engine ───────────────────

func (ce *CosmologyEngine) SetupAddressing() *CosmicSubnetManager {
	sm := NewCosmicSubnetManager(ce)
	// Criar sub‑redes por escala cosmológica
	sm.AddSubnet("Quantum Foam", ScaleQuantum, 16)
	sm.AddSubnet("Particle Cloud", ScaleParticle, 16)
	sm.AddSubnet("Atomic Network", ScaleAtomic, 16)
	sm.AddSubnet("Cellular Mesh", ScaleCellular, 16)
	sm.AddSubnet("Organism Net", ScaleOrganism, 16)
	sm.AddSubnet("Ecosystem Grid", ScaleEcosystem, 16)
	sm.AddSubnet("Planetary Net", ScalePlanetary, 16)
	sm.AddSubnet("Stellar Link", ScaleStellar, 16)
	sm.AddSubnet("Galactic Web", ScaleGalactic, 16)
	sm.AddSubnet("Cluster Fabric", ScaleCluster, 16)
	sm.AddSubnet("Supercluster Backbone", ScaleSupercluster, 16)
	sm.AddSubnet("Horizon Edge", ScaleHorizon, 16)
	sm.AddSubnet("Multiverse Root", ScaleMultiverse, 16)
	// Atribuir nós existentes
	for id := range ce.Nodes {
		sm.AssignNode(id)
	}
	return sm
}

func (ce *CosmologyEngine) RoutePacket(packet []byte, destAddr CosmicAddress) error {
	// 1. Encontrar o nó local que melhor case com o prefixo destino
	// 2. Verificar canais de teleportação diretos (mesmo ramo)
	// 3. Se não houver, encaminhar para o gateway de ramo mais próximo
	// (implementação simplificada)
	fmt.Printf("Routing packet of size %d to %s\n", len(packet), destAddr.String())
	return nil
}
