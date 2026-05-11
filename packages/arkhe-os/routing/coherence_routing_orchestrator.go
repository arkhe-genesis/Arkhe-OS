// arkhe_os/routing/coherence_routing_orchestrator.go
package routing

import (
	"context"
	"fmt"
	"math"
	"sync"
	"time"
)

type PathEntropyCalculator struct{}

func NewPathEntropyCalculator(a *CoherencePotentialField, b *NodeRegistry) *PathEntropyCalculator {
	return &PathEntropyCalculator{}
}

type TopologySelfOptimizer struct{}

func NewTopologySelfOptimizer(a *CoherencePotentialField, b *NodeRegistry, c bool) *TopologySelfOptimizer {
	return &TopologySelfOptimizer{}
}
func (t *TopologySelfOptimizer) OptimizationLoop(ch chan struct{}) {}

// ─── TIPO PRINCIPAL ───────────────────────────────────────────────────

// CoherenceRoutingOrchestrator orquestra todos os componentes de roteamento por coerência
type CoherenceRoutingOrchestrator struct {
	config        OrchestratorConfig
	field         *CoherencePotentialField
	router        *GradientFollowingRouter
	pathFormation *DynamicPathFormation
	entropyCalc   *PathEntropyCalculator
	topologyOpt   *TopologySelfOptimizer

	nodeRegistry *NodeRegistry
	teleportMgr  *TeleportationManager

	activeRoutes map[string]*ActiveRoute // packetID → rota ativa
	mu           sync.RWMutex
	metrics      OrchestratorMetrics
	shutdownCh   chan struct{}
}

// OrchestratorConfig contém configuração do orquestrador
type OrchestratorConfig struct {
	EnableGradientRouting bool
	EnableDynamicPaths    bool
	EnableTeleport        bool
	EnableEntropyAware    bool
	EnableTopologyOpt     bool
	FieldUpdateInterval   time.Duration
	LogLevel              string
}

// ActiveRoute representa uma rota ativa para um pacote em trânsito
type ActiveRoute struct {
	PacketID     string
	Path         *Path
	CurrentNode  string
	HopCount     int
	TotalEntropy float64
	StartTime    time.Time
	LastHopTime  time.Time
}

// OrchestratorMetrics contém métricas consolidadas do roteamento
type OrchestratorMetrics struct {
	PacketsProcessed  int64   `json:"packets_processed"`
	AvgHopsPerPacket  float64 `json:"avg_hops_per_packet"`
	AvgRoutingTimeMs  float64 `json:"avg_routing_time_ms"`
	TeleportUsageRate float64 `json:"teleport_usage_rate"`
	AvgPathEntropy    float64 `json:"avg_path_entropy"`
	SuccessRate       float64 `json:"success_rate"`
}

// ─── CONSTRUTOR ───────────────────────────────────────────────────────

// NewCoherenceRoutingOrchestrator cria orquestrador completo de roteamento por coerência
func NewCoherenceRoutingOrchestrator(
	config OrchestratorConfig,
	nodes map[string]*CosmicNode,
	teleportMgr *TeleportationManager,
) (*CoherenceRoutingOrchestrator, error) {
	// Inicializar componentes base
	nodeRegistry := &NodeRegistry{}

	field, err := NewCoherencePotentialField(nodes, 0.15)
	if err != nil {
		return nil, fmt.Errorf("failed to create coherence field: %w", err)
	}

	routerCfg := RouterConfig{
		EnableTeleport:     config.EnableTeleport,
		EnableEntropyAware: config.EnableEntropyAware,
		LogLevel:           config.LogLevel,
	}

	router, err := NewGradientFollowingRouter(field, teleportMgr, nodeRegistry, routerCfg)
	if err != nil {
		return nil, fmt.Errorf("failed to create router: %w", err)
	}

	pathCfg := PathFormationConfig{
		CoherenceWindow: 30 * time.Second,
		MinResonance:    0.7,
		MaxPaths:        100,
	}

	pathFormation := NewDynamicPathFormation(field, nodeRegistry, pathCfg)
	entropyCalc := NewPathEntropyCalculator(field, nodeRegistry)
	topologyOpt := NewTopologySelfOptimizer(field, nodeRegistry, config.EnableTopologyOpt)

	orch := &CoherenceRoutingOrchestrator{
		config:        config,
		field:         field,
		router:        router,
		pathFormation: pathFormation,
		entropyCalc:   entropyCalc,
		topologyOpt:   topologyOpt,
		nodeRegistry:  nodeRegistry,
		teleportMgr:   teleportMgr,
		activeRoutes:  make(map[string]*ActiveRoute),
		shutdownCh:    make(chan struct{}),
	}

	// Registrar callbacks para atualização do campo de coerência
	orch.registerFieldUpdates()

	return orch, nil
}

// ─── OPERAÇÕES PRINCIPAIS ─────────────────────────────────────────────

// RouteAndForward encaminha pacote do início ao fim usando roteamento por coerência
func (orch *CoherenceRoutingOrchestrator) RouteAndForward(
	ctx context.Context,
	sourceNodeID string,
	destAddr CosmicAddress,
	packet []byte,
	packetCtx PacketContext,
) error {
	start := time.Now()
	packetID := generatePacketID(sourceNodeID, destAddr, time.Now())

	// Criar registro de rota ativa
	route := &ActiveRoute{
		PacketID:    packetID,
		CurrentNode: sourceNodeID,
		StartTime:   time.Now(),
		LastHopTime: time.Now(),
	}

	orch.mu.Lock()
	orch.activeRoutes[packetID] = route
	orch.mu.Unlock()

	defer func() {
		orch.mu.Lock()
		delete(orch.activeRoutes, packetID)
		orch.mu.Unlock()
	}()

	// Loop de encaminhamento hop-by-hop
	for route.HopCount < MaxHops {
		// Verificar deadline
		if !packetCtx.Deadline.IsZero() && time.Now().After(packetCtx.Deadline) {
			return fmt.Errorf("packet deadline exceeded")
		}

		// Decidir próximo salto
		decision, err := orch.router.RoutePacket(ctx, route.CurrentNode, destAddr, packetCtx)
		if err != nil {
			return fmt.Errorf("routing decision failed: %w", err)
		}

		// Verificar se chegou ao destino
		if decision.NextHop == route.CurrentNode {
			// Destino alcançado
			orch.updateMetrics(start, route.HopCount, route.TotalEntropy, true)
			return nil
		}

		// Atualizar métricas da rota
		route.HopCount++
		route.TotalEntropy += decision.EntropyCost
		route.LastHopTime = time.Now()

		// Registrar uso do caminho se formado dinamicamente
		if orch.config.EnableDynamicPaths && decision.NextHop != "" {
			orch.pathFormation.RecordCoherence(route.CurrentNode, decision.ExpectedPhiC)
		}

		// Encaminhar pacote
		if err := orch.router.ForwardPacket(ctx, decision, packet); err != nil {
			return fmt.Errorf("forwarding failed at hop %d: %w", route.HopCount, err)
		}

		// Atualizar posição atual
		route.CurrentNode = decision.NextHop

		// Pequeno delay para evitar congestionamento
		select {
		case <-time.After(10 * time.Millisecond):
		case <-ctx.Done():
			return ctx.Err()
		}
	}

	return fmt.Errorf("max hops exceeded (%d)", MaxHops)
}

// registerFieldUpdates registra callbacks para atualização do campo de coerência
func (orch *CoherenceRoutingOrchestrator) registerFieldUpdates() {
	// Atualizar campo periodicamente baseado em mudanças nos nós
	go func() {
		ticker := time.NewTicker(orch.config.FieldUpdateInterval)
		defer ticker.Stop()

		for {
			select {
			case <-orch.shutdownCh:
				return
			case <-ticker.C:
				// Atualizar campo com novas medições de coerência
				for nodeID, node := range orch.nodeRegistry.GetAllNodes() {
					orch.pathFormation.RecordCoherence(nodeID, node.Coherence)
				}
			}
		}
	}()
}

// updateMetrics atualiza métricas do orquestrador após roteamento
func (orch *CoherenceRoutingOrchestrator) updateMetrics(
	start time.Time,
	hops int,
	entropy float64,
	success bool,
) {
	elapsed := time.Since(start).Milliseconds()

	orch.mu.Lock()
	defer orch.mu.Unlock()

	orch.metrics.PacketsProcessed++

	// Médias móveis
	orch.metrics.AvgHopsPerPacket = orch.metrics.AvgHopsPerPacket*0.99 + float64(hops)*0.01
	orch.metrics.AvgRoutingTimeMs = orch.metrics.AvgRoutingTimeMs*0.99 + float64(elapsed)*0.01
	orch.metrics.AvgPathEntropy = orch.metrics.AvgPathEntropy*0.99 + entropy*0.01

	if success {
		orch.metrics.SuccessRate = orch.metrics.SuccessRate*0.999 + 0.001
	}
}

// Start inicia loops de fundo do orquestrador
func (orch *CoherenceRoutingOrchestrator) Start() {
	if orch.config.EnableTopologyOpt {
		go orch.topologyOpt.OptimizationLoop(orch.shutdownCh)
	}
}

// Stop para o orquestrador gracefully
func (orch *CoherenceRoutingOrchestrator) Stop() {
	close(orch.shutdownCh)
}

// GetMetrics retorna métricas consolidadas do roteamento
func (orch *CoherenceRoutingOrchestrator) GetMetrics() OrchestratorMetrics {
	orch.mu.RLock()
	defer orch.mu.RUnlock()

	// Combinar métricas dos componentes
	routerMetrics := orch.router.GetMetrics()
	_ = orch.pathFormation.GetMetrics()
	_ = orch.field.GetMetrics()

	return OrchestratorMetrics{
		PacketsProcessed:  orch.metrics.PacketsProcessed,
		AvgHopsPerPacket:  orch.metrics.AvgHopsPerPacket,
		AvgRoutingTimeMs:  orch.metrics.AvgRoutingTimeMs,
		TeleportUsageRate: float64(routerMetrics.TeleportsUsed) / math.Max(1, float64(orch.metrics.PacketsProcessed)),
		AvgPathEntropy:    orch.metrics.AvgPathEntropy,
		SuccessRate:       orch.metrics.SuccessRate,
	}
}

// Helper functions
func generatePacketID(source string, dest CosmicAddress, timestamp time.Time) string {
	return fmt.Sprintf("%x", hashString(fmt.Sprintf("%s:%s:%d", source, dest, timestamp.UnixNano()))[:16])
}
