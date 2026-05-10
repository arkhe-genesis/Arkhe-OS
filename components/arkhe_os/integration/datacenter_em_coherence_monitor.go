package integration

import (
	"math"
	"sync"
	"time"
)

// EMCoherenceMonitorConfig contém a configuração para monitoramento de coerência EM do data center
type EMCoherenceMonitorConfig struct {
	EnableGeomagSensor  bool
	EnableMetasurface   bool
	CoherenceThreshold  float64
	PromotionHysteresis float64
}

// MonitorMetrics contém as métricas de monitoramento
type MonitorMetrics struct {
	LastCoherenceValue float64
	LastFieldStrength  float64
	PowerW             float64
	ActiveComponents   int
}

// EMCoherenceMonitor mede o campo EM coletivo e calcula a coerência de fase
type EMCoherenceMonitor struct {
	mu                 sync.RWMutex
	monitorID          string
	clusterID          string
	datacenterName     string
	config             EMCoherenceMonitorConfig
	gpuComponents      map[string]*GPUComponent
	promotionCallbacks []func(string, float64)
	metrics            MonitorMetrics
	lastSnapshotTime   time.Time
}

// GPUComponent representa um componente de hardware que gera campo EM (e.g. GPU)
type GPUComponent struct {
	GPUID          string
	Position       [3]float64
	ClockFrequency float64
	PowerDrawW     float64
	PhaseOffset    float64
	ActivityLevel  float64
}

// NewEMCoherenceMonitor cria um novo monitor de coerência EM para o data center
func NewEMCoherenceMonitor(
	monitorID, clusterID, datacenterName string,
	config EMCoherenceMonitorConfig,
) (*EMCoherenceMonitor, error) {
	if config.CoherenceThreshold == 0 {
		config.CoherenceThreshold = 0.70
	}
	if config.PromotionHysteresis == 0 {
		config.PromotionHysteresis = 0.05
	}

	monitor := &EMCoherenceMonitor{
		monitorID:      monitorID,
		clusterID:      clusterID,
		datacenterName: datacenterName,
		config:         config,
		gpuComponents:  make(map[string]*GPUComponent),
	}

	// Iniciar loop de monitoramento de coerência (simulado)
	go monitor.monitoringLoop()

	return monitor, nil
}

// RegisterGPUComponent registra ou atualiza um componente GPU no monitor
func (m *EMCoherenceMonitor) RegisterGPUComponent(gpu *GPUComponent) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.gpuComponents[gpu.GPUID] = gpu
}

// RegisterPromotionCallback registra callback para notificação de potencial promoção
func (m *EMCoherenceMonitor) RegisterPromotionCallback(cb func(string, float64)) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.promotionCallbacks = append(m.promotionCallbacks, cb)
}

// GetMonitorMetrics retorna as métricas atuais de monitoramento
func (m *EMCoherenceMonitor) GetMonitorMetrics() MonitorMetrics {
	m.mu.RLock()
	defer m.mu.RUnlock()

	metrics := m.metrics
	metrics.ActiveComponents = len(m.gpuComponents)
	return metrics
}

// calculateDCPhaseCoherence calcula a coerência de fase coletiva Φ_C^DC do data center
// Usa uma fórmula simulada baseada em fusão de sensores e correlação de fase (Sensores 152+162)
func (m *EMCoherenceMonitor) calculateDCPhaseCoherence() (float64, float64, float64) {
	if len(m.gpuComponents) == 0 {
		return 0.0, 0.0, 0.0
	}

	var sumCos, sumSin float64
	var totalPower, totalField float64
	totalWeight := 0.0

	for _, gpu := range m.gpuComponents {
		// Peso baseado no nível de atividade e consumo de energia (simulado)
		weight := gpu.ActivityLevel * (gpu.PowerDrawW / 300.0) // assumindo 300W max
		if weight <= 0 {
			weight = 0.1
		}

		totalWeight += weight
		totalPower += gpu.PowerDrawW

		// Força de campo aproximada
		fieldStrength := math.Sqrt(gpu.PowerDrawW) * gpu.ActivityLevel
		totalField += fieldStrength

		// Correlação de fase (simulação do campo coletivo EM)
		sumCos += weight * math.Cos(gpu.PhaseOffset)
		sumSin += weight * math.Sin(gpu.PhaseOffset)
	}

	// Normalizar
	if totalWeight > 0 {
		sumCos /= totalWeight
		sumSin /= totalWeight
	}

	// Φ_C^DC é a magnitude do vetor de fase resultante
	coherence := math.Sqrt(sumCos*sumCos + sumSin*sumSin)

	// Adicionar um pouco de ruído ou ajustes baseados em geomag/metasurface se habilitados
	if m.config.EnableGeomagSensor {
		// Ajuste simulado do sensor geomagnético 152
		coherence *= 0.98 + 0.04*math.Sin(float64(time.Now().UnixNano())/1e9)
	}

	if m.config.EnableMetasurface {
		// Ajuste simulado do sensor de metasurface 162
		coherence *= 1.05
	}

	// Clamp entre 0.0 e 1.0
	if coherence > 1.0 {
		coherence = 1.0
	} else if coherence < 0.0 {
		coherence = 0.0
	}

	return coherence, totalField / float64(len(m.gpuComponents)), totalPower
}

// monitoringLoop executa a medição de campo EM contínua
func (m *EMCoherenceMonitor) monitoringLoop() {
	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()

	for {
		<-ticker.C

		m.mu.Lock()
		coherence, fieldStrength, totalPower := m.calculateDCPhaseCoherence()

		m.metrics.LastCoherenceValue = coherence
		m.metrics.LastFieldStrength = fieldStrength
		m.metrics.PowerW = totalPower
		m.lastSnapshotTime = time.Now()

		// Checar se deve acionar callback de promoção
		// Usa histerese para evitar oscilações
		threshold := m.config.CoherenceThreshold
		if coherence >= threshold {
			callbacks := m.promotionCallbacks
			cid := m.clusterID
			m.mu.Unlock()

			// Notificar callbacks
			for _, cb := range callbacks {
				cb(cid, coherence)
			}
		} else {
			m.mu.Unlock()
		}
	}
}
