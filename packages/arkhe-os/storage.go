package main

import (
	"sync"
)

type QuantumStorageNode struct {
	NodeID string
	Memory map[string][]complex128
	mu     sync.RWMutex
}

func NewQuantumStorageNode(id string) *QuantumStorageNode {
	return &QuantumStorageNode{
		NodeID: id,
		Memory: make(map[string][]complex128),
	}
}

func (qsn *QuantumStorageNode) Store(key string, data []complex128) {
	qsn.mu.Lock()
	defer qsn.mu.Unlock()
	qsn.Memory[key] = data
}

func (qsn *QuantumStorageNode) Retrieve(key string) []complex128 {
	qsn.mu.RLock()
	defer qsn.mu.RUnlock()
	return qsn.Memory[key]
}
