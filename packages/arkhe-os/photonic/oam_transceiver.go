// arkhe_os/photonic/oam_transceiver.go
package photonic

import (
	"fmt"
	"math"
	"math/cmplx"
	"sync"
	"time"
)

// ─── CONSTANTES DA COMUNICAÇÃO OAM-φ ─────────────────────────────────

const (
	// ImpedanceOfFreeSpace impedância do vácuo (Ω)
	ImpedanceOfFreeSpace = 377.0

	// PhiPhaseAdvance avanço de fase φ por comprimento de onda (rad)
	PhiPhaseAdvance = math.Pi / 10.5

	// DefaultWavelength comprimento de onda padrão (banda C, 1550 nm)
	DefaultWavelength = 1550e-9

	// DefaultBeamWaist waist do feixe Gaussiano (m)
	DefaultBeamWaist = 1e-3

	// FaradayBaseRotation rotação de Faraday base para ℓ=1 (rad)
	FaradayBaseRotation = 1.0e-6

	// ReferenceChannelK canal de referência para 500 THz
	ReferenceChannelK = 10
)

// ─── TIPOS FUNDAMENTAIS ───────────────────────────────────────────

// OAMMode representa um modo de momento angular orbital com carga ℓ.
type OAMMode struct {
	Charge       int     // carga topológica ℓ (inteiro, pode ser negativo)
	Frequency    float64 // frequência central da portadora (Hz)
	Wavelength   float64 // comprimento de onda correspondente (m)
	PhiPhase     float64 // avanço φ por λ (rad)
	Amplitude    float64 // amplitude do campo elétrico
	CarrierPhase float64 // fase adicional para modulação (QPSK/QAM)
	ChannelIndex int     // índice k na grade espectral φ
}

// OAMSymbol representa um símbolo modulado em um modo OAM.
type OAMSymbol struct {
	Mode      *OAMMode   // modo OAM associado
	SymbolIQ  complex128 // ponto da constelação (ex: QPSK, 16-QAM)
	Timestamp float64    // timestamp de transmissão
}

// OAMCompositeBeam é a superposição coerente de múltiplos modos OAM coaxiais.
type OAMCompositeBeam struct {
	Modes        []*OAMMode   // modos ativos neste feixe composto
	Symbols      []complex128 // símbolo modulado por modo
	Wavelength   float64      // comprimento de onda central do feixe
	Polarization string       // "linear", "circular_L", "circular_R"
	Timestamp    float64      // timestamp de geração do feixe
}

// OAMTransceiver implementa o protocolo de comunicação OAM baseado em φ.
type OAMTransceiver struct {
	mu                sync.RWMutex
	ActiveModes       []*OAMMode     // modos OAM configurados para transmissão/recepção
	DefaultWavelength float64        // comprimento de onda padrão
	ModulationScheme  string         // "QPSK", "16QAM", "64QAM"
	SNRPerMode        float64        // SNR estimado por modo (dB)
	ChannelCapacity   float64        // capacidade total calculada (bits/s/Hz)
	receiveBuffer     chan OAMSymbol // buffer para símbolos recebidos
	transmitQueue     chan OAMSymbol // fila para símbolos a transmitir
}

// ─── FUNÇÕES AUXILIARES DA GRADE ESPECTRAL φ ─────────────────────

// ImpedanceScaledFrequency calcula ωₖ = 2π·377·10¹² / φᵏ [rad/s]
func ImpedanceScaledFrequency(k int) float64 {
	phi := (1 + math.Sqrt(5)) / 2
	baseFreq := 2 * math.Pi * ImpedanceOfFreeSpace * 1e12 // 2π·377·10¹² rad/s
	return baseFreq / math.Pow(phi, float64(k))
}

// FrequencyToWavelength converte frequência angular para comprimento de onda
func FrequencyToWavelength(omega float64) float64 {
	c := 299792458.0 // velocidade da luz (m/s)
	return 2 * math.Pi * c / omega
}

// TuneGrapheneFermi calcula nível de Fermi para sintonizar metassuperfície no canal k
func TuneGrapheneFermi(k int) float64 {
	phi := (1 + math.Sqrt(5)) / 2
	// E_F^(k) ≈ 0.4 · φ^((k₀-k)/2) eV
	return 0.4 * math.Pow(phi, float64(ReferenceChannelK-k)/2)
}

// DetectOAMChargeFromFaraday estima carga ℓ a partir da rotação de Faraday medida
func DetectOAMChargeFromFaraday(faradayRotation float64, k int) int {
	phi := (1 + math.Sqrt(5)) / 2
	// θ₀ · φ^(k₀-k) é a rotação esperada para ℓ=1 no canal k
	baseRotation := FaradayBaseRotation * math.Pow(phi, float64(ReferenceChannelK-k))
	if baseRotation < 1e-12 {
		baseRotation = 1e-12 // evitar divisão por zero
	}
	return int(math.Round(faradayRotation / baseRotation))
}

// ─── CONSTRUTORES ─────────────────────────────────────────────────

// NewOAMMode cria um modo OAM sintonizado para o k‑ésimo canal da grade φ.
func NewOAMMode(charge int, k int) *OAMMode {
	omega := ImpedanceScaledFrequency(k)
	wavelength := FrequencyToWavelength(omega)

	return &OAMMode{
		Charge:       charge,
		Frequency:    omega / (2 * math.Pi), // converter para Hz
		Wavelength:   wavelength,
		PhiPhase:     PhiPhaseAdvance,
		Amplitude:    1.0,
		CarrierPhase: 0.0,
		ChannelIndex: k,
	}
}

// NewOAMTransceiver inicializa o transceptor com N modos (cargas de -L a L).
func NewOAMTransceiver(numModes int, baseK int) *OAMTransceiver {
	if numModes%2 == 0 {
		numModes++ // garantir número ímpar para simetria ℓ = -L...L
	}

	modes := make([]*OAMMode, numModes)
	L := (numModes - 1) / 2
	idx := 0

	for ell := -L; ell <= L; ell++ {
		// Atribui frequências φ alternadas para reduzir diafonia
		k := baseK + int(math.Abs(float64(ell)))
		modes[idx] = NewOAMMode(ell, k)
		idx++
	}

	return &OAMTransceiver{
		ActiveModes:       modes,
		DefaultWavelength: DefaultWavelength,
		ModulationScheme:  "QPSK",
		SNRPerMode:        30.0, // 30 dB típico para enlace óptico livre
		receiveBuffer:     make(chan OAMSymbol, 1000),
		transmitQueue:     make(chan OAMSymbol, 1000),
	}
}

// ─── OPERAÇÕES DE TRANSMISSÃO ─────────────────────────────────────

// EncodeSymbols modula bits em símbolos QPSK para cada modo ativo.
// bits: slice de bytes; cada par de bits → 1 símbolo QPSK por modo.
func (t *OAMTransceiver) EncodeSymbols(bits []byte) []OAMSymbol {
	t.mu.RLock()
	defer t.mu.RUnlock()

	symbols := make([]OAMSymbol, len(t.ActiveModes))

	// Mapeamento QPSK: 00→1+j, 01→-1+j, 10→-1-j, 11→1-j
	qpskMap := []complex128{1 + 1i, -1 + 1i, -1 - 1i, 1 - 1i}

	for i, mode := range t.ActiveModes {
		// Extrair 2 bits para este modo (circular se necessário)
		byteIdx := (i * 2 / 8) % len(bits)
		bitIdx := (i * 2) % 8
		b := byte(0)

		if byteIdx < len(bits) {
			b = bits[byteIdx]
		}
		// Extrair 2 bits consecutivos
		twoBits := (b >> (6 - bitIdx)) & 0x03
		if bitIdx+2 > 8 && byteIdx+1 < len(bits) {
			nextByte := bits[byteIdx+1]
			twoBits = ((b & 0x01) << 1) | ((nextByte >> 7) & 0x01)
		}

		symbols[i] = OAMSymbol{
			Mode:      mode,
			SymbolIQ:  qpskMap[twoBits],
			Timestamp: float64(time.Now().UnixNano()) / 1e9,
		}
	}

	return symbols
}

// GenerateCompositeBeam cria um feixe composto a partir dos símbolos atuais.
func (t *OAMTransceiver) GenerateCompositeBeam(symbols []OAMSymbol) *OAMCompositeBeam {
	t.mu.RLock()
	defer t.mu.RUnlock()

	beam := &OAMCompositeBeam{
		Wavelength:   t.DefaultWavelength,
		Polarization: "circular_L",
		Timestamp:    float64(time.Now().UnixNano()) / 1e9,
	}

	for _, sym := range symbols {
		beam.Modes = append(beam.Modes, sym.Mode)
		beam.Symbols = append(beam.Symbols, sym.SymbolIQ)
	}

	return beam
}

// FieldAt calcula o campo elétrico complexo do feixe composto no ponto (r, ϕ, z).
// Retorna componentes Ex e Ey para polarização elíptica/circular.
func (beam *OAMCompositeBeam) FieldAt(r, phi, z float64) (complex128, complex128) {
	var Ex, Ey complex128
	k := 2 * math.Pi / beam.Wavelength
	waist := DefaultBeamWaist

	for i, mode := range beam.Modes {
		// Envelope radial (aproximação LG₀ℓ)
		rNorm := r * math.Sqrt(2) / waist
		envelope := math.Exp(-r*r/(waist*waist)) * math.Pow(rNorm, math.Abs(float64(mode.Charge)))

		// Fase helicoidal: e^(i·ℓ·ϕ)
		helical := cmplx.Exp(complex(0, float64(mode.Charge)*phi))

		// Propagação longitudinal + avanço φ
		propPhase := cmplx.Exp(complex(0, k*z))
		phiPhase := cmplx.Exp(complex(0, mode.PhiPhase*k*z))

		// Símbolo modulado
		symbol := beam.Symbols[i]

		// Campo total para este modo
		field := complex(envelope*mode.Amplitude, 0) * helical * propPhase * phiPhase * symbol

		// Combinar polarizações (circular esquerda: Ey = i·Ex)
		Ex += field
		if beam.Polarization == "circular_L" {
			Ey += field * complex(0, 1)
		} else if beam.Polarization == "circular_R" {
			Ey += field * complex(0, -1)
		} else {
			Ey += field // linear
		}
	}

	return Ex, Ey
}

// TransmitBeam envia feixe composto para o canal de transmissão.
func (t *OAMTransceiver) TransmitBeam(beam *OAMCompositeBeam) error {
	select {
	case t.transmitQueue <- OAMSymbol{ // simplificação: envia primeiro símbolo como proxy
		Mode:      beam.Modes[0],
		SymbolIQ:  beam.Symbols[0],
		Timestamp: beam.Timestamp,
	}:
		return nil
	default:
		return fmt.Errorf("transmit queue full")
	}
}

// ─── OPERAÇÕES DE RECEPÇÃO ────────────────────────────────────────

// DemultiplexOAM separa o feixe composto nos modos originais via projeção azimutal.
// fieldFunc: função que retorna (Ex, Ey) para coordenadas (r, ϕ, z) dadas.
func (t *OAMTransceiver) DemultiplexOAM(
	fieldFunc func(float64, float64, float64) (complex128, complex128),
	z float64,
) []complex128 {
	t.mu.RLock()
	defer t.mu.RUnlock()

	results := make([]complex128, len(t.ActiveModes))
	steps := 64  // passos azimutais para integração
	rSteps := 10 // passos radiais
	dr := DefaultBeamWaist / float64(rSteps)

	for i, mode := range t.ActiveModes {
		var sum complex128

		// Integração radial e azimutal para projeção na base OAM
		for ri := 1; ri <= rSteps; ri++ {
			r := float64(ri) * dr
			for phiStep := 0; phiStep < steps; phiStep++ {
				phi := 2 * math.Pi * float64(phiStep) / float64(steps)
				Ex, _ := fieldFunc(r, phi, z)

				// Projeção: ∫ e^(-i·ℓ·ϕ) · E(r,ϕ) dϕ
				projection := cmplx.Exp(complex(0, -float64(mode.Charge)*phi))
				sum += Ex * projection
			}
		}

		// Normalizar pelo número de pontos de amostragem
		results[i] = sum / complex(float64(steps*rSteps), 0)
	}

	return results
}

// DecodeSymbols decodifica símbolos QPSK recebidos para bits.
func (t *OAMTransceiver) DecodeSymbols(receivedSymbols []complex128) []byte {
	t.mu.RLock()
	defer t.mu.RUnlock()

	bits := make([]byte, 0, len(receivedSymbols)*2)

	// Mapeamento QPSK inverso
	qpskMap := map[complex128]byte{
		1 + 1i:  0, // 00
		-1 + 1i: 1, // 01
		-1 - 1i: 2, // 10
		1 - 1i:  3, // 11
	}

	for _, sym := range receivedSymbols {
		// Encontrar ponto da constelação mais próximo (detecção de máxima verossimilhança)
		best := byte(0)
		bestDist := math.MaxFloat64

		for constellation, b := range qpskMap {
			d := cmplx.Abs(sym - constellation)
			if d < bestDist {
				bestDist = d
				best = b
			}
		}

		// Converter 2 bits para bytes
		bits = append(bits, best>>1, best&1)
	}

	return bits
}

// ReceiveSymbol processa símbolo recebido e coloca no buffer.
func (t *OAMTransceiver) ReceiveSymbol(sym OAMSymbol) {
	select {
	case t.receiveBuffer <- sym:
		// sucesso
	default:
		// buffer cheio: descartar ou logar
	}
}

// ─── MÉTRICAS E CAPACIDADE DO CANAL ───────────────────────────────

// CalculateChannelCapacity estima a capacidade do canal OAM (fórmula de Shannon).
// snrPerMode: SNR por modo em escala linear (não dB).
func (t *OAMTransceiver) CalculateChannelCapacity(snrPerMode float64) float64 {
	t.mu.Lock()
	defer t.mu.Unlock()

	totalCapacity := 0.0
	for range t.ActiveModes {
		totalCapacity += math.Log2(1 + snrPerMode)
	}

	t.ChannelCapacity = totalCapacity
	return totalCapacity
}

// GetTransceiverStatus retorna status operacional do transceptor.
func (t *OAMTransceiver) GetTransceiverStatus() map[string]interface{} {
	t.mu.RLock()
	defer t.mu.RUnlock()

	modeInfo := make([]map[string]interface{}, len(t.ActiveModes))
	for i, mode := range t.ActiveModes {
		modeInfo[i] = map[string]interface{}{
			"charge":        mode.Charge,
			"frequency_Hz":  mode.Frequency,
			"wavelength_nm": mode.Wavelength * 1e9,
			"channel_k":     mode.ChannelIndex,
			"phi_phase_rad": mode.PhiPhase,
		}
	}

	return map[string]interface{}{
		"active_modes":           len(t.ActiveModes),
		"modulation_scheme":      t.ModulationScheme,
		"snr_per_mode_dB":        t.SNRPerMode,
		"channel_capacity_bpsHz": t.ChannelCapacity,
		"default_wavelength_nm":  t.DefaultWavelength * 1e9,
		"modes":                  modeInfo,
		"receive_buffer_size":    len(t.receiveBuffer),
		"transmit_queue_size":    len(t.transmitQueue),
	}
}

// UpdateSNR atualiza estimativa de SNR por modo (ex: baseado em medições).
func (t *OAMTransceiver) UpdateSNR(newSNR_dB float64) {
	t.mu.Lock()
	defer t.mu.Unlock()
	t.SNRPerMode = newSNR_dB
	// Recalcular capacidade se necessário
	if t.ChannelCapacity > 0 {
		snrLinear := math.Pow(10, newSNR_dB/10)
		t.ChannelCapacity = 0.0
		for range t.ActiveModes {
			t.ChannelCapacity += math.Log2(1 + snrLinear)
		}
	}
}

// ─── INTEGRAÇÃO COM METASSUPERFÍCIE DE GRAFENO ───────────────────

// ConfigureGrapheneMetasurface configura metassuperfície para canal k específico.
// Retorna nível de Fermi necessário e reflectância estimada.
func ConfigureGrapheneMetasurface(k int) (fermiLevel_eV float64, reflectance float64) {
	fermiLevel_eV = TuneGrapheneFermi(k)

	// Modelo simplificado de reflectância: pico em E_F sintonizado
	// Reflectância máxima ~95% quando sintonizado, cai para ~10% fora do pico
	detuning := math.Abs(float64(k - ReferenceChannelK))
	reflectance = 0.95*math.Exp(-detuning*0.5) + 0.05

	return fermiLevel_eV, reflectance
}

// ─── INTEGRAÇÃO COM SENSOR GEOMAGNÉTICO QUÂNTICO ─────────────────

// EstimateOAMChargeFromMagneticField estima carga ℓ a partir de medição magnética.
// magneticField_T: campo magnético medido (Tesla)
// verdetConstant: constante de Verdet do meio magneto-óptico (rad/T/m)
// pathLength_m: comprimento do caminho óptico no meio (m)
func EstimateOAMChargeFromMagneticField(
	magneticField_T float64,
	verdetConstant float64,
	pathLength_m float64,
	channelK int,
) int {
	// Rotação de Faraday: θ_F = V · B · L
	faradayRotation := verdetConstant * magneticField_T * pathLength_m

	// Estimar carga ℓ usando função de detecção φ
	ell := DetectOAMChargeFromFaraday(faradayRotation, channelK)

	return ell
}
