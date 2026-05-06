// routing.go — Substrato 171: Distributed Coherence Routing Protocol
// A geometria da rede emerge do campo de coerência Φ_C
package main

import (
	"fmt"
	"math"
	"sync"
	"time"
)

// ─── Roteamento por Coerência ──────────────────────────

// RouteEntry representa uma rota na tabela de roteamento.
type RouteEntry struct {
	Destination   string         // destino (network ou nodeID)
	PrefixLen     int            // comprimento do prefixo
	NextHop       string         // próximo salto
	Coherence     float64        // coerência acumulada da rota (Φ_C)
	EntropyCost   float64        // custo em entropia de von Neumann
	HopCount      int
	ChannelID     string         // canal de teleportação, se aplicável
	LastUpdate    float64
	IsDirect      bool
}

// RoutingTable mantém as rotas conhecidas por um nó.
type RoutingTable struct {
	mu         sync.RWMutex
	entries    map[string]*RouteEntry // key: "dest/prefixLen"
	nodeID     string
}

func NewRoutingTable(nodeID string) *RoutingTable {
	return &RoutingTable{
		entries: make(map[string]*RouteEntry),
		nodeID:  nodeID,
	}
}

func (rt *RoutingTable) AddRoute(dest string, prefixLen int, nextHop string, coherence, entropyCost float64, hopCount int, channelID string, isDirect bool) {
	rt.mu.Lock()
	defer rt.mu.Unlock()
	key := fmt.Sprintf("%s/%d", dest, prefixLen)
	rt.entries[key] = &RouteEntry{
		Destination: dest,
		PrefixLen:   prefixLen,
		NextHop:     nextHop,
		Coherence:   coherence,
		EntropyCost: entropyCost,
		HopCount:    hopCount,
		ChannelID:   channelID,
		LastUpdate:  float64(time.Now().UnixNano()) / 1e9,
		IsDirect:    isDirect,
	}
}

func (rt *RoutingTable) BestRoute(dest string) *RouteEntry {
	rt.mu.RLock()
	defer rt.mu.RUnlock()
	var best *RouteEntry
	bestScore := -1.0
	for _, entry := range rt.entries {
		if entry.Destination == dest || (entry.PrefixLen > 0 && len(dest) >= entry.PrefixLen && dest[:entry.PrefixLen] == entry.Destination[:entry.PrefixLen]) {
			// Score: coerência - custo de entropia, favorecendo rotas diretas
			score := entry.Coherence - 0.1*entry.EntropyCost - 0.05*float64(entry.HopCount)
			if entry.IsDirect {
				score += 0.2 // bônus para roteamento direto (teleportação)
			}
			if score > bestScore {
				bestScore = score
				best = entry
			}
		}
	}
	return best
}

// ─── Coherence Router ──────────────────────────────────

// CoherenceRouter implementa o protocolo distribuído de roteamento por Φ_C.
type CoherenceRouter struct {
	engine       *CosmologyEngine
	table        *RoutingTable
	subnetMgr    *CosmicSubnetManager
	mu           sync.Mutex
}

func NewCoherenceRouter(engine *CosmologyEngine, subnetMgr *CosmicSubnetManager, nodeID string) *CoherenceRouter {
	cr := &CoherenceRouter{
		engine:    engine,
		table:     NewRoutingTable(nodeID),
		subnetMgr: subnetMgr,
	}
	// Initial routing table build
	cr.buildInitialTable(nodeID)
	// Start periodic table updates (background)
	go cr.periodicUpdate()
	return cr
}

// buildInitialTable popula a tabela de roteamento com rotas diretas e de sub‑rede.
func (cr *CoherenceRouter) buildInitialTable(nodeID string) {
	engine := cr.engine
	myNode, ok := engine.Nodes[nodeID]
	if !ok {
		return
	}
	// Adicionar rotas diretas via canais de teleportação já estabelecidos
	engine.mu.Lock()
	defer engine.mu.Unlock()
	for _, ch := range engine.Channels {
		if ch.SourceNode == nodeID && ch.IsHealthy() {
			tgtNode := engine.Nodes[ch.TargetNode]
			if tgtNode != nil {
				tgtAddr := NewCosmicAddress(tgtNode.Scale, tgtNode.Coherence, tgtNode.Resonance, 0, 0, 0, tgtNode.Name)
				coherence := ch.EntanglementFidelity * myNode.Coherence
				entropyCost := tgtNode.Entropy / math.Max(tgtNode.InformationContent, 1)
				cr.table.AddRoute(tgtAddr.String(), 256, ch.TargetNode, coherence, entropyCost, 1, ch.ChannelID, true)
			}
		}
	}
	// Adicionar rotas de sub‑rede agregadas
	for _, sn := range cr.subnetMgr.subnets {
		netAddr := sn.NetworkAddress
		coherence := 0.95 // coerência média da sub‑rede
		cr.table.AddRoute(fmt.Sprintf("%x", netAddr[:]), sn.PrefixLen, nodeID, coherence, 0.5, 2, "", false)
	}
}

// periodicUpdate mantém a tabela atualizada, trocando informações de roteamento
// com vizinhos via ecos de coerência.
func (cr *CoherenceRouter) periodicUpdate() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	for range ticker.C {
		cr.updateRoutes()
	}
}

func (cr *CoherenceRouter) updateRoutes() {
	cr.mu.Lock()
	defer cr.mu.Unlock()
	engine := cr.engine
	engine.mu.Lock()
	// Para cada canal ativo, pedir a tabela de roteamento do vizinho
	for _, ch := range engine.Channels {
		if ch.ChannelState != "ACTIVE" || !ch.IsHealthy() {
			continue
		}
		// Simula troca de tabelas: o vizinho responderia com suas melhores rotas.
		// Aqui, simplesmente recalcula as rotas diretas baseado na coerência atual.
		tgtNode := engine.Nodes[ch.TargetNode]
		if tgtNode == nil {
			continue
		}
		srcNode := engine.Nodes[ch.SourceNode]
		coherence := ch.EntanglementFidelity * srcNode.Coherence * tgtNode.Coherence
		entropyCost := tgtNode.Entropy / math.Max(tgtNode.InformationContent, 1)
		tgtAddr := NewCosmicAddress(tgtNode.Scale, tgtNode.Coherence, tgtNode.Resonance, 0, 0, 0, tgtNode.Name)
		cr.table.AddRoute(tgtAddr.String(), 256, ch.TargetNode, coherence, entropyCost, 1, ch.ChannelID, true)
	}
	engine.mu.Unlock()
}

// RoutePacket encaminha um pacote ao seu destino usando a tabela.
// Retorna o próximo salto e se deve usar teleportação (via canal).
func (cr *CoherenceRouter) RoutePacket(destAddr CosmicAddress) (nextHop string, channelID string, direct bool, err error) {
	destStr := destAddr.String()
	route := cr.table.BestRoute(destStr)
	if route == nil {
		return "", "", false, fmt.Errorf("no route to %s", destStr)
	}
	return route.NextHop, route.ChannelID, route.IsDirect, nil
}

// ─── Integração com CosmologyEngine ───────────────────

// Integração do roteador no engine.
func (ce *CosmologyEngine) EnableCoherenceRouting() *CoherenceRouter {
	sm := ce.SetupAddressing()
	// usa o primeiro nó registrado como roteador local
	var localID string
	for id := range ce.Nodes {
		localID = id
		break
	}
	router := NewCoherenceRouter(ce, sm, localID)
	return router
}
