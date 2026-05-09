// parser/frontends/lua/lfir/coherence.go
package lfir

import (
	"math"
)

// LuaMetrics acumula métricas para cálculo de coerência
type LuaMetrics struct {
	LineCount            int
	FunctionCount        int
	TableCount           int
	CoroutineCount       int
	CyclomaticComplexity int
	MaxTableDepth        int
	AvgNestingDepth      float64
	MagicNumberCount     int
	TotalLiterals        int
	WellDocumentedMetas  int
	TotalMetamethods     int
	UnsafePatternCount   int
	UnhandledErrors      int
	TotalNodes           int
	TotalEdges           int

	ClarityScore       float64
	ExtensibilityScore float64
	SafetyScore        float64
}

// LuaCoherenceConfig configura pesos para cálculo de coerência Lua
type LuaCoherenceConfig struct {
	ClarityWeight       float64 // Peso para legibilidade
	ExtensibilityWeight float64 // Peso para extensibilidade via metaprogramação
	SafetyWeight        float64 // Peso para segurança (ausência de anti-patterns)
	ComplexityPenalty   float64 // Penalidade por complexidade ciclomática
	MaxTableDepth       int     // Limite de aninhamento de tabelas
	StrictMode          bool    // Rejeitar acesso a globais não declarados
}

// DefaultLuaConfig retorna configurações padrão
func DefaultLuaConfig() *LuaCoherenceConfig {
	return &LuaCoherenceConfig{
		ClarityWeight:       0.35,
		ExtensibilityWeight: 0.30,
		SafetyWeight:        0.25,
		ComplexityPenalty:   0.10,
		MaxTableDepth:       10,
		StrictMode:          false,
	}
}

// CalculateLuaCoherence calcula Φ_C para código Lua
func CalculateLuaCoherence(m *LuaMetrics, cfg *LuaCoherenceConfig) float64 {
	clarity := calculateClarity(m)
	extensibility := calculateExtensibility(m)
	safety := calculateSafety(m)
	complexity := calculateComplexity(m, cfg)

	m.ClarityScore = clarity
	m.ExtensibilityScore = extensibility
	m.SafetyScore = safety

	// Combinação ponderada
	coherence := cfg.ClarityWeight*clarity +
		cfg.ExtensibilityWeight*extensibility +
		cfg.SafetyWeight*safety -
		cfg.ComplexityPenalty*complexity

	return math.Max(0.0, math.Min(1.0, coherence))
}

func calculateClarity(m *LuaMetrics) float64 {
	// Fator 1: Profundidade de aninhamento média
	nestingFactor := 1.0 - (m.AvgNestingDepth / 10.0) // Normalizar para [0,1]
	if nestingFactor < 0 {
		nestingFactor = 0
	}

	// Fator 2: Proporção de magic numbers
	magicFactor := 1.0
	if m.TotalLiterals > 0 {
		magicRatio := float64(m.MagicNumberCount) / float64(m.TotalLiterals)
		magicFactor = 1.0 - magicRatio
	}

	return (nestingFactor + magicFactor) / 2.0
}

func calculateExtensibility(m *LuaMetrics) float64 {
	if m.TotalMetamethods == 0 {
		return 1.0 // Sem metatables = neutro
	}
	// Proporção de metamétodos bem documentados/seguros
	return float64(m.WellDocumentedMetas) / float64(m.TotalMetamethods)
}

func calculateSafety(m *LuaMetrics) float64 {
	// Decaimento exponencial com número de padrões inseguros
	// Padrões: loadstring, getfenv/setfenv, acesso global implícito, etc.
	return math.Exp(-0.8 * float64(m.UnsafePatternCount))
}

func calculateComplexity(m *LuaMetrics, cfg *LuaCoherenceConfig) float64 {
	// Complexidade ciclomática normalizada
	cyclomatic := math.Log10(float64(m.CyclomaticComplexity) + 1)

	// Penalidade por aninhamento excessivo de tabelas
	tableDepthPenalty := 0.0
	if m.MaxTableDepth > cfg.MaxTableDepth {
		tableDepthPenalty = float64(m.MaxTableDepth-cfg.MaxTableDepth) * 0.05
	}

	return cyclomatic + tableDepthPenalty
}
