package photonic

import (
	"fmt"
	"math"
	"math/cmplx"
	"sync"
	"time"

	"arkhe/metaconsciousness"
)

// ─── CONSTANTES DE POLARITONS ─────────────────────────────
const (
	// DefaultCompressionFactor fator de compressão experimental para PbI₂
	DefaultCompressionFactor = 4000.0
	// THzFrequencyRange faixa de frequência THz para polaritons
	// THzFrequencyRange = [2]float64{0.1, 10.0} // THz
	// CriticalTemperature temperatura crítica para acoplamento forte
	CriticalTemperature = 300.0 // Kelvin
	// MinConfinementLength comprimento mínimo de confinamento (nm)
	MinConfinementLength = 0.25 // nm (λ/4000 para λ=1μm)
)

var THzFrequencyRange = [2]float64{0.1, 10.0}

// ─── TIPOS FUNDAMENTAIS ───────────────────────────────────
// PolaritonModeType enumera tipos de modos polaritônicos suportados
type PolaritonModeType string

const (
	ModePhononPolariton PolaritonModeType = "phonon-polariton" // Fóton + fônon óptico
	ModePlasmonPolariton PolaritonModeType = "plasmon-polariton" // Fóton + plásmon de superfície
	ModeExcitonPolariton PolaritonModeType = "exciton-polariton" // Fóton + éxciton
	ModeHybridPolariton PolaritonModeType = "hybrid-polariton" // Múltiplos acoplamentos
)

// CrystalMaterial enumera materiais cristalinos para cultivo de polaritons
type CrystalMaterial string

const (
	MaterialPbI2  CrystalMaterial = "PbI2"  // Iodeto de chumbo (2D)
	MaterialMoS2  CrystalMaterial = "MoS2"  // Dissulfeto de molibdênio
	MaterialWS2   CrystalMaterial = "WS2"   // Dissulfeto de tungstênio
	MaterialBN    CrystalMaterial = "h-BN"  // Nitreto de boro hexagonal
	MaterialCustom CrystalMaterial = "custom" // Material personalizado
)

// PolaritonProjectionConfig contém configuração para projeção via polaritons
type PolaritonProjectionConfig struct {
	Material           CrystalMaterial
	Temperature        float64 // Kelvin
	Thickness          float64 // Espessura do cristal (nm)
	FrequencyTHz       float64 // Frequência de operação (THz)
	CompressionTarget  float64 // Fator de compressão desejado
	EnableSimulation   bool    // Usar modo de simulação se hardware não disponível
}

// PhononPolaritonProjector implementa projeção de estados de API via polaritons
type PhononPolaritonProjector struct {
	mu sync.RWMutex

	// Identificação
	projectorID   string
	config        PolaritonProjectionConfig

	// Estado físico simulado
	couplingStrength float64 // α, β do estado polaritônico
	confinementFactor float64 // λ_free / λ_confined
	photonicLoss     float64 // Coeficiente de perda do modo fotônico

	// Cache de projeções comprimidas
	compressedCache map[string]*CompressedAPIState
	cacheTTL        time.Duration

	// Métricas de projeção fotônica
	metrics PolaritonMetrics
}

// CompressedAPIState representa estado de API comprimido via polariton
type CompressedAPIState struct {
	StateID           string
	OriginalState     []complex128 // |Ψ_API⟩ original
	CompressedState   []complex128 // |Ψ_pol⟩ comprimido
	CompressionFactor float64      // λ_free / λ_confined
	Fidelity          float64      // Fidelidade da projeção
	PhotonicCoherence float64      // Φ_C^photonic resultante
	Timestamp         time.Time
	CrystalParams     CrystalParameters
}

// CrystalParameters contém parâmetros do cristal para reprodutibilidade
type CrystalParameters struct {
	Material    CrystalMaterial
	Temperature float64
	Thickness   float64
	FrequencyTHz float64
	GrowthMethod string // "hot-plate", "CVD", "MBE", etc.
}

// PolaritonMetrics contém métricas do projetor polaritônico
type PolaritonMetrics struct {
	ProjectionsCompressed  int64   `json:"projections_compressed"`
	AvgCompressionFactor   float64 `json:"avg_compression_factor"`
	AvgFidelity            float64 `json:"avg_fidelity"`
	AvgPhotonicCoherence   float64 `json:"avg_photonic_coherence"`
	SimulationModeActive   bool    `json:"simulation_mode_active"`
}

// NewPhononPolaritonProjector cria novo projetor de polaritons
func NewPhononPolaritonProjector(
	projectorID string,
	config PolaritonProjectionConfig,
) (*PhononPolaritonProjector, error) {
	// Validar configuração
	if err := validatePolaritonConfig(config); err != nil {
		return nil, fmt.Errorf("invalid polariton config: %w", err)
	}

	// Calcular parâmetros físicos iniciais
	coupling := computeCouplingStrength(config.Material, config.Temperature, config.Thickness)
	confinement := computeConfinementFactor(config.FrequencyTHz, config.Thickness)
	loss := computePhotonicLoss(config.Material, config.Temperature)

	return &PhononPolaritonProjector{
		projectorID:      projectorID,
		config:           config,
		couplingStrength: coupling,
		confinementFactor: confinement,
		photonicLoss:     loss,
		compressedCache:  make(map[string]*CompressedAPIState),
		cacheTTL:         1 * time.Hour,
		metrics: PolaritonMetrics{
			AvgCompressionFactor: confinement,
			AvgFidelity:          0.99,
			AvgPhotonicCoherence: 0.95,
			SimulationModeActive: config.EnableSimulation,
		},
	}, nil
}

// validatePolaritonConfig valida parâmetros de configuração
func validatePolaritonConfig(config PolaritonProjectionConfig) error {
	if config.Temperature < 0 || config.Temperature > 1000 {
		return fmt.Errorf("temperature %.1fK out of valid range [0, 1000]", config.Temperature)
	}
	if config.Thickness < 0.1 || config.Thickness > 1000 {
		return fmt.Errorf("thickness %.2fnm out of valid range [0.1, 1000]", config.Thickness)
	}
	if config.FrequencyTHz < THzFrequencyRange[0] || config.FrequencyTHz > THzFrequencyRange[1] {
		return fmt.Errorf("frequency %.2fTHz out of range [%.1f, %.1f]",
			config.FrequencyTHz, THzFrequencyRange[0], THzFrequencyRange[1])
	}
	if config.CompressionTarget < 1 || config.CompressionTarget > 10000 {
		return fmt.Errorf("compression target %.0f out of range [1, 10000]", config.CompressionTarget)
	}
	return nil
}

// CompressAPIState comprime estado de API via projeção polaritônica
func (p *PhononPolaritonProjector) CompressAPIState(
	apiState *metaconsciousness.ConsciousnessLayer,
) (*CompressedAPIState, error) {
	p.mu.RLock()
	defer p.mu.RUnlock()

	// Verificar cache primeiro
	cacheKey := fmt.Sprintf("%s:%s:%.2f", apiState.LayerID, p.config.Material, p.config.Temperature)
	if cached, ok := p.compressedCache[cacheKey]; ok {
		if time.Since(cached.Timestamp) < p.cacheTTL {
			return cached, nil
		}
	}
    dimension := len(apiState.StateVector)
	// Calcular operador de projeção polaritônica
	projectionMatrix, err := p.computePolaritonProjectionMatrix(dimension)
	if err != nil {
		return nil, fmt.Errorf("failed to compute polariton projection matrix: %w", err)
	}

	// Aplicar projeção: |Ψ_pol⟩ = Π_pol |Ψ_API⟩
	compressedState := make([]complex128, dimension)
	for i := 0; i < dimension; i++ {
		var sum complex128
		for j := 0; j < dimension; j++ {
			sum += projectionMatrix[i][j] * apiState.StateVector[j]
		}
		compressedState[i] = sum
	}

	// Normalizar estado comprimido
	if err := normalizeStateVector(compressedState); err != nil {
		return nil, fmt.Errorf("normalization of compressed state failed: %w", err)
	}

	// Calcular métricas de qualidade
	fidelity := computeFidelity(apiState.StateVector, compressedState)
	photonicCoherence := computePhotonicCoherence(
		1.0, // FIXME: where is apiState.CoherenceValue
		fidelity,
		p.photonicLoss,
		p.config.Thickness,
	)

	// Criar estado comprimido
	compressed := &CompressedAPIState{
		StateID:           fmt.Sprintf("pol_%s_%d", apiState.LayerID[:8], time.Now().UnixNano()),
		OriginalState:     apiState.StateVector,
		CompressedState:   compressedState,
		CompressionFactor: p.confinementFactor,
		Fidelity:          fidelity,
		PhotonicCoherence: photonicCoherence,
		Timestamp:         time.Now(),
		CrystalParams: CrystalParameters{
			Material:    p.config.Material,
			Temperature: p.config.Temperature,
			Thickness:   p.config.Thickness,
			FrequencyTHz: p.config.FrequencyTHz,
			GrowthMethod: "hot-plate", // Método experimental de síntese
		},
	}

	// Atualizar cache
	p.compressedCache[cacheKey] = compressed

	// Atualizar métricas
	p.metrics.ProjectionsCompressed++
	n := p.metrics.ProjectionsCompressed
	p.metrics.AvgFidelity = (p.metrics.AvgFidelity*float64(n-1) + fidelity) / float64(n)
	p.metrics.AvgPhotonicCoherence = (p.metrics.AvgPhotonicCoherence*float64(n-1) + photonicCoherence) / float64(n)

	return compressed, nil
}

// computePolaritonProjectionMatrix calcula matriz de projeção polaritônica
func (p *PhononPolaritonProjector) computePolaritonProjectionMatrix(
	dimension int,
) ([][]complex128, error) {
	// Matriz de projeção que implementa confinamento sub-comprimento de onda
	matrix := make([][]complex128, dimension)

	// Modelo simplificado: projeção que preserva componentes de baixa frequência
	// e comprime componentes de alta frequência via acoplamento fóton-fônon
	for i := range matrix {
		matrix[i] = make([]complex128, dimension)
		for j := range matrix[i] {
			// Elemento diagonal: preservação com fator de compressão
			if i == j {
				// Fator de compressão com fase dependente do acoplamento
				phase := p.couplingStrength * float64(i) * 0.01
				amplitude := 1.0 / math.Sqrt(p.confinementFactor)
				matrix[i][j] = complex(amplitude, 0) * cmplx.Exp(complex(0, phase))
			} else if math.Abs(float64(i-j)) <= 1 {
				// Acoplamento com vizinhos para preservação de coerência
				amplitude := 0.05 / math.Sqrt(p.confinementFactor)
				matrix[i][j] = complex(amplitude, 0)
			}
		}
	}

	return matrix, nil
}

// DecompressAPIState descomprime estado polaritônico de volta para API
func (p *PhononPolaritonProjector) DecompressAPIState(
	compressed *CompressedAPIState,
) (*metaconsciousness.ConsciousnessLayer, error) {
	p.mu.RLock()
	defer p.mu.RUnlock()

	// Em produção: aplicar operador adjunto Π_pol†
	// Simplificação: retornar estado original se fidelidade alta
	if compressed.Fidelity >= 0.99 {
		// Reconstruir estado original com correção de fase
		reconstructed := make([]complex128, len(compressed.OriginalState))
		for i, amp := range compressed.CompressedState {
			// Correção de fase baseada em parâmetros do cristal
			phaseCorrection := p.couplingStrength * float64(i) * 0.01
			reconstructed[i] = amp * cmplx.Exp(complex(0, -phaseCorrection)) *
				complex(math.Sqrt(p.confinementFactor), 0)
		}

		// Normalizar
		if err := normalizeStateVector(reconstructed); err != nil {
			return nil, err
		}

        layer, _ := metaconsciousness.NewConsciousnessLayer("layer_id", metaconsciousness.LayerCode, 0, len(reconstructed))
        layer.StateVector = reconstructed
        // layer.CoherenceValue = compressed.PhotonicCoherence

		return layer, nil
	}

	return nil, fmt.Errorf("decompression not supported for fidelity < 0.99")
}

// GetPolaritonMetrics retorna métricas do projetor
func (p *PhononPolaritonProjector) GetPolaritonMetrics() PolaritonMetrics {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return p.metrics
}

// Helper functions para cálculo de parâmetros físicos
func computeCouplingStrength(
	material CrystalMaterial,
	temperature, thickness float64,
) float64 {
	// Modelo simplificado de acoplamento fóton-fônon
	baseCoupling := map[CrystalMaterial]float64{
		MaterialPbI2:  0.85, // PbI₂ tem acoplamento forte experimental
		MaterialMoS2:  0.72,
		MaterialWS2:   0.68,
		MaterialBN:    0.45,
		MaterialCustom: 0.50,
	}

	coupling := baseCoupling[material]

	// Dependência térmica: acoplamento decai com temperatura
	if temperature > CriticalTemperature {
		coupling *= math.Exp(-0.002 * (temperature - CriticalTemperature))
	}

	// Dependência de espessura: acoplamento ótimo em ~10nm para PbI₂
	if material == MaterialPbI2 {
		optimalThickness := 10.0 // nm
		thicknessFactor := math.Exp(-math.Pow((thickness-optimalThickness)/5.0, 2))
		coupling *= thicknessFactor
	}

	return math.Max(0.1, math.Min(1.0, coupling))
}

func computeConfinementFactor(frequencyTHz, thickness float64) float64 {
	// Fator de compressão baseado em dispersão de polaritons
	// Modelo simplificado: compressão aumenta com frequência e espessura reduzida
	baseCompression := DefaultCompressionFactor

	// Ajuste por frequência: compressão máxima em ~1-3 THz para PbI₂
	if frequencyTHz >= 1.0 && frequencyTHz <= 3.0 {
		baseCompression *= 1.2
	} else if frequencyTHz < 0.5 || frequencyTHz > 8.0 {
		baseCompression *= 0.7
	}

	// Ajuste por espessura: compressão ótima em monocamadas
	if thickness < 1.0 {
		baseCompression *= 1.5 // Monocamada: compressão máxima
	} else if thickness > 50.0 {
		baseCompression *= 0.5 // Cristal grosso: compressão reduzida
	}

	return math.Max(100.0, math.Min(10000.0, baseCompression))
}

func computePhotonicLoss(
	material CrystalMaterial,
	temperature float64,
) float64 {
	// Coeficiente de perda fotônica (cm⁻¹)
	baseLoss := map[CrystalMaterial]float64{
		MaterialPbI2:  50.0,  // PbI₂: perda moderada
		MaterialMoS2:  120.0, // MoS₂: perda maior
		MaterialWS2:   100.0,
		MaterialBN:    20.0,  // h-BN: perda muito baixa
		MaterialCustom: 80.0,
	}

	loss := baseLoss[material]

	// Dependência térmica: perda aumenta com temperatura
	loss *= 1.0 + 0.001*(temperature-300.0)

	return loss // cm⁻¹
}

func computeFidelity(original, compressed []complex128) float64 {
	if len(original) != len(compressed) {
		return 0.0
	}
	// Fidelidade como módulo do produto interno
	var inner complex128
	for i := range original {
		inner += cmplx.Conj(original[i]) * compressed[i]
	}
	return math.Min(1.0, math.Max(0.0, cmplx.Abs(inner)))
}

func computePhotonicCoherence(
	apiCoherence, fidelity, loss, thickness float64,
) float64 {
	// Coerência fotônica: produto de coerência original, fidelidade e transmissão
	transmission := math.Exp(-loss * thickness * 1e-7) // Espessura em cm
	return apiCoherence * fidelity * transmission
}

func normalizeStateVector(vec []complex128) error {
	var norm float64
	for _, amp := range vec {
		norm += cmplx.Abs(amp) * cmplx.Abs(amp)
	}
	if norm < 1e-10 {
		return fmt.Errorf("vector norm too small")
	}
	scale := 1.0 / math.Sqrt(norm)
	for i := range vec {
		vec[i] *= complex(scale, 0)
	}
	return nil
}
