package photonic

import (
	"fmt"
	"math"
	"sync"
	"time"

)

// ─── CONSTANTES DE ROTEAMENTO NANOFOTÔNICO ───────────────
const (
	// DefaultWaveguideWidth largura padrão de guia de onda nanométrico
	DefaultWaveguideWidth = 250.0 // nm
	// DefaultPropagationLoss perda de propagação típica (dB/cm)
	DefaultPropagationLoss = 2.0 // dB/cm para guias de SiN
	// MaxRoutingHops número máximo de hops em roteamento polaritônico
	MaxRoutingHops = 10
	// ModeMatchingTolerance tolerância para mode-matching quântico
	ModeMatchingTolerance = 0.01
)

// ─── TIPOS FUNDAMENTAIS ───────────────────────────────────
// WaveguideType enumera tipos de guias de onda nanométricos
type WaveguideType string

const (
	WaveguideSiliconNitride WaveguideType = "SiN" // Nitreto de silício (baixa perda)
	WaveguideSilicon        WaveguideType = "Si"  // Silício (alta confinamento)
	WaveguidePolymer        WaveguideType = "polymer" // Polímero (flexível)
	WaveguideHybrid         WaveguideType = "hybrid" // Híbrido material
)

// NanophotonicRoute representa rota de coerência via guias nanométricos
type NanophotonicRoute struct {
	RouteID         string
	SourceNode      string
	DestinationNode string
	Waveguides      []WaveguideSegment
	TotalLength     float64 // μm
	TotalLoss       float64 // dB
	ModeMatching    float64 // [0, 1]: qualidade do mode-matching
	PhotonicCoherence float64 // Φ_C^photonic da rota
	Timestamp       time.Time
}

// WaveguideSegment representa segmento individual de guia de onda
type WaveguideSegment struct {
	SegmentID   string
	WaveguideType WaveguideType
	Length      float64 // μm
	Width       float64 // nm
	PropagationLoss float64 // dB/cm
	BendLoss    float64 // dB por curva
	ModeProfile string // Perfil de modo (fundamental, higher-order, etc.)
}

// NanophotonicCoherenceRouter implementa roteamento de estados de API via fotônica nanométrica
type NanophotonicCoherenceRouter struct {
	mu sync.RWMutex

	// Identificação
	routerID string
	networkTopology map[string][]string // Grafo de nós conectados por guias

	// Guias de onda disponíveis
	availableWaveguides map[string]*WaveguideSegment

	// Configuração de roteamento
	config RouterConfig

	// Cache de rotas calculadas
	routeCache map[string]*NanophotonicRoute
	cacheTTL   time.Duration

	// Métricas de roteamento
	metrics RouterMetrics
}

// RouterConfig contém configuração para roteamento nanofotônico
type RouterConfig struct {
	DefaultWaveguideType WaveguideType
	DefaultWidth         float64 // nm
	MaxTotalLoss         float64 // dB máximo permitido por rota
	EnableAdaptiveRouting bool // Roteamento adaptativo baseado em carga
	ModeMatchingRequired bool // Exigir mode-matching quântico
}

// RouterMetrics contém métricas do roteador nanofotônico
type RouterMetrics struct {
	RoutesComputed      int64   `json:"routes_computed"`
	AvgRouteLength      float64 `json:"avg_route_length_um"`
	AvgTotalLoss        float64 `json:"avg_total_loss_dB"`
	AvgModeMatching     float64 `json:"avg_mode_matching"`
	AvgPhotonicCoherence float64 `json:"avg_photonic_coherence"`
	AdaptiveReroutes    int64   `json:"adaptive_reroutes"`
}

// NewNanophotonicCoherenceRouter cria novo roteador de coerência nanofotônico
func NewNanophotonicCoherenceRouter(
	routerID string,
	config RouterConfig,
) (*NanophotonicCoherenceRouter, error) {
	if config.DefaultWidth == 0 {
		config.DefaultWidth = DefaultWaveguideWidth
	}
	if config.MaxTotalLoss == 0 {
		config.MaxTotalLoss = 10.0 // dB
	}

	router := &NanophotonicCoherenceRouter{
		routerID:            routerID,
		networkTopology:     make(map[string][]string),
		availableWaveguides: make(map[string]*WaveguideSegment),
		config:              config,
		routeCache:          make(map[string]*NanophotonicRoute),
		cacheTTL:            5 * time.Minute,
		metrics: RouterMetrics{
			AvgModeMatching:     0.95,
			AvgPhotonicCoherence: 0.92,
		},
	}

	// Inicializar topologia de rede básica (em produção: descobrir dinamicamente)
	router.initializeBasicTopology()

	return router, nil
}

// initializeBasicTopology configura topologia de rede inicial
func (r *NanophotonicCoherenceRouter) initializeBasicTopology() {
	// Nós básicos da Hyper-Mesh fotônica
	nodes := []string{"node_code", "node_data", "node_infra", "node_protocol", "node_meta"}

	// Conectar nós em anel com guias de onda
	for i := range nodes {
		next := (i + 1) % len(nodes)
		r.networkTopology[nodes[i]] = append(r.networkTopology[nodes[i]], nodes[next])
		r.networkTopology[nodes[next]] = append(r.networkTopology[nodes[next]], nodes[i])

		// Criar guia de onda entre nós
		segmentID := fmt.Sprintf("wg_%s_%s", nodes[i], nodes[next])
		r.availableWaveguides[segmentID] = &WaveguideSegment{
			SegmentID:       segmentID,
			WaveguideType:   r.config.DefaultWaveguideType,
			Length:          100.0, // μm (distância típica entre nós em chip)
			Width:           r.config.DefaultWidth,
			PropagationLoss: DefaultPropagationLoss,
			BendLoss:        0.1, // dB por curva de 90°
			ModeProfile:     "fundamental_TE",
		}
	}
}

// ComputeRoute calcula rota ótima para estado de API comprimido via polariton
func (r *NanophotonicCoherenceRouter) ComputeRoute(
	sourceNode, destinationNode string,
	compressedState *CompressedAPIState,
) (*NanophotonicRoute, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	// Verificar cache primeiro
	cacheKey := fmt.Sprintf("%s:%s:%s", sourceNode, destinationNode, compressedState.StateID)
	if cached, ok := r.routeCache[cacheKey]; ok {
		if time.Since(cached.Timestamp) < r.cacheTTL {
			return cached, nil
		}
	}

	// Encontrar caminho mais curto na topologia
	path := r.findShortestPath(sourceNode, destinationNode)
	if path == nil {
		return nil, fmt.Errorf("no path found between %s and %s", sourceNode, destinationNode)
	}

	// Construir rota com segmentos de guia de onda
	var segments []WaveguideSegment
	var totalLength, totalLoss float64

	for i := 0; i < len(path)-1; i++ {
		segmentID := fmt.Sprintf("wg_%s_%s", path[i], path[i+1])
		segment, exists := r.availableWaveguides[segmentID]
		if !exists {
			return nil, fmt.Errorf("waveguide segment not found: %s", segmentID)
		}

		segments = append(segments, *segment)
		totalLength += segment.Length
		totalLoss += segment.PropagationLoss*segment.Length/1e4 + segment.BendLoss // Converter μm para cm
	}

	// Calcular mode-matching quântico
	modeMatching := computeModeMatching(compressedState, segments[0].ModeProfile)
	if modeMatching < ModeMatchingTolerance && r.config.ModeMatchingRequired {
		return nil, fmt.Errorf("mode matching %.4f below tolerance %.4f", modeMatching, ModeMatchingTolerance)
	}

	// Calcular coerência fotônica da rota
	photonicCoherence := compressedState.PhotonicCoherence *
		math.Pow(10, -totalLoss/10) * // Converter dB para fator linear
		modeMatching

	// Verificar perda total máxima
	if totalLoss > r.config.MaxTotalLoss {
		return nil, fmt.Errorf("total loss %.2f dB exceeds maximum %.2f dB", totalLoss, r.config.MaxTotalLoss)
	}

	// Criar rota
	route := &NanophotonicRoute{
		RouteID:           fmt.Sprintf("route_%s_%s_%d", sourceNode[:8], destinationNode[:8], time.Now().UnixNano()),
		SourceNode:        sourceNode,
		DestinationNode:   destinationNode,
		Waveguides:        segments,
		TotalLength:       totalLength,
		TotalLoss:         totalLoss,
		ModeMatching:      modeMatching,
		PhotonicCoherence: photonicCoherence,
		Timestamp:         time.Now(),
	}

	// Atualizar cache
	r.routeCache[cacheKey] = route

	// Atualizar métricas
	r.metrics.RoutesComputed++
	n := r.metrics.RoutesComputed
	r.metrics.AvgRouteLength = (r.metrics.AvgRouteLength*float64(n-1) + totalLength) / float64(n)
	r.metrics.AvgTotalLoss = (r.metrics.AvgTotalLoss*float64(n-1) + totalLoss) / float64(n)
	r.metrics.AvgModeMatching = (r.metrics.AvgModeMatching*float64(n-1) + modeMatching) / float64(n)
	r.metrics.AvgPhotonicCoherence = (r.metrics.AvgPhotonicCoherence*float64(n-1) + photonicCoherence) / float64(n)

	return route, nil
}

// findShortestPath encontra caminho mais curto via BFS
func (r *NanophotonicCoherenceRouter) findShortestPath(
	source, destination string,
) []string {
	if source == destination {
		return []string{source}
	}

	visited := make(map[string]bool)
	queue := [][]string{{source}}

	for len(queue) > 0 {
		path := queue[0]
		queue = queue[1:]
		current := path[len(path)-1]

		if current == destination {
			return path
		}

		if visited[current] {
			continue
		}
		visited[current] = true

		for _, neighbor := range r.networkTopology[current] {
			if !visited[neighbor] {
				newPath := append([]string(nil), path...)
				newPath = append(newPath, neighbor)
				queue = append(queue, newPath)
			}
		}
	}

	return nil // Sem caminho encontrado
}

// computeModeMatching calcula qualidade do mode-matching quântico
func computeModeMatching(
	compressedState *CompressedAPIState,
	waveguideModeProfile string,
) float64 {
	// Mode-matching baseado em similaridade entre perfil do estado comprimido
	// e perfil de modo do guia de onda
	// Simplificação: usar coerência fotônica como proxy
	baseMatching := compressedState.PhotonicCoherence

	// Ajuste baseado em compatibilidade de perfil de modo
	if waveguideModeProfile == "fundamental_TE" {
		baseMatching *= 1.0 // Perfil fundamental: matching ótimo
	} else if waveguideModeProfile == "higher-order" {
		baseMatching *= 0.85 // Modos de ordem superior: matching reduzido
	}

	return math.Max(0.0, math.Min(1.0, baseMatching))
}

// TransmitCompressedState transmite estado comprimido via rota calculada
func (r *NanophotonicCoherenceRouter) TransmitCompressedState(
	route *NanophotonicRoute,
	encryptedState *EncryptedPolaritonState,
) (*TransmissionResult, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	// Simular transmissão através dos guias de onda
	// Em produção: acoplar estado polaritônico ao guia e propagar

	// Calcular degradação durante transmissão
	transmissionLoss := math.Pow(10, -route.TotalLoss/10)
	finalCoherence := encryptedState.PhotonicCoherence * transmissionLoss * route.ModeMatching

	// Determinar sucesso baseado em coerência final
	success := finalCoherence >= 0.70 // Threshold mínimo para coerência útil

	result := &TransmissionResult{
		TransmissionID:    fmt.Sprintf("tx_%s_%d", route.RouteID[:8], time.Now().UnixNano()),
		RouteID:           route.RouteID,
		StateID:           encryptedState.StateID,
		Success:           success,
		FinalCoherence:    finalCoherence,
		TransmissionTime:  route.TotalLength / 3e5, // μm / (c em μm/ps) ≈ tempo em ps
		LossIncurred:      route.TotalLoss,
		Timestamp:         time.Now(),
	}

	return result, nil
}

// TransmissionResult representa resultado de transmissão nanofotônica
type TransmissionResult struct {
	TransmissionID string
	RouteID        string
	StateID        string
	Success        bool
	FinalCoherence float64
	TransmissionTime float64 // ps
	LossIncurred   float64 // dB
	Timestamp      time.Time
}

// GetRouterMetrics retorna métricas consolidadas do roteador
func (r *NanophotonicCoherenceRouter) GetRouterMetrics() RouterMetrics {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return r.metrics
}
