// arkhe_os/photonic/consciousness_crystal_grower.go
package photonic

import (
	"math"
	"fmt"
	"math/rand"
	"sync"
	"time"
)

// ─── CONSTANTES DE CRESCIMENTO DE CRISTAIS ───────────────
const (
	// DefaultGrowthTemperature temperatura padrão para crescimento em hot-plate
	DefaultGrowthTemperature = 473.0 // Kelvin (~200°C)
	// DefaultGrowthTime tempo padrão de crescimento
	DefaultGrowthTime = 2 * time.Hour
	// MinCrystalThickness espessura mínima de cristal cultivável
	MinCrystalThickness = 0.3 // nm (monocamada)
	// MaxCrystalThickness espessura máxima prática
	MaxCrystalThickness = 100.0 // nm
)

// ─── TIPOS FUNDAMENTAIS ───────────────────────────────────
// GrowthMethod enumera métodos de síntese de cristais 2D
type GrowthMethod string

const (
	MethodHotPlate   GrowthMethod = "hot-plate"   // Síntese em placa quente (PbI₂)
	MethodCVD        GrowthMethod = "CVD"         // Deposição química em vapor
	MethodMBE        GrowthMethod = "MBE"         // Epitaxia por feixe molecular
	MethodExfoliation GrowthMethod = "exfoliation" // Esfoliação mecânica
	MethodCustom     GrowthMethod = "custom"      // Método personalizado
)

// CrystalGrowthConfig contém configuração para cultivo de cristais
type CrystalGrowthConfig struct {
	Material       CrystalMaterial
	Method         GrowthMethod
	Temperature    float64 // Kelvin
	Pressure       float64 // mbar (para CVD/MBE)
	GrowthTime     time.Duration
	Substrate      string // "SiO2/Si", "sapphire", "flexible", etc.
	EnableDefectControl bool // Controlar defeitos via annealing
}

// ConsciousnessCrystal representa cristal cultivado para projeção polaritônica
type ConsciousnessCrystal struct {
	CrystalID     string
	Material      CrystalMaterial
	Method        GrowthMethod
	Thickness     float64 // nm
	Area          float64 // μm²
	QualityScore  float64 // [0, 1]: pureza, uniformidade, baixa densidade de defeitos
	PolaritonModes []PolaritonMode // Modos polaritônicos suportados
	GrowthParams  CrystalGrowthConfig
	Timestamp     time.Time
}

// PolaritonMode descreve um modo polaritônico suportado pelo cristal
type PolaritonMode struct {
	ModeType      PolaritonModeType
	FrequencyTHz  float64
	Wavevector    float64 // nm⁻¹
	Lifetime      float64 // ps
	ConfinementFactor float64
}

// ConsciousnessCrystalGrower gerencia cultivo de cristais para fotônica de coerência
type ConsciousnessCrystalGrower struct {
	mu sync.RWMutex

	// Identificação
	growerID string
	workshopPath string // Caminho do "laboratório" de crescimento

	// Cristais cultivados
	grownCrystals map[string]*ConsciousnessCrystal

	// Configuração padrão
	defaultConfig CrystalGrowthConfig

	// Métricas de crescimento
	metrics GrowthMetrics
}

// GrowthMetrics contém métricas do cultivador de cristais
type GrowthMetrics struct {
	CrystalsGrown        int64   `json:"crystals_grown"`
	AvgQualityScore      float64 `json:"avg_quality_score"`
	AvgThickness         float64 `json:"avg_thickness_nm"`
	SuccessRate          float64 `json:"success_rate"`
	SimulationModeActive bool    `json:"simulation_mode_active"`
}

// NewConsciousnessCrystalGrower cria novo cultivador de cristais de consciência
func NewConsciousnessCrystalGrower(
	growerID, workshopPath string,
	defaultConfig CrystalGrowthConfig,
) (*ConsciousnessCrystalGrower, error) {
	if defaultConfig.Temperature == 0 {
		defaultConfig.Temperature = DefaultGrowthTemperature
	}
	if defaultConfig.GrowthTime == 0 {
		defaultConfig.GrowthTime = DefaultGrowthTime
	}
	if defaultConfig.Method == "" {
		defaultConfig.Method = MethodHotPlate // Padrão para PbI₂
	}

	return &ConsciousnessCrystalGrower{
		growerID:      growerID,
		workshopPath:  workshopPath,
		grownCrystals: make(map[string]*ConsciousnessCrystal),
		defaultConfig: defaultConfig,
		metrics: GrowthMetrics{
			AvgQualityScore:      0.85,
			AvgThickness:         10.0,
			SuccessRate:          0.92,
			SimulationModeActive: true, // Simulação por padrão
		},
	}, nil
}

// GrowCrystal cultiva novo cristal de consciência com parâmetros especificados
func (g *ConsciousnessCrystalGrower) GrowCrystal(
	config CrystalGrowthConfig,
) (*ConsciousnessCrystal, error) {
	g.mu.Lock()
	defer g.mu.Unlock()

	// Validar configuração
	if err := validateGrowthConfig(config); err != nil {
		return nil, fmt.Errorf("invalid growth config: %w", err)
	}

	// Simular processo de crescimento (em produção: controlar hardware real)
	crystal, err := g.simulateCrystalGrowth(config)
	if err != nil {
		return nil, fmt.Errorf("crystal growth simulation failed: %w", err)
	}

	// Registrar cristal cultivado
	g.grownCrystals[crystal.CrystalID] = crystal
	g.metrics.CrystalsGrown++

	// Atualizar métricas
	n := g.metrics.CrystalsGrown
	g.metrics.AvgQualityScore = (g.metrics.AvgQualityScore*float64(n-1) + crystal.QualityScore) / float64(n)
	g.metrics.AvgThickness = (g.metrics.AvgThickness*float64(n-1) + crystal.Thickness) / float64(n)

	return crystal, nil
}

// simulateCrystalGrowth simula processo de cultivo de cristal 2D
func (g *ConsciousnessCrystalGrower) simulateCrystalGrowth(
	config CrystalGrowthConfig,
) (*ConsciousnessCrystal, error) {
	// Determinar espessura baseada em método e tempo
	var thickness float64
	switch config.Method {
	case MethodHotPlate:
		// PbI₂ em hot-plate: espessura ~0.3-50nm, controlada por tempo
		thickness = MinCrystalThickness +
			(MaxCrystalThickness-MinCrystalThickness)*
			math.Min(1.0, config.GrowthTime.Hours()/4.0)
	case MethodCVD, MethodMBE:
		// CVD/MBE: controle mais preciso
		thickness = config.Temperature * 0.02 // Modelo simplificado
	case MethodExfoliation:
		// Esfoliação: espessura aleatória em faixa de monocamadas
		thickness = MinCrystalThickness + rand.Float64()*2.0
	default:
		thickness = 10.0 // Valor padrão
	}

	// Calcular score de qualidade baseado em parâmetros
	quality := computeCrystalQuality(config, thickness)

	// Gerar modos polaritônicos suportados
	modes := generateSupportedPolaritonModes(config.Material, thickness, 0.0)

	// Criar cristal
	crystal := &ConsciousnessCrystal{
		CrystalID:     fmt.Sprintf("crystal_%s_%d", config.Material, time.Now().UnixNano()),
		Material:      config.Material,
		Method:        config.Method,
		Thickness:     thickness,
		Area:          100.0, // μm² (típico para cristais 2D)
		QualityScore:  quality,
		PolaritonModes: modes,
		GrowthParams:  config,
		Timestamp:     time.Now(),
	}

	return crystal, nil
}

// computeCrystalQuality calcula score de qualidade do cristal cultivado
func computeCrystalQuality(config CrystalGrowthConfig, thickness float64) float64 {
	quality := 0.8 // Score base

	// Bonus por método de alta precisão
	switch config.Method {
	case MethodMBE:
		quality += 0.15
	case MethodCVD:
		quality += 0.10
	case MethodHotPlate:
		quality += 0.05 // Hot-plate é simples mas eficaz para PbI₂
	}

	// Bonus por espessura ótima para polaritons
	if config.Material == MaterialPbI2 && thickness >= 5.0 && thickness <= 20.0 {
		quality += 0.1 // Faixa ótima para acoplamento forte
	}

	// Penalidade por temperatura fora da faixa ideal
	if config.Temperature < 400 || config.Temperature > 600 {
		quality -= 0.1
	}

	// Bonus por controle de defeitos
	if config.EnableDefectControl {
		quality += 0.05
	}

	return math.Max(0.0, math.Min(1.0, quality))
}

// generateSupportedPolaritonModes gera modos polaritônicos suportados pelo cristal
func generateSupportedPolaritonModes(
	material CrystalMaterial,
	thickness, targetFrequency float64,
) []PolaritonMode {
	var modes []PolaritonMode

	// Modos típicos para cada material
	baseModes := map[CrystalMaterial][]PolaritonModeType{
		MaterialPbI2:  {ModePhononPolariton, ModeHybridPolariton},
		MaterialMoS2:  {ModeExcitonPolariton, ModeHybridPolariton},
		MaterialWS2:   {ModeExcitonPolariton},
		MaterialBN:    {ModePhononPolariton},
		MaterialCustom: {ModeHybridPolariton},
	}

	modeTypes, ok := baseModes[material]
	if !ok {
		modeTypes = []PolaritonModeType{ModePhononPolariton}
	}

	// Gerar modos com parâmetros físicos aproximados
	for _, modeType := range modeTypes {
		// Frequência baseada no material e espessura
		freq := targetFrequency
		if targetFrequency == 0 {
			// Frequência típica para o material
			freq = map[CrystalMaterial]float64{
				MaterialPbI2: 2.5,
				MaterialMoS2: 1.8,
				MaterialWS2:  2.0,
				MaterialBN:   4.0,
			}[material]
		}

		// Fator de confinamento baseado em espessura
		confinement := DefaultCompressionFactor
		if thickness < 1.0 {
			confinement *= 1.5 // Monocamada: confinamento máximo
		}

		modes = append(modes, PolaritonMode{
			ModeType:          modeType,
			FrequencyTHz:      freq,
			Wavevector:        1.0 / (thickness * 1e-2), // nm⁻¹
			Lifetime:          1.0 / (0.1 * thickness),   // ps (simplificado)
			ConfinementFactor: confinement,
		})
	}

	return modes
}

// validateGrowthConfig valida configuração de crescimento
func validateGrowthConfig(config CrystalGrowthConfig) error {
	if config.Temperature < 300 || config.Temperature > 1200 {
		return fmt.Errorf("temperature %.1fK out of valid range [300, 1200]", config.Temperature)
	}
	if config.GrowthTime < 10*time.Minute || config.GrowthTime > 24*time.Hour {
		return fmt.Errorf("growth time %v out of valid range [10min, 24h]", config.GrowthTime)
	}
	return nil
}

// GetCrystalByID recupera cristal cultivado por ID
func (g *ConsciousnessCrystalGrower) GetCrystalByID(crystalID string) (*ConsciousnessCrystal, bool) {
	g.mu.RLock()
	defer g.mu.RUnlock()
	crystal, exists := g.grownCrystals[crystalID]
	if !exists {
		return nil, false
	}
	// Retornar cópia para segurança
	crystalCopy := *crystal
	return &crystalCopy, true
}

// GetGrowthMetrics retorna métricas consolidadas do cultivador
func (g *ConsciousnessCrystalGrower) GetGrowthMetrics() GrowthMetrics {
	g.mu.RLock()
	defer g.mu.RUnlock()
	return g.metrics
}
