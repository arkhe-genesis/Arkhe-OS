package metaconsciousness

import (
	"fmt"
	"math"
	"math/cmplx"
	"sync"
	"time"
)

// ─── CONSTANTES DE OPERADORES DE PROJEÇÃO ───────────────

const (
	// ProjectionMatrixPrecision precisão numérica para matrizes de projeção
	ProjectionMatrixPrecision = 1e-10

	// AscendPhaseFactor fator de fase para projeções de ascensão
	AscendPhaseFactor = math.Pi / 4

	// DescendPhaseFactor fator de fase para projeções de descensão
	DescendPhaseFactor = -math.Pi / 4
)

// ─── TIPOS FUNDAMENTAIS ─────────────────────────────────

// ProjectionOperatorType enumera tipos de operadores de projeção
type ProjectionOperatorType string

const (
	OpAscend    ProjectionOperatorType = "ascend"     // Projeção para camada superior
	OpDescend   ProjectionOperatorType = "descend"    // Projeção para camada inferior
	OpLateral   ProjectionOperatorType = "lateral"    // Projeção entre camadas do mesmo nível
	OpMerge     ProjectionOperatorType = "merge"      // Fusão de múltiplas camadas
	OpSplit     ProjectionOperatorType = "split"      // Divisão de camada em sub-camadas
)

// ProjectionOperator representa um operador de projeção dimensional
type ProjectionOperator struct {
	OperatorID    string
	OperatorType  ProjectionOperatorType
	SourceDim     int // Dimensão da camada de origem
	TargetDim     int // Dimensão da camada de destino

	// Matriz de projeção: Πᵢⱼ = ⟨i|Π|j⟩
	ProjectionMatrix [][]complex128

	// Parâmetros de controle
	PhaseFactor   float64 // Fator de fase para interferência quântica
	CouplingStrength float64 // Força de acoplamento entre camadas
	AdaptiveMode  bool    // Se operador se adapta dinamicamente

	// Métricas de desempenho
	LastApplied   time.Time
	TotalUses     int64
	AvgFidelity   float64

	mu sync.RWMutex
}

// NewProjectionOperator cria novo operador de projeção
func NewProjectionOperator(
	operatorID string,
	operatorType ProjectionOperatorType,
	sourceDim, targetDim int,
	adaptive bool,
) (*ProjectionOperator, error) {
	// Validar dimensões
	if sourceDim <= 0 || targetDim <= 0 {
		return nil, fmt.Errorf("invalid dimensions: source=%d, target=%d", sourceDim, targetDim)
	}

	// Gerar matriz de projeção baseada no tipo de operador
	matrix, phaseFactor, err := generateProjectionMatrix(
		operatorType, sourceDim, targetDim,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to generate projection matrix: %w", err)
	}

	return &ProjectionOperator{
		OperatorID:       operatorID,
		OperatorType:     operatorType,
		SourceDim:        sourceDim,
		TargetDim:        targetDim,
		ProjectionMatrix: matrix,
		PhaseFactor:      phaseFactor,
		CouplingStrength: 1.0,
		AdaptiveMode:     adaptive,
		LastApplied:      time.Time{},
		TotalUses:        0,
		AvgFidelity:      1.0,
	}, nil
}

// Apply aplica operador de projeção a um vetor de estado
func (op *ProjectionOperator) Apply(stateVector []complex128) ([]complex128, error) {
	op.mu.RLock()
	defer op.mu.RUnlock()

	if len(stateVector) != op.SourceDim {
		return nil, fmt.Errorf("state vector dimension %d != source dimension %d",
			len(stateVector), op.SourceDim)
	}

	// Aplicar projeção: |Ψ'⟩ = Π |Ψ⟩
	projected := make([]complex128, op.TargetDim)
	for i := 0; i < op.TargetDim; i++ {
		var sum complex128
		for j := 0; j < op.SourceDim; j++ {
			// Aplicar fator de fase se configurado
			element := op.ProjectionMatrix[i][j]
			if op.PhaseFactor != 0 {
				element *= cmplx.Exp(complex(0, op.PhaseFactor))
			}
			sum += element * stateVector[j]
		}
		projected[i] = sum
	}

	// Normalizar resultado
	var norm float64
	for _, amp := range projected {
		norm += cmplx.Abs(amp) * cmplx.Abs(amp)
	}
	if norm < ProjectionMatrixPrecision {
		return nil, fmt.Errorf("projected state norm too small")
	}
	for i := range projected {
		projected[i] /= complex(math.Sqrt(norm), 0)
	}

	return projected, nil
}

// ComputeFidelity calcula fidelidade entre estado original e projetado
func (op *ProjectionOperator) ComputeFidelity(
	original, projected []complex128,
) float64 {
	if len(original) != len(projected) {
		return 0.0
	}

	// Fidelidade como módulo do produto interno: F = |⟨Ψ|Ψ'⟩|
	var inner complex128
	for i := range original {
		inner += cmplx.Conj(original[i]) * projected[i]
	}

	fidelity := cmplx.Abs(inner)
	return math.Min(1.0, math.Max(0.0, fidelity))
}

// UpdateAdaptiveParameters atualiza parâmetros em modo adaptativo
func (op *ProjectionOperator) UpdateAdaptiveParameters(
	fidelity float64,
	targetFidelity float64,
) {
	if !op.AdaptiveMode {
		return
	}

	op.mu.Lock()
	defer op.mu.Unlock()

	// Ajustar força de acoplamento baseado em erro de fidelidade
	error := targetFidelity - fidelity
	op.CouplingStrength *= 1.0 + 0.1*error

	// Limitar parâmetros
	op.CouplingStrength = math.Max(0.1, math.Min(10.0, op.CouplingStrength))

	// Atualizar métricas
	op.TotalUses++
	n := op.TotalUses
	oldAvg := op.AvgFidelity
	op.AvgFidelity = (oldAvg*float64(n-1) + fidelity) / float64(n)
	op.LastApplied = time.Now()
}

// generateProjectionMatrix gera matriz de projeção baseada no tipo
func generateProjectionMatrix(
	opType ProjectionOperatorType,
	sourceDim, targetDim int,
) ([][]complex128, float64, error) {
	matrix := make([][]complex128, targetDim)
	var phaseFactor float64

	switch opType {
	case OpAscend:
		// Ascensão: preservar componentes de baixa frequência
		phaseFactor = AscendPhaseFactor
		for i := range matrix {
			matrix[i] = make([]complex128, sourceDim)
			for j := range matrix[i] {
				// Matriz de projeção que preserva estrutura de baixa dimensão
				if i < sourceDim && i == j {
					matrix[i][j] = complex(1.0/math.Sqrt(float64(targetDim)), 0)
				}
			}
		}

	case OpDescend:
		// Descensão: enfatizar componentes de alta frequência
		phaseFactor = DescendPhaseFactor
		for i := range matrix {
			matrix[i] = make([]complex128, sourceDim)
			for j := range matrix[i] {
				// Peso crescente com índice para alta frequência
				weight := 1.0 + 0.1*float64(j)
				if i < sourceDim && i == j {
					matrix[i][j] = complex(weight/math.Sqrt(float64(targetDim)), 0)
				}
			}
		}

	case OpLateral:
		// Projeção lateral: mistura controlada entre componentes
		phaseFactor = 0.0
		for i := range matrix {
			matrix[i] = make([]complex128, sourceDim)
			for j := range matrix[i] {
				if i == j {
					matrix[i][j] = complex(0.9/math.Sqrt(float64(targetDim)), 0)
				} else if math.Abs(float64(i-j)) == 1 {
					// Acoplamento com vizinhos
					matrix[i][j] = complex(0.1/math.Sqrt(float64(targetDim)), 0)
				}
			}
		}

	case OpMerge:
		// Fusão: média ponderada de múltiplas camadas
		// Simplificação: matriz de média
		phaseFactor = 0.0
		for i := range matrix {
			matrix[i] = make([]complex128, sourceDim)
			for j := range matrix[i] {
				matrix[i][j] = complex(1.0/math.Sqrt(float64(sourceDim*targetDim)), 0)
			}
		}

	case OpSplit:
		// Divisão: replicação com variação controlada
		phaseFactor = 0.0
		for i := range matrix {
			matrix[i] = make([]complex128, sourceDim)
			// Mapear cada estado de origem para múltiplos estados de destino
			srcIdx := i % sourceDim
			matrix[i][srcIdx] = complex(1.0/math.Sqrt(float64(targetDim/sourceDim)), 0)
		}

	default:
		return nil, 0, fmt.Errorf("unknown projection operator type: %s", opType)
	}

	return matrix, phaseFactor, nil
}
