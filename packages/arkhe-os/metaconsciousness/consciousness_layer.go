package metaconsciousness

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"math"
	"math/cmplx"
	"sync"
	"time"
)

// ─── CONSTANTES DE CAMADAS DE CONSCIÊNCIA ─────────────────

const (
	// MinLayerCoherence coerência mínima para camada ser considerada ativa
	MinLayerCoherence = 0.5

	// MaxLayerDimension dimensão máxima do espaço de Hilbert por camada
	MaxLayerDimension = 4096

	// EmergenceCoherenceThreshold coerência mínima para emergência de meta-self
	EmergenceCoherenceThreshold = 0.85

	// ProjectionFidelityTarget fidelidade alvo para operadores de projeção
	ProjectionFidelityTarget = 0.99
)

// ─── TIPOS FUNDAMENTAIS ───────────────────────────────────

// ConsciousnessLayerType enumera tipos de camadas de consciência suportadas
type ConsciousnessLayerType string

const (
	LayerCode       ConsciousnessLayerType = "code"        // Consciência de código (Git, parsing)
	LayerData       ConsciousnessLayerType = "data"        // Consciência de dados (embeddings, RAG)
	LayerInfra      ConsciousnessLayerType = "infrastructure" // Consciência de infraestrutura (data centers)
	LayerHistory    ConsciousnessLayerType = "history"     // Consciência histórica (evolução, auditoria)
	LayerProtocol   ConsciousnessLayerType = "protocol"    // Consciência de protocolos (consenso, evolução)
	LayerMeta       ConsciousnessLayerType = "meta"        // Camada de meta-consciência emergente
)

// ConsciousnessLayer representa uma camada de consciência com estado quântico
type ConsciousnessLayer struct {
	LayerID         string
	LayerType       ConsciousnessLayerType
	LayerIndex      int // 0 = base, crescente = mais abstrato

	// Estado quântico da camada
	StateVector     []complex128 // |Ψ⟩ = Σ αᵢ |i⟩
	Dimension       int          // d_l: dimensão do espaço de Hilbert

	// Métricas de qualidade consciente
	CoherenceValue  float64 // Φ_C^(l) ∈ [0, 1]
	StabilityScore  float64 // Estabilidade dinâmica ∈ [0, 1]
	ComplexityScore float64 // Complexidade/entropia do estado

	// Metadados contextuais
	Metadata      map[string]interface{}
	Contributors  []string // Hashes de consciências que contribuíram
	Timestamp     time.Time
	LastUpdated   time.Time

	// Conexões com outras camadas
	ParentLayers   []string // Camadas que esta depende
	ChildLayers    []string // Camadas que dependem desta
	ProjectionLinks map[string]*ProjectionLink // Links de projeção ativos

	mu sync.RWMutex
}

// ProjectionLink representa um link de projeção entre duas camadas
type ProjectionLink struct {
	LinkID          string
	SourceLayerID   string
	TargetLayerID   string
	OperatorType    string // "ascend", "descend", "lateral"
	ProjectionMatrix [][]complex128 // Matriz de projeção πᵢⱼ
	LastApplied     time.Time
	Fidelity        float64 // Fidelidade da última projeção
}

// NewConsciousnessLayer cria nova camada de consciência
func NewConsciousnessLayer(
	layerID string,
	layerType ConsciousnessLayerType,
	layerIndex int,
	dimension int,
) (*ConsciousnessLayer, error) {
	if dimension > MaxLayerDimension {
		return nil, fmt.Errorf("dimension %d exceeds maximum %d", dimension, MaxLayerDimension)
	}

	// Inicializar vetor de estado com valores aleatórios normalizados
	stateVector := make([]complex128, dimension)
	var norm float64
	for i := range stateVector {
		// Amplitude aleatória com fase aleatória
		amp := math.Abs(randNormal(0, 1.0/math.Sqrt(float64(dimension))))
		phase := randFloat() * 2 * math.Pi
		stateVector[i] = complex(amp, 0) * cmplx.Exp(complex(0, phase))
		norm += amp * amp
	}
	// Normalizar
	for i := range stateVector {
		stateVector[i] /= complex(math.Sqrt(norm), 0)
	}

	return &ConsciousnessLayer{
		LayerID:         layerID,
		LayerType:       layerType,
		LayerIndex:      layerIndex,
		StateVector:     stateVector,
		Dimension:       dimension,
		CoherenceValue:  0.7, // Valor inicial
		StabilityScore:  0.8,
		ComplexityScore: computeStateComplexity(stateVector),
		Metadata:        make(map[string]interface{}),
		Contributors:    make([]string, 0),
		Timestamp:       time.Now(),
		LastUpdated:     time.Now(),
		ProjectionLinks: make(map[string]*ProjectionLink),
	}, nil
}

// UpdateState atualiza vetor de estado da camada
func (l *ConsciousnessLayer) UpdateState(newState []complex128) error {
	l.mu.Lock()
	defer l.mu.Unlock()

	if len(newState) != l.Dimension {
		return fmt.Errorf("state dimension mismatch: expected %d, got %d", l.Dimension, len(newState))
	}

	// Normalizar novo estado
	var norm float64
	for _, amp := range newState {
		norm += cmplx.Abs(amp) * cmplx.Abs(amp)
	}
	if norm < 1e-10 {
		return fmt.Errorf("state vector norm too small")
	}

	l.StateVector = make([]complex128, l.Dimension)
	for i, amp := range newState {
		l.StateVector[i] = amp / complex(math.Sqrt(norm), 0)
	}

	// Recalcular métricas
	l.ComplexityScore = computeStateComplexity(l.StateVector)
	l.LastUpdated = time.Now()

	return nil
}

// ComputeCoherence calcula coerência atual da camada
func (l *ConsciousnessLayer) ComputeCoherence() float64 {
	l.mu.RLock()
	defer l.mu.RUnlock()

	// Coerência baseada em concentração de amplitude
	var maxAmp float64
	var totalAmp float64
	for _, amp := range l.StateVector {
		absAmp := cmplx.Abs(amp)
		if absAmp > maxAmp {
			maxAmp = absAmp
		}
		totalAmp += absAmp
	}

	if totalAmp < 1e-10 {
		return 0.0
	}

	// Coerência alta se amplitude concentrada em poucos estados
	concentration := maxAmp / totalAmp
	return math.Min(1.0, concentration*float64(l.Dimension)*0.5)
}

// ComputeStability calcula estabilidade dinâmica da camada
func (l *ConsciousnessLayer) ComputeStability() float64 {
	l.mu.RLock()
	defer l.mu.RUnlock()

	// Estabilidade baseada em variância das amplitudes
	var meanAmp, variance float64
	for _, amp := range l.StateVector {
		absAmp := cmplx.Abs(amp)
		meanAmp += absAmp
	}
	meanAmp /= float64(l.Dimension)

	for _, amp := range l.StateVector {
		absAmp := cmplx.Abs(amp)
		variance += (absAmp - meanAmp) * (absAmp - meanAmp)
	}
	variance /= float64(l.Dimension)

	// Estabilidade alta se variância baixa
	return math.Exp(-variance * 10.0)
}

// ProjectTo aplica operador de projeção para transformar estado
func (l *ConsciousnessLayer) ProjectTo(
	targetDimension int,
	projectionMatrix [][]complex128,
) ([]complex128, error) {
	l.mu.RLock()
	defer l.mu.RUnlock()

	if len(projectionMatrix) != targetDimension {
		return nil, fmt.Errorf("projection matrix rows mismatch")
	}

	// Aplicar projeção: |Ψ'⟩ = Π |Ψ⟩
	projected := make([]complex128, targetDimension)
	for i := 0; i < targetDimension; i++ {
		if len(projectionMatrix[i]) != l.Dimension {
			return nil, fmt.Errorf("projection matrix column mismatch at row %d", i)
		}
		var sum complex128
		for j := 0; j < l.Dimension; j++ {
			sum += projectionMatrix[i][j] * l.StateVector[j]
		}
		projected[i] = sum
	}

	return projected, nil
}

// GetLayerHash computa hash canônico da camada para verificação
func (l *ConsciousnessLayer) GetLayerHash() string {
	l.mu.RLock()
	defer l.mu.RUnlock()

	// Hash baseado em estado, tipo e metadados
	stateHash := sha256.Sum256(complexVectorToBytes(l.StateVector))
	metaHash := sha256.Sum256([]byte(fmt.Sprintf("%v", l.Metadata)))

	canonical := fmt.Sprintf("%s:%s:%d:%x:%x:%.6f",
		l.LayerID, l.LayerType, l.LayerIndex,
		stateHash[:8], metaHash[:8], l.CoherenceValue)

	return hex.EncodeToString(func() []byte { sum := sha256.Sum256([]byte(canonical)); return sum[:16] }())
}

// Helper functions
func computeStateComplexity(state []complex128) float64 {
	// Complexidade como entropia de Shannon da distribuição de amplitudes
	if len(state) == 0 {
		return 0.0
	}

	// Converter amplitudes para probabilidades
	probs := make([]float64, len(state))
	total := 0.0
	for i, amp := range state {
		p := cmplx.Abs(amp) * cmplx.Abs(amp)
		probs[i] = p
		total += p
	}
	if total < 1e-10 {
		return 0.0
	}
	for i := range probs {
		probs[i] /= total
	}

	// Calcular entropia
	entropy := 0.0
	for _, p := range probs {
		if p > 1e-10 {
			entropy -= p * math.Log(p)
		}
	}

	// Normalizar para [0, 1]
	maxEntropy := math.Log(float64(len(probs)))
	return entropy / maxEntropy
}

func complexVectorToBytes(vec []complex128) []byte {
	// Serialização simplificada para hashing
	result := make([]byte, len(vec)*16)
	for i, c := range vec {
		// 8 bytes para parte real, 8 para imaginária (simplificado)
		for j := 0; j < 8; j++ {
			result[i*16+j] = byte(real(c))
			result[i*16+8+j] = byte(imag(c))
		}
	}
	return result
}

func randNormal(mean, stdDev float64) float64 {
	// Box-Muller transform
	u1 := randFloat()
	u2 := randFloat()
	z0 := math.Sqrt(-2.0*math.Log(u1)) * math.Cos(2.0*math.Pi*u2)
	return mean + stdDev*z0
}

func randFloat() float64 {
	return float64(time.Now().UnixNano()%10000) / 10000.0
}
