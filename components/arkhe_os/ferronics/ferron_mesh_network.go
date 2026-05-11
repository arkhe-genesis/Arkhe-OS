// arkhe_os/ferronics/ferron_mesh_network.go
package ferronics

import (
	"fmt"
	"math"
	"sync"
	"time"
)

// ─── CONSTANTES DA REDE FERRÔNICA ───────────────────────────

const (
	// HandoverSNRHigh threshold superior para handover (SNR bom)
	HandoverSNRHigh = 25.0 // dB

	// HandoverSNRLow threshold inferior para handover (SNR ruim)
	HandoverSNRLow = 15.0 // dB

	// HandoverHysteresis histerese para evitar oscilação de handover
	HandoverHysteresis = 3.0 // dB

	// CrystalScanInterval intervalo de varredura de cristais disponíveis
	CrystalScanInterval = 100 * time.Millisecond

	// MaxHandoverTime tempo máximo permitido para handover completo
	MaxHandoverTime = 50 * time.Millisecond

	THzMaxRange = 100.0 // m
)

// ─── TIPOS FUNDAMENTAIS ─────────────────────────────────────

type FerronConfig struct {
	EnableQuantumMode   bool
	CoherenceTarget     float64
	EnableTHzComm       bool
}

type FerronTransceiver struct {
	Material string
	Config   FerronConfig
}

func NewFerronTransceiver(material string, config FerronConfig) (*FerronTransceiver, error) {
	return &FerronTransceiver{Material: material, Config: config}, nil
}

type THzLinkConfig struct {
	CarrierFrequency float64
	Bandwidth        float64
	Range_m          float64
	ModulationScheme string
}

type THzLinkMetrics struct {
	SignalToNoiseRatio float64
	LinkEstablished    bool
}

type FerronTHzLink struct {
	localNodeID  string
	targetNodeID string
	config       THzLinkConfig
	transceiver  *FerronTransceiver
	metrics      THzLinkMetrics
}

func NewFerronTHzLink(local, target string, config THzLinkConfig, trans *FerronTransceiver) (*FerronTHzLink, error) {
	return &FerronTHzLink{
		localNodeID:  local,
		targetNodeID: target,
		config:       config,
		transceiver:  trans,
		metrics:      THzLinkMetrics{SignalToNoiseRatio: 30.0, LinkEstablished: false},
	}, nil
}

func (l *FerronTHzLink) EstablishLink() error {
	l.metrics.LinkEstablished = true
	return nil
}

func (l *FerronTHzLink) SendData(data []byte) error {
	if !l.metrics.LinkEstablished {
		return fmt.Errorf("link not established")
	}
	return nil
}

func (l *FerronTHzLink) GetLinkMetrics() THzLinkMetrics {
	return l.metrics
}

// CrystalNode representa um cristal ferroelétrico na rede ferrônica
type CrystalNode struct {
	NodeID          string
	Position        [3]float64      // posição no espaço da estação
	Velocity        [3]float64      // velocidade relativa (para handover preditivo)
	FerronTransceiver *FerronTransceiver
	AvailableModes  []int           // modos espectrais disponíveis
	CurrentLoad     float64         // carga atual [0, 1]
	SignalQuality   float64         // qualidade de sinal média
	LastHeartbeat   time.Time
	Status          string          // active, busy, degraded, offline
}

// HandoverState representa estado de processo de handover
type HandoverState struct {
	HandoverID      string
	SourceNode      string
	TargetNode      string
	StartTime       time.Time
	CurrentSNR      float64
	TargetSNR       float64
	Progress        float64         // [0, 1]
	Status          string          // initializing, synchronizing, transferring, completed, failed
	DataBuffer      [][]byte        // buffer de dados em transferência
}

// FerronMeshNetwork representa rede mesh de comunicação ferrônica intra-estação
type FerronMeshNetwork struct {
	NetworkID       string
	CrystalNodes    map[string]*CrystalNode
	ActiveLinks     map[string]*FerronTHzLink
	HandoverManager *CrystalHandoverManager
	mu              sync.RWMutex
	metrics         MeshMetrics
	config          MeshConfig
}

// MeshConfig contém configuração da rede ferrônica
type MeshConfig struct {
	EnableAutoHandover   bool
	HandoverThresholdHigh float64
	HandoverThresholdLow  float64
	MaxNodesPerMesh      int
	PredictionHorizon    time.Duration // para handover preditivo
}

// MeshMetrics contém métricas da rede ferrônica
type MeshMetrics struct {
	ActiveNodes          int64   `json:"active_nodes"`
	ActiveLinks          int64   `json:"active_links"`
	HandoversCompleted   int64   `json:"handovers_completed"`
	HandoversFailed      int64   `json:"handovers_failed"`
	AvgHandoverTimeMs    float64 `json:"avg_handover_time_ms"`
	NetworkThroughputGbps float64 `json:"network_throughput_gbps"`
	AvgSignalQuality     float64 `json:"avg_signal_quality"`
}

func (m *FerronMeshNetwork) GetMeshMetrics() MeshMetrics {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.metrics
}

// CrystalHandoverManager gerencia handover automático entre cristais
type CrystalHandoverManager struct {
	network         *FerronMeshNetwork
	activeHandovers map[string]*HandoverState
	predictionCache map[string]HandoverPrediction
	mu              sync.RWMutex
}

// HandoverPrediction contém predição para handover
type HandoverPrediction struct {
	TargetNode      string
	PredictedTime   time.Time
	Confidence      float64 // [0, 1]
	ExpectedSNR     float64
	Reason          string
}

// ─── CONSTRUTORES ───────────────────────────────────────────

// NewFerronMeshNetwork cria nova rede mesh ferrônica
func NewFerronMeshNetwork(networkID string, config MeshConfig) (*FerronMeshNetwork, error) {
	if config.HandoverThresholdHigh == 0 {
		config.HandoverThresholdHigh = HandoverSNRHigh
	}
	if config.HandoverThresholdLow == 0 {
		config.HandoverThresholdLow = HandoverSNRLow
	}

	mesh := &FerronMeshNetwork{
		NetworkID:    networkID,
		CrystalNodes: make(map[string]*CrystalNode),
		ActiveLinks:  make(map[string]*FerronTHzLink),
		config:       config,
	}

	// Iniciar gerenciador de handover
	mesh.HandoverManager = NewCrystalHandoverManager(mesh)

	// Iniciar loop de monitoramento se handover automático habilitado
	if config.EnableAutoHandover {
		go mesh.monitoringLoop()
	}

	return mesh, nil
}

// NewCrystalHandoverManager cria gerenciador de handover
func NewCrystalHandoverManager(network *FerronMeshNetwork) *CrystalHandoverManager {
	return &CrystalHandoverManager{
		network:         network,
		activeHandovers: make(map[string]*HandoverState),
		predictionCache: make(map[string]HandoverPrediction),
	}
}

// ─── OPERAÇÕES DA REDE FERRÔNICA ───────────────────────────

// RegisterCrystalNode registra novo cristal na rede
func (mesh *FerronMeshNetwork) RegisterCrystalNode(node *CrystalNode) error {
	mesh.mu.Lock()
	defer mesh.mu.Unlock()

	if _, exists := mesh.CrystalNodes[node.NodeID]; exists {
		return fmt.Errorf("node %s already registered", node.NodeID)
	}

	mesh.CrystalNodes[node.NodeID] = node
	mesh.metrics.ActiveNodes++

	// Iniciar heartbeat do nó
	go mesh.nodeHeartbeatLoop(node)

	return nil
}

// EstablishLink estabelece enlace THz entre dois cristais
func (mesh *FerronMeshNetwork) EstablishLink(sourceID, targetID string) (*FerronTHzLink, error) {
	mesh.mu.RLock()
	sourceNode, srcOk := mesh.CrystalNodes[sourceID]
	targetNode, tgtOk := mesh.CrystalNodes[targetID]
	mesh.mu.RUnlock()

	if !srcOk || !tgtOk {
		return nil, fmt.Errorf("one or both nodes not found")
	}

	// Calcular distância entre nós
	distance := computeDistance(sourceNode.Position, targetNode.Position)
	if distance > THzMaxRange {
		return nil, fmt.Errorf("distance %.1f m exceeds THz range %.1f m", distance, THzMaxRange)
	}

	// Configurar enlace
	linkConfig := THzLinkConfig{
		CarrierFrequency: 1.0e12,
		Bandwidth:        10e9,
		Range_m:          distance,
		ModulationScheme: "QPSK",
	}

	// Criar enlace (usar transceiver do nó fonte)
	link, err := NewFerronTHzLink(
		sourceID,
		targetID,
		linkConfig,
		sourceNode.FerronTransceiver,
	)
	if err != nil {
		return nil, err
	}

	// Estabelecer enlace
	if err := link.EstablishLink(); err != nil {
		return nil, err
	}

	// Registrar enlace ativo
	linkID := fmt.Sprintf("%s_%s", sourceID, targetID)
	mesh.mu.Lock()
	mesh.ActiveLinks[linkID] = link
	mesh.metrics.ActiveLinks++
	mesh.mu.Unlock()

	return link, nil
}

// SendWithHandover envia dados com handover automático se necessário
func (mesh *FerronMeshNetwork) SendWithHandover(
	sourceID string,
	data []byte,
	priority float64,
) (string, error) {
	mesh.mu.RLock()
	sourceNode, ok := mesh.CrystalNodes[sourceID]
	mesh.mu.RUnlock()
	if !ok {
		return "", fmt.Errorf("source node %s not found", sourceID)
	}

	// Encontrar melhor nó de destino baseado em qualidade de sinal
	targetNode := mesh.selectBestTarget(sourceNode, priority)
	if targetNode == nil {
		return "", fmt.Errorf("no suitable target node found")
	}

	// Verificar se handover é necessário
	currentLink := mesh.getActiveLink(sourceID)
	if currentLink != nil {
		metrics := currentLink.GetLinkMetrics()
		if metrics.SignalToNoiseRatio < mesh.config.HandoverThresholdLow-HandoverHysteresis {
			// Iniciar handover
			handoverID, err := mesh.HandoverManager.InitiateHandover(
				sourceID, targetNode.NodeID, data,
			)
			if err != nil {
				return "", fmt.Errorf("handover initiation failed: %w", err)
			}
			return handoverID, nil
		}
		// Usar enlace existente
		if err := currentLink.SendData(data); err != nil {
			return "", err
		}
		return fmt.Sprintf("%.2f", currentLink.config.CarrierFrequency), nil
	}

	// Estabelecer novo enlace se necessário
	link, err := mesh.EstablishLink(sourceID, targetNode.NodeID)
	if err != nil {
		return "", err
	}

	if err := link.SendData(data); err != nil {
		return "", err
	}

	return fmt.Sprintf("%.2f", link.config.CarrierFrequency), nil
}

// selectBestTarget seleciona melhor nó alvo baseado em métricas
func (mesh *FerronMeshNetwork) selectBestTarget(
	source *CrystalNode,
	priority float64,
) *CrystalNode {
	mesh.mu.RLock()
	defer mesh.mu.RUnlock()

	var bestNode *CrystalNode
	bestScore := -1.0

	for _, node := range mesh.CrystalNodes {
		if node.NodeID == source.NodeID || node.Status != "active" {
			continue
		}

		// Calcular score baseado em múltiplos fatores
		distance := computeDistance(source.Position, node.Position)
		if distance > THzMaxRange {
			continue
		}

		// Score: qualidade de sinal, carga, prioridade
		signalScore := node.SignalQuality * 0.4
		loadScore := (1.0 - node.CurrentLoad) * 0.3
		distanceScore := (1.0 - distance/THzMaxRange) * 0.2
		priorityScore := priority * 0.1

		score := signalScore + loadScore + distanceScore + priorityScore

		if score > bestScore {
			bestScore = score
			bestNode = node
		}
	}

	return bestNode
}

// getActiveLink retorna enlace ativo para nó fonte
func (mesh *FerronMeshNetwork) getActiveLink(sourceID string) *FerronTHzLink {
	mesh.mu.RLock()
	defer mesh.mu.RUnlock()

	for _, link := range mesh.ActiveLinks {
		if link.localNodeID == sourceID && link.metrics.LinkEstablished {
			return link
		}
	}
	return nil
}

// monitoringLoop monitora qualidade de enlace e inicia handover se necessário
func (mesh *FerronMeshNetwork) monitoringLoop() {
	ticker := time.NewTicker(CrystalScanInterval)
	defer ticker.Stop()

	for range ticker.C {
		mesh.mu.RLock()
		nodes := make([]*CrystalNode, 0, len(mesh.CrystalNodes))
		for _, node := range mesh.CrystalNodes {
			nodes = append(nodes, node)
		}
		mesh.mu.RUnlock()

		for _, node := range nodes {
			// Verificar qualidade de enlaces ativos
			for _, link := range mesh.ActiveLinks {
				if link.localNodeID == node.NodeID {
					metrics := link.GetLinkMetrics()
					if metrics.SignalToNoiseRatio < mesh.config.HandoverThresholdLow {
						// Iniciar handover preditivo se habilitado
						if mesh.config.PredictionHorizon > 0 {
							mesh.HandoverManager.PredictAndPrepareHandover(node, link)
						}
					}
				}
			}
		}
	}
}

// nodeHeartbeatLoop mantém heartbeat do nó cristalino
func (mesh *FerronMeshNetwork) nodeHeartbeatLoop(node *CrystalNode) {
	ticker := time.NewTicker(1 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		// Atualizar métricas do nó (simulado)
		node.SignalQuality = 0.8 + 0.2*math.Sin(float64(time.Now().Unix())*0.1)
		node.CurrentLoad = 0.3 + 0.4*math.Sin(float64(time.Now().Unix())*0.05)
		node.LastHeartbeat = time.Now()

		// Verificar status
		if time.Since(node.LastHeartbeat) > 5*time.Second {
			node.Status = "offline"
		} else {
			node.Status = "active"
		}
	}
}

// ─── OPERAÇÕES DE HANDOVER AUTOMÁTICO ──────────────────────

// InitiateHandover inicia processo de handover entre cristais
func (hm *CrystalHandoverManager) InitiateHandover(
	sourceID, targetID string,
	data []byte,
) (string, error) {
	hm.mu.Lock()
	defer hm.mu.Unlock()

	handoverID := fmt.Sprintf("ho_%s_%s_%d",
		sourceID, targetID, time.Now().UnixNano())

	state := &HandoverState{
		HandoverID: handoverID,
		SourceNode: sourceID,
		TargetNode: targetID,
		StartTime:  time.Now(),
		DataBuffer: [][]byte{data},
		Status:     "initializing",
	}

	hm.activeHandovers[handoverID] = state

	// Executar handover em background
	go hm.executeHandover(state)

	return handoverID, nil
}

// executeHandover executa processo completo de handover
func (hm *CrystalHandoverManager) executeHandover(state *HandoverState) {
	defer func() {
		hm.mu.Lock()
		delete(hm.activeHandovers, state.HandoverID)
		hm.mu.Unlock()
	}()

	// Fase 1: Sincronização de fase entre cristais
	state.Status = "synchronizing"
	if err := hm.synchronizePhases(state.SourceNode, state.TargetNode); err != nil {
		state.Status = "failed"
		return
	}
	state.Progress = 0.3

	// Fase 2: Transferência de dados em buffer
	state.Status = "transferring"
	for _, _ = range state.DataBuffer {
		// Transferir via enlace temporário ou buffer compartilhado
		// Em produção: usar protocolo de transferência atômica
		time.Sleep(10 * time.Millisecond) // simular transferência
	}
	state.Progress = 0.8

	// Fase 3: Confirmação e limpeza
	state.Status = "completed"
	state.Progress = 1.0

	// Atualizar métricas da rede
	hm.network.mu.Lock()
	hm.network.metrics.HandoversCompleted++
	hm.network.mu.Unlock()
}

// synchronizePhases sincroniza fase entre cristais para handover suave
func (hm *CrystalHandoverManager) synchronizePhases(sourceID, targetID string) error {
	// Em produção: implementar protocolo de phase-locking entre transceptores
	// Aqui: simular sincronização bem-sucedida
	time.Sleep(5 * time.Millisecond)
	return nil
}

// PredictAndPrepareHandover prediz e prepara handover baseado em mobilidade
func (hm *CrystalHandoverManager) PredictAndPrepareHandover(
	node *CrystalNode,
	currentLink *FerronTHzLink,
) {
	// Analisar velocidade e direção do nó
	// Predizer quando SNR cairá abaixo do threshold
	// Preparar nó alvo para handover iminente

	// Implementação simplificada:
	prediction := HandoverPrediction{
		TargetNode:    "predicted_node",
		PredictedTime: time.Now().Add(500 * time.Millisecond),
		Confidence:    0.85,
		ExpectedSNR:   20.0,
		Reason:        "mobility_based_prediction",
	}

	hm.mu.Lock()
	hm.predictionCache[node.NodeID] = prediction
	hm.mu.Unlock()
}

// GetHandoverStatus retorna status de handover ativo
func (hm *CrystalHandoverManager) GetHandoverStatus(handoverID string) (*HandoverState, bool) {
	hm.mu.RLock()
	defer hm.mu.RUnlock()
	state, ok := hm.activeHandovers[handoverID]
	return state, ok
}

// Helper functions
func computeDistance(a, b [3]float64) float64 {
	dx := a[0] - b[0]
	dy := a[1] - b[1]
	dz := a[2] - b[2]
	return math.Sqrt(dx*dx + dy*dy + dz*dz)
}