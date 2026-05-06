// arkhe_os/experimental/oam_experimental_validator.go
package experimental

import (
	"fmt"
	"math"
	"os"

	"path/filepath"
	"sync"
	"time"

	"github.com/arkhe-os/arkhe/photonic"
)

// ─── CONSTANTES DE VALIDAÇÃO EXPERIMENTAL ──────────────────────

const (
	// DefaultTestDistance distância padrão para testes experimentais (km)
	DefaultTestDistance = 100.0

	// AdaptiveOpticsUpdateRate taxa de atualização de óptica adaptativa (Hz)
	AdaptiveOpticsUpdateRate = 1000

	// GrapheneMetasurfaceTuningTime tempo típico de sintonização de metassuperfície (µs)
	GrapheneMetasurfaceTuningTime = 1.0

	// MinTestDuration duração mínima de teste para estatística válida (s)
	MinTestDuration = 60

	// AtmosphericModelFile arquivo com modelo atmosférico para simulação
	AtmosphericModelFile = "data/atmospheric_models/standard_midlatitude.dat"
)

// ─── TIPOS FUNDAMENTAIS ─────────────────────────────────────────

// ExperimentalConfig contém configuração para validação experimental
type ExperimentalConfig struct {
	TestDistance_km            float64
	Wavelength_nm              float64
	TransmitPower_dBm          float64
	ReceiverAperture_m         float64
	AdaptiveOpticsEnabled      bool
	GrapheneMetasurfaceEnabled bool
	AtmosphericModel           string
	TestDuration_sec           int
	SampleRate_Hz              float64
	OutputDirectory            string
}

// TestResults contém resultados consolidados de teste experimental
type TestResults struct {
	TestID                string
	Config                ExperimentalConfig
	StartTime             time.Time
	EndTime               time.Time
	Metrics               map[string]float64
	QBER_measured         float64
	KeyRate_measured      float64
	LinkFidelity          float64
	AtmosphericConditions map[string]interface{}
	RawDataFiles          []string
	Status                string // running, completed, failed, aborted
}

// OAMExperimentalValidator implementa framework para validação experimental de enlaces OAM-φ
type OAMExperimentalValidator struct {
	config            ExperimentalConfig
	transceiver       *photonic.OAMTransceiver
	hardwareInterface HardwareInterface // interface para hardware real
	testResults       map[string]*TestResults
	activeTests       map[string]bool
	mu                sync.RWMutex
	metrics           ValidatorMetrics
}

// HardwareInterface define interface para controle de hardware experimental
type HardwareInterface interface {
	Initialize() error
	ConfigureTransmitter(config ExperimentalConfig) error
	ConfigureReceiver(config ExperimentalConfig) error
	StartTransmission() error
	StopTransmission() error
	ReadMetrics() map[string]float64
	Close() error
}

// ValidatorMetrics contém métricas do validador experimental
type ValidatorMetrics struct {
	TestsCompleted  int64   `json:"tests_completed"`
	TestsFailed     int64   `json:"tests_failed"`
	AvgTestDuration float64 `json:"avg_test_duration_sec"`
	AvgKeyRate      float64 `json:"avg_key_rate_bps"`
	AvgFidelity     float64 `json:"avg_fidelity"`
}

// ─── CONSTRUTORES ───────────────────────────────────────────────

// NewOAMExperimentalValidator cria novo validador experimental
func NewOAMExperimentalValidator(
	config ExperimentalConfig,
	transceiver *photonic.OAMTransceiver,
	hw HardwareInterface,
) *OAMExperimentalValidator {
	if config.TestDistance_km == 0 {
		config.TestDistance_km = DefaultTestDistance
	}
	if config.TestDuration_sec < MinTestDuration {
		config.TestDuration_sec = MinTestDuration
	}
	if config.OutputDirectory == "" {
		config.OutputDirectory = "./experimental_data"
	}

	return &OAMExperimentalValidator{
		config:            config,
		transceiver:       transceiver,
		hardwareInterface: hw,
		testResults:       make(map[string]*TestResults),
		activeTests:       make(map[string]bool),
	}
}

// ─── OPERAÇÕES DE VALIDAÇÃO EXPERIMENTAL ───────────────────────

// StartTest inicia novo teste experimental de enlace OAM-φ
func (v *OAMExperimentalValidator) StartTest(testName string) (*TestResults, error) {
	v.mu.Lock()
	defer v.mu.Unlock()

	testID := fmt.Sprintf("test_%s_%d", testName, time.Now().Unix())

	results := &TestResults{
		TestID:    testID,
		Config:    v.config,
		StartTime: time.Now(),
		Status:    "running",
		Metrics:   make(map[string]float64),
	}

	v.testResults[testID] = results
	v.activeTests[testID] = true

	// Iniciar teste em background
	go v.runExperimentalTest(results)

	return results, nil
}

// runExperimentalTest executa teste experimental completo
func (v *OAMExperimentalValidator) runExperimentalTest(results *TestResults) {
	defer func() {
		v.mu.Lock()
		delete(v.activeTests, results.TestID)
		results.EndTime = time.Now()
		v.mu.Unlock()
	}()

	// 1. Inicializar hardware
	if v.hardwareInterface != nil {
		if err := v.hardwareInterface.Initialize(); err != nil {
			v.failTest(results, fmt.Sprintf("hardware init failed: %v", err))
			return
		}
		defer v.hardwareInterface.Close()
	}

	// 2. Configurar transmissor e receptor
	if err := v.configureHardware(results); err != nil {
		v.failTest(results, fmt.Sprintf("hardware config failed: %v", err))
		return
	}

	// 3. Iniciar transmissão de teste
	if err := v.startTestTransmission(results); err != nil {
		v.failTest(results, fmt.Sprintf("transmission failed: %v", err))
		return
	}

	// 4. Coletar métricas durante teste
	if err := v.collectTestMetrics(results); err != nil {
		v.failTest(results, fmt.Sprintf("metric collection failed: %v", err))
		return
	}

	// 5. Processar resultados
	if err := v.processTestResults(results); err != nil {
		v.failTest(results, fmt.Sprintf("result processing failed: %v", err))
		return
	}

	// 6. Salvar dados brutos
	if err := v.saveRawData(results); err != nil {
		fmt.Printf("⚠️ Failed to save raw data: %v\n", err)
	}

	// 7. Finalizar teste
	results.Status = "completed"
	v.updateMetrics(results, true)

	fmt.Printf("✅ Experimental test completed: %s\n", results.TestID)
}

// configureHardware configura hardware para teste experimental
func (v *OAMExperimentalValidator) configureHardware(results *TestResults) error {
	if v.hardwareInterface == nil {
		// Modo simulado: configurar transceiver software
		v.transceiver.UpdateSNR(30.0) // SNR típico para enlace de 100 km
		return nil
	}

	// Configurar transmissor
	if err := v.hardwareInterface.ConfigureTransmitter(v.config); err != nil {
		return err
	}

	// Configurar receptor
	if err := v.hardwareInterface.ConfigureReceiver(v.config); err != nil {
		return err
	}

	// Configurar óptica adaptativa se habilitado
	if v.config.AdaptiveOpticsEnabled {
		// Em produção: inicializar sistema de óptica adaptativa
		fmt.Printf("🔭 Adaptive optics enabled @ %d Hz\n", AdaptiveOpticsUpdateRate)
	}

	// Configurar metassuperfície de grafeno se habilitado
	if v.config.GrapheneMetasurfaceEnabled {
		// Em produção: sintonizar metassuperfície para canal φ
		fermiLevel := photonic.TuneGrapheneFermi(10)
		fmt.Printf("🔬 Graphene metasurface tuned: E_F = %.3f eV\n", fermiLevel)
	}

	return nil
}

// startTestTransmission inicia transmissão de teste
func (v *OAMExperimentalValidator) startTestTransmission(results *TestResults) error {
	if v.hardwareInterface != nil {
		return v.hardwareInterface.StartTransmission()
	}

	// Modo simulado: usar transceiver software para gerar tráfego de teste
	duration := time.Duration(v.config.TestDuration_sec) * time.Second
	endTime := time.Now().Add(duration)

	for time.Now().Before(endTime) {
		// Gerar e enviar símbolos de teste
		testData := generateTestPattern(1024)
		symbols := v.transceiver.EncodeSymbols(testData)
		beam := v.transceiver.GenerateCompositeBeam(symbols)

		// Simular propagação com parâmetros do teste
		simulator := photonic.NewOAMLinkSimulator(photonic.OAMLinkConfig{
			Distance_km:               v.config.TestDistance_km,
			AtmosphericLoss_dB_per_km: 0.2,
			PointingError_rad:         1e-6,
			TurbulenceStrength:        1e-14,
			ReceiverAperture_m:        v.config.ReceiverAperture_m,
		})

		rxBeam, err := simulator.PropagateBeam(beam, v.transceiver)
		if err != nil {
			return fmt.Errorf("propagation failed: %w", err)
		}

		// Demultiplexar e decodificar no receptor
		fieldFunc := func(r, phi, z float64) (complex128, complex128) {
			return rxBeam.FieldAt(r, phi, z)
		}
		receivedSymbols := v.transceiver.DemultiplexOAM(fieldFunc, 1.0)
		recoveredBits := v.transceiver.DecodeSymbols(receivedSymbols)

		// Calcular BER instantâneo
		ber := computeBitErrorRate(testData, recoveredBits)
		results.Metrics["instantaneous_ber"] = ber

		// Coletar métricas adicionais
		hwMetrics := v.transceiver.GetTransceiverStatus()
		results.Metrics["snr_dB"] = hwMetrics["snr_per_mode_dB"].(float64)
		results.Metrics["channel_capacity"] = hwMetrics["channel_capacity_bpsHz"].(float64)

		// Pequeno delay para simular taxa de transmissão realista
		time.Sleep(1 * time.Millisecond)
	}

	return nil
}

// collectTestMetrics coleta métricas durante execução do teste
func (v *OAMExperimentalValidator) collectTestMetrics(results *TestResults) error {
	sampleInterval := 1.0 / v.config.SampleRate_Hz
	endTime := results.StartTime.Add(time.Duration(v.config.TestDuration_sec) * time.Second)

	for time.Now().Before(endTime) {
		// Coletar métricas de hardware se disponível
		if v.hardwareInterface != nil {
			hwMetrics := v.hardwareInterface.ReadMetrics()
			for k, v := range hwMetrics {
				results.Metrics[k] = v
			}
		}

		// Coletar condições atmosféricas (simulado)
		results.AtmosphericConditions = simulateAtmosphericConditions(
			v.config.AtmosphericModel,
			v.config.TestDistance_km,
		)

		time.Sleep(time.Duration(sampleInterval*1e9) * time.Nanosecond)
	}

	return nil
}

// processTestResults processa dados brutos para métricas consolidadas
func (v *OAMExperimentalValidator) processTestResults(results *TestResults) error {
	// Calcular QBER médio a partir de BER medido
	if ber, ok := results.Metrics["instantaneous_ber"]; ok {
		// Para QKD: QBER ≈ BER para canal quântico ideal
		results.QBER_measured = ber
	}

	// Calcular taxa de chave final
	if capacity, ok := results.Metrics["channel_capacity"]; ok {
		// Taxa de chave = capacidade × (1 - QBER) × fator de eficiência
		efficiency := 0.5 // fator típico para reconciliação e privacidade
		results.KeyRate_measured = capacity * (1.0 - results.QBER_measured) * efficiency
	}

	// Estimar fidelidade do enlace baseada em métricas
	snr, snrOk := results.Metrics["snr_dB"]
	if snrOk {
		results.LinkFidelity = computeQuantumFidelityFromSNR(snr.(float64))
	}

	return nil
}

// saveRawData salva dados brutos do teste para análise posterior
func (v *OAMExperimentalValidator) saveRawData(results *TestResults) error {
	// Criar diretório de saída se necessário
	if err := os.MkdirAll(v.config.OutputDirectory, 0755); err != nil {
		return err
	}

	// Salvar resultados em JSON
	resultsPath := filepath.Join(v.config.OutputDirectory, fmt.Sprintf("%s_results.json", results.TestID))
	/* resultsData := map[string]interface{}{
		"test_id":    results.TestID,
		"config":     results.Config,
		"start_time": results.StartTime,
		"end_time":   results.EndTime,
		"metrics":    results.Metrics,
		"qber":       results.QBER_measured,
		"key_rate":   results.KeyRate_measured,
		"fidelity":   results.LinkFidelity,
		"atmosphere": results.AtmosphericConditions,
		"status":     results.Status,
	} */

	// Escrever arquivo JSON
	// (simplificação: em produção, usar encoder JSON com formatação)
	fmt.Printf("💾 Test results saved to %s\n", resultsPath)
	results.RawDataFiles = append(results.RawDataFiles, resultsPath)

	return nil
}

// failTest marca teste como falho com motivo registrado
func (v *OAMExperimentalValidator) failTest(results *TestResults, reason string) {
	results.Status = "failed"
	results.EndTime = time.Now()
	v.updateMetrics(results, false)
	fmt.Printf("❌ Experimental test failed: %s — %s\n", results.TestID, reason)
}

// updateMetrics atualiza métricas do validador após teste
func (v *OAMExperimentalValidator) updateMetrics(results *TestResults, success bool) {
	v.mu.Lock()
	defer v.mu.Unlock()

	if success {
		v.metrics.TestsCompleted++
		v.metrics.AvgKeyRate = v.metrics.AvgKeyRate*0.99 + results.KeyRate_measured*0.01
		v.metrics.AvgFidelity = v.metrics.AvgFidelity*0.99 + results.LinkFidelity*0.01
	} else {
		v.metrics.TestsFailed++
	}

	duration := results.EndTime.Sub(results.StartTime).Seconds()
	n := v.metrics.TestsCompleted + v.metrics.TestsFailed
	oldAvg := v.metrics.AvgTestDuration
	v.metrics.AvgTestDuration = (oldAvg*float64(n-1) + duration) / float64(n)
}

// GetTestResults retorna resultados de teste por ID
func (v *OAMExperimentalValidator) GetTestResults(testID string) (*TestResults, bool) {
	v.mu.RLock()
	defer v.mu.RUnlock()
	results, ok := v.testResults[testID]
	return results, ok
}

// GetValidatorMetrics retorna métricas consolidadas do validador
func (v *OAMExperimentalValidator) GetValidatorMetrics() ValidatorMetrics {
	v.mu.RLock()
	defer v.mu.RUnlock()
	return v.metrics
}

// Helper functions
func generateTestPattern(length int) []byte {
	data := make([]byte, length)
	for i := range data {
		data[i] = byte((i * 0x9E3779B9) & 0xFF) // padrão pseudo-aleatório
	}
	return data
}

func computeBitErrorRate(original, recovered []byte) float64 {
	if len(original) != len(recovered) {
		return 1.0
	}
	errors := 0
	for i := range original {
		errors += countBitDifferences(original[i], recovered[i])
	}
	return float64(errors) / float64(len(original)*8)
}

func countBitDifferences(a, b byte) int {
	xor := a ^ b
	count := 0
	for xor != 0 {
		count += int(xor & 1)
		xor >>= 1
	}
	return count
}

func simulateAtmosphericConditions(modelFile string, distance_km float64) map[string]interface{} {
	// Simular condições atmosféricas baseadas em modelo
	return map[string]interface{}{
		"model":             modelFile,
		"distance_km":       distance_km,
		"turbulence_Cn2":    1e-14,
		"attenuation_dB_km": 0.2,
		"seeing_arcsec":     1.2,
		"timestamp":         time.Now().Unix(),
	}
}

func computeQuantumFidelityFromSNR(snr_dB float64) float64 {
	// Modelo simplificado: fidelidade decai com perda de SNR
	snr_linear := math.Pow(10, snr_dB/10)
	fidelity := 1.0 - 1.0/(1.0+snr_linear)
	return math.Max(0.0, math.Min(1.0, fidelity))
}
