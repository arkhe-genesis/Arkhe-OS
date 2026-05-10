package core

import (
	"errors"
	"fmt"
	"sync"
)

// ============================================================================
// Temporal Hash Chain
// ============================================================================

var (
	ErrBlockExists      = errors.New("bloco já existe")
	ErrBlockNotFound    = errors.New("bloco não encontrado")
	ErrOrphanBlock      = errors.New("bloco órfão (prev_hash não encontrado)")
	ErrHashMismatch     = errors.New("hash do bloco não confere")
	ErrChainReorg       = errors.New("reorganização de cadeia detectada")
	ErrTimestampInvalid = errors.New("timestamp inválido (fora de ordem)")
)

// TemporalHashChain é a cadeia temporal de blocos do ARKHE.
type TemporalHashChain struct {
	mu      sync.RWMutex
	blocks  map[TemporalIndex]*TemporalBlock // index → block
	hashes  map[Address]TemporalIndex        // block hash → index
	heights map[Address]TemporalIndex        // state root → height (para forks)

	// Gerenciamento de forks
	heads        []Address              // todas as cabeças (uma por fork)
	longestChain []TemporalIndex        // índices da chain mais longa

	genesis *TemporalBlock
	length  uint64
}

// NewTemporalHashChain cria uma nova cadeia temporal com bloco gênesis.
func NewTemporalHashChain(genesis *TemporalBlock) (*TemporalHashChain, error) {
	if genesis.Index != 0 {
		return nil, fmt.Errorf("bloco gênesis deve ter index 0, tem %d", genesis.Index)
	}

	chain := &TemporalHashChain{
		blocks:  make(map[TemporalIndex]*TemporalBlock),
		hashes:  make(map[Address]TemporalIndex),
		heights: make(map[Address]TemporalIndex),
		genesis: genesis,
		length:  1,
	}

	genesisHash := genesis.Hash()
	chain.blocks[0] = genesis
	chain.hashes[genesisHash] = 0
	chain.heads = append(chain.heads, genesisHash)
	chain.longestChain = []TemporalIndex{0}

	return chain, nil
}

// Append adiciona um novo bloco à cadeia.
func (c *TemporalHashChain) Append(block *TemporalBlock) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	// Validação básica
	if block == nil {
		return errors.New("bloco nulo")
	}

	if block.Index == 0 {
		return errors.New("não é possível adicionar bloco gênesis")
	}

	// Verificar se o bloco já existe
	if _, exists := c.hashes[block.Hash()]; exists {
		return ErrBlockExists
	}

	// Verificar bloco pai
	parentBlock, exists := c.blocks[block.Index-1]
	if !exists {
		return ErrOrphanBlock
	}

	// Verificar hash do pai
	parentHash := parentBlock.Hash()
	if block.PrevHash != parentHash {
		return ErrHashMismatch
	}

	// Verificar timestamp (causalidade)
	if block.Timestamp <= parentBlock.Timestamp {
		return ErrTimestampInvalid
	}

	// Bloco válido — adicionar
	blockHash := block.Hash()
	c.blocks[block.Index] = block
	c.hashes[blockHash] = block.Index

	// Atualizar state root height
	if block.Height > 0 {
		c.heights[block.StateRoot] = block.Index
	}

	// Atualizar cabeças
	c.updateHeads(blockHash, parentHash)

	// Atualizar chain mais longa
	c.updateLongestChain(block.Index)

	c.length++

	return nil
}

// Get retorna o bloco pelo índice.
func (c *TemporalHashChain) Get(index TemporalIndex) (*TemporalBlock, error) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	block, exists := c.blocks[index]
	if !exists {
		return nil, ErrBlockNotFound
	}
	return block, nil
}

// GetByHash retorna o bloco pelo hash.
func (c *TemporalHashChain) GetByHash(hash Address) (*TemporalBlock, error) {
	c.mu.RLock()
	defer c.mu.RUnlock()

	index, exists := c.hashes[hash]
	if !exists {
		return nil, ErrBlockNotFound
	}
	return c.blocks[index], nil
}

// Head retorna o bloco mais recente da chain mais longa.
func (c *TemporalHashChain) Head() *TemporalBlock {
	c.mu.RLock()
	defer c.mu.RUnlock()

	if len(c.longestChain) == 0 {
		return nil
	}
	return c.blocks[c.longestChain[len(c.longestChain)-1]]
}

// Length retorna o comprimento da chain mais longa.
func (c *TemporalHashChain) Length() uint64 {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.length
}

// ForkExists verifica se existe um fork ativo a partir de um dado bloco.
func (c *TemporalHashChain) ForkExists(since TemporalIndex) bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return len(c.heads) > 1
}

// GetForks retorna todos os forks ativos.
func (c *TemporalHashChain) GetForks() [][]TemporalIndex {
	c.mu.RLock()
	defer c.mu.RUnlock()

	forks := make([][]TemporalIndex, 0, len(c.heads))
	for _, head := range c.heads {
		if headIndex, ok := c.hashes[head]; ok {
			// Reconstruir fork até a divergência
			fork := c.reconstructFork(headIndex)
			forks = append(forks, fork)
		}
	}
	return forks
}

func (c *TemporalHashChain) updateHeads(newHead, oldHead Address) {
	for i, h := range c.heads {
		if h == oldHead {
			c.heads = append(c.heads[:i], c.heads[i+1:]...)
			break
		}
	}
	c.heads = append(c.heads, newHead)
}

func (c *TemporalHashChain) updateLongestChain(newIndex TemporalIndex) {
	if newIndex > c.longestChain[len(c.longestChain)-1] {
		c.longestChain = append(c.longestChain, newIndex)
	}
}

func (c *TemporalHashChain) reconstructFork(from TemporalIndex) []TemporalIndex {
	// Simplificado: retorna índices sequenciais
	fork := make([]TemporalIndex, 0)
	for i := from; i >= 0; i-- {
		fork = append([]TemporalIndex{i}, fork...)
		if i == 0 {
			break
		}
	}
	return fork
}

// TemporalIterator itera sobre blocos temporais.
type TemporalIterator struct {
	chain  *TemporalHashChain
	index  TemporalIndex
	ascend bool
}

// Iterate retorna um iterador sobre a cadeia temporal.
func (c *TemporalHashChain) Iterate(ascend bool) *TemporalIterator {
	idx := TemporalIndex(0)
	if !ascend {
		c.mu.RLock()
		idx = c.longestChain[len(c.longestChain)-1]
		c.mu.RUnlock()
	}
	return &TemporalIterator{
		chain:  c,
		index:  idx,
		ascend: ascend,
	}
}

func (it *TemporalIterator) Next() (*TemporalBlock, error) {
	block, err := it.chain.Get(it.index)
	if err != nil {
		return nil, err
	}
	if it.ascend {
		it.index++
	} else {
		if it.index == 0 {
			return block, ErrBlockNotFound // fim da cadeia
		}
		it.index--
	}
	return block, nil
}

// Reconcile realiza reconciliação de forks (consenso).
func (c *TemporalHashChain) Reconcile(forkBlocks []*TemporalBlock) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	for _, block := range forkBlocks {
		if err := c.Append(block); err != nil && err != ErrBlockExists {
			// Tentar rebase
			if err == ErrOrphanBlock {
				continue // bloco órfão, ignorar por enquanto
			}
		}
	}

	return nil
}

// Event é um evento emitido pela cadeia.
type Event struct {
	Type      string
	BlockHash Address
	Index     TemporalIndex
	Timestamp Timestamp
	Data      map[string]interface{}
}

// Subscribe retorna um canal de eventos.
func (c *TemporalHashChain) Subscribe() chan Event {
	ch := make(chan Event, 100) // buffer de 100 eventos
	go func() {
		// Simulação: em produção, emitiria eventos reais
		defer close(ch)
	}()
	return ch
}

// StateSnapshot é um snapshot do estado da cadeia.
type StateSnapshot struct {
	Index        TemporalIndex
	StateRoot    Address
	MessageCount int
	Timestamp    Timestamp
	Hash         Address
}
