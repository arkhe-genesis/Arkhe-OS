// simulation_174.go — Substrato 174: Simulação de Roteamento por Coerência em Larga Escala
// Testa roteamento e evolução em uma topologia de 10.000+ nós com tráfego realista.
package main

import (
	"context"
	"fmt"
	"math"
	"math/rand"
	"sort"
	"sync"
	"sync/atomic"
	"time"
)

// ─── Configuração da Simulação ─────────────────────────────────────
type SimulationConfig struct {
	NumNodes          int           // número de nós (ex: 10_000)
	NumChannels       int           // canais quânticos por nó
	NumPackets        int           // total de pacotes a rotear
	PacketRate        float64       // pacotes por segundo
	CoherenceDecay    float64       // decaimento de coerência por segundo
	TeleportThreshold float64       // limiar para teleporte
	EvolutionEnabled  bool          // ativa auto-evolução durante a simulação
	Duration          time.Duration // duração máxima da simulação
}

type SimulationMetrics struct {
	TotalPackets    int64
	SuccessPackets  int64
	TotalHops       int64
	TeleportsUsed   int64
	AvgCoherence    float64
	AvgEntropy      float64
	AvgLatencyMs    float64
	EvolutionEvents int64
}

// ─── Nó da Simulação ────────────────────────────────────────────────
type SimNode struct {
	ID        string
	Coherence float64
	Load      float64
	Neighbors []string
	Routes    sync.Map // dest -> nextHop
}

// ─── Motor da Simulação ─────────────────────────────────────────────
type CoherenceSimulation struct {
	config  SimulationConfig
	nodes   map[string]*SimNode
	router  *CoherenceRouter // reutiliza o roteador do Substrato 171
	metrics SimulationMetrics
	mu      sync.Mutex
}

func NewCoherenceSimulation(cfg SimulationConfig) *CoherenceSimulation {
	sim := &CoherenceSimulation{
		config: cfg,
		nodes:  make(map[string]*SimNode),
	}
	sim.generateTopology()
	return sim
}

// generateTopology cria uma rede small‑world com 10.000+ nós.
func (sim *CoherenceSimulation) generateTopology() {
	n := sim.config.NumNodes
	for i := 0; i < n; i++ {
		id := fmt.Sprintf("node_%06d", i)
		sim.nodes[id] = &SimNode{
			ID:        id,
			Coherence: 0.7 + rand.Float64()*0.3,
			Neighbors: make([]string, 0, sim.config.NumChannels),
		}
	}
	// conexões small‑world: anel + atalhos aleatórios
	ids := make([]string, 0, n)
	for id := range sim.nodes {
		ids = append(ids, id)
	}
	sort.Strings(ids)
	for i, id := range ids {
		// vizinhos no anel
		for k := 1; k <= sim.config.NumChannels/2; k++ {
			neighbor := ids[(i+k)%n]
			sim.nodes[id].Neighbors = append(sim.nodes[id].Neighbors, neighbor)
		}
		// atalhos aleatórios (small‑world)
		for len(sim.nodes[id].Neighbors) < sim.config.NumChannels {
			randIdx := rand.Intn(n)
			if randIdx != i {
				sim.nodes[id].Neighbors = append(sim.nodes[id].Neighbors, ids[randIdx])
			}
		}
	}
	// inicializa tabelas de roteamento simples (vizinho direto)
	for _, node := range sim.nodes {
		for _, nb := range node.Neighbors {
			node.Routes.Store(nb, nb)
		}
	}
}

// Run executa a simulação completa.
func (sim *CoherenceSimulation) Run(ctx context.Context) SimulationMetrics {
	start := time.Now()
	// dispara gerador de tráfego
	go sim.trafficGenerator(ctx)
	// dispara atualizador de coerência
	go sim.coherenceUpdater(ctx)
	// se habilitado, dispara evolução periódica
	if sim.config.EvolutionEnabled {
		go sim.evolutionLoop(ctx)
	}
	// aguarda duração ou cancelamento
	select {
	case <-ctx.Done():
	case <-time.After(sim.config.Duration):
	}
	elapsed := time.Since(start).Seconds()
	sim.mu.Lock()
	defer sim.mu.Unlock()
	// consolida métricas
	if sim.metrics.TotalPackets > 0 {
		sim.metrics.AvgLatencyMs = float64(sim.metrics.TotalHops) * 5.0 / float64(sim.metrics.TotalPackets) // modelo simples de latência por hop
	}
	sim.metrics.AvgCoherence = sim.averageCoherence()
	_ = elapsed
	return sim.metrics
}

func (sim *CoherenceSimulation) trafficGenerator(ctx context.Context) {
	ticker := time.NewTicker(time.Duration(1e9/sim.config.PacketRate) * time.Nanosecond)
	defer ticker.Stop()
	packetID := int64(0)
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			atomic.AddInt64(&packetID, 1)
			src, dst := sim.randomPair()
			go sim.routePacket(src, dst, packetID)
		}
	}
}

func (sim *CoherenceSimulation) randomPair() (string, string) {
	ids := make([]string, 0, len(sim.nodes))
	for id := range sim.nodes {
		ids = append(ids, id)
	}
	src := ids[rand.Intn(len(ids))]
	dst := ids[rand.Intn(len(ids))]
	for dst == src {
		dst = ids[rand.Intn(len(ids))]
	}
	return src, dst
}

func (sim *CoherenceSimulation) routePacket(src, dst string, pktID int64) {
	current := src
	hops := 0
	coherenceSum := 0.0
	for current != dst && hops < 64 {
		node := sim.nodes[current]
		if node == nil {
			break
		}
		// decisão de roteamento por coerência (usa vizinho com maior coerência)
		nextHop := ""
		bestCoh := -1.0
		for _, nb := range node.Neighbors {
			if neighbor, ok := sim.nodes[nb]; ok {
				// tenta teleporte se coerência alta
				if neighbor.Coherence > sim.config.TeleportThreshold && rand.Float64() < 0.3 {
					atomic.AddInt64(&sim.metrics.TeleportsUsed, 1)
					nextHop = nb
					break
				}
				if neighbor.Coherence > bestCoh {
					bestCoh = neighbor.Coherence
					nextHop = nb
				}
			}
		}
		if nextHop == "" || nextHop == current {
			break
		}
		coherenceSum += bestCoh
		current = nextHop
		hops++
	}
	sim.mu.Lock()
	sim.metrics.TotalPackets++
	sim.metrics.TotalHops += int64(hops)
	if current == dst {
		sim.metrics.SuccessPackets++
	}
	if sim.metrics.TotalPackets > 0 {
		sim.metrics.AvgCoherence = (sim.metrics.AvgCoherence*float64(sim.metrics.TotalPackets-1) + coherenceSum/math.Max(1, float64(hops))) / float64(sim.metrics.TotalPackets)
	}
	sim.mu.Unlock()
}

func (sim *CoherenceSimulation) coherenceUpdater(ctx context.Context) {
	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			sim.mu.Lock()
			for _, node := range sim.nodes {
				// decai coerência com o tempo e ruído
				node.Coherence = node.Coherence*(1-sim.config.CoherenceDecay) + rand.Float64()*0.05
				if node.Coherence > 1.0 {
					node.Coherence = 1.0
				}
				if node.Coherence < 0.2 {
					node.Coherence = 0.2
				}
			}
			sim.mu.Unlock()
		}
	}
}

func (sim *CoherenceSimulation) evolutionLoop(ctx context.Context) {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			// seleciona uma função aleatória para evoluir (placeholder)
			atomic.AddInt64(&sim.metrics.EvolutionEvents, 1)
		}
	}
}

func (sim *CoherenceSimulation) averageCoherence() float64 {
	sum := 0.0
	for _, n := range sim.nodes {
		sum += n.Coherence
	}
	return sum / float64(len(sim.nodes))
}

func InitSubstrate174() {
	cfg := SimulationConfig{
		NumNodes:          10_000,
		NumChannels:       8, // vizinhos por nó
		NumPackets:        100_000,
		PacketRate:        5000, // pacotes / s
		CoherenceDecay:    0.0001,
		TeleportThreshold: 0.85,
		EvolutionEnabled:  true,
		Duration:          5 * time.Second,
	}

	sim := NewCoherenceSimulation(cfg)
	ctx, cancel := context.WithTimeout(context.Background(), cfg.Duration)
	defer cancel()

	fmt.Println("\n[SUBSTRATO 174] Simulação de Roteamento por Coerência em Larga Escala")
	metrics := sim.Run(ctx)

	fmt.Printf("\n📊 Resultados da Simulação (%d nós, %d pacotes):\n", cfg.NumNodes, metrics.TotalPackets)
	fmt.Printf("   ✅ Sucesso: %d / %d (%.2f%%)\n", metrics.SuccessPackets, metrics.TotalPackets, 100*float64(metrics.SuccessPackets)/float64(metrics.TotalPackets))
	fmt.Printf("   📡 Hops médios: %.2f\n", float64(metrics.TotalHops)/math.Max(1, float64(metrics.TotalPackets)))
	fmt.Printf("   🌀 Teleportes usados: %d (%.2f%%)\n", metrics.TeleportsUsed, 100*float64(metrics.TeleportsUsed)/math.Max(1, float64(metrics.TotalPackets)))
	fmt.Printf("   💎 Coerência média da rede: %.4f\n", metrics.AvgCoherence)
	fmt.Printf("   🧬 Eventos de evolução disparados: %d\n", metrics.EvolutionEvents)
}
