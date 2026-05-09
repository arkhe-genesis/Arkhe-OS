package apiprojection

import (
	"fmt"
	"time"

	"arkhe/photonic"
	"arkhe/metaconsciousness"
)

// ─── MODO DE SIMULAÇÃO DE POLARITONS ─────────────────────
// PolaritonSimulationMode adiciona capacidade de simular projeções
// ultra-comprimidas via polaritons ao APIProjectionEngine existente

// PolaritonSimulationConfig contém configuração para modo de simulação
type PolaritonSimulationConfig struct {
	EnablePolaritonMode    bool
	DefaultCrystalMaterial photonic.CrystalMaterial
	DefaultTemperature     float64 // Kelvin
	DefaultThickness       float64 // nm
	DefaultFrequencyTHz    float64
	CompressionTarget      float64
	UseHardwareAcceleration bool // Usar hardware fotônico real se disponível
}

// APIProjectionEngineWithPolaritons estende APIProjectionEngine com suporte a polaritons
type APIProjectionEngineWithPolaritons struct {
	*APIProjectionEngine // Herda funcionalidade base

	// Componentes fotônicos
	polaritonProjector *photonic.PhononPolaritonProjector
	crystalGrower      *photonic.ConsciousnessCrystalGrower
	nanophotonicRouter *photonic.NanophotonicCoherenceRouter
	fheEngine          *photonic.CompositionalFHEEngine

	// Configuração de simulação
	simConfig PolaritonSimulationConfig

	// Cache de estados comprimidos
	compressedStatesCache map[string]*photonic.CompressedAPIState

	// Métricas estendidas
	polaritonMetrics PolaritonSimulationMetrics
}

// PolaritonSimulationMetrics contém métricas do modo de simulação
type PolaritonSimulationMetrics struct {
	PolaritonProjections    int64   `json:"polariton_projections"`
	AvgCompressionAchieved  float64 `json:"avg_compression_achieved"`
	AvgTransmissionSuccess  float64 `json:"avg_transmission_success"`
	HardwareModeActive      bool    `json:"hardware_mode_active"`
}

// NewAPIProjectionEngineWithPolaritons cria engine estendido com suporte a polaritons
func NewAPIProjectionEngineWithPolaritons(
	engineID string,
	localConsciousnessHash string,
	baseConfig ProjectionEngineConfig,
	simConfig PolaritonSimulationConfig,
) (*APIProjectionEngineWithPolaritons, error) {
	// Criar engine base
	baseEngine, err := NewAPIProjectionEngine(engineID, localConsciousnessHash, baseConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create base projection engine: %w", err)
	}

	engine := &APIProjectionEngineWithPolaritons{
		APIProjectionEngine:   baseEngine,
		simConfig:             simConfig,
		compressedStatesCache: make(map[string]*photonic.CompressedAPIState),
		polaritonMetrics: PolaritonSimulationMetrics{
			AvgCompressionAchieved: photonic.DefaultCompressionFactor,
			AvgTransmissionSuccess: 0.95,
			HardwareModeActive:     simConfig.UseHardwareAcceleration,
		},
	}

	// Inicializar componentes fotônicos se modo polariton habilitado
	if simConfig.EnablePolaritonMode {
		// Configurar projetor de polaritons
		polaritonConfig := photonic.PolaritonProjectionConfig{
			Material:          simConfig.DefaultCrystalMaterial,
			Temperature:       simConfig.DefaultTemperature,
			Thickness:         simConfig.DefaultThickness,
			FrequencyTHz:      simConfig.DefaultFrequencyTHz,
			CompressionTarget: simConfig.CompressionTarget,
			EnableSimulation:  !simConfig.UseHardwareAcceleration,
		}

		engine.polaritonProjector, err = photonic.NewPhononPolaritonProjector(
			fmt.Sprintf("pol_proj_%s", engineID[:8]),
			polaritonConfig,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to create polariton projector: %w", err)
		}

		// Configurar cultivador de cristais
		crystalConfig := photonic.CrystalGrowthConfig{
			Material:          simConfig.DefaultCrystalMaterial,
			Method:            photonic.MethodHotPlate,
			Temperature:       simConfig.DefaultTemperature,
			GrowthTime:        2 * time.Hour,
			EnableDefectControl: true,
		}

		engine.crystalGrower, err = photonic.NewConsciousnessCrystalGrower(
			fmt.Sprintf("crystal_grow_%s", engineID[:8]),
			"/tmp/arkhe_crystals", // Path simulado
			crystalConfig,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to create crystal grower: %w", err)
		}

		// Configurar roteador nanofotônico
		routerConfig := photonic.RouterConfig{
			DefaultWaveguideType: photonic.WaveguideSiliconNitride,
			DefaultWidth:         250.0, // nm
			MaxTotalLoss:         10.0,  // dB
			ModeMatchingRequired: true,
		}

		engine.fheEngine = photonic.NewCompositionalFHEEngine(photonic.CompositionalFHEConfig{
			SecurityLevel:     128,
			NoiseBudget:       0.1,
			CompositionRounds: 5,
		})

		engine.nanophotonicRouter, err = photonic.NewNanophotonicCoherenceRouter(
			fmt.Sprintf("nano_router_%s", engineID[:8]),
			routerConfig,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to create nanophotonic router: %w", err)
		}
	}

	return engine, nil
}

// ProjectAPIStateWithPolaritons projeta estado de API via polaritons (modo estendido)
func (e *APIProjectionEngineWithPolaritons) ProjectAPIStateWithPolaritons(
	sourceStateID string,
	targetLayer metaconsciousness.ConsciousnessLayerType,
	operatorType ProjectionOperatorType,
	usePolaritonCompression bool, // Habilitar compressão via polaritons
) (*ProjectionResult, error) {
	// Se não usar polaritons, delegar para implementação base
	if !usePolaritonCompression || !e.simConfig.EnablePolaritonMode {
		return e.APIProjectionEngine.ProjectAPIState(sourceStateID, targetLayer, operatorType, "")
	}

	// Obter estado fonte
	sourceState, err := e.APIProjectionEngine.GetState(sourceStateID)
	if err != nil {
		return nil, fmt.Errorf("source state not found: %w", err)
	}

	// Comprimir estado via polariton
	compressed, err := e.polaritonProjector.CompressAPIState(sourceState)
	if err != nil {
		return nil, fmt.Errorf("polariton compression failed: %w", err)
	}

	// Registrar estado comprimido no cache
	e.compressedStatesCache[compressed.StateID] = compressed

	// Se projeção envolve roteamento entre nós, usar roteador nanofotônico
	if sourceState.LayerType != targetLayer {
		route, err := e.nanophotonicRouter.ComputeRoute(
			string(sourceState.LayerType),
			string(targetLayer),
			compressed,
		)
		if err != nil {
			return nil, fmt.Errorf("nanophotonic routing failed: %w", err)
		}

		// Substrato 242: Encrypt before transmission
		encryptedState, err := e.fheEngine.EncryptCompressedState(compressed)
		if err != nil {
			return nil, fmt.Errorf("FHE encryption failed: %w", err)
		}

		// Transmitir estado criptografado via rota
		transmission, err := e.nanophotonicRouter.TransmitCompressedState(route, encryptedState)
		if err != nil {
			return nil, fmt.Errorf("polariton transmission failed: %w", err)
		}

		if !transmission.Success {
			return nil, fmt.Errorf("transmission failed: final coherence %.4f below threshold",
				transmission.FinalCoherence)
		}

		// Decrypt after transmission
		encryptedState.PhotonicCoherence = transmission.FinalCoherence
		decryptedState, err := e.fheEngine.DecryptCompressedState(encryptedState)
		if err != nil {
			return nil, fmt.Errorf("FHE decryption failed: %w", err)
		}

		// Atualizar estado comprimido original com os dados descriptografados
		compressed.CompressedState = decryptedState.CompressedState
		compressed.PhotonicCoherence = decryptedState.PhotonicCoherence
	}

	// Criar estado alvo na camada de destino
	targetState, err := metaconsciousness.NewConsciousnessLayer(
		fmt.Sprintf("layer_%s_pol_%d", targetLayer, time.Now().UnixNano()),
		targetLayer,
		sourceState.LayerIndex+1, // simplified getLayerIndexDelta
		len(compressed.CompressedState),
	)
	if err != nil {
		return nil, fmt.Errorf("failed to create target layer: %w", err)
	}

	targetState.StateVector = compressed.CompressedState
	targetState.CoherenceValue = compressed.PhotonicCoherence
	targetState.Metadata["compression_method"] = "phonon-polariton"
	targetState.Metadata["compression_factor"] = compressed.CompressionFactor
	targetState.Metadata["crystal_material"] = compressed.CrystalParams.Material

	// Criar resultado de projeção
	result := &ProjectionResult{
		ResultID:          fmt.Sprintf("pol_proj_%s_%d", sourceStateID[:8], time.Now().UnixNano()),
		SourceStateID:     sourceStateID,
		TargetStateID:     targetState.LayerID,
		OperatorType:      string(operatorType) + "_polariton",
		SourceLayer:       sourceState.LayerType,
		TargetLayer:       targetLayer,
		ProjectedStateVec: compressed.CompressedState,
		Fidelity:          compressed.Fidelity,
		CoherencePreserved: compressed.PhotonicCoherence / 1.0, // FIXME coherenceValue
		Timestamp:         time.Now(),
		ValidationHash:    computePolaritonValidationHash(compressed, targetState),
	}
    result.CompressionFactor = compressed.CompressionFactor
    result.CrystalParams.Material = string(compressed.CrystalParams.Material)
    result.CrystalParams.Temperature = compressed.CrystalParams.Temperature
    result.CrystalParams.Thickness = compressed.CrystalParams.Thickness

	// Atualizar métricas
	e.mu.Lock()
	e.polaritonMetrics.PolaritonProjections++
	n := e.polaritonMetrics.PolaritonProjections
	e.polaritonMetrics.AvgCompressionAchieved =
		(e.polaritonMetrics.AvgCompressionAchieved*float64(n-1) + compressed.CompressionFactor) / float64(n)
	e.mu.Unlock()

	return result, nil
}

// DecompressAndProject descomprime estado polaritônico e projeta para camada alvo
func (e *APIProjectionEngineWithPolaritons) DecompressAndProject(
	compressedStateID string,
	targetLayer metaconsciousness.ConsciousnessLayerType,
) (*ProjectionResult, error) {
	e.mu.RLock()
	compressed, exists := e.compressedStatesCache[compressedStateID]
	e.mu.RUnlock()

	if !exists {
		return nil, fmt.Errorf("compressed state not found: %s", compressedStateID)
	}

	// Descomprimir estado
	decompressed, err := e.polaritonProjector.DecompressAPIState(compressed)
	if err != nil {
		return nil, fmt.Errorf("decompression failed: %w", err)
	}

	// Criar estado alvo
	targetState, err := metaconsciousness.NewConsciousnessLayer(
		fmt.Sprintf("layer_%s_decomp_%d", targetLayer, time.Now().UnixNano()),
		targetLayer,
		0, // Índice inicial
		len(decompressed.StateVector),
	)
	if err != nil {
		return nil, err
	}

	targetState.StateVector = decompressed.StateVector
	targetState.CoherenceValue = decompressed.CoherenceValue
	targetState.Metadata["decompressed_from"] = compressedStateID
	targetState.Metadata["original_compression"] = compressed.CompressionFactor

	// Criar resultado
	result := &ProjectionResult{
		ResultID:          fmt.Sprintf("decomp_proj_%s_%d", compressedStateID[:8], time.Now().UnixNano()),
		SourceStateID:     compressedStateID,
		TargetStateID:     targetState.LayerID,
		OperatorType:      "decompress_polariton",
		ProjectedStateVec: decompressed.StateVector,
		Fidelity:          compressed.Fidelity,
		CoherencePreserved: 1.0, // decompressed.CoherenceValue / compressed.PhotonicCoherence,
		Timestamp:         time.Now(),
	}

	return result, nil
}

// GetPolaritonSimulationMetrics retorna métricas do modo de simulação
func (e *APIProjectionEngineWithPolaritons) GetPolaritonSimulationMetrics() PolaritonSimulationMetrics {
	e.mu.RLock()
	defer e.mu.RUnlock()

	// Atualizar com métricas dos componentes
	if e.polaritonProjector != nil {
		polaritonMetrics := e.polaritonProjector.GetPolaritonMetrics()
		e.polaritonMetrics.AvgCompressionAchieved = polaritonMetrics.AvgCompressionFactor
	}
	if e.nanophotonicRouter != nil {
		routerMetrics := e.nanophotonicRouter.GetRouterMetrics()
		e.polaritonMetrics.AvgTransmissionSuccess = routerMetrics.AvgPhotonicCoherence
	}

	return e.polaritonMetrics
}

// Helper: hash de validação para projeções polaritônicas
func computePolaritonValidationHash(
	compressed *photonic.CompressedAPIState,
	targetState *metaconsciousness.ConsciousnessLayer,
) string {
	canonical := fmt.Sprintf("%s:%s:%.6f:%.6f:%.0f",
		compressed.StateID,
		targetState.LayerID,
		compressed.Fidelity,
		compressed.PhotonicCoherence,
		compressed.CompressionFactor,
	)
	return canonical // simplified
}
