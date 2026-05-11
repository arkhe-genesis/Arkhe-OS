package integration

import (
	"fmt"
	"math"
	"sync"
	"time"
)

// ActionPotential representa um disparo neuronal simulado
type ActionPotential struct {
	PotentialID  string
	GPUID        string
	Timestamp    time.Time
	AmplitudeV   float64 // Voltagem do potencial de ação (geralmente em mV mas armazenado em V)
	Frequency_Hz float64 // Taxa de disparo
	Fired        bool    // Se ultrapassou o threshold
}

// GradientToActionPotentialMapper converte gradientes de loss em potenciais de ação
type GradientToActionPotentialMapper struct {
	mu             sync.Mutex
	config         map[string]float64
	gpuRefractory  map[string]time.Time // Período refratário por GPU
	potentialCount int64
}

// NewGradientToActionPotentialMapper cria um novo mapeador
func NewGradientToActionPotentialMapper(config map[string]float64) *GradientToActionPotentialMapper {
	if config == nil {
		config = map[string]float64{
			"scale_factor":   1e-6,
			"fire_threshold": 0.1,
			"resting_mv":     -70.0,
			"peak_mv":        30.0,
			"refractory_ms":  2.0, // Período refratário absoluto
		}
	}

	// Garantir defaults
	if _, ok := config["scale_factor"]; !ok { config["scale_factor"] = 1e-6 }
	if _, ok := config["fire_threshold"]; !ok { config["fire_threshold"] = 0.1 }
	if _, ok := config["resting_mv"]; !ok { config["resting_mv"] = -70.0 }
	if _, ok := config["peak_mv"]; !ok { config["peak_mv"] = 30.0 }
	if _, ok := config["refractory_ms"]; !ok { config["refractory_ms"] = 2.0 }

	return &GradientToActionPotentialMapper{
		config:        config,
		gpuRefractory: make(map[string]time.Time),
	}
}

// MapGradientToPotential mapeia um vetor gradiente ∇ℒ para um ActionPotential
func (m *GradientToActionPotentialMapper) MapGradientToPotential(
	gpuID string,
	gradient []float64,
	timestamp time.Time,
) ActionPotential {
	m.mu.Lock()
	defer m.mu.Unlock()

	// 1. Checar período refratário
	if lastFire, exists := m.gpuRefractory[gpuID]; exists {
		refractoryDuration := time.Duration(m.config["refractory_ms"] * float64(time.Millisecond))
		if timestamp.Sub(lastFire) < refractoryDuration {
			// Ainda no período refratário, não dispara
			return ActionPotential{
				PotentialID:  fmt.Sprintf("ap_refractory_%d", m.potentialCount),
				GPUID:        gpuID,
				Timestamp:    timestamp,
				AmplitudeV:   m.config["resting_mv"] / 1000.0,
				Frequency_Hz: 0,
				Fired:        false,
			}
		}
	}

	// 2. Calcular a norma L2 do gradiente (||∇ℒ||)
	var normSq float64
	for _, val := range gradient {
		normSq += val * val
	}
	norm := math.Sqrt(normSq)

	// 3. Normalização sigmoide (simulando a resposta não-linear de um neurônio)
	// scaled_norm = norm * scale_factor
	scaledNorm := norm * m.config["scale_factor"]

	// sigmoid(x) = 1 / (1 + exp(-x))
	// Nós ajustamos para que entrada 0 resulte em ativação ~0
	normalized := (2.0 / (1.0 + math.Exp(-scaledNorm))) - 1.0

	// 4. Checar threshold de disparo
	threshold := m.config["fire_threshold"]
	fired := normalized >= threshold

	var amplitudeV float64
	var freqHz float64

	if fired {
		// V_action = V_resting + (V_peak - V_resting) * normalized
		resting := m.config["resting_mv"]
		peak := m.config["peak_mv"]

		// Calcular a amplitude interpolada e converter de mV para V
		amplitudeMV := resting + ((peak - resting) * normalized)
		amplitudeV = amplitudeMV / 1000.0

		// Frequência baseada na intensidade (Rate Coding)
		// Quanto maior a ativação, maior a taxa de disparo (ex: 10Hz a 150Hz)
		freqHz = 10.0 + (normalized * 140.0)

		// Atualizar período refratário
		m.gpuRefractory[gpuID] = timestamp
		m.potentialCount++
	} else {
		// Mantém o potencial de repouso
		amplitudeV = m.config["resting_mv"] / 1000.0
		freqHz = 0.0
	}

	return ActionPotential{
		PotentialID:  fmt.Sprintf("ap_%s_%d", gpuID, m.potentialCount),
		GPUID:        gpuID,
		Timestamp:    timestamp,
		AmplitudeV:   amplitudeV,
		Frequency_Hz: freqHz,
		Fired:        fired,
	}
}
