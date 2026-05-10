package temporal

import (
	"crypto/sha3"
	"encoding/json"
	"fmt"
	"time"
)

// TemporalMessage representa uma mensagem no ledger temporal ARKHE
type TemporalMessage struct {
	ID              string            `json:"id" cbor:"1"`
	Content         json.RawMessage   `json:"content" cbor:"2"`
	SourceTimestamp float64           `json:"source_timestamp" cbor:"3"`
	TargetTimestamp float64           `json:"target_timestamp" cbor:"4"`
	SenderSeal      string            `json:"sender_seal" cbor:"5"`
	ReceiverSeal    string            `json:"receiver_seal" cbor:"6"`
	Metadata        map[string]string `json:"metadata,omitempty" cbor:"7,omitempty"`
}

// NewMessage cria uma nova mensagem com ID único
func NewMessage(content interface{}, sender, receiver string) (*TemporalMessage, error) {
	contentBytes, err := json.Marshal(content)
	if err != nil {
		return nil, fmt.Errorf("marshal content: %w", err)
	}

	return &TemporalMessage{
		ID:              fmt.Sprintf("msg-%d-%x", time.Now().UnixNano(), func() []byte { hash := sha3.Sum256(contentBytes); return hash[:8] }()),
		Content:         contentBytes,
		SourceTimestamp: float64(time.Now().UnixNano()) / 1e9,
		TargetTimestamp: float64(time.Now().UnixNano()) / 1e9,
		SenderSeal:      sender,
		ReceiverSeal:    receiver,
		Metadata:        make(map[string]string),
	}, nil
}

// Hash calcula SHA3-256 canônico da mensagem
func (m *TemporalMessage) Hash() [32]byte {
	// Serialização canônica para hash
	type canonical struct {
		ID              string            `json:"id"`
		Content         json.RawMessage   `json:"content"`
		SourceTimestamp float64           `json:"source_timestamp"`
		TargetTimestamp float64           `json:"target_timestamp"`
		SenderSeal      string            `json:"sender_seal"`
		ReceiverSeal    string            `json:"receiver_seal"`
		Metadata        map[string]string `json:"metadata"`
	}
	c := canonical{
		ID:              m.ID,
		Content:         m.Content,
		SourceTimestamp: m.SourceTimestamp,
		TargetTimestamp: m.TargetTimestamp,
		SenderSeal:      m.SenderSeal,
		ReceiverSeal:    m.ReceiverSeal,
		Metadata:        m.Metadata,
	}
	data, _ := json.Marshal(c) // Marshal canônico nunca falha para este struct
	return sha3.Sum256(data)
}

// TemporalDelta retorna Δt = target - source
func (m *TemporalMessage) TemporalDelta() float64 {
	return m.TargetTimestamp - m.SourceTimestamp
}

// IsRetrocausal verifica se a mensagem é retrocausal (Δt < 0)
func (m *TemporalMessage) IsRetrocausal() bool {
	return m.TemporalDelta() < 0
}

// Validate verifica integridade básica da mensagem
func (m *TemporalMessage) Validate() error {
	if m.ID == "" {
		return fmt.Errorf("message ID required")
	}
	if len(m.Content) == 0 {
		return fmt.Errorf("message content required")
	}
	if m.SenderSeal == "" || m.ReceiverSeal == "" {
		return fmt.Errorf("sender and receiver seals required")
	}
	return nil
}
