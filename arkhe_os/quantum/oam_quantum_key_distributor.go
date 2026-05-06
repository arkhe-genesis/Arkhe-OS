// arkhe_os/quantum/oam_quantum_key_distributor.go
package quantum

import (
	crand "crypto/rand"
	"crypto/sha256"
	"math/rand"

	"fmt"
	"math"

	"sync"
	"time"

	"github.com/arkhe-os/arkhe/photonic"
	"golang.org/x/crypto/hkdf"
)

// ─── CONSTANTES DE QKD OAM ────────────────────────────────────────

const (
	// QuditDimension dimensão do espaço de qudits OAM (d = 2L+1)
	QuditDimension = 7 // ℓ = -3, -2, -1, 0, +1, +2, +3

	// BB84Bases número de bases mutuamente não-comutativas
	BB84Bases = 2 // Base Z (computacional) e Base X (Fourier)

	// QBERThreshold threshold de erro quântico para abortar protocolo
	QBERThreshold = 0.11 // ~11% para d=7

	// PrivacyAmplificationFactor fator de compressão para amplificação de privacidade
	PrivacyAmplificationFactor = 0.5

	// MaxQKDSessionDuration duração máxima de sessão QKD
	MaxQKDSessionDuration = 3600 * time.Second
)

// ─── TIPOS FUNDAMENTAIS ─────────────────────────────────────────

// OAMQudit representa um qudit codificado em modo OAM
type OAMQudit struct {
	Charge         int        // carga topológica ℓ ∈ [-L, +L]
	Amplitude      complex128 // coeficiente c_ℓ da superposição
	Phase          float64    // fase global do estado
	Basis          string     // "Z" (computacional) ou "X" (Fourier)
	Timestamp      time.Time
	EntanglementID string // ID para pares emaranhados
}

// OAMQKDSession representa uma sessão de distribuição de chaves quânticas
type OAMQKDSession struct {
	SessionID       string
	LocalNodeID     string
	RemoteNodeID    string
	Protocol        string // "BB84-d", "E91-OAM", etc.
	QuditDimension  int
	TotalQuditsSent int
	TotalQuditsRecv int
	RawKeyBits      []byte
	SiftedKeyBits   []byte
	EstimatedQBER   float64
	FinalKeyBits    []byte
	Status          string // initializing, sifting, error_correction, privacy_amplification, complete, aborted
	StartTime       time.Time
	EndTime         time.Time
	mu              sync.RWMutex
}

// OAMQuantumKeyDistributor implementa protocolo QKD usando qudits OAM
type OAMQuantumKeyDistributor struct {
	localNodeID    string
	transceiver    *photonic.OAMTransceiver
	sessions       map[string]*OAMQKDSession
	activeSessions map[string]bool
	mu             sync.RWMutex
	metrics        QKDMetrics
	config         QKDConfig
	// Callbacks para notificação de eventos QKD
	keyGeneratedCallbacks []func(sessionID string, keyBits []byte)
}

// QKDConfig contém configuração para distribuição de chaves quânticas
type QKDConfig struct {
	Protocol             string  // "BB84-d", "E91-OAM"
	QuditDimension       int     // d = 2L+1
	ErrorCorrectionCode  string  // "Cascade", "LDPC", "Winnow"
	PrivacyAmplification bool    // Habilitar amplificação de privacidade
	QBERThreshold        float64 // Threshold para abortar sessão
	MaxSessionDuration   time.Duration
	MinKeyRate           float64 // bits/s mínimo para considerar sessão válida
}

// QKDMetrics contém métricas de distribuição de chaves quânticas
type QKDMetrics struct {
	SessionsCompleted    int64   `json:"sessions_completed"`
	SessionsAborted      int64   `json:"sessions_aborted"`
	TotalRawBits         int64   `json:"total_raw_bits"`
	TotalFinalBits       int64   `json:"total_final_bits"`
	AvgQBER              float64 `json:"avg_qber"`
	AvgKeyRate           float64 `json:"avg_key_rate_bps"`
	EntanglementFidelity float64 `json:"entanglement_fidelity"`
}

// ─── CONSTRUTORES ───────────────────────────────────────────────

// NewOAMQuantumKeyDistributor cria novo distribuidor de chaves quânticas OAM
func NewOAMQuantumKeyDistributor(
	localNodeID string,
	transceiver *photonic.OAMTransceiver,
	config QKDConfig,
) *OAMQuantumKeyDistributor {
	if config.QuditDimension == 0 {
		config.QuditDimension = QuditDimension
	}
	if config.QBERThreshold == 0 {
		config.QBERThreshold = QBERThreshold
	}
	if config.MaxSessionDuration == 0 {
		config.MaxSessionDuration = MaxQKDSessionDuration
	}

	return &OAMQuantumKeyDistributor{
		localNodeID:    localNodeID,
		transceiver:    transceiver,
		sessions:       make(map[string]*OAMQKDSession),
		activeSessions: make(map[string]bool),
		config:         config,
	}
}

// ─── OPERAÇÕES DE QKD OAM ───────────────────────────────────────

// StartQKDSession inicia nova sessão de distribuição de chaves quânticas
func (qkd *OAMQuantumKeyDistributor) StartQKDSession(
	remoteNodeID string,
	protocol string,
) (*OAMQKDSession, error) {
	qkd.mu.Lock()
	defer qkd.mu.Unlock()

	sessionID := fmt.Sprintf("qkd_%s_%s_%d",
		qkd.localNodeID[:8],
		remoteNodeID[:8],
		time.Now().UnixNano(),
	)

	session := &OAMQKDSession{
		SessionID:      sessionID,
		LocalNodeID:    qkd.localNodeID,
		RemoteNodeID:   remoteNodeID,
		Protocol:       protocol,
		QuditDimension: qkd.config.QuditDimension,
		Status:         "initializing",
		StartTime:      time.Now(),
	}

	qkd.sessions[sessionID] = session
	qkd.activeSessions[sessionID] = true

	// Iniciar fase de preparação em background
	go qkd.runQKDProtocol(session)

	return session, nil
}

// runQKDProtocol executa protocolo QKD completo em background
func (qkd *OAMQuantumKeyDistributor) runQKDProtocol(session *OAMQKDSession) {
	defer func() {
		qkd.mu.Lock()
		delete(qkd.activeSessions, session.SessionID)
		qkd.mu.Unlock()
	}()

	// Fase 1: Preparação e envio de qudits
	if err := qkd.prepareAndSendQudits(session); err != nil {
		qkd.abortSession(session, fmt.Sprintf("preparation failed: %v", err))
		return
	}

	// Fase 2: Sifting (peneiramento de bases)
	if err := qkd.performSifting(session); err != nil {
		qkd.abortSession(session, fmt.Sprintf("sifting failed: %v", err))
		return
	}

	// Fase 3: Estimação de QBER
	qber := qkd.estimateQBER(session)
	session.mu.Lock()
	session.EstimatedQBER = qber
	session.mu.Unlock()

	if qber > qkd.config.QBERThreshold {
		qkd.abortSession(session, fmt.Sprintf("QBER %.3f > threshold %.3f", qber, qkd.config.QBERThreshold))
		return
	}

	// Fase 4: Correção de erros
	if err := qkd.performErrorCorrection(session); err != nil {
		qkd.abortSession(session, fmt.Sprintf("error correction failed: %v", err))
		return
	}

	// Fase 5: Amplificação de privacidade (se habilitado)
	if qkd.config.PrivacyAmplification {
		if err := qkd.performPrivacyAmplification(session); err != nil {
			qkd.abortSession(session, fmt.Sprintf("privacy amplification failed: %v", err))
			return
		}
	}

	// Fase 6: Finalização
	session.mu.Lock()
	session.Status = "complete"
	session.EndTime = time.Now()
	finalKey := make([]byte, len(session.FinalKeyBits))
	copy(finalKey, session.FinalKeyBits)
	session.mu.Unlock()

	// Atualizar métricas
	qkd.updateMetrics(session, true)

	// Notificar callbacks
	for _, callback := range qkd.keyGeneratedCallbacks {
		callback(session.SessionID, finalKey)
	}

	// Logar conclusão
	duration := session.EndTime.Sub(session.StartTime).Seconds()
	keyRate := float64(len(finalKey)*8) / duration
	fmt.Printf("✅ QKD session complete: %s, key=%d bits, rate=%.2f bps, QBER=%.3f\n",
		session.SessionID, len(finalKey)*8, keyRate, session.EstimatedQBER)
}

// prepareAndSendQudits prepara e envia sequência de qudits para QKD
func (qkd *OAMQuantumKeyDistributor) prepareAndSendQudits(session *OAMQKDSession) error {
	session.mu.Lock()
	session.Status = "sending"
	session.mu.Unlock()

	// Número de qudits a enviar (ajustável baseado em taxa alvo)
	numQudits := 10000 // 10k qudits para estatística suficiente

	for i := 0; i < numQudits; i++ {
		// Escolher base aleatória (Z ou X)
		basis := "Z"
		if rand.Intn(2) == 1 {
			basis = "X"
		}

		// Escolher valor aleatório dentro da dimensão do qudit
		value := rand.Intn(session.QuditDimension)
		charge := value - session.QuditDimension/2 // mapear para ℓ ∈ [-L, +L]

		// Criar qudit
		qudit := OAMQudit{
			Charge:    charge,
			Amplitude: complex(1.0, 0.0),
			Phase:     0.0,
			Basis:     basis,
			Timestamp: time.Now(),
		}

		// Se base X, aplicar transformada de Fourier discreta
		if basis == "X" {
			qudit = qkd.applyFourierTransform(qudit, session.QuditDimension)
		}

		// Codificar qudit em símbolo OAM e enviar
		// (simplificação: em produção, usar hardware quântico real)
		if err := qkd.sendOAMQudit(session, qudit); err != nil {
			return fmt.Errorf("failed to send qudit %d: %w", i, err)
		}

		session.mu.Lock()
		session.TotalQuditsSent++
		session.mu.Unlock()

		// Pequeno delay para simular taxa de transmissão realista
		time.Sleep(10 * time.Microsecond)
	}

	return nil
}

// sendOAMQudit codifica qudit em feixe OAM e transmite
func (qkd *OAMQuantumKeyDistributor) sendOAMQudit(session *OAMQKDSession, qudit OAMQudit) error {
	// Mapear qudit para símbolo OAM (simplificação)
	// Em produção: usar modulador espacial de luz (SLM) para gerar modo ℓ exato

	// Codificar valor e base em bits clássicos para sincronização
	metaBits := []byte{
		byte(qudit.Charge + session.QuditDimension/2), // valor em [0, d-1]
		byte(map[bool]byte{true: 1, false: 0}[qudit.Basis == "X"]),
	}

	// Criar símbolo OAM com metadados
	symbol := photonic.OAMSymbol{
		Mode:      photonic.NewOAMMode(qudit.Charge, 10), // canal k=10
		SymbolIQ:  complex(float64(metaBits[0])/255.0, float64(metaBits[1])/255.0),
		Timestamp: float64(qudit.Timestamp.UnixNano()) / 1e9,
	}

	// Enviar via transceiver OAM
	beam := qkd.transceiver.GenerateCompositeBeam([]photonic.OAMSymbol{symbol})
	return qkd.transceiver.TransmitBeam(beam)
}

// applyFourierTransform aplica transformada de Fourier discreta para base X
func (qkd *OAMQuantumKeyDistributor) applyFourierTransform(qudit OAMQudit, d int) OAMQudit {
	// Transformada de Fourier discreta: |m̃⟩ = (1/√d) Σ_ℓ e^(2πiℓm/d) |ℓ⟩
	// Para qudit puro |ℓ₀⟩, a transformada resulta em superposição uniforme com fases

	// Simplificação: retornar qudit com fase modificada para representar base X
	m := qudit.Charge + d/2 // mapear ℓ para índice m ∈ [0, d-1]
	phase := 2 * math.Pi * float64(qudit.Charge*m) / float64(d)

	return OAMQudit{
		Charge:    qudit.Charge,
		Amplitude: complex(1.0/math.Sqrt(float64(d)), 0.0),
		Phase:     phase,
		Basis:     "X",
		Timestamp: qudit.Timestamp,
	}
}

// performSifting executa peneiramento de bases entre Alice e Bob
func (qkd *OAMQuantumKeyDistributor) performSifting(session *OAMQKDSession) error {
	session.mu.Lock()
	session.Status = "sifting"
	session.mu.Unlock()

	// Em produção: trocar bases via canal clássico autenticado
	// Aqui: simular sifting com correlação perfeita (canal ideal)

	session.mu.Lock()
	defer session.mu.Unlock()

	// Manter apenas qudits onde bases coincidiram (50% em média)
	// Simplificação: assumir que metade dos qudits são mantidos
	keptFraction := 0.5
	session.TotalQuditsRecv = int(float64(session.TotalQuditsSent) * keptFraction)

	// Gerar chave bruta simulada
	rawKeyBits := make([]byte, session.TotalQuditsRecv/4) // 2 bits por qudit para d=7
	crand.Read(rawKeyBits)
	session.RawKeyBits = rawKeyBits

	return nil
}

// estimateQBER estima taxa de erro quântico a partir de subconjunto público
func (qkd *OAMQuantumKeyDistributor) estimateQBER(session *OAMQKDSession) float64 {
	// Em produção: revelar subconjunto público da chave para estimar erros
	// Aqui: simular QBER baseado em parâmetros do enlace

	// QBER simulado: função da distância, SNR, e fidelidade do transceiver
	status := qkd.transceiver.GetTransceiverStatus()
	snr := status["snr_per_mode_dB"].(float64)

	// Modelo simplificado de QBER
	qber := 0.01 + 0.05*math.Exp(-snr/10) // QBER base + decaimento com SNR

	// Adicionar ruído aleatório realista
	qber += (rand.Float64() - 0.5) * 0.02

	return math.Max(0.0, math.Min(1.0, qber))
}

// performErrorCorrection executa correção de erros na chave peneirada
func (qkd *OAMQuantumKeyDistributor) performErrorCorrection(session *OAMQKDSession) error {
	session.mu.Lock()
	session.Status = "error_correction"
	session.mu.Unlock()

	// Em produção: usar protocolo Cascade, LDPC ou Winnow
	// Aqui: simular correção perfeita com overhead conhecido

	// Overhead de correção de erros (típico: 1.1-1.3x)
	overhead := 1.15
	session.SiftedKeyBits = session.RawKeyBits[:len(session.RawKeyBits)/int(overhead)]

	return nil
}

// performPrivacyAmplification executa amplificação de privacidade via hashing
func (qkd *OAMQuantumKeyDistributor) performPrivacyAmplification(session *OAMQKDSession) error {
	session.mu.Lock()
	session.Status = "privacy_amplification"
	session.mu.Unlock()

	// Amplificação de privacidade via HKDF (HMAC-based Key Derivation Function)
	seed := sha256.Sum256([]byte(session.SessionID + time.Now().String()))
	hkdf := hkdf.New(sha256.New, session.SiftedKeyBits, seed[:], []byte("arkhe-qkd-privacy"))

	// Comprimir chave por fator de amplificação
	finalLen := int(float64(len(session.SiftedKeyBits)) * PrivacyAmplificationFactor)
	session.FinalKeyBits = make([]byte, finalLen)
	_, err := hkdf.Read(session.FinalKeyBits)

	return err
}

// abortSession aborta sessão QKD com motivo registrado
func (qkd *OAMQuantumKeyDistributor) abortSession(session *OAMQKDSession, reason string) {
	session.mu.Lock()
	session.Status = "aborted"
	session.EndTime = time.Now()
	session.mu.Unlock()

	qkd.updateMetrics(session, false)
	fmt.Printf("⚠️ QKD session aborted: %s — %s\n", session.SessionID, reason)
}

// updateMetrics atualiza métricas de QKD após conclusão de sessão
func (qkd *OAMQuantumKeyDistributor) updateMetrics(session *OAMQKDSession, success bool) {
	qkd.mu.Lock()
	defer qkd.mu.Unlock()

	if success {
		qkd.metrics.SessionsCompleted++
		qkd.metrics.TotalFinalBits += int64(len(session.FinalKeyBits) * 8)
	} else {
		qkd.metrics.SessionsAborted++
	}

	qkd.metrics.TotalRawBits += int64(len(session.RawKeyBits) * 8)
	qkd.metrics.AvgQBER = qkd.metrics.AvgQBER*0.99 + session.EstimatedQBER*0.01

	if session.EndTime.After(session.StartTime) {
		duration := session.EndTime.Sub(session.StartTime).Seconds()
		if duration > 0 && success {
			keyRate := float64(len(session.FinalKeyBits)*8) / duration
			qkd.metrics.AvgKeyRate = qkd.metrics.AvgKeyRate*0.99 + keyRate*0.01
		}
	}
}

// RegisterKeyGeneratedCallback registra callback para chaves geradas
func (qkd *OAMQuantumKeyDistributor) RegisterKeyGeneratedCallback(callback func(string, []byte)) {
	qkd.keyGeneratedCallbacks = append(qkd.keyGeneratedCallbacks, callback)
}

// GetQKDMetrics retorna métricas consolidadas de QKD
func (qkd *OAMQuantumKeyDistributor) GetQKDMetrics() QKDMetrics {
	qkd.mu.RLock()
	defer qkd.mu.RUnlock()
	return qkd.metrics
}

// GetActiveSessions retorna sessões QKD ativas
func (qkd *OAMQuantumKeyDistributor) GetActiveSessions() []*OAMQKDSession {
	qkd.mu.RLock()
	defer qkd.mu.RUnlock()

	sessions := make([]*OAMQKDSession, 0, len(qkd.activeSessions))
	for id := range qkd.activeSessions {
		if session, ok := qkd.sessions[id]; ok {
			sessions = append(sessions, session)
		}
	}
	return sessions
}
