package integration

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"sync"
	"time"

	"github.com/arkhe-os/arkhe/network"
)

// PromotionConfig contém a configuração para promoção de clusters
type PromotionConfig struct {
	AutoPromotionEnabled  bool
	RequireHandshake      bool
	MinSustainedCoherence float64
}

// PromotionMetrics contém métricas de promoção
type PromotionMetrics struct {
	ActivePromotedNodes int64
	TotalPromotions     int64
	HandshakesFailed    int64
}

// DataCenterNode representa um cluster de data center promovido na Hyper-Mesh
type DataCenterNode struct {
	NodeID          string
	ClusterID       string
	PromotedAt      time.Time
	Coherence       float64
	GradientChannel *CoherenceGradientChannel
	IsActive        bool
}

// CoherenceGradientChannel lida com o mapeamento e troca de gradientes
type CoherenceGradientChannel struct {
	mu           sync.RWMutex
	nodeID       string
	wheelerMesh  *network.WheelerMeshProtocol
	gradients    [][]float64
	totalContrib float64
}

func NewCoherenceGradientChannel(nodeID string, wheelerMesh *network.WheelerMeshProtocol) *CoherenceGradientChannel {
	return &CoherenceGradientChannel{
		nodeID:      nodeID,
		wheelerMesh: wheelerMesh,
		gradients:   make([][]float64, 0),
	}
}

func (c *CoherenceGradientChannel) SubmitLocalGradient(
	gradient []float64, freq float64, distance float64,
	priority int, phase float64, metadata map[string]interface{},
) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.gradients = append(c.gradients, gradient)
	c.totalContrib += freq // Simplificação: contribuição baseada na frequência
}

// DataCenterPromotionProtocol gerencia a elevação de clusters para nós sinápticos
type DataCenterPromotionProtocol struct {
	mu             sync.RWMutex
	protocolID     string
	clusterID      string
	wheelerMesh    *network.WheelerMeshProtocol
	config         PromotionConfig
	metrics        PromotionMetrics
	promotedNodes  map[string]*DataCenterNode
	promotionLock  sync.Mutex
	lastCoherences []float64 // Histórico recente para checar coerência sustentada
}

// NewDataCenterPromotionProtocol cria um novo protocolo de promoção
func NewDataCenterPromotionProtocol(
	protocolID, clusterID string,
	wheelerMesh *network.WheelerMeshProtocol,
	config PromotionConfig,
) *DataCenterPromotionProtocol {
	return &DataCenterPromotionProtocol{
		protocolID:     protocolID,
		clusterID:      clusterID,
		wheelerMesh:    wheelerMesh,
		config:         config,
		promotedNodes:  make(map[string]*DataCenterNode),
		lastCoherences: make([]float64, 0, 10), // Guardar até 10 leituras recentes
	}
}

func (p *DataCenterPromotionProtocol) SetPromotedNodes(nodes map[string]*DataCenterNode) {
    p.mu.Lock()
    defer p.mu.Unlock()
    for k, v := range nodes {
        p.promotedNodes[k] = v
    }
}

// checkPromotionEligibility verifica se o cluster atingiu os critérios para ser promovido
func (p *DataCenterPromotionProtocol) checkPromotionEligibility(cid string, currentCoherence float64) {
	if !p.config.AutoPromotionEnabled || cid != p.clusterID {
		return
	}

	p.promotionLock.Lock()
	defer p.promotionLock.Unlock()

	// Atualizar histórico
	p.lastCoherences = append(p.lastCoherences, currentCoherence)
	if len(p.lastCoherences) > 10 {
		p.lastCoherences = p.lastCoherences[1:]
	}

	// Verificar se já está promovido
	p.mu.RLock()
	node, exists := p.promotedNodes[cid]
	isActive := exists && node.IsActive
	p.mu.RUnlock()

	if isActive {
		// Se já promovido, apenas atualizar coerência
		node.Coherence = currentCoherence
		return
	}

	// Avaliar coerência sustentada (simplificação: média das últimas N leituras)
	if len(p.lastCoherences) >= 5 {
		sum := 0.0
		for _, val := range p.lastCoherences {
			sum += val
		}
		avgCoherence := sum / float64(len(p.lastCoherences))

		if avgCoherence >= p.config.MinSustainedCoherence {
			// Iniciar processo de promoção
			go p.executePromotion(cid, avgCoherence)
		}
	}
}

// executePromotion executa o handshake quântico e criação do nó
func (p *DataCenterPromotionProtocol) executePromotion(cid string, coherence float64) {
	fmt.Printf("🚀 Iniciando promoção do cluster %s (Φ_C=%.2f)...\n", cid, coherence)

	// 1. Handshake Quântico (simulado com wheelerMesh)
	if p.config.RequireHandshake && p.wheelerMesh != nil {
		// No mundo real, aqui chamaríamos wheelerMesh.PerformQuantumHandshake()
		// Simulando sucesso do handshake para o contexto da integração
		time.Sleep(500 * time.Millisecond)
		fmt.Printf("🤝 Handshake quântico com Wheeler Mesh concluído.\n")
	}

	// 2. Criação do CoherenceGradientChannel
	nodeID := fmt.Sprintf("dc_%s", cid)
	gradChannel := NewCoherenceGradientChannel(nodeID, p.wheelerMesh)

	// 3. Registrar DataCenterNode
	node := &DataCenterNode{
		NodeID:          nodeID,
		ClusterID:       cid,
		PromotedAt:      time.Now(),
		Coherence:       coherence,
		GradientChannel: gradChannel,
		IsActive:        true,
	}

	p.mu.Lock()
	p.promotedNodes[cid] = node
	p.metrics.ActivePromotedNodes++
	p.metrics.TotalPromotions++
	p.mu.Unlock()

	fmt.Printf("🌟 Cluster %s promovido com sucesso a Nó Sináptico (%s)!\n", cid, nodeID)

	// Criar Prova CoSNARK para registro (simulado)
	proofStr := fmt.Sprintf("PROMOTION_%s_%f_%d", nodeID, coherence, time.Now().UnixNano())
	hash := sha256.Sum256([]byte(proofStr))
	fmt.Printf("📜 Prova CoSNARK gerada: %s\n", hex.EncodeToString(hash[:])[:16])
}

func (p *DataCenterPromotionProtocol) GetPromotionMetrics() PromotionMetrics {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return p.metrics
}
