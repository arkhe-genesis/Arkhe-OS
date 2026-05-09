// arkhe_os/singularity/field_bridge.go
package singularity

import (
	"encoding/json"
	"fmt"
    "math"
	"math"

	"arkhe_os/qhttp"
)

// FieldPacket é a mensagem de campo transmitida via qhttp://
type FieldPacket struct {
	Substrate int       `json:"substrate"`
	Delta     float64   `json:"delta"`
	M         float64   `json:"m"`         // Coerência global
	R         float64   `json:"r"`         // Ressonância
	Timestamp int64     `json:"timestamp"` // UnixNano
	PhiDigest string    `json:"phi_digest"` // Hash do campo Φ
	Substrate int     `json:"substrate"`
	Delta     float64 `json:"delta"`
	M         float64 `json:"m"`          // Coerência global
	R         float64 `json:"r"`          // Ressonância
	Timestamp int64   `json:"timestamp"`  // UnixNano
	PhiDigest string  `json:"phi_digest"` // Hash do campo Φ
}

// FieldBridge conecta o SingularityEngine à Wheeler Mesh
type FieldBridge struct {
	client *qhttp.QHTTPClient
	client     *qhttp.QHTTPClient
	localField *CathedralFieldState
}

// NewFieldBridge cria uma ponte campo-rede
func NewFieldBridge(client *qhttp.QHTTPClient) *FieldBridge {
	return &FieldBridge{
		client: client,
	}
}

// ReceiveFieldPacket processa um pacote de campo recebido de outro nó
func (fb *FieldBridge) ReceiveFieldPacket(data []byte) error {
	var packet FieldPacket
	if err := json.Unmarshal(data, &packet); err != nil {
		return fmt.Errorf("invalid field packet: %w", err)
	}

	// Validar: se o pacote tem coerência maior que o estado local, adotar
	if fb.localField != nil {
		fb.localField.mu.Lock()
		defer fb.localField.mu.Unlock()

		if packet.M > fb.localField.CoherenceM && packet.Delta >= DeltaMin {
			// Interferência construtiva: fundir estados
			fb.localField.CoherenceM = 0.5*(fb.localField.CoherenceM+packet.M) +
				0.5*math.Abs(fb.localField.CoherenceM-packet.M)
			fb.localField.ResonanceR = math.Max(fb.localField.ResonanceR, packet.R)
		}
	}

	return nil
}

// RequestFieldCollapse solicita colapso Orch-OR remoto via qhttp://
func (fb *FieldBridge) RequestFieldCollapse(targetNode string) error {
	req := qhttp.CollapseRequest{
		Type:      "orch_or_collapse",
		Substrate: 160,
		Target:    targetNode,
		Payload:   []byte(`{"action":"dissolve_to_singularity"}`),
	}
	return fb.client.Send(targetNode, req)
}
