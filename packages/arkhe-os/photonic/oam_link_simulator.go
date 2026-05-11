// arkhe_os/photonic/oam_link_simulator.go
package photonic

import (
	"math"
	"time"
)

// OAMLinkConfig contém parâmetros de configuração de enlace OAM.
type OAMLinkConfig struct {
	Distance_km               float64 // distância do enlace (km)
	AtmosphericLoss_dB_per_km float64 // perda atmosférica típica
	PointingError_rad         float64 // erro de apontamento (rad)
	TurbulenceStrength        float64 // Cn² para turbulência atmosférica
	ReceiverAperture_m        float64 // diâmetro da abertura do receptor
}

// OAMLinkSimulator simula propagação de feixe OAM através de meio interestelar.
type OAMLinkSimulator struct {
	config OAMLinkConfig
	phi    float64 // razão áurea pré-computada
}

// NewOAMLinkSimulator cria novo simulador de enlace OAM.
func NewOAMLinkSimulator(config OAMLinkConfig) *OAMLinkSimulator {
	return &OAMLinkSimulator{
		config: config,
		phi:    (1 + math.Sqrt(5)) / 2,
	}
}

// PropagateBeam simula propagação do feixe composto do transmissor ao receptor.
// Inclui: perda por distância, turbulência atmosférica, erro de apontamento.
func (s *OAMLinkSimulator) PropagateBeam(
	txBeam *OAMCompositeBeam,
	rxTransceiver *OAMTransceiver,
) (*OAMCompositeBeam, error) {
	// 1. Perda por distância (lei do inverso do quadrado + perdas atmosféricas)
	distance_m := s.config.Distance_km * 1000
	freeSpaceLoss := 20 * math.Log10(4*math.Pi*distance_m/txBeam.Wavelength)
	atmosphericLoss := s.config.AtmosphericLoss_dB_per_km * s.config.Distance_km
	totalLoss_dB := freeSpaceLoss + atmosphericLoss

	// Fator de atenuação linear
	attenuation := math.Pow(10, -totalLoss_dB/20)

	// 2. Efeito de turbulência atmosférica (modelo simplificado de Rytov)
	rytovVariance := 1.23 * s.config.TurbulenceStrength *
		math.Pow(2*math.Pi/txBeam.Wavelength, 7/6) *
		math.Pow(distance_m, 11/6)
	scintillationFactor := math.Exp(-0.5 * rytovVariance)

	// 3. Perda por erro de apontamento (modelo Gaussiano)
	pointingLoss := math.Exp(-math.Pow(s.config.PointingError_rad*distance_m/s.config.ReceiverAperture_m, 2))

	// Fator de atenuação total
	totalAttenuation := attenuation * scintillationFactor * pointingLoss

	// 4. Aplicar atenuação aos símbolos recebidos
	rxSymbols := make([]complex128, len(txBeam.Symbols))
	for i, sym := range txBeam.Symbols {
		// Adicionar ruído térmico (AWGN) com SNR configurado
		snrLinear := math.Pow(10, rxTransceiver.SNRPerMode/10)
		noiseVariance := 1.0 / snrLinear

		// Ruído complexo Gaussiano
		noise := complex(
			math.Sqrt(noiseVariance/2)*randNormal(),
			math.Sqrt(noiseVariance/2)*randNormal(),
		)

		// Símbolo recebido = símbolo transmitido × atenuação + ruído
		rxSymbols[i] = sym*complex(totalAttenuation, 0) + noise
	}

	// Criar feixe recebido (simplificação: mantém mesma estrutura de modos)
	rxBeam := &OAMCompositeBeam{
		Modes:        txBeam.Modes,
		Symbols:      rxSymbols,
		Wavelength:   txBeam.Wavelength,
		Polarization: txBeam.Polarization,
		Timestamp:    float64(time.Now().UnixNano()) / 1e9,
	}

	return rxBeam, nil
}

// CalculateLinkBudget calcula orçamento de enlace completo para configuração dada.
func (s *OAMLinkSimulator) CalculateLinkBudget(txPower_dBm float64, numModes int) map[string]float64 {
	distance_m := s.config.Distance_km * 1000
	wavelength := DefaultWavelength

	// Ganho de antena óptica (aproximação para abertura circular)
	txGain := 10 * math.Log10(math.Pow(math.Pi*s.config.ReceiverAperture_m/wavelength, 2))
	rxGain := txGain // assumir mesma abertura no receptor

	// Perdas
	freeSpaceLoss := 20 * math.Log10(4*math.Pi*distance_m/wavelength)
	atmosphericLoss := s.config.AtmosphericLoss_dB_per_km * s.config.Distance_km
	pointingLoss := 10 * math.Log10(1/s.config.PointingError_rad) // simplificado

	// Margem de turbulência (estimativa conservativa)
	turbulenceMargin := 3.0 * math.Sqrt(s.config.TurbulenceStrength*distance_m/1e6)

	// Potência recebida por modo
	receivedPowerPerMode := txPower_dBm + txGain + rxGain -
		freeSpaceLoss - atmosphericLoss - pointingLoss - turbulenceMargin

	// Capacidade total do enlace (Shannon)
	snrPerMode_linear := math.Pow(10, (receivedPowerPerMode-(-174+10*math.Log10(1e9)))/10)
	capacityPerMode := math.Log2(1 + snrPerMode_linear)        // bits/s/Hz
	totalCapacity := capacityPerMode * float64(numModes) * 1e9 // assumir 1 GHz de banda por modo

	return map[string]float64{
		"tx_power_dBm":                txPower_dBm,
		"free_space_loss_dB":          freeSpaceLoss,
		"atmospheric_loss_dB":         atmosphericLoss,
		"pointing_loss_dB":            pointingLoss,
		"turbulence_margin_dB":        turbulenceMargin,
		"received_power_per_mode_dBm": receivedPowerPerMode,
		"snr_per_mode_dB":             receivedPowerPerMode - (-174 + 10*math.Log10(1e9)),
		"capacity_per_mode_bps":       capacityPerMode * 1e9,
		"total_capacity_bps":          totalCapacity,
	}
}

// randNormal gera número aleatório com distribuição normal padrão.
func randNormal() float64 {
	// Box-Muller transform simplificado
	u1 := float64(time.Now().Nanosecond()%10000) / 10000.0
	u2 := float64(time.Now().UnixNano()%10000) / 10000.0
	return math.Sqrt(-2*math.Log(u1+1e-10)) * math.Cos(2*math.Pi*u2)
}
