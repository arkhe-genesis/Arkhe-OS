// arkhe_os/routing/oam_coherence_router.go
package routing

import (
	"fmt"
	"math"
	"sort"
	"sync"
	"time"

	"arkhe_os/photonic"
	"arkhe_os/quantum"
)

// ─── CONSTANTES DO ROTEADOR OAM-COHERENCE ───────────────────────

const (
	// RouteUpdateInterval intervalo entre atualizações de métricas de rota
	RouteUpdateInterval = 5 * time.Second

	// MinQuantumFidelity fidelidade quântica mínima para rota válida
	MinQuantumFidelity = 0.85

	// CoherenceWeight peso da coerência Φ_C na métrica de qualidade de rota
	CoherenceWeight = 0.4

	// FidelityWeight peso da fidelidade quântica na métrica de rota
	FidelityWeight = 0.4

	// LossWeight peso da perda na métrica de rota (negativo)
	LossWeight = 0.2
)

// ─── TIPOS FUNDAMENTAIS ─────────────────────────────────────────

// QuantumRouteMetric contém métricas de qualidade para rota quântica OAM
type QuantumRouteMetric struct {
	RouteID           string
	SourceNode        string
	DestinationNode   string
	IntermediateNodes []string
	QuantumFidelity   float64 // [0, 1] — fidelidade quântica estimada
	CoherencePhiC     float64 // [0, 1] — coerência média dos nós na rota
	TotalLoss_dB      float64 // perda total do caminho em dB
	Latency_ms        float64 // latência de ponta a ponta em ms
	Bandwidth_Gbps    float64 // largura de banda disponível
	QualityScore      float64 // métrica agregada de qualidade [0, 1]
	LastUpdated       time.Time
}

// ComputeQualityScore calcula score de qualidade agregado para rota
func (m *QuantumRouteMetric) ComputeQualityScore() float64 {
	// Normalizar perda para [0, 1] (menor perda = maior score)
	lossScore := math.Max(0, 1.0-m.TotalLoss_dB/100.0)

	// Combinar métricas com pesos configurados
	score := CoherenceWeight*m.CoherencePhiC +
		FidelityWeight*m.QuantumFidelity +
		LossWeight*lossScore

	return math.Max(0.0, math.Min(1.0, score))
}

// OAMCoherenceRouter integra transceptores OAM com roteamento baseado em coerência
type OAMCoherenceRouter struct {
	nodeID       string
	transceiver  *photonic.OAMTransceiver
	qkd          *quantum.OAMQuantumKeyDistributor
	knownRoutes  map[string]*QuantumRouteMetric
	routeCache   map[string]string // (src,dst) -> best_route_id
	mu           sync.RWMutex
	metrics      RouterMetrics
	config       RouterConfig
	updateTicker *time.Ticker
}

// RouterConfig contém configuração do roteador adaptativo
type RouterConfig struct {
	EnableQuantumRouting     bool
	EnableCoherenceWeighting bool
	RouteDiscoveryInterval   time.Duration
	MaxCachedRoutes          int
	MinRouteQuality          float64
}

// RouterMetrics contém métricas do roteador
type RouterMetrics struct {
	RoutesDiscovered    int64   `json:"routes_discovered"`
	RoutesUsed          int64   `json:"routes_used"`
	AvgRouteQuality     float64 `json:"avg_route_quality"`
	QuantumKeyExchanges int64   `json:"quantum_key_exchanges"`
	ReroutingEvents     int64   `json:"rerouting_events"`
}

// ─── CONSTRUTORES ───────────────────────────────────────────────

// NewOAMCoherenceRouter cria novo roteador adaptativo OAM-coerência
func NewOAMCoherenceRouter(
	nodeID string,
	transceiver *photonic.OAMTransceiver,
	qkd *quantum.OAMQuantumKeyDistributor,
	config RouterConfig,
) *OAMCoherenceRouter {
	if config.RouteDiscoveryInterval == 0 {
		config.RouteDiscoveryInterval = RouteUpdateInterval
	}
	if config.MinRouteQuality == 0 {
		config.MinRouteQuality = 0.7
	}

	router := &OAMCoherenceRouter{
		nodeID:       nodeID,
		transceiver:  transceiver,
		qkd:          qkd,
		knownRoutes:  make(map[string]*QuantumRouteMetric),
		routeCache:   make(map[string]string),
		config:       config,
		updateTicker: time.NewTicker(config.RouteDiscoveryInterval),
	}

	// Iniciar loop de descoberta de rotas
	go router.routeDiscoveryLoop()

	return router
}

// ─── OPERAÇÕES DE ROTEAMENTO ADAPTATIVO ─────────────────────────

// routeDiscoveryLoop executa descoberta periódica de rotas
func (r *OAMCoherenceRouter) routeDiscoveryLoop() {
	for range r.updateTicker.C {
		// Em produção: enviar sondas OAM para descoberta de topologia
		// Aqui: simular atualização de métricas de rotas conhecidas
		r.updateRouteMetrics()
	}
}

// updateRouteMetrics atualiza métricas de rotas conhecidas
func (r *OAMCoherenceRouter) updateRouteMetrics() {
	r.mu.Lock()
	defer r.mu.Unlock()

	for routeID, metric := range r.knownRoutes {
		// Atualizar fidelidade quântica baseada em SNR do transceiver
		status := r.transceiver.GetTransceiverStatus()
		snr := status["snr_per_mode_dB"].(float64)
		metric.QuantumFidelity = computeQuantumFidelityFromSNR(snr)

		// Atualizar perda baseada em distância simulada
		metric.TotalLoss_dB = simulatePathLoss(metric.IntermediateNodes)

		// Recalcular score de qualidade
		metric.QualityScore = metric.ComputeQualityScore()
		metric.LastUpdated = time.Now()

		// Remover rotas de baixa qualidade do cache
		if metric.QualityScore < r.config.MinRouteQuality {
			cacheKey := fmt.Sprintf("%s:%s", metric.SourceNode, metric.DestinationNode)
			delete(r.routeCache, cacheKey)
		}

		r.knownRoutes[routeID] = metric
	}
}

// computeQuantumFidelityFromSNR estima fidelidade quântica a partir de SNR
func computeQuantumFidelityFromSNR(snr_dB float64) float64 {
	// Modelo simplificado: fidelidade decai com perda de SNR
	snr_linear := math.Pow(10, snr_dB/10)
	fidelity := 1.0 - 1.0/(1.0+snr_linear)
	return math.Max(0.0, math.Min(1.0, fidelity))
}

// simulatePathLoss simula perda de caminho baseada em nós intermediários
func simulatePathLoss(nodes []string) float64 {
	// Perda base por nó + perda por distância simulada
	baseLoss := 3.0 // dB por nó
	distanceLoss := float64(len(nodes)) * 0.5
	return baseLoss*float64(len(nodes)+1) + distanceLoss
}

// SelectBestRoute seleciona melhor rota para par (src, dst) baseado em métricas quânticas
func (r *OAMCoherenceRouter) SelectBestRoute(
	source, destination string,
	requireQuantum bool,
) (*QuantumRouteMetric, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	cacheKey := fmt.Sprintf("%s:%s", source, destination)

	// Verificar cache primeiro
	if cachedRouteID, ok := r.routeCache[cacheKey]; ok {
		if route, exists := r.knownRoutes[cachedRouteID]; exists {
			if route.QualityScore >= r.config.MinRouteQuality {
				r.metrics.RoutesUsed++
				return route, nil
			}
		}
	}

	// Buscar todas as rotas válidas para o par
	var validRoutes []*QuantumRouteMetric
	for _, route := range r.knownRoutes {
		if route.SourceNode == source && route.DestinationNode == destination {
			if !requireQuantum || route.QuantumFidelity >= MinQuantumFidelity {
				if route.QualityScore >= r.config.MinRouteQuality {
					validRoutes = append(validRoutes, route)
				}
			}
		}
	}

	if len(validRoutes) == 0 {
		return nil, fmt.Errorf("no valid routes found for %s -> %s", source, destination)
	}

	// Ordenar por score de qualidade (decrescente)
	sort.Slice(validRoutes, func(i, j int) bool {
		return validRoutes[i].QualityScore > validRoutes[j].QualityScore
	})

	bestRoute := validRoutes[0]

	// Atualizar cache
	r.routeCache[cacheKey] = bestRoute.RouteID
	r.metrics.RoutesUsed++

	return bestRoute, nil
}

// RegisterRoute registra nova rota descoberta no roteador
func (r *OAMCoherenceRouter) RegisterRoute(metric *QuantumRouteMetric) {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.knownRoutes[metric.RouteID] = metric
	r.metrics.RoutesDiscovered++

	// Invalidar cache para pares afetados
	cacheKey := fmt.Sprintf("%s:%s", metric.SourceNode, metric.DestinationNode)
	delete(r.routeCache, cacheKey)
}

// ForwardQuantumPacket encaminha pacote quântico via rota selecionada
func (r *OAMCoherenceRouter) ForwardQuantumPacket(
	source, destination string,
	payload []byte,
	useQuantumChannel bool,
) error {
	// Selecionar melhor rota
	route, err := r.SelectBestRoute(source, destination, useQuantumChannel)
	if err != nil {
		return fmt.Errorf("route selection failed: %w", err)
	}

	// Se requer canal quântico, usar QKD para estabelecer chave
	if useQuantumChannel && r.qkd != nil {
		// Iniciar sessão QKD se necessário
		session, err := r.qkd.StartQKDSession(destination, "BB84-d")
		if err != nil {
			return fmt.Errorf("QKD session failed: %w", err)
		}

		// Aguardar chave (simplificação: em produção, usar callback)
		time.Sleep(100 * time.Millisecond)

		// Criptografar payload com chave quântica (simulado)
		encryptedPayload := xorEncrypt(payload, session.FinalKeyBits)
		payload = encryptedPayload
		r.metrics.QuantumKeyExchanges++
	}

	// Encaminhar pacote via transceiver OAM
	// (simplificação: em produção, usar protocolo de encaminhamento real)
	fmt.Printf("📦 Forwarding packet via route %s: %s -> %s (quality=%.3f)\n",
		route.RouteID, source, destination, route.QualityScore)

	return nil
}

// xorEncrypt criptografia XOR simples para demonstração
func xorEncrypt(data, key []byte) []byte {
	result := make([]byte, len(data))
	for i := range data {
		result[i] = data[i] ^ key[i%len(key)]
	}
	return result
}

// GetRouterMetrics retorna métricas consolidadas do roteador
func (r *OAMCoherenceRouter) GetRouterMetrics() RouterMetrics {
	r.mu.RLock()
	defer r.mu.RUnlock()

	// Calcular qualidade média de rotas
	var totalQuality float64
	count := 0
	for _, route := range r.knownRoutes {
		totalQuality += route.QualityScore
		count++
	}
	if count > 0 {
		r.metrics.AvgRouteQuality = totalQuality / float64(count)
	}

	return r.metrics
}

// GetKnownRoutes retorna rotas conhecidas, opcionalmente filtradas
func (r *OAMCoherenceRouter) GetKnownRoutes(minQuality float64) []*QuantumRouteMetric {
	r.mu.RLock()
	defer r.mu.RUnlock()

	routes := make([]*QuantumRouteMetric, 0, len(r.knownRoutes))
	for _, route := range r.knownRoutes {
		if route.QualityScore >= minQuality {
			routes = append(routes, route)
		}
	}
	return routes
}

// Stop interrompe o roteador e libera recursos
func (r *OAMCoherenceRouter) Stop() {
	if r.updateTicker != nil {
		r.updateTicker.Stop()
	}
}
