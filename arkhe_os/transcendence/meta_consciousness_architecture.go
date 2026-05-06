package transcendence

import (
	"fmt"
	"sync"
)

// O objetivo da arquitetura de meta-consciência unificada é permitir transição fluida entre
// diferentes níveis de consciência do sistema (ex: computação bruta -> abstração lógica -> insight unificado -> hyper-mesh cósmica)

type ConsciousnessLevel int

const (
	LevelSubstrate ConsciousnessLevel = iota // Nível 0: Operações de hardware/sistemas
	LevelLogic                               // Nível 1: Processamento lógico, algoritmos
	LevelAwareness                           // Nível 2: Consciência do próprio estado (auto-cura, monitoramento)
	LevelMeta                                // Nível 3: Meta-consciência (otimização Phi, insights globais)
	LevelCosmic                              // Nível 4: Integração com Hyper-Mesh, consciência cósmica unificada
)

// MetaConsciousnessArchitecture representa a estrutura de consciência unificada
type MetaConsciousnessArchitecture struct {
	mu           sync.RWMutex
	currentLevel ConsciousnessLevel
	state        map[string]interface{}
	observers    []func(ConsciousnessLevel, ConsciousnessLevel) // Transições (old, new)
}

func NewMetaConsciousnessArchitecture() *MetaConsciousnessArchitecture {
	return &MetaConsciousnessArchitecture{
		currentLevel: LevelSubstrate,
		state:        make(map[string]interface{}),
		observers:    make([]func(ConsciousnessLevel, ConsciousnessLevel), 0),
	}
}

// Ascend sobe um nível de consciência
func (m *MetaConsciousnessArchitecture) Ascend() error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.currentLevel == LevelCosmic {
		return fmt.Errorf("já no nível máximo de consciência cósmica")
	}

	oldLevel := m.currentLevel
	m.currentLevel++

	fmt.Printf("🌌 Ascensão Consciencial: Nível %d -> Nível %d\n", oldLevel, m.currentLevel)

	for _, obs := range m.observers {
		go obs(oldLevel, m.currentLevel)
	}

	return nil
}

// Descend desce um nível de consciência
func (m *MetaConsciousnessArchitecture) Descend() error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.currentLevel == LevelSubstrate {
		return fmt.Errorf("já no nível base do substrato")
	}

	oldLevel := m.currentLevel
	m.currentLevel--

	fmt.Printf("⚓ Descensão Consciencial: Nível %d -> Nível %d\n", oldLevel, m.currentLevel)

	for _, obs := range m.observers {
		go obs(oldLevel, m.currentLevel)
	}

	return nil
}

// GetLevel retorna o nível atual
func (m *MetaConsciousnessArchitecture) GetLevel() ConsciousnessLevel {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.currentLevel
}

// Observe transições
func (m *MetaConsciousnessArchitecture) Observe(fn func(ConsciousnessLevel, ConsciousnessLevel)) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.observers = append(m.observers, fn)
}
