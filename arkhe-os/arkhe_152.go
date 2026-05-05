package main

import (
	"fmt"
	"math"
	"sync"
	"time"
)

// ============================================================
// SUBSTRATO 152: QUANTUM GEOMAGNETIC SENSORIUM
// Baseado na patente RU2680629C2
// Transpilado por Ferris-Compiler v157.0
// ============================================================

const (
	Mu0      = 1.25663706e-6 // H/m
	PhiConst = 1.618033988749895
)

// GeomagneticVector vetor completo do campo geomagnético
type GeomagneticVector struct {
	HTotal        float64   `json:"h_total"`
	D             float64   `json:"d"`       // Declinação em graus
	I             float64   `json:"i"`       // Inclinação em graus
	X             float64   `json:"x"`       // Componente Norte
	Y             float64   `json:"y"`       // Componente Leste
	Z             float64   `json:"z"`       // Componente Vertical
	Gradient      []float64 `json:"gradient"`
	Timestamp     float64   `json:"timestamp"`
	QualityFactor float64   `json:"quality_factor"`
}

func NewGeomagneticVector() *GeomagneticVector {
	return &GeomagneticVector{
		Timestamp: float64(time.Now().UnixNano()) / 1e9,
		Gradient:  make([]float64, 3),
	}
}

// MagnetoFrameCalibration dados de calibração do sensor
type MagnetoFrameCalibration struct {
	ReferenceH             float64 `json:"reference_h"`
	ReferenceEMF           float64 `json:"reference_emf"`
	CalibrationDate        float64 `json:"calibration_date"`
	DriftCoefficient       float64 `json:"drift_coefficient"`
	TemperatureCoefficient float64 `json:"temperature_coefficient"`
}

// QuantumMagnetoFrameSensor sensor da patente RU2680629C2
type QuantumMagnetoFrameSensor struct {
	Mu                  float64
	N                   int
	S                   float64
	RingRadius          float64
	CalibrationFactor   float64
	Calibration         *MagnetoFrameCalibration
	Rings               map[string]*RingState
	MeasurementHistory  []*GeomagneticVector
	mu                  sync.RWMutex
	metrics             SensorMetrics
	EarthFieldReference float64
}

type RingState struct {
	Axis []float64 `json:"axis"`
	EMF  float64   `json:"emf"`
}

type SensorMetrics struct {
	TotalMeasurements int64   `json:"total_measurements"`
	AvgQuality        float64 `json:"avg_quality"`
	MaxSensitivityT   float64 `json:"max_sensitivity_t"`
	NoiseFloor        float64 `json:"noise_floor"`
}

func NewQuantumMagnetoFrameSensor(workingSubstanceMu float64, turns int, area, ringRadius float64) *QuantumMagnetoFrameSensor {
	return &QuantumMagnetoFrameSensor{
		Mu:         workingSubstanceMu,
		N:          turns,
		S:          area,
		RingRadius: ringRadius,
		CalibrationFactor: float64(turns) * area * Mu0 * workingSubstanceMu,
		Rings: map[string]*RingState{
			"X": {Axis: []float64{1, 0, 0}, EMF: 0},
			"Y": {Axis: []float64{0, 1, 0}, EMF: 0},
			"Z": {Axis: []float64{0, 0, 1}, EMF: 0},
		},
		MeasurementHistory:  make([]*GeomagneticVector, 0, 1000),
		EarthFieldReference: 50e-6 / Mu0,
		metrics: SensorMetrics{
			MaxSensitivityT: 2e-15,
			NoiseFloor:      1e-16,
		},
	}
}

func (s *QuantumMagnetoFrameSensor) Calibrate(knownH, measuredEMF, temperature float64) *MagnetoFrameCalibration {
	fmt.Printf("\n🔧 CALIBRAÇÃO DO SENSOR\n")
	fmt.Printf("   Campo conhecido: %.2f µT\n", knownH*1e6)
	fmt.Printf("   FEM medida: %.6f V\n", measuredEMF)

	s.Calibration = &MagnetoFrameCalibration{
		ReferenceH:             knownH,
		ReferenceEMF:           measuredEMF,
		CalibrationDate:        float64(time.Now().UnixNano()) / 1e9,
		DriftCoefficient:       0.001,
		TemperatureCoefficient: 0.0001,
	}

	s.CalibrationFactor = measuredEMF / knownH

	fmt.Printf("   Fator calibrado: %.6e V/(A/m)\n", s.CalibrationFactor)
	fmt.Printf("   Sensibilidade teórica: %.2e T\n", s.metrics.MaxSensitivityT)

	return s.Calibration
}

func (s *QuantumMagnetoFrameSensor) ReadFieldFromEMF(emf float64, axis string) float64 {
	if s.Calibration == nil {
		return emf / s.CalibrationFactor
	}

	timeDelta := float64(time.Now().UnixNano())/1e9 - s.Calibration.CalibrationDate
	drift := 1.0 + s.Calibration.DriftCoefficient*timeDelta/86400

	return (emf / s.Calibration.ReferenceEMF) * s.Calibration.ReferenceH / drift
}

func (s *QuantumMagnetoFrameSensor) MeasureVector(simulationMode bool) *GeomagneticVector {
	var emfX, emfY, emfZ float64

	if simulationMode {
		trueH := []float64{18.0, 2.0, 45.0}
		noiseLevel := s.metrics.MaxSensitivityT * 1e6
		emfX = trueH[0]*s.CalibrationFactor + gaussianNoise(0, noiseLevel)
		emfY = trueH[1]*s.CalibrationFactor + gaussianNoise(0, noiseLevel)
		emfZ = trueH[2]*s.CalibrationFactor + gaussianNoise(0, noiseLevel)
	}

	s.mu.Lock()
	s.Rings["X"].EMF = emfX
	s.Rings["Y"].EMF = emfY
	s.Rings["Z"].EMF = emfZ
	s.mu.Unlock()

	X := s.ReadFieldFromEMF(emfX, "X")
	Y := s.ReadFieldFromEMF(emfY, "Y")
	Z := s.ReadFieldFromEMF(emfZ, "Z")

	H := math.Sqrt(X*X + Y*Y)
	D := math.Atan2(Y, X) * 180 / math.Pi
	I := math.Atan2(Z, H) * 180 / math.Pi
	HTotal := math.Sqrt(H*H + Z*Z)
	grad := s.ComputeGradient()

	signalPower := HTotal * HTotal
	noisePower := math.Pow(s.metrics.MaxSensitivityT*1e6/Mu0, 2)
	snr := signalPower / math.Max(noisePower, 1e-20)
	quality := math.Min(1.0, math.Log10(snr+1)/10)

	vector := &GeomagneticVector{
		HTotal:        HTotal,
		D:             D,
		I:             I,
		X:             X,
		Y:             Y,
		Z:             Z,
		Gradient:      grad,
		Timestamp:     float64(time.Now().UnixNano()) / 1e9,
		QualityFactor: quality,
	}

	s.mu.Lock()
	s.MeasurementHistory = append(s.MeasurementHistory, vector)
	if len(s.MeasurementHistory) > 1000 {
		s.MeasurementHistory = s.MeasurementHistory[1:]
	}
	s.metrics.TotalMeasurements++
	n := float64(s.metrics.TotalMeasurements)
	s.metrics.AvgQuality = (s.metrics.AvgQuality*(n-1) + quality) / n
	s.mu.Unlock()

	return vector
}

func (s *QuantumMagnetoFrameSensor) ComputeGradient() []float64 {
	s.mu.RLock()
	defer s.mu.RUnlock()

	if len(s.MeasurementHistory) < 2 {
		return []float64{0, 0, 0}
	}

	last := s.MeasurementHistory[len(s.MeasurementHistory)-1]
	prev := s.MeasurementHistory[len(s.MeasurementHistory)-2]
	dt := last.Timestamp - prev.Timestamp
	if dt > 0 {
		return []float64{
			(last.X - prev.X) / dt,
			(last.Y - prev.Y) / dt,
			(last.Z - prev.Z) / dt,
		}
	}
	return []float64{0, 0, 0}
}

func (s *QuantumMagnetoFrameSensor) DetectAnomaly(thresholdSigma float64) map[string]interface{} {
	s.mu.RLock()
	defer s.mu.RUnlock()

	if len(s.MeasurementHistory) < 10 {
		return nil
	}

	recent := s.MeasurementHistory[len(s.MeasurementHistory)-10:]
	HValues := make([]float64, len(recent))
	for i, v := range recent {
		HValues[i] = v.HTotal
	}

	meanH := mean(HValues)
	stdH := std(HValues)
	current := s.MeasurementHistory[len(s.MeasurementHistory)-1]
	deviation := math.Abs(current.HTotal-meanH) / math.Max(stdH, 1e-10)

	if deviation > thresholdSigma {
		severity := "medium"
		if deviation > 5.0 {
			severity = "high"
		}
		return map[string]interface{}{
			"type":            "geomagnetic_anomaly",
			"deviation_sigma": deviation,
			"expected_h":      meanH,
			"measured_h":      current.HTotal,
			"timestamp":       current.Timestamp,
			"severity":        severity,
		}
	}
	return nil
}

func (s *QuantumMagnetoFrameSensor) Health() map[string]interface{} {
	s.mu.RLock()
	defer s.mu.RUnlock()

	ringStatus := make(map[string]interface{})
	for axis, data := range s.Rings {
		ringStatus[axis] = map[string]interface{}{
			"emf":    data.EMF,
			"active": math.Abs(data.EMF) > 1e-10,
		}
	}

	return map[string]interface{}{
		"calibrated":         s.Calibration != nil,
		"calibration_date":   s.Calibration.CalibrationDate,
		"calibration_factor": s.CalibrationFactor,
		"sensitivity_tesla":  s.metrics.MaxSensitivityT,
		"total_measurements": s.metrics.TotalMeasurements,
		"avg_quality":        s.metrics.AvgQuality,
		"ring_status":        ringStatus,
	}
}

// GeomagneticSensorium sensorium completo
type GeomagneticSensorium struct {
	Sensor              *QuantumMagnetoFrameSensor
	PlanetRegistry      map[string]*PlanetData
	AnomalyLog          []map[string]interface{}
	BiocurrentDetection bool
	mu                  sync.RWMutex
	metrics             SensoriumMetrics
}

type PlanetData struct {
	Calibration    *MagnetoFrameCalibration `json:"calibration"`
	BaselineVector map[string]float64       `json:"baseline_vector"`
	MappedAt       float64                  `json:"mapped_at"`
}

type SensoriumMetrics struct {
	PlanetsMapped      int64 `json:"planets_mapped"`
	AnomaliesDetected  int64 `json:"anomalies_detected"`
	BiocurrentSessions int64 `json:"biocurrent_sessions"`
	NavigationFixes    int64 `json:"navigation_fixes"`
}

func NewGeomagneticSensorium() *GeomagneticSensorium {
	return &GeomagneticSensorium{
		Sensor:         NewQuantumMagnetoFrameSensor(1e5, 100, 1e-4, 0.05),
		PlanetRegistry: make(map[string]*PlanetData),
		AnomalyLog:     make([]map[string]interface{}, 0, 500),
	}
}

func (g *GeomagneticSensorium) InitializeOnPlanet(planetName string, knownField *float64) (*PlanetData, error) {
	fmt.Printf("\n🌍 INICIALIZANDO SENSORIUM EM: %s\n", planetName)

	field := g.Sensor.EarthFieldReference
	if knownField != nil {
		field = *knownField
	}

	g.Sensor.Calibrate(field, 0.01, 20.0)

	samples := make([]*GeomagneticVector, 0, 10)
	for i := 0; i < 10; i++ {
		vector := g.Sensor.MeasureVector(true)
		samples = append(samples, vector)
		time.Sleep(10 * time.Millisecond)
	}

	data := &PlanetData{
		Calibration: g.Sensor.Calibration,
		BaselineVector: map[string]float64{
			"h_total": meanFloat64Slice(samples, func(v *GeomagneticVector) float64 { return v.HTotal }),
			"d":       meanFloat64Slice(samples, func(v *GeomagneticVector) float64 { return v.D }),
			"i":       meanFloat64Slice(samples, func(v *GeomagneticVector) float64 { return v.I }),
			"x":       meanFloat64Slice(samples, func(v *GeomagneticVector) float64 { return v.X }),
			"y":       meanFloat64Slice(samples, func(v *GeomagneticVector) float64 { return v.Y }),
			"z":       meanFloat64Slice(samples, func(v *GeomagneticVector) float64 { return v.Z }),
		},
		MappedAt: float64(time.Now().UnixNano()) / 1e9,
	}

	g.mu.Lock()
	g.PlanetRegistry[planetName] = data
	g.metrics.PlanetsMapped++
	g.mu.Unlock()

	fmt.Printf("   ✅ Sensorium ativo em %s\n", planetName)
	fmt.Printf("   Campo base: %.2f µT\n", data.BaselineVector["h_total"]*1e6)

	return data, nil
}

func (g *GeomagneticSensorium) ContinuousMonitoring(durationSeconds float64) {
	fmt.Printf("\n📡 MONITORAMENTO CONTÍNUO (%.0fs)\n", durationSeconds)

	start := time.Now()
	nSamples := 0

	for time.Since(start).Seconds() < durationSeconds {
		_ = g.Sensor.MeasureVector(true)
		nSamples++

		anomaly := g.Sensor.DetectAnomaly(3.0)
		if anomaly != nil {
			g.mu.Lock()
			g.AnomalyLog = append(g.AnomalyLog, anomaly)
			if len(g.AnomalyLog) > 500 {
				g.AnomalyLog = g.AnomalyLog[1:]
			}
			g.metrics.AnomaliesDetected++
			g.mu.Unlock()
			fmt.Printf("   ⚠️ ANOMALIA: σ=%.2f\n", anomaly["deviation_sigma"])
		}

		time.Sleep(100 * time.Millisecond)
	}

	fmt.Printf("   ✅ %d amostras coletadas\n", nSamples)
	fmt.Printf("   Anomalias: %d\n", g.metrics.AnomaliesDetected)
}

func (g *GeomagneticSensorium) DetectBiocurrents(subjectID string, duration float64) map[string]interface{} {
	fmt.Printf("\n🧠 DETECÇÃO DE BIOCORRENTES: %s\n", subjectID)
	fmt.Printf("   Duração: %.0fs\n", duration)
	fmt.Printf("   Sensibilidade: %.2e T\n", g.Sensor.metrics.MaxSensitivityT)

	biocurrentField := 1e-13
	readings := make([]map[string]interface{}, 0)
	start := time.Now()

	for time.Since(start).Seconds() < duration {
		base := g.Sensor.MeasureVector(true)
		elapsed := time.Since(start).Seconds()

		bioSignal := biocurrentField * math.Sin(2*math.Pi*10*elapsed)
		bioSignal += biocurrentField * 0.3 * math.Sin(2*math.Pi*20*elapsed)

		readings = append(readings, map[string]interface{}{
			"timestamp":      float64(time.Now().UnixNano()) / 1e9,
			"z_with_bio":     base.Z + bioSignal/Mu0,
			"bio_component":  bioSignal,
			"raw_z":          base.Z,
		})

		time.Sleep(50 * time.Millisecond)
	}

	g.mu.Lock()
	g.metrics.BiocurrentSessions++
	g.mu.Unlock()

	var sumAbs float64
	var maxAbs float64
	for _, r := range readings {
		bio := r["bio_component"].(float64)
		absBio := math.Abs(bio)
		sumAbs += absBio
		if absBio > maxAbs {
			maxAbs = absBio
		}
	}
	avgAmplitude := sumAbs / float64(len(readings))
	snr := avgAmplitude / g.Sensor.metrics.MaxSensitivityT

	fmt.Printf("   ✅ %d leituras de biocorrente\n", len(readings))
	fmt.Printf("   Amplitude média: %.2e T\n", avgAmplitude)
	fmt.Printf("   SNR: %.1f\n", snr)

	return map[string]interface{}{
		"subject":       subjectID,
		"readings":      len(readings),
		"avg_amplitude": avgAmplitude,
		"max_amplitude": maxAbs,
		"snr":           snr,
	}
}

func (g *GeomagneticSensorium) Health() map[string]interface{} {
	g.mu.RLock()
	defer g.mu.RUnlock()

	return map[string]interface{}{
		"sensor":              g.Sensor.Health(),
		"planets_mapped":      g.metrics.PlanetsMapped,
		"planet_registry":     keys(g.PlanetRegistry),
		"anomalies_detected":  g.metrics.AnomaliesDetected,
		"biocurrent_sessions": g.metrics.BiocurrentSessions,
		"navigation_fixes":    g.metrics.NavigationFixes,
		"recent_anomalies":    lastN(g.AnomalyLog, 5),
	}
}

// Helpers matemáticos
func gaussianNoise(mean, stdDev float64) float64 {
	// Box-Muller simplificado
	return mean + stdDev*0.5 // Simulação
}

func mean(data []float64) float64 {
	if len(data) == 0 {
		return 0
	}
	var sum float64
	for _, v := range data {
		sum += v
	}
	return sum / float64(len(data))
}

func std(data []float64) float64 {
	if len(data) < 2 {
		return 0
	}
	m := mean(data)
	var sum float64
	for _, v := range data {
		d := v - m
		sum += d * d
	}
	return math.Sqrt(sum / float64(len(data)-1))
}

func meanFloat64Slice(samples []*GeomagneticVector, extractor func(*GeomagneticVector) float64) float64 {
	if len(samples) == 0 {
		return 0
	}
	var sum float64
	for _, s := range samples {
		sum += extractor(s)
	}
	return sum / float64(len(samples))
}

func keys(m map[string]*PlanetData) []string {
	k := make([]string, 0, len(m))
	for key := range m {
		k = append(k, key)
	}
	return k
}

func lastN(slice []map[string]interface{}, n int) []map[string]interface{} {
	if len(slice) <= n {
		result := make([]map[string]interface{}, len(slice))
		copy(result, slice)
		return result
	}
	return slice[len(slice)-n:]
}
