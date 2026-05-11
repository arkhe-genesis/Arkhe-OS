// arkhe_os/routing/gradient_following_router.go
package routing

import (
	"context"
	"fmt"
	"math"
	"sync"
	"time"
)

type NodeRegistry struct{}

func (nr *NodeRegistry) IsLocalNode(a string, b CosmicAddress) bool       { return false }
func (nr *NodeRegistry) GetReachableNeighbors(a string) ([]string, error) { return []string{}, nil }
func (nr *NodeRegistry) GetAddress(a string) CosmicAddress                { return CosmicAddress{} }
func (nr *NodeRegistry) FindNodeByAddress(a CosmicAddress) string         { return "" }
func (nr *NodeRegistry) SendToNode(a string, b []byte) error              { return nil }
func (nr *NodeRegistry) GetAllNodes() map[string]*CosmicNode              { return map[string]*CosmicNode{} }

type TeleportationManager struct{}
type TeleportChannel struct {
	ChannelID string
	Fidelity  float64
}

func (tc *TeleportChannel) IsHealthy() bool { return true }
func (tm *TeleportationManager) GetChannel(a, b string) (*TeleportChannel, error) {
	return &TeleportChannel{}, nil
}
func (tm *TeleportationManager) Teleport(ctx context.Context, channelID string, packet []byte) error {
	return nil
}

// ─── CONSTANTES DO ROTEADOR ───────────────────────────────────────────

const (
	// Alpha: peso da atração ao destino na equação de movimento
	DefaultAlpha = 1.0

	// Beta: peso da atração a alta coerência
	DefaultBeta = 0.8

	// Gamma: peso da repulsão de alta entropia
	DefaultGamma = 0.3

	// TeleportThreshold: Φ_C mínimo para considerar teleporte quântico
	TeleportThreshold = 0.85

	// MaxHops: número máximo de saltos antes de declarar falha
	MaxHops = 50

	// HopTimeout: tempo máximo por salto
	HopTimeout = 2 * time.Second
)

// ─── TIPOS FUNDAMENTAIS ───────────────────────────────────────────────

// RoutingDecision contém a decisão de roteamento para um pacote
type RoutingDecision struct {
	NextHop      string  // ID do próximo nó
	UseTeleport  bool    // se usar teleporte quântico
	ChannelID    string  // ID do canal de teleporte (se aplicável)
	ExpectedPhiC float64 // Φ_C esperado no próximo salto
	EntropyCost  float64 // entropia acumulada estimada
	Confidence   float64 // confiança na decisão [0, 1]
	Reason       string  // justificativa da decisão
}

// PacketContext contém metadados do pacote para roteamento inteligente
type PacketContext struct {
	Priority       float64   // prioridade do pacote [0, 1]
	MaxEntropy     float64   // entropia máxima tolerável
	PreferTeleport bool      // preferência por teleporte quântico
	Deadline       time.Time // deadline de entrega
	PayloadSize    int       // tamanho do payload em bytes
}

// GradientFollowingRouter implementa roteamento por seguimento de gradiente de Φ_C
type GradientFollowingRouter struct {
	field        *CoherencePotentialField
	teleportMgr  *TeleportationManager
	nodeRegistry *NodeRegistry
	config       RouterConfig
	mu           sync.RWMutex
	metrics      RouterMetrics
}

// RouterConfig contém configuração do roteador
type RouterConfig struct {
	Alpha, Beta, Gamma float64 // pesos da equação de movimento
	EnableTeleport     bool    // habilitar teleporte quântico adaptativo
	EnableEntropyAware bool    // considerar entropia nas decisões
	MaxRetries         int     // número máximo de tentativas por pacote
	LogLevel           string  // nível de log: "debug", "info", "warn", "error"
}

// RouterMetrics contém métricas de roteamento
type RouterMetrics struct {
	PacketsRouted     int64   `json:"packets_routed"`
	TeleportsUsed     int64   `json:"teleports_used"`
	AvgHopsPerPacket  float64 `json:"avg_hops_per_packet"`
	AvgRoutingTimeMs  float64 `json:"avg_routing_time_ms"`
	SuccessRate       float64 `json:"success_rate"`
	AvgEntropyPerPath float64 `json:"avg_entropy_per_path"`
}

// ─── CONSTRUTORES ─────────────────────────────────────────────────────

// NewGradientFollowingRouter cria novo roteador por gradiente de coerência
func NewGradientFollowingRouter(
	field *CoherencePotentialField,
	teleportMgr *TeleportationManager,
	nodeRegistry *NodeRegistry,
	config RouterConfig,
) (*GradientFollowingRouter, error) {
	if config.Alpha == 0 {
		config.Alpha = DefaultAlpha
	}
	if config.Beta == 0 {
		config.Beta = DefaultBeta
	}
	if config.Gamma == 0 {
		config.Gamma = DefaultGamma
	}

	return &GradientFollowingRouter{
		field:        field,
		teleportMgr:  teleportMgr,
		nodeRegistry: nodeRegistry,
		config:       config,
	}, nil
}

// ─── OPERAÇÕES DE ROTEAMENTO ──────────────────────────────────────────

// RoutePacket determina a rota para um pacote baseado no campo de coerência
func (r *GradientFollowingRouter) RoutePacket(
	ctx context.Context,
	currentNodeID string,
	destAddr CosmicAddress,
	packetCtx PacketContext,
) (*RoutingDecision, error) {
	start := time.Now()

	// Verificar se destino é local
	if r.nodeRegistry.IsLocalNode(currentNodeID, destAddr) {
		return &RoutingDecision{
			NextHop:    currentNodeID,
			Confidence: 1.0,
			Reason:     "destination_is_local",
		}, nil
	}

	// Obter vizinhos alcançáveis do nó atual
	neighbors, err := r.nodeRegistry.GetReachableNeighbors(currentNodeID)
	if err != nil {
		return nil, fmt.Errorf("failed to get neighbors: %w", err)
	}

	if len(neighbors) == 0 {
		return nil, fmt.Errorf("no reachable neighbors from node %s", currentNodeID)
	}

	// Verificar possibilidade de teleporte quântico direto
	if r.config.EnableTeleport && packetCtx.PreferTeleport {
		if decision, ok := r.tryDirectTeleport(currentNodeID, destAddr, packetCtx); ok {
			r.metrics.TeleportsUsed++
			r.updateMetrics(start, 1, decision.EntropyCost, true)
			return decision, nil
		}
	}

	// Roteamento por gradiente: encontrar melhor próximo salto
	nextHop, score, err := r.field.FindNextHop(currentNodeID, destAddr, neighbors)
	if err != nil {
		return nil, fmt.Errorf("failed to find next hop: %w", err)
	}

	// Calcular métricas do caminho estimado
	phiC, _, err := r.field.Evaluate(r.nodeRegistry.GetAddress(nextHop))
	if err != nil {
		phiC = 0.5 // valor default se avaliação falhar
	}

	entropyCost := r.estimatePathEntropy(currentNodeID, nextHop, destAddr)

	// Calcular confiança baseada em score e métricas
	confidence := computeRoutingConfidence(score, phiC, entropyCost, packetCtx)

	decision := &RoutingDecision{
		NextHop:      nextHop,
		UseTeleport:  false,
		ExpectedPhiC: phiC,
		EntropyCost:  entropyCost,
		Confidence:   confidence,
		Reason:       fmt.Sprintf("gradient_following(score=%.3f)", score),
	}

	// Atualizar métricas
	r.updateMetrics(start, 1, entropyCost, false)

	return decision, nil
}

// tryDirectTeleport tenta estabelecer teleporte quântico direto ao destino
func (r *GradientFollowingRouter) tryDirectTeleport(
	currentNodeID string,
	destAddr CosmicAddress,
	packetCtx PacketContext,
) (*RoutingDecision, bool) {
	// Encontrar nó que possui o endereço de destino
	destNodeID := r.nodeRegistry.FindNodeByAddress(destAddr)
	if destNodeID == "" {
		return nil, false
	}

	// Verificar se canal de teleporte existe e é saudável
	channel, err := r.teleportMgr.GetChannel(currentNodeID, destNodeID)
	if err != nil || channel == nil {
		return nil, false
	}

	if !channel.IsHealthy() {
		return nil, false
	}

	// Verificar condições para teleporte: fidelidade e coerência
	phiCSource, _, _ := r.field.Evaluate(r.nodeRegistry.GetAddress(currentNodeID))
	phiCDest, _, _ := r.field.Evaluate(r.nodeRegistry.GetAddress(destNodeID))

	teleportCondition := channel.Fidelity * phiCSource * phiCDest
	if teleportCondition < TeleportThreshold {
		return nil, false
	}

	// Calcular entropia do salto direto (muito baixa para teleporte)
	entropyCost := 0.01 * float64(packetCtx.PayloadSize) / 1000.0 // entropia proporcional ao tamanho

	decision := &RoutingDecision{
		NextHop:      destNodeID,
		UseTeleport:  true,
		ChannelID:    channel.ChannelID,
		ExpectedPhiC: phiCDest,
		EntropyCost:  entropyCost,
		Confidence:   channel.Fidelity * 0.95, // alta confiança para teleporte saudável
		Reason:       fmt.Sprintf("quantum_teleport(fidelity=%.3f, Φ=%.3f)", channel.Fidelity, teleportCondition),
	}

	return decision, true
}

// estimatePathEntropy estima entropia acumulada para um caminho
func (r *GradientFollowingRouter) estimatePathEntropy(
	fromNode, toNode string,
	destAddr CosmicAddress,
) float64 {
	// Simplificação: entropia baseada em coerência dos nós e distância
	fromAddr := r.nodeRegistry.GetAddress(fromNode)
	toAddr := r.nodeRegistry.GetAddress(toNode)

	phiFrom, _, _ := r.field.Evaluate(fromAddr)
	phiTo, _, _ := r.field.Evaluate(toAddr)

	// Entropia de von Neumann aproximada: S ≈ -Φ·log(Φ) - (1-Φ)·log(1-Φ)
	entropyFrom := binaryEntropy(phiFrom)
	entropyTo := binaryEntropy(phiTo)

	// Distância geodésica no espaço de endereços
	dist := addressDistance(fromAddr, toAddr)

	// Entropia acumulada: média dos nós + penalidade de distância
	return (entropyFrom+entropyTo)/2 + 0.1*dist
}

// binaryEntropy calcula entropia binária para valor de coerência
func binaryEntropy(p float64) float64 {
	if p <= 0 || p >= 1 {
		return 0
	}
	return -p*math.Log(p) - (1-p)*math.Log(1-p)
}

// computeRoutingConfidence calcula confiança na decisão de roteamento
func computeRoutingConfidence(
	score, phiC, entropy float64,
	packetCtx PacketContext,
) float64 {
	// Confiança base no score de roteamento
	confidence := 0.5 + 0.3*score // score ∈ [-1, 1] → confidence ∈ [0.2, 0.8]

	// Ajustar por coerência esperada
	if phiC > 0.9 {
		confidence += 0.1
	} else if phiC < 0.5 {
		confidence -= 0.1
	}

	// Penalizar alta entropia se pacote for sensível
	if packetCtx.MaxEntropy > 0 && entropy > packetCtx.MaxEntropy {
		confidence -= 0.2
	}

	// Bonus por prioridade alta (mais recursos para garantir entrega)
	if packetCtx.Priority > 0.8 {
		confidence += 0.05
	}

	return math.Max(0.0, math.Min(1.0, confidence))
}

// updateMetrics atualiza métricas do roteador após decisão
func (r *GradientFollowingRouter) updateMetrics(
	start time.Time,
	hops int,
	entropy float64,
	usedTeleport bool,
) {
	elapsed := time.Since(start).Milliseconds()

	r.mu.Lock()
	defer r.mu.Unlock()

	r.metrics.PacketsRouted++

	// Média móvel para hops por pacote
	r.metrics.AvgHopsPerPacket = r.metrics.AvgHopsPerPacket*0.99 + float64(hops)*0.01

	// Média móvel para tempo de roteamento
	r.metrics.AvgRoutingTimeMs = r.metrics.AvgRoutingTimeMs*0.99 + float64(elapsed)*0.01

	// Média móvel para entropia por caminho
	r.metrics.AvgEntropyPerPath = r.metrics.AvgEntropyPerPath*0.99 + entropy*0.01

	// Taxa de sucesso (simplificado: assume sucesso se decisão foi tomada)
	r.metrics.SuccessRate = r.metrics.SuccessRate*0.999 + 0.001
}

// ForwardPacket encaminha pacote para próximo salto (integração com camada de transporte)
func (r *GradientFollowingRouter) ForwardPacket(
	ctx context.Context,
	decision *RoutingDecision,
	packet []byte,
) error {
	if decision.UseTeleport {
		// Usar teleporte quântico
		return r.teleportMgr.Teleport(ctx, decision.ChannelID, packet)
	}

	// Encaminhamento clássico para próximo salto
	return r.nodeRegistry.SendToNode(decision.NextHop, packet)
}

// GetMetrics retorna métricas consolidadas do roteador
func (r *GradientFollowingRouter) GetMetrics() RouterMetrics {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.metrics
}
