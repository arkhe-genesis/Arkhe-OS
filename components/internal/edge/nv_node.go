// internal/edge/nv_node.go
package edge

import (
	"context"
	"encoding/json"
	"math"
	"time"

	"github.com/nats-io/nats.go"
)

// Mocking nv driver for integration
type NVParams struct {
	Omega float64
	Delta float64
	Phi   float64
}

type NVDriver struct{}

func (d *NVDriver) EstimateMultiparameter() (*NVParams, error) {
	// Real world would use FPGA/AWG via SPI/Ethernet
	return &NVParams{Omega: 1.0, Delta: 0.5, Phi: 0.1}, nil
}

type KuramotoMessage struct {
	NodeID    string    `json:"node_id"`
	Phase     float64   `json:"phase"`
	Omega     float64   `json:"omega"`
	Timestamp int64     `json:"timestamp"`
}

type NVEdgeNode struct {
	ID       string
	nvDriver *NVDriver
	nc       *nats.Conn
	phase    float64
	omega    float64
}

func NewNVEdgeNode(id string, nc *nats.Conn) *NVEdgeNode {
	return &NVEdgeNode{
		ID:       id,
		nvDriver: &NVDriver{},
		nc:       nc,
	}
}

func (n *NVEdgeNode) Run(ctx context.Context) error {
	ticker := time.NewTicker(10 * time.Millisecond) // 100 Hz
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			// 1. Executa estimativa multiparâmetro no NV
			params, err := n.nvDriver.EstimateMultiparameter()
			if err != nil {
				continue
			}

			// 2. Converte para fase (mapeamento não-linear)
			n.phase = math.Atan2(params.Omega, params.Delta) + params.Phi
			n.omega = params.Omega // Frequência natural do oscilador

			// 3. Publica no cluster Kuramoto
			msg := KuramotoMessage{
				NodeID:    n.ID,
				Phase:     n.phase,
				Omega:     n.omega,
				Timestamp: time.Now().UnixNano(),
			}
			data, _ := json.Marshal(msg)
			if n.nc != nil {
				n.nc.Publish("kuramoto.local."+n.ID, data)
			}

		case <-ctx.Done():
			return nil
		}
	}
}
