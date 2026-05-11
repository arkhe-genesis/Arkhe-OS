package fhe

import (
	"fmt"
	"sync"

	"arkhe/crypto/fhe/schemes"
	"arkhe/photonic"
)

// CompositionalPolaritonFHE gerencia composição de esquemas FHE para modos polaritônicos híbridos
type CompositionalPolaritonFHE struct {
	mu sync.RWMutex

	// Esquemas FHE registrados por modo polaritônico
	schemesByMode map[photonic.PolaritonModeType]schemes.FHEScheme

	// Mapeadores de conversão entre esquemas
	conversionMappers map[string]SchemeConversionMapper

	// Configuração de composição
	config CompositionalFHEConfig

	// Métricas de composição
	metrics CompositionalMetrics
}

// CompositionalFHEConfig contém configuração para composição de esquemas FHE
type CompositionalFHEConfig struct {
	EnableAdaptiveSwitching bool   // Habilitar switching adaptativo entre esquemas
	MaxCompositionDepth     int    // Profundidade máxima de composição de esquemas
	CrossModeCompatibility  bool   // Habilitar compatibilidade entre modos diferentes
	OptimizationLevel       string // "speed", "security", "balanced"
}

// SchemeConversionMapper mapeia conversões entre esquemas FHE de diferentes modos
type SchemeConversionMapper struct {
	SourceMode         photonic.PolaritonModeType
	TargetMode         photonic.PolaritonModeType
	ConversionFunc     func(schemes.Ciphertext, schemes.FHEScheme, schemes.FHEScheme) (schemes.Ciphertext, error)
	CompatibilityScore float64 // [0, 1]: quão bem os esquemas são compatíveis
}

// CompositionalMetrics contém métricas da composição FHE
type CompositionalMetrics struct {
	CompositionsPerformed int64   `json:"compositions_performed"`
	CrossModeConversions  int64   `json:"cross_mode_conversions"`
	AvgCompatibilityScore float64 `json:"avg_compatibility_score"`
	SwitchingOverhead     float64 `json:"switching_overhead_ms"`
}

// NewCompositionalPolaritonFHE cria novo gerenciador de composição FHE para polaritons
func NewCompositionalPolaritonFHE(
	config CompositionalFHEConfig,
	schemesByMode map[photonic.PolaritonModeType]schemes.FHEScheme,
) (*CompositionalPolaritonFHE, error) {
	if config.MaxCompositionDepth == 0 {
		config.MaxCompositionDepth = 3
	}
	if config.OptimizationLevel == "" {
		config.OptimizationLevel = "balanced"
	}

	composer := &CompositionalPolaritonFHE{
		schemesByMode:     schemesByMode,
		conversionMappers: make(map[string]SchemeConversionMapper),
		config:            config,
		metrics: CompositionalMetrics{
			AvgCompatibilityScore: 0.85,
		},
	}

	// Registrar mapeadores de conversão padrão entre modos compatíveis
	composer.registerDefaultConversionMappers()

	return composer, nil
}

// registerDefaultConversionMappers registra conversões padrão entre modos polaritônicos
func (c *CompositionalPolaritonFHE) registerDefaultConversionMappers() {
	// Conversões entre modos com esquemas compatíveis
	conversions := []struct {
		source, target photonic.PolaritonModeType
		score          float64
	}{
		{photonic.ModePhononPolariton, photonic.ModeHybridPolariton, 0.9},
		{photonic.ModePlasmonPolariton, photonic.ModeHybridPolariton, 0.85},
		{photonic.ModeExcitonPolariton, photonic.ModeHybridPolariton, 0.95},
		// Conversões bidirecionais
		{photonic.ModeHybridPolariton, photonic.ModePhononPolariton, 0.9},
		{photonic.ModeHybridPolariton, photonic.ModePlasmonPolariton, 0.85},
		{photonic.ModeHybridPolariton, photonic.ModeExcitonPolariton, 0.95},
	}

	for _, conv := range conversions {
		key := conversionKey(conv.source, conv.target)
		c.conversionMappers[key] = SchemeConversionMapper{
			SourceMode:         conv.source,
			TargetMode:         conv.target,
			ConversionFunc:     createDefaultConversionFunction(conv.source, conv.target),
			CompatibilityScore: conv.score,
		}
	}
}

// ComposeEncryptedState compõe estado criptografado de múltiplos modos polaritônicos
func (c *CompositionalPolaritonFHE) ComposeEncryptedState(
	encryptedByMode map[photonic.PolaritonModeType]schemes.Ciphertext,
	compositionFunction string,
) (schemes.Ciphertext, error) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	if len(encryptedByMode) == 0 {
		return nil, fmt.Errorf("no encrypted modes provided for composition")
	}

	// Selecionar modo base para composição (modo com maior peso ou primeiro)
	var baseMode photonic.PolaritonModeType
	var baseCiphertext schemes.Ciphertext
	for mode, ct := range encryptedByMode {
		baseMode = mode
		baseCiphertext = ct
		break
	}

	// Converter todos os outros modos para o esquema do modo base
	convertedCiphertexts := []schemes.Ciphertext{baseCiphertext}
	for mode, ct := range encryptedByMode {
		if mode == baseMode {
			continue
		}

		// Converter ciphertext do modo atual para esquema do modo base
		converted, err := c.convertCiphertextBetweenModes(ct, mode, baseMode)
		if err != nil {
			return nil, fmt.Errorf("conversion from %s to %s failed: %w", mode, baseMode, err)
		}
		convertedCiphertexts = append(convertedCiphertexts, converted)
		c.metrics.CrossModeConversions++
	}

	// Aplicar função de composição sobre ciphertexts convertidos
	result, err := c.schemesByMode[baseMode].Evaluate(compositionFunction, convertedCiphertexts...)
	if err != nil {
		return nil, fmt.Errorf("composition evaluation failed: %w", err)
	}

	c.metrics.CompositionsPerformed++
	return result, nil
}

// convertCiphertextBetweenModes converte ciphertext entre esquemas de modos diferentes
func (c *CompositionalPolaritonFHE) convertCiphertextBetweenModes(
	ciphertext schemes.Ciphertext,
	sourceMode, targetMode photonic.PolaritonModeType,
) (schemes.Ciphertext, error) {
	if sourceMode == targetMode {
		return ciphertext, nil // Sem conversão necessária
	}

	key := conversionKey(sourceMode, targetMode)
	mapper, exists := c.conversionMappers[key]
	if !exists {
		return nil, fmt.Errorf("no conversion mapper registered for %s → %s", sourceMode, targetMode)
	}

	// Verificar compatibilidade mínima
	if mapper.CompatibilityScore < 0.7 {
		return nil, fmt.Errorf("compatibility score %.2f below threshold 0.7 for %s → %s",
			mapper.CompatibilityScore, sourceMode, targetMode)
	}

	// Executar conversão
	converted, err := mapper.ConversionFunc(
		ciphertext,
		c.schemesByMode[sourceMode],
		c.schemesByMode[targetMode],
	)
	if err != nil {
		return nil, err
	}

	// Atualizar métricas de compatibilidade
	c.metrics.AvgCompatibilityScore = c.metrics.AvgCompatibilityScore*0.99 + mapper.CompatibilityScore*0.01

	return converted, nil
}

// SwitchScheme adaptivamente troca esquema FHE baseado em requisitos de operação
func (c *CompositionalPolaritonFHE) SwitchScheme(
	ciphertext schemes.Ciphertext,
	currentMode photonic.PolaritonModeType,
	targetMode photonic.PolaritonModeType,
	operationRequirements map[string]interface{},
) (schemes.Ciphertext, error) {
	if !c.config.EnableAdaptiveSwitching {
		return ciphertext, nil // Switching desabilitado
	}

	// Avaliar se switching é benéfico baseado em requisitos
	if shouldSwitchScheme(operationRequirements, currentMode, targetMode) {
		return c.convertCiphertextBetweenModes(ciphertext, currentMode, targetMode)
	}

	return ciphertext, nil
}

// GetCompositionalMetrics retorna métricas consolidadas da composição FHE
func (c *CompositionalPolaritonFHE) GetCompositionalMetrics() CompositionalMetrics {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.metrics
}

// Helper functions
func conversionKey(source, target photonic.PolaritonModeType) string {
	return string(source) + "→" + string(target)
}

func createDefaultConversionFunction(
	source, target photonic.PolaritonModeType,
) func(schemes.Ciphertext, schemes.FHEScheme, schemes.FHEScheme) (schemes.Ciphertext, error) {
	// Função de conversão padrão: decriptar e re-criptografar (simplificação)
	// Em produção: usar switching de chave ou relinearização para eficiência
	return func(ct schemes.Ciphertext, sourceScheme, targetScheme schemes.FHEScheme) (schemes.Ciphertext, error) {
		// Decriptar com esquema de origem (requer chave privada - simplificação)
		// Em produção: usar key switching ou proxy re-encryption
		return nil, fmt.Errorf("direct conversion not implemented - requires key switching")
	}
}

func shouldSwitchScheme(
	requirements map[string]interface{},
	currentMode, targetMode photonic.PolaritonModeType,
) bool {
	// Lógica de decisão para switching adaptativo baseado em requisitos
	// Exemplo: switch para CKKS se operação requer precisão de ponto flutuante
	if precision, ok := requirements["precision"].(string); ok && precision == "high" {
		// Preferir CKKS para alta precisão
		return targetMode == photonic.ModeExcitonPolariton || targetMode == photonic.ModeHybridPolariton
	}
	return false
}
