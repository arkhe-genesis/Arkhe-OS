package interlink

import (
	"crypto/sha3"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"math"
	"sync"
	"time"

	"github.com/arkhe-os/arkhe-go/pkg/temporal"
	"go.uber.org/zap"
)

// Constantes físicas
const (
	SpeedOfLight      = 299792458.0 // m/s
	LyToMeters        = 9.461e15    // 1 ano-luz em metros
	DefaultWavelength = 1550e-9     // 1550 nm (banda C)
	DefaultTxPower    = 100.0       // Watts
	DefaultApertureTx = 0.30        // metros
	DefaultApertureRx = 1.0         // metros
	MinSNRdB          = 3.0         // SNR mínimo para demodulação
	MaxBER            = 1e-9        // BER máximo aceitável
)

// LaserLinkConfig configura o enlace laser
type LaserLinkConfig struct {
	Wavelength       float64 `json:"wavelength_m"`
	TxPower          float64 `json:"tx_power_w"`
	ApertureTx       float64 `json:"aperture_tx_m"`
	ApertureRx       float64 `json:"aperture_rx_m"`
	PointingErrorRad float64 `json:"pointing_error_rad"`
	FECOverhead      float64 `json:"fec_overhead"`
	SymbolRateBaud   float64 `json:"symbol_rate_baud"`
	Modulation       string  `json:"modulation"` // "DP-QPSK", "QAM-64", etc.
}

// DefaultConfig retorna configuração padrão para enlace interestelar
func DefaultConfig() LaserLinkConfig {
	return LaserLinkConfig{
		Wavelength:       DefaultWavelength,
		TxPower:          DefaultTxPower,
		ApertureTx:       DefaultApertureTx,
		ApertureRx:       DefaultApertureRx,
		PointingErrorRad: 1e-6,  // 1 µrad
		FECOverhead:      0.067, // Reed-Solomon (255,239)
		SymbolRateBaud:   1e9,   // 1 GBaud
		Modulation:       "DP-QPSK",
	}
}

// LinkBudget resultado do cálculo de enlace
type LinkBudget struct {
	FreeSpaceLossDB   float64 `json:"free_space_loss_db"`
	PointingLossDB    float64 `json:"pointing_loss_db"`
	AtmosphericLossDB float64 `json:"atmospheric_loss_db"`
	ReceiverGainDB    float64 `json:"receiver_gain_db"`
	ReceivedPowerDBm  float64 `json:"received_power_dbm"`
	NoisePowerDBm     float64 `json:"noise_power_dbm"`
	SNRdB             float64 `json:"snr_db"`
	BEREstimate       float64 `json:"ber_estimate"`
	LinkMarginDB      float64 `json:"link_margin_db"`
	Achievable        bool    `json:"achievable"`
}

// LaserEngine motor de comunicação laser
type LaserEngine struct {
	mu         sync.RWMutex
	nodeID     string
	config     LaserLinkConfig
	positionAU [3]float64 // Posição em UA
	peers      map[string]*PeerInfo
	seqNum     uint32
	logger     *zap.Logger
	stats      Stats
}

// PeerInfo informações sobre um peer
type PeerInfo struct {
	ID          string
	PositionAU  [3]float64
	Config      LaserLinkConfig
	LastContact time.Time
	SNRdB       *float64
	LinkStatus  string // "unknown", "active", "inactive"
}

// Stats estatísticas do engine
type Stats struct {
	FramesSent     uint64
	FramesReceived uint64
	BytesSent      uint64
	BytesReceived  uint64
	AvgSNRdB       float64
	LinkFailures   uint64
}

// NewLaserEngine cria um novo motor de enlace
func NewLaserEngine(nodeID string, config LaserLinkConfig, positionAU [3]float64, logger *zap.Logger) *LaserEngine {
	return &LaserEngine{
		nodeID:     nodeID,
		config:     config,
		positionAU: positionAU,
		peers:      make(map[string]*PeerInfo),
		logger:     logger,
	}
}

// RegisterPeer registra um peer para comunicação
func (e *LaserEngine) RegisterPeer(peerID string, positionAU [3]float64, config *LaserLinkConfig) {
	e.mu.Lock()
	defer e.mu.Unlock()

	if config == nil {
		c := e.config
		config = &c
	}

	e.peers[peerID] = &PeerInfo{
		ID:         peerID,
		PositionAU: positionAU,
		Config:     *config,
		LinkStatus: "unknown",
	}
}

// CalculateDistance calcula distância para um peer em metros
func (e *LaserEngine) CalculateDistance(peerID string) (float64, error) {
	e.mu.RLock()
	peer, ok := e.peers[peerID]
	e.mu.RUnlock()
	if !ok {
		return 0, fmt.Errorf("peer %s not registered", peerID)
	}

	// Distância euclidiana em UA, depois converter para metros
	var sum float64
	for i := 0; i < 3; i++ {
		diff := e.positionAU[i] - peer.PositionAU[i]
		sum += diff * diff
	}
	distanceAU := math.Sqrt(sum)
	return distanceAU * 1.496e11, nil // UA → metros
}

// EvaluateLink calcula link budget para um peer
func (e *LaserEngine) EvaluateLink(peerID string) (*LinkBudget, error) {
	distanceM, err := e.CalculateDistance(peerID)
	if err != nil {
		return nil, err
	}

	e.mu.RLock()
	peer := e.peers[peerID]
	config := peer.Config
	e.mu.RUnlock()

	return CalculateLinkBudget(config, distanceM, false, 290.0), nil
}

// CalculateLinkBudget calcula orçamento de enlace completo
func CalculateLinkBudget(config LaserLinkConfig, distanceM float64, atmospheric bool, temperatureK float64) *LinkBudget {
	// 1. Perda de espaço livre (Friis)
	fsplDB := 20 * math.Log10(4*math.Pi*distanceM/config.Wavelength)

	// 2. Perda por pointing error
	pointingLossDB := 10 * math.Log10(
		math.Exp(-math.Pow(config.PointingErrorRad, 2)/
			(2*math.Pow(config.Wavelength/(math.Pi*config.ApertureTx), 2))),
	)

	// 3. Perdas atmosféricas
	atmosphericLossDB := 0.0
	if atmospheric {
		atmosphericLossDB = 0.2 * distanceM / 1000 // 0.2 dB/km simplificado
	}

	// 4. Ganho do receptor
	receiverGainDB := 10 * math.Log10(
		math.Pow(math.Pi*config.ApertureRx/config.Wavelength, 2),
	)

	// 5. Potência recebida
	txPowerDBm := 10*math.Log10(config.TxPower*1000) + 30 // W → mW → dBm
	receivedPowerDBm := txPowerDBm - fsplDB - pointingLossDB - atmosphericLossDB + receiverGainDB

	// 6. Ruído térmico
	const Boltzmann = 1.380649e-23
	bandwidthHz := config.SymbolRateBaud * BitsPerSymbol(config.Modulation)
	noisePowerDBm := 10 * math.Log10(Boltzmann*temperatureK*bandwidthHz*1000)

	// 7. SNR e BER
	snrDB := receivedPowerDBm - noisePowerDBm
	ber := EstimateBER(snrDB, config.Modulation)

	// 8. Margem de link
	requiredSNR := RequiredSNR(config.Modulation, MaxBER)
	linkMarginDB := snrDB - requiredSNR

	return &LinkBudget{
		FreeSpaceLossDB:   fsplDB,
		PointingLossDB:    pointingLossDB,
		AtmosphericLossDB: atmosphericLossDB,
		ReceiverGainDB:    receiverGainDB,
		ReceivedPowerDBm:  receivedPowerDBm,
		NoisePowerDBm:     noisePowerDBm,
		SNRdB:             snrDB,
		BEREstimate:       ber,
		LinkMarginDB:      linkMarginDB,
		Achievable:        snrDB >= MinSNRdB && ber <= MaxBER,
	}
}

// BitsPerSymbol retorna bits por símbolo baseado na modulação
func BitsPerSymbol(modulation string) float64 {
	switch modulation {
	case "OOK", "BPSK":
		return 1.0
	case "QPSK":
		return 2.0
	case "DP-QPSK", "QAM-16":
		return 4.0
	case "QAM-64":
		return 6.0
	case "QAM-256":
		return 8.0
	default:
		return 1.0
	}
}

// EstimateBER estima BER baseado em SNR e modulação
func EstimateBER(snrDB float64, modulation string) float64 {
	snrLinear := math.Pow(10, snrDB/10)

	var ber float64
	switch modulation {
	case "OOK", "BPSK", "QPSK":
		ber = 0.5 * math.Exp(-snrLinear/2)
	case "DP-QPSK":
		ber = math.Exp(-snrLinear / 4)
	case "QAM-16":
		ber = 0.75 * math.Exp(-snrLinear/10)
	case "QAM-64":
		ber = 0.875 * math.Exp(-snrLinear/21)
	case "QAM-256":
		// Aproximação para QAM-256
		M := 256.0
		arg := math.Sqrt(3 * snrLinear / (M - 1))
		if arg > 10 {
			ber = 0.5 * math.Exp(-arg*arg/2) / (arg * math.Sqrt(2*math.Pi))
		} else {
			// Aproximação da função erfc
			ber = 0.5 * math.Exp(-arg*arg/2)
		}
		ber *= (4 / math.Log2(M)) * (1 - 1/math.Sqrt(M))
	default:
		ber = 0.5
	}

	// Aplicar ganho de FEC (~6 dB)
	fecGainDB := 6.0
	berCorrected := 0.5 * math.Exp(-(math.Pow(10, snrDB/10)*math.Pow(10, fecGainDB/10))/2)

	return math.Min(0.5, math.Max(1e-15, berCorrected))
}

// RequiredSNR retorna SNR mínimo necessário para BER alvo
func RequiredSNR(modulation string, targetBER float64) float64 {
	requirements := map[string]float64{
		"OOK":     12.0,
		"BPSK":    12.0,
		"QPSK":    15.0,
		"DP-QPSK": 18.0,
		"QAM-16":  22.0,
		"QAM-64":  28.0,
		"QAM-256": 34.0,
	}
	if req, ok := requirements[modulation]; ok {
		return req
	}
	return 20.0
}

// InterlinkFrame frame do protocolo INTERLINK
type InterlinkFrame struct {
	Sequence        uint32
	Payload         []byte
	Timestamp       float64
	SourceNode      string
	DestNode        string
	Priority        uint8
	TTLHops         uint16
	CompressionFlag bool
}

// Serialize serializa frame para transmissão
func (f *InterlinkFrame) Serialize() []byte {
	// Header canônico: sync(8) + seq(4) + src(32) + dst(32) + ts(8) + prio(1) + ttl(2) + flags(1) = 88 bytes
	header := make([]byte, 88)
	binary.BigEndian.PutUint64(header[0:8], 0xA5A5A5A5A5A5A5A5) // Sync
	binary.BigEndian.PutUint32(header[8:12], f.Sequence)
	copy(header[12:44], f.SourceNode)
	copy(header[44:76], f.DestNode)
	binary.BigEndian.PutUint64(header[76:84], uint64(f.Timestamp*1e6)) // µs
	header[84] = f.Priority
	binary.BigEndian.PutUint16(header[85:87], f.TTLHops)
	if f.CompressionFlag {
		header[87] = 1
	}

	// Payload (comprimido se flag)
	payload := f.Payload
	if f.CompressionFlag && len(payload) > 256 {
		// Em produção: usar snappy/zstd
		// Aqui: simplificado
	}

	// CRC32
	crc := sha3.Sum256(append(header, payload...))
	frame := append(header, payload...)
	frame = append(frame, crc[:4]...) // CRC truncado para 32 bits

	return frame
}

// Deserialize desserializa frame recebido
func DeserializeInterlinkFrame(data []byte) (*InterlinkFrame, error) {
	if len(data) < 92 { // header(88) + crc(4) mínimo
		return nil, fmt.Errorf("frame too short")
	}

	// Verificar CRC
	expectedCRC := sha3.Sum256(data[:len(data)-4])
	receivedCRC := data[len(data)-4:]
	for i := 0; i < 4; i++ {
		if expectedCRC[i] != receivedCRC[i] {
			return nil, fmt.Errorf("CRC mismatch")
		}
	}

	// Verificar sync
	if binary.BigEndian.Uint64(data[0:8]) != 0xA5A5A5A5A5A5A5A5 {
		return nil, fmt.Errorf("invalid sync pattern")
	}

	frame := &InterlinkFrame{
		Sequence:        binary.BigEndian.Uint32(data[8:12]),
		SourceNode:      string(data[12:44]),
		DestNode:        string(data[44:76]),
		Timestamp:       float64(binary.BigEndian.Uint64(data[76:84])) / 1e6,
		Priority:        data[84],
		TTLHops:         binary.BigEndian.Uint16(data[85:87]),
		CompressionFlag: data[87] == 1,
		Payload:         data[88 : len(data)-4],
	}

	return frame, nil
}

// Transmit envia uma mensagem via enlace laser
func (e *LaserEngine) Transmit(msg *temporal.TemporalMessage, peerID string) error {
	e.mu.Lock()
	e.seqNum++
	seq := e.seqNum
	e.mu.Unlock()

	// Preparar frame
	payload, _ := json.Marshal(msg)
	frame := &InterlinkFrame{
		Sequence:   seq,
		Payload:    payload,
		Timestamp:  float64(time.Now().UnixNano()) / 1e9,
		SourceNode: e.nodeID,
		DestNode:   peerID,
		TTLHops:    1000,
	}

	// Avaliar enlace
	budget, err := e.EvaluateLink(peerID)
	if err != nil {
		return fmt.Errorf("evaluate link: %w", err)
	}
	if !budget.Achievable {
		return fmt.Errorf("link not achievable: SNR=%.1fdB, BER=%.2e", budget.SNRdB, budget.BEREstimate)
	}

	// Serializar e "transmitir" (simulado)
	raw := frame.Serialize()

	e.mu.Lock()
	e.stats.FramesSent++
	e.stats.BytesSent += uint64(len(raw))
	e.mu.Unlock()

	e.logger.Debug("Frame transmitted",
		zap.String("peer", peerID),
		zap.Uint32("seq", seq),
		zap.Int("size", len(raw)),
		zap.Float64("snr_db", budget.SNRdB),
	)

	return nil
}

// Stats retorna estatísticas do engine
func (e *LaserEngine) Stats() Stats {
	e.mu.RLock()
	defer e.mu.RUnlock()
	return e.stats
}
