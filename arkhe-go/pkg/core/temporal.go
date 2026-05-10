package core

import (
	"crypto/sha512"
	"encoding/json"
	"fmt"
	"time"

	"golang.org/x/exp/constraints"
)

// ============================================================================
// Tipos Fundamentais do ARKHE
// ============================================================================

// Address é a identidade de um nó no ARKHE.
type Address [32]byte

// NewAddress cria um Address a partir de uma string.
func NewAddress(s string) Address {
	h := sha512.Sum512_256([]byte(s))
	var a Address
	copy(a[:], h[:])
	return a
}

func (a Address) String() string {
	return fmt.Sprintf("%x", a[:8])
}

// TemporalIndex é o índice temporal de um evento (block height lógico).
type TemporalIndex uint64

// Timestamp é um instante no tempo ARKHE (nanossegundos desde epoch).
type Timestamp int64

// Now retorna o timestamp ARKHE atual.
func Now() Timestamp {
	return Timestamp(time.Now().UnixNano())
}

// ============================================================================
// Mensagem Temporal
// ============================================================================

// TemporalMessage é a unidade fundamental de informação no ARKHE.
type TemporalMessage struct {
	// Identidade
	ID          string     `json:"id"`
	Sender      Address    `json:"sender"`
	Receiver    Address    `json:"receiver"`

	// Temporal
	SourceTimestamp Timestamp `json:"source_ts"`
	TargetTimestamp Timestamp `json:"target_ts"`

	// Conteúdo
	Content   string            `json:"content"`   // Payload textual
	Payload   []byte            `json:"-"`         // Payload binário (não serializado)
	Metadata  map[string]string `json:"metadata,omitempty"`

	// Consistência (preenchido pelo Oracle)
	ConsistencyScore float64                 `json:"consistency_score"`
	ConsistencyReport map[string]interface{} `json:"consistency_report,omitempty"`
	ParadoxType      string                  `json:"paradox_type,omitempty"`

	// Assinatura
	Signature []byte `json:"signature,omitempty"`

	// ZK Proof
	ZKProof []byte `json:"zk_proof,omitempty"`

	// Cache interno
	hash      *Address
	sizeBytes int
}

// Hash calcula o hash da mensagem.
func (m *TemporalMessage) Hash() Address {
	if m.hash != nil {
		return *m.hash
	}
	data, _ := json.Marshal(m)
	h := sha512.Sum512_256(data)
	var a Address
	copy(a[:], h[:])
	m.hash = &a
	return a
}

// Size retorna o tamanho estimado da mensagem em bytes.
func (m *TemporalMessage) Size() int {
	if m.sizeBytes > 0 {
		return m.sizeBytes
	}
	data, _ := json.Marshal(m)
	m.sizeBytes = len(data) + len(m.Payload)
	return m.sizeBytes
}

// IsTemporallyValid verifica se a mensagem é temporalmente válida.
func (m *TemporalMessage) IsTemporallyValid(now Timestamp) bool {
	return m.SourceTimestamp <= now && m.TargetTimestamp >= now
}

// CausalPrecedes verifica se esta mensagem precede causalmente outra.
func (m *TemporalMessage) CausalPrecedes(other *TemporalMessage) bool {
	return m.TargetTimestamp <= other.SourceTimestamp
}

// String implementa Stringer.
func (m *TemporalMessage) String() string {
	return fmt.Sprintf("MSG[%s]: %s → %s @[%d→%d] score=%.4f",
		m.ID, m.Sender, m.Receiver,
		m.SourceTimestamp, m.TargetTimestamp,
		m.ConsistencyScore)
}

// ============================================================================
// Bloco Temporal
// ============================================================================

// TemporalBlock é um bloco na cadeia temporal do ARKHE.
type TemporalBlock struct {
	Index        TemporalIndex   `json:"index"`
	PrevHash     Address         `json:"prev_hash"`
	Timestamp    Timestamp       `json:"timestamp"`
	Messages     []*TemporalMessage `json:"messages"`
	StateRoot    Address         `json:"state_root"`
	OracleRoot   Address         `json:"oracle_root"`
	ValidatorSig []byte          `json:"validator_sig"`
	Height       TemporalIndex   `json:"height"`

	// Cache
	hash *Address
	size int
}

// Hash calcula o hash do bloco.
func (b *TemporalBlock) Hash() Address {
	if b.hash != nil {
		return *b.hash
	}
	data, _ := json.Marshal(struct {
		Index     TemporalIndex   `json:"index"`
		PrevHash  Address         `json:"prev_hash"`
		Timestamp Timestamp       `json:"timestamp"`
		StateRoot Address         `json:"state_root"`
		OracleRoot Address        `json:"oracle_root"`
		MsgHashes []Address       `json:"msg_hashes"`
	}{
		Index:     b.Index,
		PrevHash:  b.PrevHash,
		Timestamp: b.Timestamp,
		StateRoot: b.StateRoot,
		OracleRoot: b.OracleRoot,
		MsgHashes: b.messageHashes(),
	})
	h := sha512.Sum512_256(data)
	var a Address
	copy(a[:], h[:])
	b.hash = &a
	return a
}

func (b *TemporalBlock) messageHashes() []Address {
	hashes := make([]Address, len(b.Messages))
	for i, msg := range b.Messages {
		hashes[i] = msg.Hash()
	}
	return hashes
}

// Size retorna o tamanho total do bloco.
func (b *TemporalBlock) Size() int {
	if b.size > 0 {
		return b.size
	}
	s := 8 + 32 + 8 + 8 + 32 + len(b.ValidatorSig) // cabeçalho fixo
	for _, msg := range b.Messages {
		s += msg.Size()
	}
	b.size = s
	return s
}

// MessageCount retorna o número de mensagens no bloco.
func (b *TemporalBlock) MessageCount() int {
	return len(b.Messages)
}

// ============================================================================
// Parâmetros de Rede
// ============================================================================

const (
	// BlockSizeMax é o tamanho máximo de um bloco em bytes.
	BlockSizeMax = 4 * 1024 * 1024 // 4 MB

	// BlockInterval é o intervalo alvo entre blocos (nanossegundos).
	BlockInterval = 10 * 1e9 // 10 segundos

	// MaxMessagesPerBlock é o número máximo de mensagens por bloco.
	MaxMessagesPerBlock = 8192

	// ConsistencyThreshold é o threshold mínimo de consistência.
	ConsistencyThreshold = 0.85

	// ParadoxScore é o score abaixo do qual uma mensagem é considerada paradoxal.
	ParadoxScore = 0.30
)

// Configuração da rede.
type NetworkConfig struct {
	BlockInterval     Timestamp  `json:"block_interval"`
	BlockSizeMax      int        `json:"block_size_max"`
	MaxMessagesPerBlock int      `json:"max_messages_per_block"`
	ConsistencyThreshold float64 `json:"consistency_threshold"`
	ParanoidMode      bool       `json:"paranoid_mode"` // todos os checks, nenhum atalho
}

// DefaultConfig retorna a configuração padrão.
func DefaultConfig() *NetworkConfig {
	return &NetworkConfig{
		BlockInterval:        BlockInterval,
		BlockSizeMax:         BlockSizeMax,
		MaxMessagesPerBlock:  MaxMessagesPerBlock,
		ConsistencyThreshold: ConsistencyThreshold,
		ParanoidMode:         false,
	}
}

// Validate valida a configuração.
func (c *NetworkConfig) Validate() error {
	if c.BlockInterval < 1e6 { // mínimo 1ms
		return fmt.Errorf("block interval muito curto: %dns", c.BlockInterval)
	}
	if c.BlockSizeMax < 1024 {
		return fmt.Errorf("block size max muito pequeno: %d bytes", c.BlockSizeMax)
	}
	if c.MaxMessagesPerBlock <= 0 {
		return fmt.Errorf("max messages per block deve ser > 0")
	}
	if c.ConsistencyThreshold < 0 || c.ConsistencyThreshold > 1 {
		return fmt.Errorf("consistency threshold fora do range [0,1]: %f", c.ConsistencyThreshold)
	}
	return nil
}

// ============================================================================
// Utility Functions
// ============================================================================

// Clamp limita um valor entre min e max.
func Clamp[T constraints.Ordered](v, min, max T) T {
	if v < min {
		return min
	}
	if v > max {
		return max
	}
	return v
}

// Lerp interpola linearmente entre a e b pelo fator t.
func Lerp(a, b, t float64) float64 {
	return a + (b-a)*t
}

// Normalize normaliza um valor para o range [0, 1].
func Normalize(v, min, max float64) float64 {
	if max == min {
		return 0
	}
	return Clamp((v-min)/(max-min), 0, 1)
}
