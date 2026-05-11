// cmd/akasha/main.go
package main

import (
	"fmt"
	"net/http"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
)

// Representa um nó Cooper no cluster
type CooperNode struct {
	ID      string `json:"id"`
	Address string `json:"address"` // IP/Port
	Inbox   chan Message
	Outbox  chan Message
}

// Mensagem trocada entre nós (ex: Heartbeat, Block Proposal)
type Message struct {
	From      string `json:"from"`
	Type      string `json:"type"` // "heartbeat", "new_block", "verify_block"
	Payload   []byte `json:"payload"`
	Timestamp int64  `json:"timestamp"`
}

// Banco de nós Cooper
var (
	nodes      = make(map[string]*CooperNode)
	nodesMutex sync.RWMutex
	messageBus = make(chan Message, 1024) // Canal de broadcast
)

func main() {
	r := gin.Default()

	// Inicializa 3 nós Cooper para demo
	registerCooperNode("node-alpha", "localhost:8081")
	registerCooperNode("node-beta", "localhost:8082")
	registerCooperNode("node-gamma", "localhost:8083")

	// Inicia o Gerenciador de Broadcast
	go broadcastManager()

	// Inicia os handlers da API Akasha
	r.POST("/akasha/commit", handleAkashaCommit)

	r.Run(":8080")
}

func registerCooperNode(id, addr string) {
	node := &CooperNode{
		ID:      id,
		Address: addr,
		Inbox:   make(chan Message, 100),
		Outbox:  make(chan Message, 100),
	}

	nodesMutex.Lock()
	nodes[id] = node
	nodesMutex.Unlock()

	// Inicia o loop de escuta do nó
	go nodeLoop(node)
	fmt.Printf("[SISTEMA] Nó %s registrado em %s\n", id, addr)
}

func nodeLoop(node *CooperNode) {
	for msg := range node.Inbox {
		fmt.Printf("[%s] Recebido de %s: %s\n", node.ID, msg.From, msg.Type)
		// Processa a mensagem (ex: validar bloco, atualizar estado local)
	}
}

// Broadcast Manager: distribui mensagens para todos os nós
func broadcastManager() {
	for msg := range messageBus {
		nodesMutex.RLock()

		for _, node := range nodes {
			select {
			case node.Inbox <- msg:
				// Envio não-bloqueante.
			default:
				// Nó ocupado, descarta para evitar deadlocks
				continue
			}
		}
		nodesMutex.RUnlock()
	}
}

// API Gateway: Recebe requisições HTTP e as converte em mensagens internas
func handleAkashaCommit(c *gin.Context) {
	var req struct {
		BlockHash string `json:"block_hash"`
		Signature string `json:"signature"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(400, gin.H{"error": err.Error()})
		return
	}

	// Cria mensagem de consenso
	msg := Message{
		From:      "api-gateway",
		Type:      "verify_block",
		Payload:   []byte(fmt.Sprintf("hash:%s", req.BlockHash)),
		Timestamp: time.Now().Unix(),
	}

	// Broadcast para o cluster
	messageBus <- msg

	// Aguarda validação (simulada)
	time.Sleep(50 * time.Millisecond) // Espera 50ms para os Cooper Nodes processarem

	c.JSON(200, gin.H{
		"status": "submitted_to_cluster",
		"nodes_contacted": len(nodes),
	})
}
