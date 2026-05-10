// arkhe_os/quantum/quantum_repeater_node.go
package quantum

import (
	"crypto/sha256"
	"fmt"
	"math"
	"sync"
	"time"
)

// ─── CONSTANTES DE REPETIDORES QUÂNTICOS ────────────────────────

const (
	// MemoryCoherenceTime tempo de coerência típico de memória quântica (ms)
	MemoryCoherenceTime = 100.0

	// EntanglementSwappingSuccessRate taxa de sucesso de swapping de emaranhamento
	EntanglementSwappingSuccessRate = 0.9

	// MaxRepeaterChainLength comprimento máximo de cadeia de repetidores
	MaxRepeaterChainLength = 10

	// EntanglementPurificationRounds rodadas de purificação de emaranhamento
	EntanglementPurificationRounds = 2
)

// ─── TIPOS FUNDAMENTAIS ─────────────────────────────────────────

// QuantumMemory representa uma memória quântica para armazenamento de estados
type QuantumMemory struct {
	MemoryID          string
	QubitType         string // "ion_trap", "cold_atom", "nv_center", "superconducting"
	CoherenceTime_ms  float64
	StorageEfficiency float64 // [0, 1] — eficiência de leitura/escrita
	Occupied          bool
	StoredStateID     string
	StoredAt          time.Time
}

// EntangledPair representa um par de qubits emaranhados
type EntangledPair struct {
	PairID         string
	QubitA         string  // ID do qubit local
	QubitB         string  // ID do qubit remoto (nó parceiro)
	Fidelity       float64 // [0, 1] — fidelidade do emaranhamento
	CreatedAt      time.Time
	Protocol       string // "E91", "BBM92", "DLCZ"
	ExpirationTime time.Time
}

// QuantumRepeaterNode implementa nó repetidor com memória quântica
type QuantumRepeaterNode struct {
	nodeID         string
	position_km    float64 // posição ao longo do enlace (para cálculo de perda)
	memoryBank     map[string]*QuantumMemory
	entangledPairs map[string]*EntangledPair
	neighbors      map[string]string // nodeID -> channelID
	mu             sync.RWMutex
	metrics        RepeaterMetrics
	config         RepeaterConfig
}

// RepeaterConfig contém configuração do nó repetidor
type RepeaterConfig struct {
	MemoryType           string
	MemoryCount          int
	EntanglementProtocol string
	PurificationEnabled  bool
	MaxPairAge_sec       int
}

// RepeaterMetrics contém métricas do repetidor quântico
type RepeaterMetrics struct {
	PairsGenerated      int64   `json:"pairs_generated"`
	SwapsPerformed      int64   `json:"swaps_performed"`
	PurificationsDone   int64   `json:"purifications_done"`
	AvgFidelity         float64 `json:"avg_fidelity"`
	MemoryUtilization   float64 `json:"memory_utilization"`
	KeyRateContribution float64 `json:"key_rate_contribution_bps"`
}

// ─── CONSTRUTORES ───────────────────────────────────────────────

// NewQuantumRepeaterNode cria novo nó repetidor quântico
func NewQuantumRepeaterNode(
	nodeID string,
	position_km float64,
	config RepeaterConfig,
) *QuantumRepeaterNode {
	if config.MemoryCount == 0 {
		config.MemoryCount = 10
	}
	if config.EntanglementProtocol == "" {
		config.EntanglementProtocol = "DLCZ"
	}

	memoryBank := make(map[string]*QuantumMemory)
	for i := 0; i < config.MemoryCount; i++ {
		memoryID := fmt.Sprintf("mem_%s_%d", nodeID[:8], i)
		memoryBank[memoryID] = &QuantumMemory{
			MemoryID:          memoryID,
			QubitType:         config.MemoryType,
			CoherenceTime_ms:  MemoryCoherenceTime,
			StorageEfficiency: 0.95,
			Occupied:          false,
		}
	}

	return &QuantumRepeaterNode{
		nodeID:         nodeID,
		position_km:    position_km,
		memoryBank:     memoryBank,
		entangledPairs: make(map[string]*EntangledPair),
		neighbors:      make(map[string]string),
		config:         config,
	}
}

// ─── OPERAÇÕES DE REPETIÇÃO QUÂNTICA ───────────────────────────

// GenerateEntangledPair gera par emaranhado com nó vizinho
func (r *QuantumRepeaterNode) GenerateEntangledPair(
	neighborID string,
	protocol string,
) (*EntangledPair, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	// Encontrar memória disponível
	var freeMemory *QuantumMemory
	for _, mem := range r.memoryBank {
		if !mem.Occupied {
			freeMemory = mem
			break
		}
	}
	if freeMemory == nil {
		return nil, fmt.Errorf("no available quantum memory")
	}

	// Gerar par emaranhado (simulado)
	pairID := fmt.Sprintf("pair_%s_%s_%d",
		r.nodeID[:8], neighborID[:8], time.Now().UnixNano())

	// Fidelidade inicial baseada em distância e protocolo
	distance_km := math.Abs(r.position_km - getNodePosition(neighborID))
	baseFidelity := 0.95 * math.Exp(-distance_km/100.0) // decaimento com distância

	pair := &EntangledPair{
		PairID:         pairID,
		QubitA:         freeMemory.MemoryID,
		QubitB:         fmt.Sprintf("remote_%s", pairID),
		Fidelity:       baseFidelity,
		CreatedAt:      time.Now(),
		Protocol:       protocol,
		ExpirationTime: time.Now().Add(time.Duration(MemoryCoherenceTime) * time.Millisecond),
	}

	// Marcar memória como ocupada
	freeMemory.Occupied = true
	freeMemory.StoredStateID = pairID
	freeMemory.StoredAt = time.Now()

	r.entangledPairs[pairID] = pair
	r.metrics.PairsGenerated++

	fmt.Printf("🔗 Entangled pair generated: %s (fidelity=%.3f)\n",
		pairID, pair.Fidelity)

	return pair, nil
}

// PerformEntanglementSwapping executa swapping de emaranhamento entre dois pares
func (r *QuantumRepeaterNode) PerformEntanglementSwapping(
	pair1ID, pair2ID string,
) (*EntangledPair, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	pair1, ok1 := r.entangledPairs[pair1ID]
	pair2, ok2 := r.entangledPairs[pair2ID]
	if !ok1 || !ok2 {
		return nil, fmt.Errorf("one or both pairs not found")
	}

	// Verificar que pares são compatíveis para swapping
	if pair1.QubitB != pair2.QubitA {
		return nil, fmt.Errorf("pairs not compatible for swapping")
	}

	// Executar Bell measurement (simulado)
	success := randFloat() < EntanglementSwappingSuccessRate
	if !success {
		// Liberar memórias em caso de falha
		r.freeMemory(pair1.QubitA)
		r.freeMemory(pair2.QubitB)
		delete(r.entangledPairs, pair1ID)
		delete(r.entangledPairs, pair2ID)
		return nil, fmt.Errorf("entanglement swapping failed")
	}

	// Criar novo par emaranhado entre extremidades
	newPair := &EntangledPair{
		PairID:         fmt.Sprintf("swapped_%s", pair1ID[:8]),
		QubitA:         pair1.QubitA,
		QubitB:         pair2.QubitB,
		Fidelity:       pair1.Fidelity * pair2.Fidelity * 0.98, // pequena perda no swapping
		CreatedAt:      time.Now(),
		Protocol:       "swapping",
		ExpirationTime: time.Now().Add(time.Duration(MemoryCoherenceTime) * time.Millisecond),
	}

	// Liberar memórias dos pares originais
	r.freeMemory(pair1.QubitA)
	r.freeMemory(pair2.QubitB)
	delete(r.entangledPairs, pair1ID)
	delete(r.entangledPairs, pair2ID)

	// Armazenar novo par
	r.entangledPairs[newPair.PairID] = newPair
	r.metrics.SwapsPerformed++

	fmt.Printf("🔄 Entanglement swapping successful: %s -> %s (fidelity=%.3f)\n",
		pair1ID, newPair.PairID, newPair.Fidelity)

	return newPair, nil
}

// PerformEntanglementPurification executa purificação para melhorar fidelidade
func (r *QuantumRepeaterNode) PerformEntanglementPurification(
	pairID string,
	rounds int,
) (*EntangledPair, error) {
	r.mu.Lock()
	defer r.mu.Unlock()

	pair, exists := r.entangledPairs[pairID]
	if !exists {
		return nil, fmt.Errorf("pair not found")
	}

	if rounds <= 0 {
		rounds = EntanglementPurificationRounds
	}

	currentPair := pair
	for i := 0; i < rounds; i++ {
		// Purificação consome dois pares de mesma fidelidade para produzir um melhor
		// Simplificação: aumentar fidelidade com fator de ganho
		gainFactor := 1.0 + 0.05*float64(rounds-i)
		newFidelity := currentPair.Fidelity * gainFactor
		newFidelity = math.Min(0.999, newFidelity) // limite superior

		currentPair = &EntangledPair{
			PairID:         fmt.Sprintf("%s_purified_%d", pairID, i+1),
			QubitA:         currentPair.QubitA,
			QubitB:         currentPair.QubitB,
			Fidelity:       newFidelity,
			CreatedAt:      time.Now(),
			Protocol:       "purification",
			ExpirationTime: currentPair.ExpirationTime,
		}

		r.metrics.PurificationsDone++
	}

	// Substituir par original pelo purificado
	delete(r.entangledPairs, pairID)
	r.entangledPairs[currentPair.PairID] = currentPair

	// Atualizar métrica de fidelidade média
	r.metrics.AvgFidelity = r.metrics.AvgFidelity*0.99 + currentPair.Fidelity*0.01

	fmt.Printf("✨ Entanglement purified: %s → %s (fidelity=%.3f)\n",
		pairID, currentPair.PairID, currentPair.Fidelity)

	return currentPair, nil
}

// ExtractKeyFromEntanglement extrai bits de chave a partir de pares emaranhados
func (r *QuantumRepeaterNode) ExtractKeyFromEntanglement(
	pairID string,
	measurementBasis string,
) ([]byte, error) {
	r.mu.RLock()
	pair, exists := r.entangledPairs[pairID]
	r.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("pair not found")
	}

	// Verificar se par ainda é válido
	if time.Now().After(pair.ExpirationTime) {
		return nil, fmt.Errorf("pair expired")
	}

	// Extrair bits baseado em medição na base especificada
	// Simplificação: gerar bits aleatórios com viés baseado na fidelidade
	numBits := 256 // tamanho típico de bloco de chave
	keyBits := make([]byte, numBits/8)

	for i := range keyBits {
		// Probabilidade de erro = 1 - fidelidade
		errorProb := 1.0 - pair.Fidelity
		byteVal := byte(0)
		for bit := 0; bit < 8; bit++ {
			if randFloat() > errorProb {
				byteVal |= (1 << bit)
			}
		}
		keyBits[i] = byteVal
	}

	fmt.Printf("🔑 Extracted %d key bits from pair %s (fidelity=%.3f)\n",
		len(keyBits)*8, pairID, pair.Fidelity)

	return keyBits, nil
}

// freeMemory libera memória quântica para reuso
func (r *QuantumRepeaterNode) freeMemory(memoryID string) {
	if mem, ok := r.memoryBank[memoryID]; ok {
		mem.Occupied = false
		mem.StoredStateID = ""
	}
}

// GetAvailableMemories retorna número de memórias disponíveis
func (r *QuantumRepeaterNode) GetAvailableMemories() int {
	r.mu.RLock()
	defer r.mu.RUnlock()

	available := 0
	for _, mem := range r.memoryBank {
		if !mem.Occupied {
			available++
		}
	}
	return available
}

// GetRepeaterMetrics retorna métricas consolidadas do repetidor
func (r *QuantumRepeaterNode) GetRepeaterMetrics() RepeaterMetrics {
	r.mu.RLock()
	defer r.mu.RUnlock()

	// Calcular utilização de memória
	occupied := 0
	for _, mem := range r.memoryBank {
		if mem.Occupied {
			occupied++
		}
	}
	r.metrics.MemoryUtilization = float64(occupied) / float64(len(r.memoryBank))

	// Estimar contribuição para taxa de chave
	if len(r.entangledPairs) > 0 {
		avgFidelity := 0.0
		for _, pair := range r.entangledPairs {
			avgFidelity += pair.Fidelity
		}
		avgFidelity /= float64(len(r.entangledPairs))
		// Taxa estimada: proporcional a fidelidade² e número de pares
		r.metrics.KeyRateContribution = avgFidelity * avgFidelity * float64(len(r.entangledPairs)) * 100
	}

	return r.metrics
}

// Helper functions
func getNodePosition(nodeID string) float64 {
	// Em produção: consultar banco de dados de topologia
	// Aqui: posição simulada baseada em hash do ID
	hash := sha256.Sum256([]byte(nodeID))
	return float64(int(hash[0])*256+int(hash[1])) % 10000
}

func randFloat() float64 {
	return float64(time.Now().UnixNano()%10000) / 10000.0
}
